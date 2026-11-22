$ErrorActionPreference = 'Stop'

function Save-VerifiedAsset($url, $path, $algorithm, $expected) {
  $parent = Split-Path -Parent $path
  New-Item -ItemType Directory -Force -Path $parent | Out-Null
  Invoke-WebRequest -Uri $url -OutFile $path
  $bytes = [IO.File]::ReadAllBytes((Resolve-Path $path).Path)
  $hash = [Security.Cryptography.HashAlgorithm]::Create($algorithm)
  try { $actual = [Convert]::ToBase64String($hash.ComputeHash($bytes)) }
  finally { $hash.Dispose() }
  if ($actual -cne $expected) { throw "Hash mismatch for $path" }
  Write-Output "Verified $path"
}

Save-VerifiedAsset 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css' 'static/vendor/bootstrap/bootstrap.min.css' 'SHA384' 'sRIl4kxILFvY47J16cr9ZwB07vP4J8+LH7qKQnuqkuIAvNWLzeN8tE5YBujZqJLB'
Save-VerifiedAsset 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js' 'static/vendor/bootstrap/bootstrap.bundle.min.js' 'SHA384' 'FKyoEForCGlyvwx9Hj09JcYn3nv7wiPVlz7YYwJrWVcXK/BmnVDxM+D2scQbITxI'
$sourceMaps = @(
  @{ Url = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css.map'; Path = 'static/vendor/bootstrap/bootstrap.min.css.map'; FileName = 'bootstrap.min.css' },
  @{ Url = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js.map'; Path = 'static/vendor/bootstrap/bootstrap.bundle.min.js.map'; FileName = 'bootstrap.bundle.min.js' }
)
foreach ($sourceMapAsset in $sourceMaps) {
  Invoke-WebRequest -Uri $sourceMapAsset.Url -OutFile $sourceMapAsset.Path
  $sourceMap = Get-Content $sourceMapAsset.Path -Raw | ConvertFrom-Json
  if ($sourceMap.version -ne 3 -or $sourceMap.sources.Count -eq 0 -or ($sourceMap.file -and $sourceMap.file -notlike "*$($sourceMapAsset.FileName)*")) {
    throw "Unexpected source map: $($sourceMapAsset.Path)"
  }
  Write-Output "Verified source map $($sourceMapAsset.Path)"
}
Save-VerifiedAsset 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css' 'static/vendor/leaflet/leaflet.css' 'SHA256' 'p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY='
Save-VerifiedAsset 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js' 'static/vendor/leaflet/leaflet.js' 'SHA256' '20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo='
$sourceMapPath = 'static/vendor/leaflet/leaflet.js.map'
Invoke-WebRequest -Uri 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js.map' -OutFile $sourceMapPath
$sourceMap = Get-Content $sourceMapPath -Raw | ConvertFrom-Json
if ($sourceMap.version -ne 3 -or $sourceMap.sources.Count -eq 0 -or $sourceMap.file -notlike '*.js.map') { throw 'Unexpected Leaflet source map.' }
Write-Output "Verified Leaflet source map $sourceMapPath"

$imageNames = @('layers.png', 'layers-2x.png', 'marker-icon.png', 'marker-icon-2x.png', 'marker-shadow.png')
New-Item -ItemType Directory -Force -Path 'static/vendor/leaflet/images' | Out-Null
foreach ($name in $imageNames) {
  $path = "static/vendor/leaflet/images/$name"
  Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/$name" -OutFile $path
  $bytes = [IO.File]::ReadAllBytes((Resolve-Path $path).Path)
  if ($bytes.Length -lt 8 -or [BitConverter]::ToString($bytes[0..7]).Replace('-', '') -ne '89504E470D0A1A0A') {
    throw "Invalid PNG signature for $path"
  }
  Write-Output "Verified PNG $path"
}

$licenses = @(
  @{ Url = 'https://raw.githubusercontent.com/twbs/bootstrap/v5.3.8/LICENSE'; Path = 'static/vendor/bootstrap/LICENSE.txt'; Marker = 'MIT License' },
  @{ Url = 'https://raw.githubusercontent.com/Leaflet/Leaflet/v1.9.4/LICENSE'; Path = 'static/vendor/leaflet/LICENSE.txt'; Marker = 'BSD 2-Clause License' }
)
foreach ($license in $licenses) {
  Invoke-WebRequest -Uri $license.Url -OutFile $license.Path
  if (-not (Get-Content $license.Path -Raw).Contains($license.Marker)) { throw "Unexpected license text in $($license.Path)" }
  Write-Output "Verified license $($license.Path)"
}
