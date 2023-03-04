import operator
import os
import keyring
import requests
from requests import auth

from utils import log
import config


class FsClient(requests.Session, log.Logger):
    """Class derived from :class:`requests.Session` with some custom methods.
    """
    def __init__(self):
        super().__init__()
        self.auth = auth.HTTPBasicAuth(
            config.conf['username'],
            keyring.get_password('system', config.conf['username'])
        )
        self.device = None
        if not os.path.isdir(config.conf['download_dir']):
            os.mkdir(config.conf['download_dir'])

    @staticmethod
    def sort_packages(packages: list, reverse: bool = True) -> list:
        """Sort list of dict objects (packages) using key 'some_key'.

        :param packages: list of package objects
        :type packages: list

        :param reverse: sort order (descending by default)
        :type reverse: bool

        :return: sorted list of package objects
        :rtype: list
        """
        # TODO: define key
        return \
            sorted(packages, key=operator.itemgetter('some_key'), reverse=reverse)

    def search_packages(self, device: dict) -> list:
        """Get list of packages using search.

        :param device: device's data
        :type device: dict

        :return: list of packages
        :rtype: list
        """
        self.device = device
        # TODO: code depends on server's API; must be implemented
        raise NotImplementedError

    def download_package(self, package: dict) -> str:
        """Download package from server.

        :param package: package's data
        :type package: dict

        :return: name of downloaded package
        :rtype: str
        """
        # TODO: code depends on server's API; must be implemented
        raise NotImplementedError
