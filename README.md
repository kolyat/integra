# Integra
[DRAFT]

Tool for multiplatform deployment, which supports:
- Windows
- Android
- *nix systems: macOS, Raspberry Pi OS, Debian/Ubuntu
- Samsung Tizen (SSSP)
- LG webOS: production-ready or debug packages
- web deployment in Docker container


### Requirements

1. Install [Android SDK platform tools](https://developer.android.com/tools/releases/platform-tools) or [scrcpy](https://github.com/Genymobile/scrcpy) in order to get ADB.


### Preparing platforms

##### Windows

1. Create ``C:\swap``
2. Run ``cmd`` as administrator
3. Execute the [following](https://ru.stackoverflow.com/questions/949887/%d0%91%d1%8b%d1%81%d1%82%d1%80%d0%be%d0%b5-%d1%80%d0%b0%d0%b7%d0%b2%d0%b5%d1%80%d1%82%d1%8b%d0%b2%d0%b0%d0%bd%d0%b8%d0%b5-ansible-%d0%bd%d0%b0-windows-%d1%85%d0%be%d1%81%d1%82%d0%b0%d1%85/949971#949971):
   ```
   powershell Set-ExecutionPolicy -ExecutionPolicy Unrestricted
   powershell Enable-PSRemoting
   sc \\localhost config winrm start= auto
   netsh firewall set icmpsetting 8
   netsh firewall set portopening TCP 5985 ENABLE
   netsh firewall set portopening TCP 5986 ENABLE
   winrm quickconfig /quiet && winrm set winrm/config/client/auth @{Basic="true"} && winrm set winrm/config/service/auth @{Basic="true"} && winrm set winrm/config/service @{AllowUnencrypted="true"}
   winrm enumerate winrm/config/listener
   ```
   
##### Android

1. Enable developer options.
2. Switch on USB debugging.
3. Enable ``Install via USB``.
4. Disable adb authorization timeout.
5. Switch off ```Verify apps over USB```.
6. Enable wireless debugging or run ``adb tcpip 5555``.

##### macOS

1. Go to ``System preferences``->``Sharing``.
2. Enable ``Remote Login``.
3. ``Allow access for`` an account that's going to be used.

##### Raspberry Pi OS

1. Go to ``Preferences``->``Raspberry Pi Configuration``.
2. Switch to ``Interfaces`` tab.
3. Enable ``SSH``.

##### Ubuntu

1. [Install](https://ubuntu.com/server/docs/service-openssh) and start ``openssh-server``.
2. Enable ``PasswordAuthentication`` in ``/etc/ssh/sshd_config``.
3. Execute ``sudo systemctl restart ssh``
