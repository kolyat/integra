set author=Kolyat

pyinstaller --clean integra.spec

mkdir ".\dist\utils"
mkdir ".\dist\utils\bundletool"

mdpdf --author %author% ^
  --title "Integra general README" ^
  --output ".\dist\README.pdf" ^
  "README.md"
mdpdf --author %author% ^
  --title "Integra bundletool README" ^
  --output ".\dist\utils\bundletool\README.pdf" ^
  ".\utils\bundletool\README.md"

copy /y ".\utils\bundletool\*.*" ".\dist\utils\bundletool"
copy /y "config.yaml" ".\dist"
copy /y "devices.yaml" ".\dist"
copy /y "LICENSE" ".\dist"
