# Integra
[DRAFT]

Tool for multiplatform deployment of test packages, which supports:
- Windows
- Android
- *nix systems: macOS, Raspberry Pi OS, Debian-like systems, and others
- Samsung Tizen (SSSP)
- LG webOS: production-ready or debug packages
- web deployment in Docker container


## Requirements

### Operating system

Windows 7 or higher.

### Tools

1. [**Android SDK platform tools**](https://developer.android.com/tools/releases/platform-tools) or [**scrcpy**](https://github.com/Genymobile/scrcpy) in order to get ADB.
2. [**webOS CLI**](https://webostv.developer.lge.com/develop/tools/cli-installation).


## Keeping passwords

Use ``Set password`` feature to keep all necessary credentials.


## Settings

### config.yaml

``fileserver_url``: URL to a server where test packages are stored.

``username``: username to access file server (do not forget to set up password 
with ``setpwd`` utility).

``download_dir``: local directory for storing test packages.

``ptypes``: package types

``editions``: package editions

### devices.yaml

``name``: name of a device.

``cleanup``: perform clean-up procedure (uninstall previous version of a test 
package, remove residual data, clean deployment directory, etc.).

``ptype``: type of package (e.g., win64, arm).

``edition``: package's edition.

``remote``: local or remote deployment (for browser version only).

``host``: target host.

``port``: target port.

``cport``: port of Docker container (for browser version only).

``username``: username on a target host.

``upload_dir``: deployment directory.

``description``: description of a target.

### bundletool

Prepare _bundletool_ in order to deploy Android ``aab`` packages.

See ``/utils/bundletool/README`` for details.


## Preparing platforms

### Windows

1. Create ``C:\swap``
2. Run ``cmd`` as administrator
3. Execute the [**following**](https://ru.stackoverflow.com/questions/949887/%d0%91%d1%8b%d1%81%d1%82%d1%80%d0%be%d0%b5-%d1%80%d0%b0%d0%b7%d0%b2%d0%b5%d1%80%d1%82%d1%8b%d0%b2%d0%b0%d0%bd%d0%b8%d0%b5-ansible-%d0%bd%d0%b0-windows-%d1%85%d0%be%d1%81%d1%82%d0%b0%d1%85/949971#949971):
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
   
### Android

1. Enable developer options.
2. Switch on USB debugging.
3. Enable ``Install via USB``.
4. Disable adb authorization timeout.
5. Switch off ```Verify apps over USB```.
6. Enable wireless debugging or run ``adb tcpip 5555``.

### macOS

1. Go to ``System preferences``->``Sharing``.
2. Enable ``Remote Login``.
3. ``Allow access for`` an account that's going to be used.

### Raspberry Pi OS

1. Go to ``Preferences``->``Raspberry Pi Configuration``.
2. Switch to ``Interfaces`` tab.
3. Enable ``SSH``.

### Ubuntu

1. Install and start 
[**openssh-server**](https://ubuntu.com/server/docs/service-openssh).
2. Enable ``PasswordAuthentication`` in ``/etc/ssh/sshd_config``.
3. Execute ``sudo systemctl restart ssh``

### Tizen

1. Make sure that target host is available by SMB and does not 
require authentication.
2. _URL launcher_ of target device is configured properly.

### webOS

1. Make sure that target host is available by SMB and does not 
require authentication.
2. _SI Server_ settings of target device are configured properly.

For debug packages:
1. Enable Developer mode on target device.
2. Register device with ``ares-setup-device``.
3. Get SSH key from device
with ``ares-novacom --device target_device --getkey``.
4. Update device (add passphrase and key path) with ``ares-setup-device``. 

### Browser version

1. Prepare target host with Ubuntu (see _Ubuntu_ section).
2. Install [**Docker engine**](https://docs.docker.com/engine/install/ubuntu/).
3. Get nginx image: ``sudo docker image pull nginx``.
4. [**Set up**](https://stackoverflow.com/questions/44411828/cannot-connect-to-the-docker-daemon-port-2375)
Docker daemon.
