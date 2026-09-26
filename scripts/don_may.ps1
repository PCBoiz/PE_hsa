# DỌN MÁY — tìm và dừng tiến trình dev mồ côi của pe_hsa.
#
# VÌ SAO (26/09/2026). Anh Sơn: *"chạy duplicate tabs liên tục gây sập máy tôi"*.
# Đo lúc 09:51 trên máy anh (15,9 GB RAM):
#
#   · 12 tiến trình Python — trong đó BỐN cái `runserver 9300`, mà một cổng chỉ
#     một tiến trình bind được; ba cái kia sống vô ích từ 07:39;
#   · 10 tiến trình Node — hai bộ `next dev` (3100 và 3500), bộ 3500 thuộc một
#     worktree agent đã dừng từ lâu;
#   · 11 tiến trình Chromium giữ 788 MB cho MỘT tab trống.
#
# Dừng những cái mồ côi trả lại 0,63 GB ngay. Gốc rễ nằm ở `scripts/lib/phien_do.mjs`
# (bộ đo không đóng trình duyệt); tệp này là cái chổi cho phần đã lỡ rơi vãi.
#
#     powershell -File scripts/don_may.ps1              # CHỈ XEM, không đụng gì
#     powershell -File scripts/don_may.ps1 -Don         # dừng tiến trình mồ côi
#     powershell -File scripts/don_may.ps1 -Don -CaCong # dừng cả cái đang giữ cổng
#
# MẶC ĐỊNH KHÔNG GIẾT GÌ. Phải gõ `-Don` mới đụng vào tiến trình — một cái chổi
# tự quét khi chưa ai bảo thì nguy hơn là rác.

[CmdletBinding()]
param(
  [switch]$Don,       # thật sự dừng, thay vì chỉ liệt kê
  [switch]$CaCong,    # dừng cả tiến trình đang giữ cổng (dùng khi muốn dọn sạch)
  [switch]$Json       # in JSON cho bộ kiểm khác đọc
)

$ErrorActionPreference = 'Stop'

# ── Dữ liệu, không phải logic ────────────────────────────────────────────────
# Thêm một loại tiến trình mới = thêm một dòng ở đây. Không hàm nào phải sửa
# (SOLID · O). `Giu` là cổng mà tiến trình ấy PHẢI đang giữ mới đáng sống.
$QUY_TAC = @(
  @{ Ten = 'Django (backend)';  Dau = 'manage.py runserver'; Cong = @(9000, 9300, 9400, 9500) }
  # `next dev` đẻ ra ba tiến trình: npx → bin/next → start-server.js, và CHỈ cái
  # cuối bind cổng. Bỏ sót `start-server` thì hai cái kia thành "mồ côi" giả.
  @{ Ten = 'Next (frontend)';   Dau = 'next.*(dev|start-server|turbopack)'; Cong = @(3100, 3500, 3600) }
  @{ Ten = 'Playwright server'; Dau = 'playwright.*test-server'; Cong = @() }
  @{ Ten = 'Bộ đo (scripts)';   Dau = 'pe_hsa.scripts.do_';  Cong = @() }
)

# Tiến trình KHÔNG BAO GIỜ được đụng tới, dù khớp quy tắc nào.
$CAM = 'Code|claude|cursor|explorer|powershell|WindowsTerminal'

function Get-CongDangGiu {
  # PID → danh sách cổng nó đang nghe. Một lời gọi, dùng lại cho mọi quy tắc.
  $b = @{}
  foreach ($c in (Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue)) {
    if (-not $b.ContainsKey($c.OwningProcess)) { $b[$c.OwningProcess] = @() }
    if ($b[$c.OwningProcess] -notcontains $c.LocalPort) { $b[$c.OwningProcess] += $c.LocalPort }
  }
  return $b
}

function Get-TienTrinhDuAn {
  # Mọi node/python/chromium thuộc pe_hsa, kèm cổng đang giữ. CHỈ ĐỌC.
  param([hashtable]$Cong)
  $ra = @()
  $ds = Get-CimInstance Win32_Process -Filter "Name='node.exe' OR Name='python.exe' OR Name='chrome.exe'" -ErrorAction SilentlyContinue
  foreach ($p in $ds) {
    $cmd = $p.CommandLine
    if (-not $cmd) { continue }
    if ($cmd -notmatch 'pe_hsa|pe-hsa') { continue }
    if ($cmd -match $CAM) { continue }
    $loai = $null
    foreach ($r in $QUY_TAC) { if ($cmd -match $r.Dau) { $loai = $r; break } }
    if (-not $loai -and $p.Name -eq 'chrome.exe') {
      $loai = @{ Ten = 'Chromium (bộ đo)'; Cong = @() }
    }
    if (-not $loai) { continue }
    $ra += [pscustomobject]@{
      Pid     = [int]$p.ProcessId
      Cha     = [int]$p.ParentProcessId
      Loai    = $loai.Ten
      MB      = [math]::Round($p.WorkingSetSize / 1MB, 0)
      BatDau  = $p.CreationDate
      Cong    = ($Cong[[uint32]$p.ProcessId] -join ',')
      Lenh    = $cmd
    }
  }
  return $ra
}

