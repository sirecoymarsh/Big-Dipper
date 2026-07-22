param([string]$GameDir = 'P:\SteamLibrary\steamapps\common\Big Dipper\WIN')
$ErrorActionPreference = 'Stop'

function Get-Sha256([string]$Path) {
    (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

$PatchDir = Join-Path $PSScriptRoot 'patch'
$ManifestPath = Join-Path $PSScriptRoot 'manifest.json'
$Manifest = Get-Content -Raw -Encoding UTF8 $ManifestPath | ConvertFrom-Json
$DataDir = Join-Path $GameDir 'Big Dipper_Data'
$Resources = Join-Path $DataDir 'resources.assets'
$Shared = Join-Path $DataDir 'sharedassets1.assets'
$BackupDir = Join-Path $GameDir '_KoreanPatchBackup'
$BackupResources = Join-Path $BackupDir 'resources.assets'
$BackupShared = Join-Path $BackupDir 'sharedassets1.assets'
$Marker = Join-Path $GameDir '.bigdipper-korean-installed'

if (Get-Process -Name 'Big Dipper' -ErrorAction SilentlyContinue) {
    throw '게임이 실행 중입니다. Big Dipper를 종료한 뒤 다시 설치해 주세요.'
}
if (!(Test-Path -LiteralPath (Join-Path $GameDir 'Big Dipper.exe'))) {
    throw "게임 실행 파일이 없습니다: $GameDir"
}
foreach ($path in @($Resources, $Shared)) {
    if (!(Test-Path -LiteralPath $path)) { throw "필수 게임 파일이 없습니다: $path" }
}

# 배포 파일 자체가 손상되거나 일부만 복사된 경우 게임을 건드리기 전에 중단한다.
foreach ($property in $Manifest.payload_files.PSObject.Properties) {
    $relative = $property.Name.Replace('/', [IO.Path]::DirectorySeparatorChar)
    $payload = Join-Path $PatchDir $relative
    if (!(Test-Path -LiteralPath $payload)) { throw "패치 파일이 없습니다: $relative" }
    if ((Get-Sha256 $payload) -ne ([string]$property.Value).ToLowerInvariant()) {
        throw "패치 파일 해시가 일치하지 않습니다: $relative"
    }
}

$originalR = ([string]$Manifest.original_resources_sha256).ToLowerInvariant()
$originalS = ([string]$Manifest.original_sharedassets1_sha256).ToLowerInvariant()
$patchedR = ([string]$Manifest.patched_resources_sha256).ToLowerInvariant()
$patchedS = ([string]$Manifest.patched_sharedassets1_sha256).ToLowerInvariant()
$currentR = Get-Sha256 $Resources
$currentS = Get-Sha256 $Shared
$ownedInstall = Test-Path -LiteralPath $Marker

if ((Test-Path -LiteralPath (Join-Path $GameDir 'winhttp.dll')) -and !$ownedInstall) {
    throw '다른 모드 로더가 발견되어 자동 설치를 중단합니다.'
}

# 이전 시험판이 설치되어 있으면 검증된 원본 백업으로 되돌린 뒤 새 버전을 적용한다.
if (($currentR -notin @($originalR, $patchedR)) -or ($currentS -notin @($originalS, $patchedS))) {
    $backupsValid = (Test-Path -LiteralPath $BackupResources) -and
                    (Test-Path -LiteralPath $BackupShared) -and
                    ((Get-Sha256 $BackupResources) -eq $originalR) -and
                    ((Get-Sha256 $BackupShared) -eq $originalS)
    if (!$ownedInstall -or !$backupsValid) {
        throw "지원하지 않는 게임 파일 버전입니다. resources=$currentR sharedassets1=$currentS"
    }
    Copy-Item -LiteralPath $BackupResources -Destination $Resources -Force
    Copy-Item -LiteralPath $BackupShared -Destination $Shared -Force
    $currentR = Get-Sha256 $Resources
    $currentS = Get-Sha256 $Shared
}

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
if (Test-Path -LiteralPath $BackupResources) {
    if ((Get-Sha256 $BackupResources) -ne $originalR) { throw 'resources.assets 원본 백업 해시가 올바르지 않습니다.' }
} elseif ($currentR -eq $originalR) {
    Copy-Item -LiteralPath $Resources -Destination $BackupResources
} else { throw 'resources.assets 원본 백업을 만들 수 없습니다.' }

if (Test-Path -LiteralPath $BackupShared) {
    if ((Get-Sha256 $BackupShared) -ne $originalS) { throw 'sharedassets1.assets 원본 백업 해시가 올바르지 않습니다.' }
} elseif ($currentS -eq $originalS) {
    Copy-Item -LiteralPath $Shared -Destination $BackupShared
} else { throw 'sharedassets1.assets 원본 백업을 만들 수 없습니다.' }

$tempFiles = @()
try {
    # 0.9 시험판의 구형 플러그인이 남아 있으면 중복 로딩을 막기 위해 제거한다.
    $legacyPlugin = Join-Path $GameDir 'BepInEx\plugins\BigDipperKorean'
    if ($ownedInstall -and (Test-Path -LiteralPath $legacyPlugin)) {
        $legacyFull = [IO.Path]::GetFullPath($legacyPlugin)
        $rootFull = [IO.Path]::GetFullPath($GameDir).TrimEnd('\') + '\'
        if ($legacyFull.StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $legacyFull -Recurse -Force
        }
    }

    # 두 대형 자산은 임시 파일에 복사·검증한 뒤 한 번에 교체한다.
    foreach ($entry in @(
        @{ Source = Join-Path $PatchDir 'Big Dipper_Data\resources.assets'; Target = $Resources; Hash = $patchedR },
        @{ Source = Join-Path $PatchDir 'Big Dipper_Data\sharedassets1.assets'; Target = $Shared; Hash = $patchedS }
    )) {
        $temp = $entry.Target + '.koreanpatch.tmp'
        $tempFiles += $temp
        Copy-Item -LiteralPath $entry.Source -Destination $temp -Force
        if ((Get-Sha256 $temp) -ne $entry.Hash) { throw "임시 파일 검증에 실패했습니다: $temp" }
        Move-Item -LiteralPath $temp -Destination $entry.Target -Force
    }

    # 나머지 로더·플러그인 파일을 설치한다.
    foreach ($property in $Manifest.payload_files.PSObject.Properties) {
        $relative = $property.Name.Replace('/', [IO.Path]::DirectorySeparatorChar)
        if ($relative -in @('Big Dipper_Data\resources.assets', 'Big Dipper_Data\sharedassets1.assets')) { continue }
        $source = Join-Path $PatchDir $relative
        $target = Join-Path $GameDir $relative
        $parent = Split-Path -Parent $target
        if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
        Copy-Item -LiteralPath $source -Destination $target -Force
        if ((Get-Sha256 $target) -ne ([string]$property.Value).ToLowerInvariant()) {
            throw "설치 파일 검증에 실패했습니다: $relative"
        }
    }

    if ((Get-Sha256 $Resources) -ne $patchedR -or (Get-Sha256 $Shared) -ne $patchedS) {
        throw '설치 후 Unity 자산 검증에 실패했습니다.'
    }

    # 플러그인 교체 후 BepInEx가 삭제된 구버전 DLL 정보를 계속 사용하는 일을 막는다.
    $cacheDir = Join-Path $GameDir 'BepInEx\cache'
    if (Test-Path -LiteralPath $cacheDir) {
        $cacheFull = [IO.Path]::GetFullPath($cacheDir)
        $rootFull = [IO.Path]::GetFullPath($GameDir).TrimEnd('\') + '\'
        if (!$cacheFull.StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'BepInEx 캐시 경로가 게임 폴더 밖을 가리킵니다.'
        }
        Remove-Item -LiteralPath $cacheFull -Recurse -Force
    }

    @{ version = $Manifest.patch_version; installed_utc = [DateTime]::UtcNow.ToString('o') } |
        ConvertTo-Json | Set-Content -LiteralPath $Marker -Encoding UTF8
}
catch {
    foreach ($temp in $tempFiles) { if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force } }
    if (Test-Path -LiteralPath $BackupResources) { Copy-Item -LiteralPath $BackupResources -Destination $Resources -Force }
    if (Test-Path -LiteralPath $BackupShared) { Copy-Item -LiteralPath $BackupShared -Destination $Shared -Force }
    throw
}

Write-Host "Big Dipper 한국어 패치 $($Manifest.patch_version) 설치 완료." -ForegroundColor Green
Write-Host '게임을 실행하면 한국어 슬롯이 자동으로 선택됩니다.'
