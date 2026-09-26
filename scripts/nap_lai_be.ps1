# NẠP LẠI BACKEND — dừng Django đang giữ một cổng rồi bật lại, và CHỜ tới khi nó trả lời.
#
# VÌ SAO (26/09/2026). `manage.py runserver --noreload` không nạp mã mới, nên sửa
# backend xong mà quên tắt/bật lại thì màn hình vẫn chạy mã CŨ — và bộ đo báo
# "tính năng không dựng" trong khi mã hoàn toàn đúng. Sáng và chiều hôm ấy lead
# mất BA lượt đo vì đúng một lý do này, mỗi lượt mươi phút. Bẫy đã ghi trong
# brief agent từ trước mà vẫn vấp lại — nên nó cần một lệnh, không cần một lời
# nhắc.
#
#     powershell -File scripts/nap_lai_be.ps1            # cổng 9000 (bản dev chính)
#     powershell -File scripts/nap_lai_be.ps1 -Cong 9600 # cổng của một worktree agent
#
# Dùng CÙNG lệnh `runserver <cổng> --noreload` như trước, chỉ tự động hoá phần
# tắt–bật–chờ. Không đổi cách chạy sẵn có: `--noreload` vẫn là mặc định vì bản
# tự nạp lại chạy hai tiến trình và nhân đôi mọi luồng nền.

[CmdletBinding()]
param(
  [int]$Cong = 9000,
  [int]$ChoGiay = 40
)

$ErrorActionPreference = 'Stop'
$goc = Split-Path $PSScriptRoot -Parent

# Worktree của agent KHÔNG có `.venv` riêng — nó dùng venv của repo chính, và
# `git rev-parse --git-common-dir` là chỗ duy nhất biết repo chính nằm đâu (cổng
# pre-push cũng tìm bằng đúng câu ấy). Thiếu bước này thì script chạy ở gốc mà
# đổ ở mọi worktree — tức đổ đúng chỗ agent cần nó nhất (agent E3 báo 26/09).
$py = Join-Path $goc 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path $py)) {
  $chung = (& git -C $goc rev-parse --git-common-dir 2>$null)
  if ($chung) {
    # `--git-common-dir` trả đường TUYỆT ĐỐI ở worktree (`D:/pe_hsa/.git`) và đường TƯƠNG
    # ĐỐI ở repo thường (`.git`). Bản cũ nối thẳng vào `$goc` cho cả hai — mà `Join-Path`
    # của PowerShell 5.1 KHÔNG bỏ qua phần con khi phần con là đường tuyệt đối, nên ở
    # worktree ra một đường không tồn tại: `Resolve-Path` trả rỗng và script chết với
    # "Không thấy python của backend" ở CHÍNH tình huống nó sinh ra để cứu.
    #
    # Hai agent tìm ra chỗ này độc lập trong cùng một ngày, mỗi bên ở worktree của mình.
    # Một lệnh viết ra để chặn bẫy "`--noreload` không nạp mã mới" mà lại hỏng ở đúng
    # người cần nó nhất thì tệ hơn là không có lệnh ấy.
    if (-not [System.IO.Path]::IsPathRooted($chung)) { $chung = Join-Path $goc $chung }
    $chung = (Resolve-Path (Join-Path $chung '..') -ErrorAction SilentlyContinue)
    if ($chung) {
      $thu = Join-Path $chung 'backend\.venv\Scripts\python.exe'
      if (Test-Path $thu) { $py = $thu; "dùng venv của repo chính: $py" }
    }
  }
}
if (-not (Test-Path $py)) { Write-Error "Không thấy python của backend (thử cả repo chính)"; exit 1 }

# ── Dừng cái đang giữ cổng, và cả tiến trình cha của nó ──────────────────────
$giu = Get-NetTCPConnection -State Listen -LocalPort $Cong -ErrorAction SilentlyContinue
$ids = @()
if ($giu) { $ids += $giu.OwningProcess }
# `runserver` là một cặp tiến trình (bộ khởi động + bản chạy thật); giết mỗi cái
# giữ cổng thì cái kia sống tiếp và chiếm lại cổng ngay sau đó.
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match "runserver\s+$Cong\b" } |
  ForEach-Object { $ids += $_.ProcessId }

foreach ($p in ($ids | Sort-Object -Unique)) {
  try { Stop-Process -Id $p -Force -ErrorAction Stop; "dừng $p" } catch { }
}
Start-Sleep -Milliseconds 800

# ── Bật lại ──────────────────────────────────────────────────────────────────
$log = Join-Path $env:TEMP "pe_hsa_be_$Cong.log"
Start-Process -FilePath $py `
  -ArgumentList 'manage.py', 'runserver', "$Cong", '--noreload' `
  -WorkingDirectory (Join-Path $goc 'backend') `
  -RedirectStandardOutput $log -RedirectStandardError "$log.err" `
  -WindowStyle Hidden | Out-Null

# ── Chờ tới khi nó TRẢ LỜI, không chỉ tới khi tiến trình tồn tại ─────────────
# Django mất vài giây nạp ứng dụng; báo "xong" lúc tiến trình vừa sinh ra là lời
# hứa suông, và lượt đo ngay sau đó sẽ gặp lỗi kết nối.
$het = (Get-Date).AddSeconds($ChoGiay)
while ((Get-Date) -lt $het) {
  try {
    $r = Invoke-WebRequest -Uri "http://localhost:$Cong/health" -TimeoutSec 3 -UseBasicParsing
    if ($r.StatusCode -eq 200) {
      "Django cổng $Cong đã sẵn sàng (nhật ký: $log)"
      exit 0
    }
  } catch { Start-Sleep -Milliseconds 700 }
}
Write-Error "Cổng $Cong không trả lời sau $ChoGiay giây — xem $log.err"
exit 1
