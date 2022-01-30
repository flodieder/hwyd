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
from datetime import date, datetime, timedelta
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
    """ A widget that displays analyses of a question. """

    analysis_changed = BooleanProperty(True)

    def __init__(self, data, **kwargs):
        super(AnaQuestionWidget, self).__init__(orientation='vertical', size_hint=(1, 1))
        self.question_json = kwargs
        self.data = data

        if platform == 'android':
            self.font_size = 28
        else:
            self.font_size = 12

        for i, question in enumerate(self.data['format']):
            if question['question'][0] == self.question_json['question'][0]:
                try:
                    self.analysis = self.data['format'][i]['analysis']
                    if len(self.analysis) < 4:
                        raise KeyError('u know if u know')
                except KeyError:
                    self.data['format'][i]['analysis'] = ['none', True, 'All', '30', '0']
                    self.analysis = self.data['format'][i]['analysis']
                    self.analysis_changed = not self.analysis_changed

        self.question_label = Label(text=self.question_json['question'][0], size_hint=(1, 0.1))
        self.add_widget(self.question_label)

        self.top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        self.ana_spinner = Spinner(text=self.analysis[0],
                                   values=('none', 'pie', 'line', 'streak', 'histogram'),
                                   size_hint=(0.3, 1))
        self.missing_data_cb = CheckBox(size_hint=(0.2, 1))
        self.missing_data_cb.active = self.analysis[1]
        self.ana_spinner.bind(text=lambda instance, text: self.on_ana_spinner())
        self.missing_data_cb.bind(active=lambda instance, value: self.on_missing_data())
        self.top_layout.add_widget(Label(text='Choose analysis type: '))
        self.top_layout.add_widget(self.ana_spinner)
        self.top_layout.add_widget(Label(text='Use missing data '))
        self.top_layout.add_widget(self.missing_data_cb)

        self.range_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        self.range_or_last_spinner = Spinner(text=self.analysis[2],
                                             values=('All', 'Last', 'Range'),
                                             size_hint=(0.3, 1))
        self.range_or_last_spinner.bind(
            text=lambda instance, text: self.on_range_or_last_spinner(text))
        self.init_range_layout()

        self.analysis_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.7))
        self.analysis_canvas = Label()
        self.analysis_layout.add_widget(self.analysis_canvas)

        self.create_graph()

        self.add_widget(self.top_layout)
        self.add_widget(self.range_layout)
        self.add_widget(self.analysis_layout)

    def on_ana_spinner(self):
        self.analysis[0] = self.ana_spinner.text
        self.analysis_changed = not self.analysis_changed
        self.create_graph()

    def on_missing_data(self):
        self.analysis[1] = self.missing_data_cb.active
        self.analysis_changed = not self.analysis_changed
        self.create_graph()

    def on_range_or_last_spinner(self, text):
        self.analysis[2] = text
        if text == 'Last':
            self.analysis[3] = '30'
        elif text == 'Range':
            week_back = timedelta(days=7)
            self.analysis[3] = (datetime.now() - week_back).strftime("%d.%m.%Y")
            self.analysis[4] = datetime.now().strftime("%d.%m.%Y")
        self.analysis_changed = not self.analysis_changed
        self.init_range_layout()
        self.create_graph()

    def on_last_x_text(self, text):
        self.analysis[3] = text
        self.analysis_changed = not self.analysis_changed
        self.create_graph()

    def in_range(self, local_date):
        if self.analysis[2] == 'All':
            return True
        elif self.analysis[2] == 'Last':
            try:
                if int(self.analysis[3]) < abs(datetime.today() -
                                               datetime.strptime(local_date, "%d.%m.%Y")).days:
                    return False
            except ValueError:
                return False
        elif self.analysis[2] == 'Range':
            try:
                l = datetime.strptime(local_date, "%d.%m.%Y")
                min_date = datetime.strptime(self.analysis[3], "%d.%m.%Y")
                max_date = datetime.strptime(self.analysis[4], "%d.%m.%Y")
                return min_date <= l <= max_date
            except ValueError:
                return False
            return False
        return True

    def generate_data_range(self):
        if self.analysis[2] == 'All':
            for key in self.data:
                if key != 'format':
                    yield key
        elif self.analysis[2] == 'Last':
            try:
                i = int(self.analysis[3]) - 1
            except ValueError:
                i = 0
            while i >= 0:
                d = datetime.today() - timedelta(days=i)
                i -= 1
                yield datetime.strftime(d, "%d.%m.%Y")
        elif self.analysis[2] == 'Range':
            start = datetime.strptime(self.analysis[3], "%d.%m.%Y")
            stop = datetime.strptime(self.analysis[4], "%d.%m.%Y")
            delta = stop - start

            for i in range(delta.days + 1):
                day = start + timedelta(days=i)
                yield datetime.strftime(day, "%d.%m.%Y")

    def init_range_layout(self):
        self.range_layout.clear_widgets()
        self.range_layout.add_widget(Label(text='Use '))
        self.range_layout.add_widget(self.range_or_last_spinner)
        if self.analysis[2] == 'All':
            self.range_layout.add_widget(Label(text='days'))
        elif self.analysis[2] == 'Last':
            last_x_text = TextInput(text=self.analysis[3],
                                    multiline=False,
                                    size_hint=(0.2, 1),
                                    input_type='number')
            last_x_text.bind(text=lambda instance, value: self.on_last_x_text(value))
            self.range_layout.add_widget(last_x_text)
            self.range_layout.add_widget(Label(text='days'))
        elif self.analysis[2] == 'Range':
            self.range_layout.add_widget(Label(text='Start'))
            range_start_text = TextInput(text=self.analysis[3],
                                         multiline=False,
                                         size_hint=(1, 1),
                                         input_type='number')
            range_start_text.bind(text=lambda instance, value: self.on_range_start_text(value))
            range_stop_text = TextInput(text=self.analysis[4],
                                        multiline=False,
                                        size_hint=(1, 1),
                                        input_type='number')
            range_stop_text.bind(text=lambda instance, value: self.on_range_stop_text(value))
            self.range_layout.add_widget(range_start_text)
            self.range_layout.add_widget(Label(text='End'))
            self.range_layout.add_widget(range_stop_text)

    def on_range_start_text(self, text):
        try:
            l = datetime.strptime(text, "%d.%m.%Y")
            self.analysis[3] = text
            self.analysis_changed = not self.analysis_changed
            self.create_graph()
        except:
            pass

    def on_range_stop_text(self, text):
        try:
            l = datetime.strptime(text, "%d.%m.%Y")
            self.analysis[4] = text
            self.analysis_changed = not self.analysis_changed
            self.create_graph()
        except:
            pass

    def create_histogram_canvas(self):
        y = []
        for date in self.generate_data_range():
            try:
                for option, value in self.data[date][self.question_json['question'][0]].items():
                    if value:
                        y.append(option)
            except KeyError:
                pass
        fig1 = plt.figure(figsize=(3, 3), facecolor='black')
        ax = fig1.add_subplot(1, 1, 1)
        ax.hist(list(y), bins=len(self.question_json['options']))
        ax.set_facecolor('black')
        ax.spines['left'].set_color('white')
        ax.spines['bottom'].set_color('white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.tick_params(axis='x', colors='white', labelsize=self.font_size)
        ax.tick_params(axis='y', colors='white', labelsize=self.font_size)

        return FigureCanvas(fig1)

    def create_pi_canvas(self):
        x = {}
        use_missing_data = self.analysis[1]
        if use_missing_data:
            x['no data'] = 0
        for option in self.question_json['options']:
            x[option[1]] = 0
        for date in self.generate_data_range():
            try:
                no_value = True
                for option in self.data[date][self.question_json['question'][0]]:
                    if self.data[date][self.question_json['question'][0]][option]:
                        x[option] += 1
                        no_value = False
                if no_value and use_missing_data:
                    x['no data'] += 1
            except KeyError:
                if use_missing_data:
                    x['no data'] += 1
        fig1 = plt.figure(figsize=(3, 3), facecolor='black')
        ax = fig1.add_subplot(1, 1, 1)
        try:
            ax.pie(list(x.values()),
                   labels=x.keys(),
                   autopct='%.0f%%',
                   textprops={
                       'color': 'white',
                       'size': self.font_size
                   })
        except ValueError as error:
            ax.pie([1],
                   labels=['Error'],
                   autopct='%.0f%%',
                   textprops={
                       'color': 'white',
                       'size': self.font_size
                   })
        return FigureCanvas(fig1)

    def create_streak_canvas(self):
        x = []
        y = []
        use_missing_data = self.analysis[1]
        if self.question_json['options'][0][0] == 'exclusive option':
            for key in self.data:
                if key != 'format' and self.in_range(key):
                    try:
                        for option, value in self.data[key][self.question_json['question']
                                                            [0]].items():
                            if value:
                                x.append(key)
                                y.append(option)
                    except KeyError:
                        pass
        # TODO Streak info for inclusive option does not work as intended
        elif self.question_json['options'][0][0] == 'inclusive option':
            for key in self.data:
                if key != 'format' and self.in_range(key):
                    try:
                        y.append([])
                        for option, value in self.data[key][self.question_json['question']
                                                            [0]].items():
                            # input(option)
                            # input(value)
                            if value:
                                y[-1].append(option)
                    except KeyError:
                        pass
                    x.append(key)
        elif self.question_json['options'][0][0] == 'counter':
            for key in self.data:
                if key != 'format' and self.in_range(key):
                    try:
                        for option, value in self.data[key][self.question_json['question']
                                                            [0]].items():
                            y.append(value)
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
        else:
            fig1 = plt.figure(figsize=(3, 3), facecolor='black')
            return FigureCanvas(fig1)
        streak_info = {}
        for _, option_name in self.question_json['options']:
            streak_info[option_name] = {'max': 0, 'current': 0}
        if len(x) < 1:
            fig1 = plt.figure(figsize=(3, 3), facecolor='black')
            return FigureCanvas(fig1)
        day_before = x[0]
        for opt, day in zip(y, x):
            if 1 < abs(
                    datetime.strptime(day, "%d.%m.%Y") -
                    datetime.strptime(day_before, "%d.%m.%Y")).days:
                for _, option_name in self.question_json['options']:
                    streak_info[option_name]['current'] = 0
            for option_type, option_name in self.question_json['options']:
                if option_type != 'exclusive option' and option_type != 'inclusive option':
                    break
                if option_name in opt:
                    streak_info[option_name]['current'] += 1
                    if streak_info[option_name]['max'] < streak_info[option_name]['current']:
                        streak_info[option_name]['max'] = streak_info[option_name]['current']
                else:
                    streak_info[option_name]['current'] = 0
            day_before = day
        bar_labels = []
        bar_max = []
        bar_current = []
        for key in streak_info:
            bar_labels.append(key)
            bar_max.append(streak_info[key]['max'])
            bar_current.append(streak_info[key]['current'])
        bar_pos = np.arange(len(bar_labels))
        bar_width = 0.35

        fig1 = plt.figure(figsize=(3, 3), facecolor='black')
        ax = fig1.add_subplot(1, 1, 1)
        ax.set_facecolor('black')
        ax.barh(bar_pos + bar_width / 2, bar_max, bar_width, label='Maximum Streak')
        ax.barh(bar_pos - bar_width / 2, bar_current, bar_width, label='Current Streak')
        ax.set_yticks(bar_pos)
        ax.set_yticklabels(bar_labels)
        ax.spines['left'].set_color('white')
        ax.spines['bottom'].set_color('white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.tick_params(axis='x', colors='white', labelsize=self.font_size)
        ax.tick_params(axis='y', colors='white', labelsize=self.font_size)
        leg = ax.legend(facecolor='black', fontsize=self.font_size)
        for text in leg.get_texts():
            plt.setp(text, color='w')

        return FigureCanvas(fig1)

    def create_line_canvas(self):
        x = []
        y = []
        use_missing_data = self.analysis[1]
        for date in self.generate_data_range():
            if self.question_json['options'][0][0] == 'exclusive option':
                try:
                    for option, value in self.data[date][self.question_json['question'][0]].items():
                        if value:
                            x.append(date)
                            y.append(int(option))
                except KeyError:
                    pass
            elif self.question_json['options'][0][0] == 'counter':
                try:
                    for option, value in self.data[date][self.question_json['question'][0]].items():
                        y.append(float(value))
                        x.append(date)
                except KeyError:
                    if use_missing_data:
                        x.append(date)
                        y.append(0)
                    pass
                except ValueError:
                    if use_missing_data:
                        x.append(date)
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
        return FigureCanvas(fig1)

    def create_graph(self):
        self.analysis_layout.remove_widget(self.analysis_canvas)
        ana_type = self.analysis[0]
        if ana_type == 'none':
            self.analysis_canvas = Label()
        elif ana_type == 'histogram':
            self.analysis_canvas = self.create_histogram_canvas()
        elif ana_type == 'pie':
            self.analysis_canvas = self.create_pi_canvas()
        elif ana_type == 'streak':
            self.analysis_canvas = self.create_streak_canvas()
        elif ana_type == 'line':
            self.analysis_canvas = self.create_line_canvas()
        self.analysis_layout.add_widget(self.analysis_canvas)
        return
