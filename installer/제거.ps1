param([string]$GameDir = 'P:\SteamLibrary\steamapps\common\Big Dipper\WIN')
$ErrorActionPreference = 'Stop'

function Get-Sha256([string]$Path) {
    (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

$Manifest = Get-Content -Raw -Encoding UTF8 (Join-Path $PSScriptRoot 'manifest.json') | ConvertFrom-Json
$BackupDir = Join-Path $GameDir '_KoreanPatchBackup'
$Resources = Join-Path $GameDir 'Big Dipper_Data\resources.assets'
$Shared = Join-Path $GameDir 'Big Dipper_Data\sharedassets1.assets'
$BackupResources = Join-Path $BackupDir 'resources.assets'
$BackupShared = Join-Path $BackupDir 'sharedassets1.assets'
$Marker = Join-Path $GameDir '.bigdipper-korean-installed'

if (Get-Process -Name 'Big Dipper' -ErrorAction SilentlyContinue) {
    throw '게임이 실행 중입니다. Big Dipper를 종료한 뒤 다시 제거해 주세요.'
}
foreach ($entry in @(
    @{ Path = $BackupResources; Hash = ([string]$Manifest.original_resources_sha256).ToLowerInvariant() },
    @{ Path = $BackupShared; Hash = ([string]$Manifest.original_sharedassets1_sha256).ToLowerInvariant() }
)) {
    if (!(Test-Path -LiteralPath $entry.Path)) { throw "원본 백업이 없습니다: $($entry.Path)" }
    if ((Get-Sha256 $entry.Path) -ne $entry.Hash) { throw "원본 백업 해시가 올바르지 않습니다: $($entry.Path)" }
}

foreach ($entry in @(
    @{ Source = $BackupResources; Target = $Resources; Hash = ([string]$Manifest.original_resources_sha256).ToLowerInvariant() },
    @{ Source = $BackupShared; Target = $Shared; Hash = ([string]$Manifest.original_sharedassets1_sha256).ToLowerInvariant() }
)) {
    $temp = $entry.Target + '.koreanpatch.restore.tmp'
    Copy-Item -LiteralPath $entry.Source -Destination $temp -Force
    if ((Get-Sha256 $temp) -ne $entry.Hash) { throw "복원용 임시 파일 검증에 실패했습니다: $temp" }
    Move-Item -LiteralPath $temp -Destination $entry.Target -Force
}

if ((Get-Sha256 $Resources) -ne ([string]$Manifest.original_resources_sha256).ToLowerInvariant() -or
    (Get-Sha256 $Shared) -ne ([string]$Manifest.original_sharedassets1_sha256).ToLowerInvariant()) {
    throw '원본 복원 후 해시 검증에 실패했습니다.'
}

# 설치 표식이 있을 때만 이 패치가 소유한 로더를 제거한다.
if (Test-Path -LiteralPath $Marker) {
    foreach ($name in @('winhttp.dll', 'doorstop_config.ini', '.doorstop_version', 'changelog.txt')) {
        $path = Join-Path $GameDir $name
        if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
    }
    $bep = [IO.Path]::GetFullPath((Join-Path $GameDir 'BepInEx'))
    $root = [IO.Path]::GetFullPath($GameDir).TrimEnd('\') + '\'
    if ((Test-Path -LiteralPath $bep) -and $bep.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $bep -Recurse -Force
    }
    Remove-Item -LiteralPath $Marker -Force
}

Write-Host '한국어 패치를 제거하고 두 Unity 자산을 원본으로 복원했습니다.' -ForegroundColor Green
