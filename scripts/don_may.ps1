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
  [switch]$Worktree,  # dừng MỌI tiến trình dev của worktree agent, kể cả đang giữ cổng
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

# Dưới ngần này GB trống thì máy sắp không thở được: Windows bắt đầu đổi trang, mọi thứ
# chậm lại, và lượt `next dev` kế tiếp có thể kéo cả máy xuống. Đo 27/09 trên máy anh Sơn:
# còn 1,5 GB / 15,9 GB vì SÁU máy chủ dev chạy cùng lúc (ba Django, ba Next; riêng một
# `next dev` của worktree agent giữ 3.047 MB). Anh Sơn: "toàn để bị OOM như này".
$NGUONG_GB = 3.0

# Tiến trình thuộc worktree agent (`D:/pe_hsa_wt/...`). Đây là chỗ `don_may.ps1` bản đầu
# nhìn sót: nó chia theo "có giữ cổng không", mà máy chủ dev của một agent ĐÃ DỪNG thì vẫn
# giữ cổng y như máy chủ đang được dùng. Giữ cổng là bằng chứng nó còn SỐNG, không phải
# bằng chứng còn ai CẦN nó. Hai thứ ấy khác nhau, và 3,9 GB nằm ở khoảng khác nhau đó.
# Tên `$MAU_WT` chứ không phải `$WORKTREE`: PowerShell KHÔNG phân biệt hoa thường cho tên
# biến, nên một hằng `$WORKTREE` sẽ đè thẳng lên tham số `-Worktree` và cả script đổ với
# "Cannot convert System.String to SwitchParameter" — ngay cả khi không ai truyền cờ ấy.
$MAU_WT = 'pe_hsa_wt'

# Cổng của BẢN DEV CHÍNH. Mọi cổng dev khác là của một worktree agent.
#
# Cần cả hai cách nhận, vì mỗi cách sót một nửa: `manage.py runserver 9600` chạy với thư
# mục làm việc là worktree nhưng dòng lệnh KHÔNG mang đường dẫn ấy, nên khớp chuỗi
# `pe_hsa_wt` không thấy nó (đo 27/09: Django 9600 lọt lưới trong khi Next 3600 thì không).
# Còn khớp theo cổng thì không thấy những tiến trình con không giữ cổng nào.
$CONG_CHINH = @(9000, 3100)

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
  # `$Ds` rỗng, hoặc một phần tử null lọt vào, thì `ContainsKey($null)` ném
  # "Key cannot be null" và cả script đổ — đúng lúc máy đang bẩn và người ta
  # cần nó nhất (agent E3 báo 26/09: "chạy được lúc máy sạch, đổ lúc cần").
  $Ds = @($Ds | Where-Object { $null -ne $_ -and $null -ne $_.Pid })
  if ($Ds.Count -eq 0) { return @{ Song = @(); Coi = @() } }
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

$troneGB = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
if ($troneGB -lt $NGUONG_GB) {
  Write-Host ("`n!! RAM TRỐNG CHỈ CÒN {0} GB (ngưỡng {1} GB) — dọn trước khi chạy thêm việc nặng." -f `
    $troneGB, $NGUONG_GB) -ForegroundColor Red
  Write-Host "   Máy chủ dev của worktree agent đã dừng vẫn giữ cổng: dùng -Worktree để dọn chúng."
}

$cuaWt = @($ds | Where-Object {
  $_.Lenh -match $MAU_WT -or
  ($_.Cong -and (($_.Cong -split ',') | Where-Object { $CONG_CHINH -notcontains [int]$_ }))
})
if ($cuaWt.Count -gt 0) {
  Write-Host "`n== CỦA WORKTREE AGENT (giữ cổng nhưng có thể không ai dùng) =="
  $cuaWt | Sort-Object MB -Descending | Format-Table Pid, Loai, MB, Cong, BatDau -AutoSize
  Write-Host ("  Tổng: {0} tiến trình, {1} MB. Agent đã xong thì dọn bằng -Don -Worktree." -f `
    $cuaWt.Count, (($cuaWt | Measure-Object MB -Sum).Sum))
}

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
if ($Worktree) {
  # Dọn cả cái ĐANG giữ cổng, miễn là của worktree agent. Lead gọi cái này sau mỗi lượt
  # agent; bỏ qua nó là cách 3,9 GB nằm lại trong máy suốt buổi mà không ai thấy.
  $tra += Stop-Nhom -Ds @($chia.Song | Where-Object {
    $_.Lenh -match $MAU_WT -or
    ($_.Cong -and (($_.Cong -split ',') | Where-Object { $CONG_CHINH -notcontains [int]$_ }))
  }) -Nhan 'worktree agent'
}
if ($CaCong) { $tra += Stop-Nhom -Ds $chia.Song -Nhan 'đang giữ cổng' }

Start-Sleep -Milliseconds 1200
$os2 = Get-CimInstance Win32_OperatingSystem
Write-Host ("`nRAM trống: {0} GB → {1} GB" -f `
  [math]::Round($os.FreePhysicalMemory / 1MB, 2), [math]::Round($os2.FreePhysicalMemory / 1MB, 2))
