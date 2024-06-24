import os
import sys
import logging
import yaml


DEFAULTS = {
    'fileserver_url': 'https://fileserver.stable.team',
    'username': 'ar_user',
    'download_dir': './downloads',
    'bundletool': './utils/bundletool/bundletool.jar',
    'aab_key': './utils/bundletool/default_aab_key.jks',
    'ptypes': {
        'win64': {
            'mask': 'win64.exe',
            'driver': 'Windows'
        },
        'arm': {
            'mask': 'arm.apk',
            'driver': 'Android'
        }
    },
    'editions': {
        'ar': {
            'general': {'app': 'com.addreality.player2'},
            'raspbian': {'app': 'Player',
                         'proc': 'Player'},
            'ubuntu': {'app': 'addreality-player',
                       'proc': 'addreality-play'},
            'linux': {'app': '"Addreality Player"',
                      'proc': '"Addreality Play"'},
        },
        'df': {
            'general': {'app': 'ai.displayforce.player'},
            'raspbian': {'app': 'Player', 'proc': 'Player'},
        }
    }
}


path1 = os.path.dirname(os.path.abspath(sys.executable))
path2 = os.path.dirname(os.path.abspath(__file__))

DEVS_FILE = 'devices.yaml'
DEVICES_FILE = os.path.join(path1, DEVS_FILE)
if not os.path.isfile(DEVICES_FILE):
    DEVICES_FILE = os.path.join(path2, DEVS_FILE)
    if not os.path.isfile(DEVICES_FILE):
        DEVICES_FILE = ''

CONF_FILE = 'config.yaml'
CONFIG_FILE = os.path.join(path1, CONF_FILE)
if not os.path.isfile(CONFIG_FILE):
    CONFIG_FILE = os.path.join(path2, CONF_FILE)
    if not os.path.isfile(CONFIG_FILE):
        CONFIG_FILE = ''

DEFAULT_EDITION = 'ar'
DEFAULT_PTYPE = 'arm'


class Config(dict):
    """Class for storing configuration options.
    """
    def __init__(self, config_file: str = CONFIG_FILE):
        """
        :param config_file: config file name
        :type config_file: str
        """
        super().__init__()
        self.config_file = config_file
        self.update(**DEFAULTS)

    def load_config(self) -> None:
        """Load and update configuration options from a config_file.
        """
        if not os.path.isfile(self.config_file):
            logging.warning(
                f'{__name__}: {self.config_file} not found, defaults loaded'
            )
            return
        try:
            stream = open(self.config_file, 'r', encoding='utf-8')
            loaded = yaml.full_load(stream)
            stream.close()
            self.update(**loaded)
            logging.info(f'{__name__}: Loaded {self.config_file}')
        except Exception as e:
            logging.error(
                f'{__name__}: Error occurred while loading {self.config_file},'
                f' using defaults'
            )
            logging.error(str(e))


conf = Config()
conf.load_config()
