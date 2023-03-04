import ctypes
import platform
import threading
import logging
import concurrent.futures

from utils import log
import client
import drivers


class Worker(log.Logger):
    """Class-worker which performs package-to-device deployment.
    """
    def deploy(self, device: dict):
        """Deploy package to a device.

        :param device: device's params
        :type device: dict
        """
        self.device = device
        try:
            fs_client = client.FsClient()
            packages = fs_client.list_packages(self.device)
            package = fs_client.download_package(packages[0])
            drivers.DRIVERS[self.device['ptype']](self.device, package).deploy()
        except IndexError:
            self.printl(f'{self.device["ptype"]} not found')
            self.printl('! ! ! ! ! ! Deployment failed')
        except Exception as e:
            self.printl(str(e))
            self.printl('! ! ! ! ! ! Deployment failed')


class Foreman:
    """Class-foreman which controls deployment procedure.
    """
    def __init__(self):
        self.executor = None
        self.futures = None

    def start_deploy(self, devices: list, button):
        """Start deployment process.

        :param devices: devices to be processed
        :type devices: list

        :param button: callback widget (button)
        :type button: kivu.uix object
        """
        logging.info(f'{__name__}: * * * * * * * * * * * * Deployment started')
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        self.futures = [
            self.executor.submit(Worker().deploy, device)
            for device in devices if device['selected']
        ]
        concurrent.futures.wait(
            self.futures,
            timeout=None,
            return_when=concurrent.futures.ALL_COMPLETED
        )
        logging.info(f'{__name__}: . . . . . . . . . . . . Deployment finished')
        button.deploy_off()

    def stop_deploy(self):
        """Interrupt deployment process.
        """
        for future in self.futures:
            logging.info(f'Cancel {str(future)}')
            future.cancel()
        version = platform.python_version_tuple()
        major = int(version[0])
        minor = int(version[1])
        if major > 3 or (major == 3 and minor > 8):
            self.executor.shutdown(wait=False, cancel_futures=True)
        else:
            self.executor.shutdown(wait=False)
        for t in threading.enumerate():
            if 'Executor' in t.name:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_long(t.ident), ctypes.py_object(SystemExit)
                )
                logging.info(f'SystemExit to {str(t)}')


foreman = Foreman()
