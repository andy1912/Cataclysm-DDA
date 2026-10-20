# Package "Cataclysm Saigon" for Windows after a Release x64 build of
# msvc-full-features\Cataclysm-vcpkg-static.sln (see doc/saigon/BUILD_PACKAGES.md).
#   powershell -ExecutionPolicy Bypass -File tools\saigon\package_windows.ps1 0.1.0
# Uses upstream's build-scripts\windist.ps1 to lay out bindist\, then makes the Saigon changes in
# the package only (the repo is not changed): dda + saigon_2000s preselected, the playtest cheat mod
# left out, the player README, the CC-Sounds pack when sound\CC-Sounds exists.  Uploads nothing.
param( [string]$Version = "0.1.0" )
$ErrorActionPreference = "Stop"
Set-Location ( Join-Path $PSScriptRoot "..\.." )

if ( -not ( Test-Path "cataclysm-tiles.exe" ) ) {
    throw "cataclysm-tiles.exe not found: build the Release x64 solution first"
}
# windist.ps1 copies lang\mo; this fork ships no translations yet
New-Item -ItemType Directory -Force -Path "lang\mo" | Out-Null
"Cataclysm Saigon $Version (windows-x64)`ncommit sha: $( git rev-parse HEAD )" | Set-Content "VERSION.txt"
.\build-scripts\windist.ps1
Remove-Item "cataclysmdda-0.J.zip" -ErrorAction SilentlyContinue

$d = "bindist"
Remove-Item -Recurse -Force "$d\data\mods\saigon_playtest" -ErrorAction SilentlyContinue
$default = "$d\data\mods\default.json"
( Get-Content $default -Raw ) -replace '"dependencies": \[[^\]]*\]', '"dependencies": [ "dda", "saigon_2000s" ]' |
    Set-Content $default -NoNewline
if ( -not ( Select-String -Path $default -Pattern '"saigon_2000s"' -Quiet ) ) {
    throw "could not set the default mods"
}
Copy-Item "doc\saigon\RELEASE_README.md" "$d\README.md" -Force
if ( Test-Path "sound\CC-Sounds" ) {
    Copy-Item -Recurse -Force "sound\CC-Sounds" "$d\data\sound\CC-Sounds"
} else {
    Write-Host "note: sound\CC-Sounds not found, packaging without a soundpack"
}
Remove-Item "VERSION.txt"

$zip = "..\CataclysmSaigon-$Version-windows-x64.zip"
Compress-Archive -Force -Path "$d\*" -DestinationPath $zip
( Get-FileHash $zip -Algorithm SHA256 ).Hash.ToLower() + "  CataclysmSaigon-$Version-windows-x64.zip" |
    Set-Content "$zip.sha256"
Write-Host "done: $( Resolve-Path $zip )"
