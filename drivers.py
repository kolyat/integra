from typing import Union, Any
import subprocess
import os
import abc
import keyring
import shutil
import zipfile

import smbclient.shutil
import wmi
import winrm
from ppadb.client import Client as AdbClient
from ppadb import InstallError
import paramiko
import docker

from utils import log
import config


class Driver(log.Logger):
    """Common driver class.

    :ivar device: dict with device's data
    :ivar package: str with package's file name
    :ivar client: client to interact with device
    :ivar obj: device's object
    :ivar dest: destination (working) directory/path
    """
    def __init__(self, device: dict, package: str):
        super().__init__()
        self.device = device
        self.package = package
        self.client = None
        self.obj = None
        self.dest = None

    @abc.abstractmethod
    def connect(self) -> Union[Any, None]:
        """Connect to remote device.

        :return: device object
        :rtype: Union[Any, None]
        """
        pass

    @abc.abstractmethod
    def cleanup(self) -> bool:
        """
        - Close existing application.
        - Perform clean-up on a remote device (uninstall previous version,
        remove residual data, reset permissoins, etc.) if self.clean == True

        :return: result of operation
        :rtype: bool
        """
        pass

    @abc.abstractmethod
    def install(self) -> bool:
        """Install package to specified device.

        :return: True on success and False on failure
        :rtype: bool
        """
        pass

    def deploy(self) -> bool:
        """Deploy package to specified device:
        1. Connect to device.
        2. Perform clean-up procedure.
        2. Install specified package to connected device.

        :return: True on success and False on failure
        :rtype: bool
        """
        result = False
        if self.connect():
            if self.device['cleanup']:
                self.cleanup()
            if self.install():
                result = True
        if result:
            self.printl('+ + + + + + Deployment succeeded')
        else:
            self.printl('! ! ! ! ! ! Deployment failed')
        return result

    @staticmethod
    def run_proc(*args, **kwargs) -> subprocess.CompletedProcess:
        """Run shell subprocess.

        :return: object of completed process
        :rtype: subprocess.CompletedProcess
        """
        return subprocess.run(
            *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            universal_newlines=True,
            **kwargs
        )


class Nix(Driver):
    """Common driver for *nix systems.
    """
    def connect(self) -> Union[Any, None]:
        self.printl(
            f'connecting to {self.device["host"]}:{self.device["port"]} ...')
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.device['host'],
                port=self.device['port'],
                username=self.device['username'],
                password=keyring.get_password('system',
                                              self.device['username'])
            )
            self.printl(f'connected to {self.device["name"]} via SSH')
            return self.client
        except Exception as e:
            self.printl('failed to connect')
            self.printl(str(e))
            return None

    def cleanup(self) -> bool:
        pass

    def install(self) -> bool:
        pass

    def upload(self, upload_path: str) -> None:
        """Upload package to remote host.

        :param upload_path: full path, which includes both destination dir and
                            filename
        :type upload_path: str
        """
        self.printl(f'copying to destination {upload_path} ...')
        sftp = self.client.open_sftp()
        sftp.put(os.path.join(config.conf['download_dir'], self.package),
                 upload_path)
        sftp.close()
        self.printl('done')

    def exec(self, cmd: str, passwd: str = None) -> None:
        """Execute one command on a server.

        :param cmd: shell command
        :type cmd: str

        :param passwd: password for sudo (None by default)
        :type passwd: str
        """
        session = self.client.get_transport().open_session()
        session.set_combine_stderr(True)
        session.get_pty()
        stdin = session.makefile('wb', -1)
        stdout = session.makefile('rb', -1)
        session.exec_command(cmd)
        if passwd:
            stdin.write(f'{passwd}\n')
            stdin.flush()
        for r in stdout.readlines():
            l = r.decode().rstrip('\n')
            self.printl(l)
        session.close()


