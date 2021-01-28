import kivy
kivy.require('2.0.0')
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from calendar_ui import CalendarWidget
from kivy.utils import platform
from kivy.uix.actionbar import ActionBar, ActionGroup, ActionView, ActionButton, ActionOverflow, ActionPrevious
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView, FileChooser
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.utils import platform
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import ObjectProperty
from kivy.properties import BooleanProperty
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
if platform == 'android':
    from android.storage import app_storage_path, primary_external_storage_path, secondary_external_storage_path
    from android.permissions import request_permissions, Permission
    from android import AndroidService

Window.softinput_mode = 'below_target'


class AnaQuestionWidget(BoxLayout):

    analysis_changed = BooleanProperty(True)

    def __init__(self, data, **kwargs):
        super(AnaQuestionWidget, self).__init__(orientation='vertical', size_hint=(1, 1))
        self.question_json = kwargs
        self.data = data

        if platform == 'android':
            self.font_size = 28
        else:
            self.font_size = 12

        try:
            self.analysis = self.question_json['analysis']
        except KeyError:
            self.analysis = ['none', True]
            self.question_json['analysis'] = self.analysis

        self.question_label = Label(text=self.question_json['question'][0], size_hint=(1, 0.1))
        self.add_widget(self.question_label)

        self.top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        self.ana_spinner = Spinner(text=self.analysis[0],
                                   values=('none', 'pie', 'line'),
                                   size_hint=(0.3, 1))
        self.missing_data_cb = CheckBox(size_hint=(0.2, 1))
        self.missing_data_cb.active = self.analysis[1]
        self.ana_spinner.bind(
            text=lambda instance, text: self.create_graph(text, self.missing_data_cb.active))
        self.missing_data_cb.bind(
            active=lambda instance, value: self.create_graph(self.ana_spinner.text, value))
        self.top_layout.add_widget(Label(text='Choose analysis type: '))
        self.top_layout.add_widget(self.ana_spinner)
        self.top_layout.add_widget(Label(text='Use missing data '))
        self.top_layout.add_widget(self.missing_data_cb)

        self.analysis_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.8))
        self.analysis_canvas = Label()
        self.analysis_layout.add_widget(self.analysis_canvas)

        self.create_graph(self.analysis[0], self.analysis[1])

        self.add_widget(self.top_layout)
        self.add_widget(self.analysis_layout)

    def create_graph(self, ana_type, use_missing_data):
        for i, question in enumerate(self.data['format']):
            if question['question'][0] == self.question_json['question'][0]:
                self.data['format'][i]['analysis'] = [ana_type, use_missing_data]
        self.analysis_changed = not self.analysis_changed
        self.analysis_layout.remove_widget(self.analysis_canvas)
        if ana_type == 'none':
            self.analysis_canvas = Label()
        elif ana_type == 'pie':
            x = {}
            if use_missing_data:
                x['no data'] = 0
            for option in self.question_json['options']:
                x[option[1]] = 0
            for key in self.data:
                if key != 'format':
                    try:
                        no_value = True
                        for option in self.data[key][self.question_json['question'][0]]:
                            if self.data[key][self.question_json['question'][0]][option]:
                                x[option] += 1
                                no_value = False
                        if no_value and use_missing_data:
                            x['no data'] += 1
                    except KeyError:
                        if use_missing_data:
                            x['no data'] += 1
            fig1 = plt.figure(figsize=(3, 3), facecolor='black')
            ax = fig1.add_subplot(1, 1, 1)
            ax.pie(list(x.values()),
                   labels=x.keys(),
                   autopct='%.0f%%',
                   textprops={
                       'color': 'white',
                       'size': self.font_size
                   })
            self.analysis_canvas = FigureCanvas(fig1)

        elif ana_type == 'line':
            x = []
            y = []
            if self.question_json['options'][0][0] == 'exclusive option':
                for key in self.data:
                    if key != 'format':
                        try:
                            for option, value in self.data[key][self.question_json['question']
                                                                [0]].items():
                                if value:
                                    x.append(key)
                                    y.append(int(option))
                        except KeyError:
                            pass
            elif self.question_json['options'][0][0] == 'counter':
                for key in self.data:
                    if key != 'format':
                        try:
                            for option, value in self.data[key][self.question_json['question']
                                                                [0]].items():
                                y.append(float(value))
                                x.append(key)
                        except KeyError:
                            if use_missing_data:
                                x.append(key)
                                y.append(0)
                            pass
                        except ValueError:
                            if use_missing_data:
                                x.append(key)
                                y.append(0)
                            pass
            fig1 = plt.figure(figsize=(3, 3), facecolor='black')
            ax = fig1.add_subplot(1, 1, 1)
            ax.set_facecolor('black')
            ax.plot(x, y, color='white')
            ax.spines['left'].set_color('white')
            ax.spines['bottom'].set_color('white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.tick_params(axis='x', colors='white', labelrotation=-15, labelsize=self.font_size)
            ax.tick_params(axis='y', colors='white', labelsize=self.font_size)
            ax.set_xticks(ax.get_xticks()[::10])
            self.analysis_canvas = FigureCanvas(fig1)
        self.analysis_layout.add_widget(self.analysis_canvas)
        return