param(
    [Parameter(Mandatory=$true)][string]$ArchivePath,
    [Parameter(Mandatory=$true)][string]$ExtractRoot,
    [string]$OutputDir = ".\ice_lut_build",
    [string]$PortableZip = ".\Firecloud-Ice-Optics-Portable-V1.zip"
)

$ErrorActionPreference = "Stop"
$ExpectedMd5 = "2fb9bbab2c2c735a869c863a680e2f70"

if (-not (Test-Path -LiteralPath $ArchivePath)) {
    throw "Archive not found: $ArchivePath"
}

Write-Host "[1/4] Verifying published MD5..."
$ActualMd5 = (Get-FileHash -LiteralPath $ArchivePath -Algorithm MD5).Hash.ToLowerInvariant()
if ($ActualMd5 -ne $ExpectedMd5) {
    throw "MD5 mismatch. Expected $ExpectedMd5, got $ActualMd5. Refusing authoritative build."
}
Write-Host "MD5 PASS: $ActualMd5"

Write-Host "[2/4] Extracting Yang/Bi V2 shortwave archive..."
New-Item -ItemType Directory -Force -Path $ExtractRoot | Out-Null
& tar -xzf $ArchivePath -C $ExtractRoot
if ($LASTEXITCODE -ne 0) { throw "tar extraction failed with exit code $LASTEXITCODE" }

Write-Host "[3/4] Running PhysicsCore authoritative source/LUT QA gate..."
& python tools/build_authoritative_ice_optics_lut.py `
    --archive $ArchivePath `
    --source-root $ExtractRoot `
    --output-dir $OutputDir `
    --portable-zip $PortableZip
if ($LASTEXITCODE -ne 0) {
    throw "Authoritative Ice LUT build gate failed with exit code $LASTEXITCODE. Inspect $OutputDir."
}

Write-Host "[4/4] COMPLETE"
Write-Host "QA output: $OutputDir"
Write-Host "Portable package: $PortableZip"
Write-Host "Do not promote Ice Optics into Formation/Viewing/Glow until the separate Phase-3 release gate."
