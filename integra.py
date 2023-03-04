from typing import Any
import os
import sys
import pathlib
import copy
import logging
import threading

import yaml

from kivy import resources
from kivy import logger
from kivy.core import window
from kivy import app as kivy_app, properties
from kivy.uix.recycleview import views
from kivy.uix import recycleview, boxlayout, textinput, button, dropdown

import config
from utils import log
import deploy


class DropdownButton(button.Button):
    pass


class DropdownMenu(dropdown.DropDown):
    caller = None

    def open(self, widget):
        super().open(widget)
        self.caller = widget

    def update(self, _, obj):
        self.caller.parent.set_data(self.caller.key, obj.text)
        self.caller.text = obj.text


class DeviceUnit(views.RecycleDataViewBehavior, boxlayout.BoxLayout):
    index = None
    selected = properties.BooleanProperty(defaultvalue=False)
    name = properties.StringProperty(defaultvalue='')
    cleanup = properties.BooleanProperty(defaultvalue=False)
    ptype = properties.StringProperty(defaultvalue='')
    edition = properties.StringProperty(defaultvalue='')
    remote = properties.BooleanProperty(defaultvalue=False)
    host = properties.StringProperty(defaultvalue='')
    port = properties.NumericProperty(defaultvalue=0)
    cport = properties.NumericProperty(defaultvalue=0)
    username = properties.StringProperty(defaultvalue='')
    upload_dir = properties.StringProperty(defaultvalue='')
    description = properties.StringProperty(defaultvalue='')

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super().refresh_view_attrs(rv, index, data)

    def get_data_row(self):
        return app.root.ids.device_table.data[self.index]

    def set_data(self, key: str, value: Any) -> None:
        self.get_data_row()[key] = value


class DeviceTable(recycleview.RecycleView):
    default = {
        'selected': False,
        'name': '',
        'cleanup': False,
        'ptype': '',
        'edition': '',
        'remote': False,
        'host': '',
        'port': 0,
        'cport': 0,
        'username': '',
        'upload_dir': '',
        'description': ''
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        devices_file = config.DEVICES_FILE
        self.data = []
        if devices_file == '':
            return
        stream = open(devices_file, 'r')
        loaded = yaml.load(stream, Loader=yaml.Loader)
        stream.close()
        logging.info(f'Devices: Loaded {devices_file}')
        self.data = [{**copy.deepcopy(self.default), **l} for l in loaded]


class DeployButton(button.Button):
    deploying = False

    def deploy_on(self):
        self.deploying = True
        self.text = 'Interrupt deployment'
        app.root.ids.console.text = ''

    def deploy_off(self):
        self.deploying = False
        self.text = 'Deploy'

    def on_release(self):
        if self.deploying:
            deploy.foreman.stop_deploy()
        else:
            self.deploy_on()
            threading.Thread(
                group=None, target=deploy.foreman.start_deploy, name='deploy',
                args=(app.root.ids.device_table.data[:], self), daemon=None
            ).start()


class Console(textinput.TextInput):
    pass


class Main(kivy_app.Widget):
    pass


class IntegraApp(kivy_app.App):
    dropdown_ptype = DropdownMenu()
    dropdown_edition = DropdownMenu()

    def build(self):
        self.icon = os.path.join(
            pathlib.Path(__file__).resolve().parent, 'media', 'integra.png'
        )
        return Main()

    def on_start(self):
        logger.Logger.addHandler(log.ConsoleHandler(self.root.ids.console,
                                                    logging.INFO))

        if config.DEVICES_FILE == '':
            logging.warning('devices.yaml not found')

        for ptype in config.PTYPES:
            item = DropdownButton(text=f'{ptype}')
            item.bind(on_release=lambda btn: self.dropdown_ptype.select(btn))
            self.dropdown_ptype.add_widget(item)
        self.dropdown_ptype.bind(on_select=self.dropdown_ptype.update)
        for edition in config.EDITIONS.keys():
            item = DropdownButton(text=f'{edition}')
            item.bind(on_release=lambda btn: self.dropdown_edition.select(btn))
            self.dropdown_edition.add_widget(item)
        self.dropdown_edition.bind(on_select=self.dropdown_edition.update)


if __name__ == '__main__':
    if hasattr(sys, '_MEIPASS'):
        resources.resource_add_path(os.path.join(sys._MEIPASS))
    window.Window.size = (1240, 768)
    window.Window.left = 30
    window.Window.top = 30

    app = IntegraApp()
    app.run()
