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
from kivy.properties import ObjectProperty, BooleanProperty
import os
import json
from pathlib import Path
from datetime import date
import plyer
import matplotlib
from garden_matplotlib.backend_kivyagg import FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
from questionWidget import QuestionWidget
from editQuestionPopup import EditQuestionPopup
from anaQuestionWidget import AnaQuestionWidget
if platform == 'android':
    from android.storage import app_storage_path, primary_external_storage_path, secondary_external_storage_path
    from android.permissions import request_permissions, Permission
    from android import AndroidService

Window.softinput_mode = 'below_target'


class AnaScreen(Screen):
    dump_data = BooleanProperty(True)
    to_main = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(AnaScreen, self).__init__()
        self.name = 'HWYD_ana_screen'
        self.screen_manager = kwargs['screen_manager']
        self.data = kwargs['data_dic']
        self.init_layout()

    def init_layout(self):
        self.question_widgets = {}
        self.top_layout = BoxLayout(orientation='vertical', spacing=dp(10))

        self.action_bar = ActionBar(pos_hint={'top': 1.3})
        self.action_view = ActionView()
        self.action_previous = ActionPrevious(with_previous=True)
        self.action_previous.bind(on_press=lambda instance: self.on_action_previous())
        self.action_view.add_widget(self.action_previous)
        self.action_bar.add_widget(self.action_view)
        self.top_layout.add_widget(self.action_bar)

        self.scroll_view = ScrollView(size_hint=(1, None),
                                      size=(Window.width,
                                            Window.height - self.action_bar.height - 10))
        self.scroll_view.do_scroll_x = False
        self.scroll_view.do_scroll_y = True
        self.scroll_view_content = GridLayout(size_hint_y=None,
                                              cols=1,
                                              spacing=dp(60),
                                              padding=(0, dp(20), 0, dp(20)))

        self.load_format()
        self.scroll_view_content.bind(
            minimum_height=lambda instance, value: self.adjust_scroll_view_height(instance, value))
        self.scroll_view.add_widget(self.scroll_view_content)

        self.top_layout.add_widget(self.scroll_view)
        self.add_widget(self.top_layout)

    def on_action_previous(self):
        self.to_main = not self.to_main

    def load_format(self):
        self.scroll_view_content.clear_widgets()
        # try if no 'format'
        for question in self.data['format']:
            qw = AnaQuestionWidget(self.data, **question)
            self.question_widgets[question['question'][0]] = qw
            qw.size_hint_y = None
            qw.height = dp(320)
            qw.bind(analysis_changed=self.on_analysis_change)
            self.scroll_view_content.add_widget(qw)

    def adjust_scroll_view_height(self, instance, value):
        new_height = 0
        for child in instance.children:
            new_height += child.height + dp(60)
        instance.height = new_height
        instance._trigger_layout()

    def on_analysis_change(self, instance, value):
        self.dump_data = not self.dump_data

    def load_data_dic(self, data_dic):
        self.data = data_dic
        self.load_format()
