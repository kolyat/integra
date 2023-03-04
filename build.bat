pyinstaller --clean ./utils/setpwd.spec
pyinstaller --clean integra.spec

mkdir ".\dist\utils"
mkdir ".\dist\utils\bundletool"

move /y ".\dist\setpwd.exe" ".\dist\utils"
copy /y ".\utils\bundletool\*.*" ".\dist\utils\bundletool"
copy /y "config.yaml" ".\dist"
copy /y "devices.yaml" ".\dist"
copy /y "LICENSE" ".\dist"
