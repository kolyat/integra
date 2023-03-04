import logging
from kivy.clock import Clock


class Logger:
    """Mix-in for logging messages.

    :ivar device: dict with device parameters from devices.yaml
    """
    def __init__(self):
        self.device = None

    def printl(self, msg: str) -> None:
        logging.info(f'{self.device["name"]}: {msg}')


class ConsoleHandler(logging.Handler):
    """Custom logging handler to write data to console widget
    (kivy.uix.textinput.TextInput)

    :ivar console: TextInput object
    """
    def __init__(self, console, level=logging.NOTSET):
        super().__init__(level=level)
        self.console = console
        self.formatter = logging.Formatter('[%(levelname)-7s] %(message)s')

    def emit(self, record):
        def write(dt=None):
            self.console.text += f'{self.format(record)}\n'
        Clock.schedule_once(write)