function Split-MoCoi {
  # Chia làm hai: ĐANG DÙNG và MỒ CÔI. Chỉ phân loại, không giết.
  #
  # "Đang dùng" LAN THEO CẢ HAI CHIỀU trong cây tiến trình. Một lượt `next dev`
  # là ba tiến trình nối nhau (npx → bin/next → start-server) và chỉ cái CUỐI
  # bind cổng; giết cha là chết cả chùm. Ngược lại, `manage.py runserver` bind ở
  # cái CON. Nên: ai giữ cổng thì cả tổ tiên lẫn hậu duệ của nó đều đang dùng.
  #
  # Bản đầu của hàm này chỉ nhìn lên cha một nấc, và xếp nhầm hai tiến trình của
  # `next dev` cổng 3100 đang chạy vào nhóm mồ côi (đo 26/09, trước khi sửa).
  param([object[]]$Ds)
  $dung = @{}
  foreach ($t in $Ds) { if ($t.Cong) { $dung[$t.Pid] = $true } }
  for ($i = 0; $i -lt 8; $i++) {           # trần vòng lặp: cây tiến trình không sâu
    $them = $false
    foreach ($t in $Ds) {
      if ($dung.ContainsKey($t.Pid)) {
        if (-not $dung.ContainsKey($t.Cha) -and ($Ds | Where-Object { $_.Pid -eq $t.Cha })) {
          $dung[$t.Cha] = $true; $them = $true          # lên cha
        }
      } elseif ($dung.ContainsKey($t.Cha)) {
        $dung[$t.Pid] = $true; $them = $true            # xuống con
      }
    }
    if (-not $them) { break }
  }
  return @{
    Song = @($Ds | Where-Object { $dung.ContainsKey($_.Pid) })
    Coi  = @($Ds | Where-Object { -not $dung.ContainsKey($_.Pid) })
  }
}

function Stop-Nhom {
  param([object[]]$Ds, [string]$Nhan)
  $tong = 0
  foreach ($t in $Ds) {
    try {
      Stop-Process -Id $t.Pid -Force -ErrorAction Stop
      Write-Host ("  dừng  {0,-6} {1,-20} {2,5} MB" -f $t.Pid, $t.Loai, $t.MB)
      $tong += $t.MB
    } catch {
      Write-Host ("  bỏ qua {0,-6} (đã thoát)" -f $t.Pid)
    }
  }
  if ($tong -gt 0) { Write-Host ("  → {0}: trả lại ~{1} MB" -f $Nhan, $tong) }
  return $tong
}

# ── Chạy ─────────────────────────────────────────────────────────────────────
$cong = Get-CongDangGiu
$ds   = Get-TienTrinhDuAn -Cong $cong
$chia = Split-MoCoi -Ds $ds

if ($Json) {
  @{ song = $chia.Song; moCoi = $chia.Coi } | ConvertTo-Json -Depth 4
  exit 0
}

$os = Get-CimInstance Win32_OperatingSystem
Write-Host ("RAM: {0} GB trống / {1} GB" -f `
  [math]::Round($os.FreePhysicalMemory / 1MB, 2), [math]::Round($os.TotalVisibleMemorySize / 1MB, 1))

Write-Host "`n== ĐANG DÙNG (giữ cổng) =="
if ($chia.Song) {
  $chia.Song | Sort-Object Loai | Format-Table Pid, Loai, MB, Cong -AutoSize
} else { Write-Host "  (không có)" }

Write-Host "== MỒ CÔI (không giữ cổng nào) =="
if ($chia.Coi) {
  $chia.Coi | Sort-Object MB -Descending | Format-Table Pid, Loai, MB, BatDau -AutoSize
  Write-Host ("  Tổng: {0} tiến trình, {1} MB" -f $chia.Coi.Count, (($chia.Coi | Measure-Object MB -Sum).Sum))
} else { Write-Host "  (sạch)`n" }

if (-not $Don) {
  if ($chia.Coi) { Write-Host "`nCHỈ XEM. Thêm -Don để dừng những tiến trình trên." }
  exit 0
}

Write-Host "`n== DỌN =="
$tra = Stop-Nhom -Ds $chia.Coi -Nhan 'mồ côi'
if ($CaCong) { $tra += Stop-Nhom -Ds $chia.Song -Nhan 'đang giữ cổng' }

Start-Sleep -Milliseconds 1200
$os2 = Get-CimInstance Win32_OperatingSystem
Write-Host ("`nRAM trống: {0} GB → {1} GB" -f `
  [math]::Round($os.FreePhysicalMemory / 1MB, 2), [math]::Round($os2.FreePhysicalMemory / 1MB, 2))