class Windows(Driver):
    """Driver for Windows devices.
    """
    def connect(self):
        self.printl(f'connecting to {self.device["host"]} ...')
        try:
            smbclient.register_session(
                self.device['host'],
                username=self.device['username'],
                password=keyring.get_password('system',
                                              self.device['username'])
            )
            # self.client = wmi.WMI(
            #     self.device['host'],
            #     user=self.device['username'],
            #     password=keyring.get_password('system',
            #                                   self.device['username'])
            # )
            # self.printl(f'connected to '
            #             f'{self.client.Win32_OperatingSystem()[0].Caption}')
            self.client = winrm.Session(
                self.device['host'],
                auth=(
                    self.device['username'],
                    keyring.get_password('system', self.device['username'])
                )
            )
            self.printl('connected')
        except Exception as e:
            self.printl('unable to connect')
            self.printl(str(e))
            return None

        self.dest = os.path.join(
            r'\\', self.device['host'], self.device['upload_dir']
        )
        if not smbclient.path.isdir(self.dest):
            self.printl(f'{self.dest} is not available')
            return None
        return self.client

    def cleanup(self) -> bool:
        # TODO: uninstall previous version
        # TODO: remove residual data
        return True

    def install(self) -> bool:
        try:
            self.printl(f'uploading {self.package} ...')
            smbclient.shutil.copy(
                os.path.join(config.conf['download_dir'], self.package),
                self.dest
            )
            self.printl(f'uploaded to {self.dest}')
        except Exception as e:
            self.printl('uploading failed')
            self.printl(str(e))
            return False

        package = os.path.join('C:', os.sep, self.device['upload_dir'],
                               self.package)
        cmd = f'{package} /VERYSILENT /SUPPRESSMSGBOXES /NOCANCEL ' \
              f'/CURRENTUSER /LOWESTPRIVILEGES=true'
        self.printl(f'installing {self.package} ...')
        # _, rvalue = self.obj.Win32_Process.Create(CommandLine=cmd)
        result = self.client.run_cmd(package, cmd.split(' '))
        rvalue = result.status_code

        if rvalue:
            self.printl(f'something went wrong, rvalue={rvalue}')
            self.printl(result.std_err)
            return False
        self.printl(f'installation launched')
        return True


