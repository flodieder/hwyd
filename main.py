import kivy
kivy.require('2.0.0')
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from calendar_ui import CalendarWidget
from kivy.utils import platform
from kivy.uix.actionbar import ActionBar, ActionGroup, ActionView, ActionButton, ActionOverflow, ActionPrevious
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView, FileChooser
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.utils import platform
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import ObjectProperty
import os
import json
from pathlib import Path
from datetime import date, datetime
import plyer
import matplotlib
from garden_matplotlib.backend_kivyagg import FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
from questionWidget import QuestionWidget
from editQuestionPopup import EditQuestionPopup
from anaScreen import AnaScreen
from hwydScreen import HwydScreen

if platform == 'android':
    from android.storage import app_storage_path, primary_external_storage_path, secondary_external_storage_path
    from android.permissions import request_permissions, Permission
    from android import AndroidService

Window.softinput_mode = 'below_target'


class HWYD(App):
    """ An App that allows to record questionaires and to analyse them."""
    screen_manager = ObjectProperty()

    def build(self):
        self.permission_requested = False
        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.CAMERA])
        self.permission_requested = True

        self.screen_manager = ScreenManager()
        root_dir = self.user_data_dir
        self.data, self.config = self.init_data(root_dir)
        self.hwyd_screen = HwydScreen(data_dic=self.data,
                                      config_dic=self.config,
                                      screen_manager=self.screen_manager, root_dir=self.config['data_file'])
        self.hwyd_screen.bind(dump_data=lambda instance, value: self.on_dump_data())
        self.hwyd_screen.bind(dump_config=lambda instance, value: self.on_dump_config())
        self.hwyd_screen.bind(load_data=lambda instance, value: self.on_load_data())
        self.hwyd_screen.bind(to_ana=lambda instance, value: self.switch_to_ana())
        self.ana_screen = AnaScreen(data_dic=self.data, screen_manager=self.screen_manager)
        self.ana_screen.bind(dump_data=lambda instance, value: self.on_dump_data())
        self.ana_screen.bind(to_main=lambda instance, value: self.switch_to_main())
        self.screen_manager.add_widget(self.hwyd_screen)
        self.screen_manager.add_widget(self.ana_screen)

        # if platform == 'android':
        #     service = AndroidService('Questionaire Reminder Service', 'started')
        #     service.start('service started')
        #     print(dir(service))
        return self.screen_manager

    def switch_to_main(self):
        self.screen_manager.switch_to(self.hwyd_screen, direction='right')

    def switch_to_ana(self):
        self.ana_screen.load_data_dic(self.data)
        self.screen_manager.switch_to(self.ana_screen, direction='left')

    def init_data(self, root_dir: str):

        if not os.path.exists(root_dir):
            os.makedirs(root_dir)
        self.config_file = os.path.join(root_dir, 'config.json')
        p = Path(self.config_file)
        p.touch(exist_ok=True)

        with open(self.config_file, 'r') as f:
            try:
                config = json.load(f)
            except:
                config = {}
        try:
            self.f_name = config['data_file']
        except KeyError:
            self.f_name = 'data.json'
            config['data_file'] = 'data.json'
            with open(self.config_file, 'w') as f:
                f.write(json.dumps(config, indent=4))

        try:
            with open(self.f_name, 'r') as f:
                try:
                    data = json.load(f)
                except:
                    data = {}
        except:
            Path(self.f_name).touch()
            data = {}
        return data, config

    def on_load_data(self):
        with open(self.config['data_file'], 'r') as f:
            try:
                self.data = json.load(f)
            except:
                self.data = {}
        self.data = {
            x: self.data[x]
            for x in sorted(self.data,
                            key=lambda value: datetime.strptime(value, '%d.%m.%Y')
                            if (value != 'format') else datetime.min)
        }
        self.hwyd_screen.load_data_dic(self.data)
        self.ana_screen.load_data_dic(self.data)

    def on_dump_data(self):
        with open(self.config['data_file'], 'w') as f:
            f.write(json.dumps(self.data, indent=4))

    def on_dump_config(self):
        with open(self.config_file, 'w') as f:
            f.write(json.dumps(self.config, indent=4))

    def on_stop(self):
        print('on_stop called')

    def on_pause(self):
        print('on_pause called')
        if self.permission_requested:
            self.on_stop()
        return True

    def on_resume(self):
        print('on_resume called')


if __name__ == '__main__':
    HWYD().run()
