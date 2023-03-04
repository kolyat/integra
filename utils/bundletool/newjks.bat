keytool -genkeypair ^
  -alias als ^
  -keyalg RSA ^
  -keysize 2048 ^
  -keypass passwd ^
  -validity 365 ^
  -keystore default_aab_key.jks ^
  -storepass passwd