class Android(Driver):
    """Driver for Android devices.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_proc('adb start-server')
        self.client = AdbClient(host='127.0.0.1', port=5037)

    def connect(self):
        self.printl(f'connecting to '
                    f'{self.device["host"]}:{self.device["port"]} ... ')
        if self.client.remote_connect(
                self.device['host'], self.device['port']):
            self.printl('connected')
        else:
            self.printl('unable to connect')
            return None
        self.obj = \
            self.client.device(f'{self.device["host"]}:{self.device["port"]}')
        return self.obj

    def cleanup(self) -> bool:
        self.obj.uninstall(config.EDITIONS[self.device['edition']])
        return True

    def install(self) -> bool:
        self.printl(f'installing {self.package} ...')
        try:
            if self.device['ptype'] == 'aab':
                aab = os.path.join(config.conf["download_dir"], self.package)
                bundletool = os.path.abspath(config.conf["bundletool"])
                aab_key = os.path.abspath(config.conf["aab_key"])
                apks = os.path.join(config.conf['download_dir'], "target.apks")

                if os.path.exists(apks):
                    os.remove(apks)

                proc = self.run_proc(
                    f'java -jar {bundletool} build-apks '
                    f'--bundle="{aab}" '
                    f'--output="{apks}" '
                    f'--overwrite '
                    f'--ks="{aab_key}" '
                    f'--ks-pass=pass:passwd '
                    f'--ks-key-alias=als '
                    f'--connected-device '
                    f'--device-id="{self.obj.serial}"'
                )
                if proc.returncode:
                    self.printl(proc.stderr)
                    raise InstallError(self.package,
                                       'failed to build target.apks')

                proc = self.run_proc(
                    f'java -jar {bundletool} install-apks '
                    f'--apks="{apks}" '
                    f'--device-id="{self.obj.serial}"'
                )
                if proc.returncode:
                    self.printl(proc.stderr)
                    raise InstallError(self.package,
                                       'failed to install target.apks')
            else:
                self.obj.install(
                    os.path.join(config.conf['download_dir'], self.package),
                    reinstall=True,
                    downgrade=True
                )
            self.printl(f'successfully installed {self.package}')
            return True
        except InstallError as e:
            self.printl(f'failed to install {self.package}')
            self.printl(str(e))
            return False


class MacOS(Nix):
    """Driver for macOS.
    """
    def cleanup(self) -> bool:
        # TODO: uninstall previous version
        # TODO: remove residual data
        return True

    def install(self) -> bool:
        working_dir = f'/Users/{self.device["username"]}/Downloads'
        pkg = f'{working_dir}/{self.package}'

        self.upload(pkg)

        self.printl(f'installing {self.package} ...')
        self.exec(
            f'sudo installer -allowUntrusted -pkg {pkg} -target /Applications',
            keyring.get_password('system', self.device['username'])
        )

        return True


class Linux(Nix):
    """Driver for Linux systems.
    """
    def cleanup(self) -> bool:
        # TODO: uninstall previous version
        # TODO: find, remove residual data
        return True

    def install(self) -> bool:
        home_dir = f'/home/{self.device["username"]}'
        working_dir = f'{home_dir}/Downloads'
        pkg = f'{working_dir}/{self.package}'
        player_dir = f'{home_dir}/{self.package.rstrip(".zip")}'

        self.printl('closing previous version')
        self.exec(
            f'pkill '
            f'{config.EDITIONS[self.device["edition"]]["linux"]["proc"]}'
        )

        self.printl(f'preparing {player_dir} ...')
        self.exec(f'rm -rf {player_dir} ; mkdir {player_dir}')
        self.printl(f'done')

        self.upload(pkg)

        self.printl(f'extracting {self.package} ...')
        self.exec(f'unzip {pkg} -d {player_dir}')
        self.printl(f'extracted to {player_dir}')

        self.printl('launching application')
        self.exec(
            f'DISPLAY=:0 nohup {player_dir}/./'
            f'{config.EDITIONS[self.device["edition"]]["linux"]["app"]}'
        )

        return True


class Raspbian(Nix):
    """Driver for Raspbian.
    """
    def cleanup(self) -> bool:
        # TODO: uninstall previous version
        # TODO: find, remove residual data
        return True

    def install(self) -> bool:
        working_dir = f'/home/{self.device["username"]}/Desktop'
        pkg = f'{working_dir}/{self.package}'

        self.printl('closing previous version')
        self.exec(
            f'pkill '
            f'{config.EDITIONS[self.device["edition"]]["raspbian"]["proc"]}'
        )

        self.upload(pkg)

        self.exec(
            f'chmod a+x {pkg} ; '
            f'cd {working_dir} ; '
            f'DISPLAY=:0 nohup ./{self.package}'
        )
        self.printl('application is being launched')

        return True


class Debian(Nix):
    """Driver for Debian-based systems (e. g., Ubuntu).
    """
    def cleanup(self) -> bool:
        # TODO: uninstall previous version
        # TODO: find, remove residual data
        return True

    def install(self) -> bool:
        working_dir = f'/home/{self.device["username"]}/Downloads'
        pkg = f'{working_dir}/{self.package}'

        self.upload(pkg)

        pwd = keyring.get_password('system', self.device['username'])

        self.printl('closing previous version')
        self.exec(
            f'pkill '
            f'{config.EDITIONS[self.device["edition"]]["ubuntu"]["proc"]}'
        )

        self.printl('installing application...')
        self.exec(f'sudo dpkg -i {pkg}', pwd)

        self.printl('launching application')
        self.exec(
            f'DISPLAY=:0 nohup '
            f'{config.EDITIONS[self.device["edition"]]["ubuntu"]["app"]}'
        )

        return True


class SharedHost(Driver):
    """Deployment to shared host (shared_host in config.yaml)
    """
    def connect(self) -> Union[Any, None]:
        self.dest = \
            f'\\\\{config.conf["shared_host"]}{self.device["upload_dir"]}'
        self.printl(f'checking {self.dest} ...')
        try:
            smbclient.ClientConfig(require_secure_negotiate=False)
            smbclient.register_session(config.conf['shared_host'],
                                       require_signing=False)
        except Exception as e:
            self.printl('unable to connect')
            self.printl(str(e))
            return None
        if not smbclient.path.isdir(self.dest):
            self.printl(f'{self.dest} is not available')
            return None
        self.printl('path found')
        return self.dest

    def cleanup(self) -> bool:
        self.printl(f'removing all data in {self.dest} ...')
        for root, dirs, files in smbclient.walk(self.dest):
            for f in files:
                smbclient.unlink(os.path.join(root, f))
            for d in dirs:
                smbclient.shutil.rmtree(os.path.join(root, d))
        self.printl(f'successfully cleaned')
        return True

    def install(self) -> bool:
        self.printl(f'extracting {self.package} ...')
        package = \
            zipfile.ZipFile(os.path.join(config.conf['download_dir'],
                                         self.package))
        package.extractall(path=self.dest)
        self.printl(f'extracted to {self.dest}')
        package.close()
        return True


class Tizen(SharedHost):
    """Driver for Samsung Smart Signage Platform (Tizen).
    """
    pass


class WebOS(SharedHost):
    """Driver for LG webOS Signage.
    Installs production package.
    """
    def install(self) -> bool:
        self.printl(f'copying {self.package} ...')
        smbclient.shutil.copy(
            os.path.join(config.conf['download_dir'], self.package),
            f'{self.dest}\\Player.ipk'
        )
        self.printl(f'copied to {self.dest}\\Player.ipk')
        return True


class WebOSdebug(Driver):
    """Driver for LG webOS Signage.
    Installs debug package.

    :ivar aid: application ID
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aid = None

    def get_aid(self) -> Union[str, None]:
        """Get application ID.

        :return: APP_ID
        :rtype: Union[str, None]
        """
        proc = self.run_proc(
            f'ares-install --device {self.device["name"]} --list')
        if proc.returncode:
            self.printl(proc.stderr)
            return None
        else:
            if 'com.lg.app.signage.dev' in proc.stdout:
                self.aid = proc.stdout.rstrip('\n')
                self.printl(f'found {self.aid}')
                return self.aid
            else:
                self.printl('no target application found')
                return None

    def connect(self) -> Union[Any, None]:
        self.printl(f'setting up {self.device["name"]}...')
        phrase = keyring.get_password('system', self.device['name'])
        info = f"'name':'{self.device['name']}'," \
               f"'host':'{self.device['host']}'," \
               f"'port':'{self.device['port']}'," \
               f"'username':'{self.device['username']}'," \
               f"'description':'{self.device['description']}'," \
               f"'privatekey':'{self.device['name']}','" \
               f"'passphrase':'{phrase}'"
        proc = self.run_proc(
            f'ares-setup-device --add {self.device["name"]} '
            f'--info "{{{info}}}"'
        )
        self.get_aid()
        if proc.returncode:
            pass
            # self.printl(proc.stderr)
        else:
            self.printl(proc.stdout)
        return True

    def cleanup(self) -> bool:
        if not self.aid:
            self.printl('previous version not found, skipping clean-up')
            return True

        proc = self.run_proc(
            f'ares-launch --device {self.device["name"]} --close {self.aid}')
        if proc.returncode:
            self.printl(proc.stderr)
        else:
            self.printl(proc.stdout)

        proc = self.run_proc(
            f'ares-install --device {self.device["name"]} --remove {self.aid}')
        if proc.returncode:
            self.printl(proc.stderr)
            return False
        self.printl(proc.stdout)

        self.printl('application closed and removed')
        return True

    def install(self) -> bool:
        self.printl(f'installing {self.package} ...')
        proc = self.run_proc(
            f'ares-install --device {self.device["name"]} '
            f'{os.path.join(config.conf["download_dir"], self.package)}'
        )
        if proc.returncode:
            self.printl('installation failed')
            self.printl(proc.stderr)
            return False
        else:
            self.printl('installation successful')
            self.get_aid()
            proc2 = self.run_proc(
                f'ares-launch --device {self.device["name"]} {self.aid}')
            if proc2.returncode:
                self.printl(proc2.stderr)
                return False
            else:
                self.printl(proc2.stdout)
        return True


