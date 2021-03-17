import kivy
kivy.require('2.0.0')
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from calendar_ui import CalendarWidget
from kivy.utils import platform
from kivy.uix.actionbar import ActionBar, ActionGroup, ActionView, ActionButton, ActionOverflow, ActionPrevious
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView, FileChooser
from kivy.utils import platform
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import DictProperty, BooleanProperty
import os
import json
from pathlib import Path
from copy import deepcopy

from questionWidget import QuestionWidget

if platform == 'android':
    from android.storage import app_storage_path, primary_external_storage_path, secondary_external_storage_path
    from android.permissions import request_permissions, Permission
    from android import AndroidService


class FilePopup(Popup):
    """ A Popup that allows to choose which file contains the data. """

    load = BooleanProperty(True)
    save = BooleanProperty(True)

    def __init__(self, **kwargs):
        content = BoxLayout(orientation='vertical')
        if platform == 'android':
            file_chooser = FileChooserListView(path=primary_external_storage_path(),
                                               dirselect=True,
                                               multiselect=False)
        else:
            file_chooser = FileChooserListView(path='/', dirselect=True, multiselect=False)
        button_layout = BoxLayout(orientation='horizontal', spacing=dp(20), size_hint=(1, 0.2))
        load_file_btn = Button(text='Load', size_hint=(0.1, 1), pos_hint={'center_x': 0.25})
        load_file_btn.bind(
            on_press=lambda instance: self.on_load_file(instance, file_chooser.selection))
        save_file_btn = Button(text='Save', size_hint=(0.1, 1), pos_hint={'center_x': 0.75})
        save_file_btn.bind(
            on_press=lambda instance: self.on_save_file(instance, file_chooser.selection))
        button_layout.add_widget(load_file_btn)
        button_layout.add_widget(save_file_btn)
        content.add_widget(file_chooser)
        content.add_widget(button_layout)

        super(FilePopup, self).__init__(title=kwargs['title'],
                                        content=content,
                                        auto_dismiss=kwargs['auto_dismiss'])

        self.data = kwargs['data_dic']
        self.config = kwargs['config_dic']

    def on_save_file(self, instance, file_path):
        if os.path.isdir(file_path[0]):
            p = Path(os.path.join(file_path[0], 'data.json'))
            p.touch(exist_ok=False)
            f_name = str(p)
        else:
            f_name = file_path[0]
        self.config['data_file'] = f_name

        self.save = not self.save
        self.dismiss()

    def on_load_file(self, instance, file_path):
        if os.path.isdir(file_path[0]):
            # Give error hint
            return
        else:
            f_name = file_path[0]
        self.config['data_file'] = f_name
        self.load = not self.load
        self.dismiss()