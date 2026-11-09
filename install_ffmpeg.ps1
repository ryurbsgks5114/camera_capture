
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================"
Write-Host "  Camera Server - FFmpeg Setup"
Write-Host "========================================"
Write-Host ""

$ffmpegPath = $null
$ffmpegBin = $null

# ========================================
# 1. Check existing FFmpeg command
# ========================================

$existing = Get-Command ffmpeg.exe -CommandType Application -ErrorAction SilentlyContinue

if ($existing) {
    $ffmpegPath = $existing.Source
}

# ========================================
# 2. Check WinGet installation directory
# ========================================

if (!$ffmpegPath) {

    $wingetPackages = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"

    if (Test-Path $wingetPackages) {

        $found = Get-ChildItem `
            -Path $wingetPackages `
            -Filter "ffmpeg.exe" `
            -Recurse `
            -ErrorAction SilentlyContinue |
            Select-Object -First 1

        if ($found) {
            $ffmpegPath = $found.FullName
        }
    }
}

# ========================================
# 3. Download and install if not found
# ========================================

if (!$ffmpegPath) {

    Write-Host "[INFO] FFmpeg not found. Starting download."

    $ffmpegRoot = Join-Path $env:LOCALAPPDATA "Programs\FFmpeg"
    $zipPath = Join-Path $env:TEMP "ffmpeg-release-essentials.zip"

    $downloadUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

    Invoke-WebRequest `
        -Uri $downloadUrl `
        -OutFile $zipPath `
        -UseBasicParsing

    if (!(Test-Path $zipPath)) {
        throw "Download failed."
    }

    Write-Host "[INFO] Extracting FFmpeg."

    New-Item `
        -ItemType Directory `
        -Path $ffmpegRoot `
        -Force | Out-Null

    Expand-Archive `
        -Path $zipPath `
        -DestinationPath $ffmpegRoot `
        -Force

    $found = Get-ChildItem `
        -Path $ffmpegRoot `
        -Filter "ffmpeg.exe" `
        -Recurse |
        Where-Object { $_.Directory.Name -eq "bin" } |
        Select-Object -First 1

    if (!$found) {
        throw "ffmpeg.exe not found after extraction."
    }

    $ffmpegPath = $found.FullName
}

# ========================================
# 4. Register PATH
# ========================================

$ffmpegBin = Split-Path $ffmpegPath -Parent

Write-Host "[INFO] FFmpeg found:"
Write-Host $ffmpegPath

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")

$pathEntries = @(
    $userPath -split ";" |
    Where-Object { $_.Trim() -ne "" }
)

$alreadyRegistered = $false

foreach ($entry in $pathEntries) {
    if ($entry.TrimEnd("\") -ieq $ffmpegBin.TrimEnd("\")) {
        $alreadyRegistered = $true
        break
    }
}

if (!$alreadyRegistered) {

    if ([string]::IsNullOrWhiteSpace($userPath)) {
        $newPath = $ffmpegBin
    }
    else {
        $newPath = "$userPath;$ffmpegBin"
    }

    [Environment]::SetEnvironmentVariable(
        "Path",
        $newPath,
        "User"
    )
}

# Update current process PATH
if ($env:Path -notlike "*$ffmpegBin*") {
    $env:Path = "$ffmpegBin;$env:Path"
}

# ========================================
# 5. Test FFmpeg
# ========================================

Write-Host ""
Write-Host "[INFO] Testing FFmpeg."

& $ffmpegPath -version

if ($LASTEXITCODE -ne 0) {
    throw "FFmpeg execution failed."
}

Write-Host ""
Write-Host "========================================"
Write-Host "  FFmpeg Setup Completed"
Write-Host "========================================"
Write-Host ""
Write-Host "Restart the terminal or application to refresh PATH."