class Web(Nix):
    """Driver for web version.

    :ivar dclient: docker client
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dclient = None

    def connect(self):
        self.dest = self.device['upload_dir']
        base_url = f'tcp://{self.device["host"]}:2375'
        try:
            self.printl(f'connecting to docker daemon at {base_url}')
            self.dclient = docker.DockerClient(
                base_url=base_url,
                tls=False,
                use_ssh_client=False
            )
            self.printl(f'daemon present')
            try:
                self.obj = self.dclient.containers.get(self.device['name'])
                self.obj.stop()
                self.obj.remove()
                self.printl(f'removed expired container {self.obj.short_id}')
            except Exception as e:
                self.printl(str(e))
        except Exception as e:
            self.printl(str(e))
            return None
        if self.device['remote']:
            return super().connect()
        else:
            return self.dclient

    def cleanup(self) -> bool:
        self.printl(f'preparing {self.dest} ...')
        if self.device['remote']:
            self.client.exec_command(f'rm -rf {self.dest} ; mkdir {self.dest}')
        else:
            if not os.path.isdir(self.dest):
                os.mkdir(self.dest)
            else:
                for root, dirs, files in os.walk(self.dest):
                    for f in files:
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d))
        self.printl(f'done')
        return True

    def install(self) -> bool:
        self.printl(f'extracting {self.package} ...')
        lpkg = os.path.join(config.conf['download_dir'], self.package)
        if self.device['remote']:
            rpkg = f'{self.dest}/{self.package}'
            sftp = self.client.open_sftp()
            sftp.put(lpkg, rpkg)
            sftp.close()
            self.client.exec_command(f'unzip {rpkg} -d {self.dest}')
        else:
            package = zipfile.ZipFile(lpkg)
            package.extractall(path=self.dest)
            package.close()
        self.printl(f'extracted to {self.dest}')

        self.printl('running docker container...')
        self.obj = self.dclient.containers.run(
            'nginx',
            detach=True,
            name=self.device['name'],
            ports={'80/tcp': self.device['cport']},
            volumes=[f'{self.dest}:/usr/share/nginx/html:ro']

            # 'ubuntu/nginx',
            # detach=True,
            # name=self.device['name'],
            # ports={'80/tcp': self.device['port']},
            # volumes=[f'{self.dest}:/var/www/html:ro']
        )
        self.printl(f'{self.obj.short_id} deployed')
        return True


DRIVERS = {
    # Windows
    'win32': Windows,
    'win64': Windows,

    # Android
    'arm':    Android,
    'armv8':  Android,
    'x86':    Android,
    'x86_64': Android,
    'aab':    Android,

    # Apple
    'pkg': MacOS,
    'ipa': 'ios',

    # Raspbian
    'linux_arm64': Raspbian,

    # Linux
    'linux_x86_64': Linux,
    'deb': Debian,

    # Samsung Tizen
    'tizen': Tizen,

    # LG webOS
    'webos.ipk': WebOS,
    'debug.ipk': WebOSdebug,

    # Web browser
    'web': Web
}
