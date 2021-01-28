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
from anaScreen import AnaScreen
if platform == 'android':
    from android.storage import app_storage_path, primary_external_storage_path, secondary_external_storage_path
    from android.permissions import request_permissions, Permission
    from android import AndroidService

Window.softinput_mode = 'below_target'


class HwydScreen(Screen):

    dump_data = BooleanProperty(True)
    dump_config = BooleanProperty(True)
    load_data = BooleanProperty(True)
    to_ana = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(HwydScreen, self).__init__()
        self.name = 'HWYD_main_screen'
        self.screen_manager = kwargs['screen_manager']
        Window.bind(on_key_down=self.on_keyboard_down)
        self.top_layout = BoxLayout(orientation='vertical', spacing=dp(10))
        # self.init_data(kwargs['root_dir'])
        self.data = kwargs['data_dic']
        self.config = kwargs['config_dic']
        self.init_layout()

    def init_layout(self):
        self.question_widgets = {}

        self.action_bar = ActionBar(pos_hint={'top': 1.3})
        self.action_view = ActionView()
        self.action_previous = ActionPrevious(with_previous=False)
        self.action_view.add_widget(self.action_previous)
        self.analysis_btn = ActionButton(text='Analysis')
        self.analysis_btn.bind(on_press=lambda instance: self.on_analysis_btn())
        self.choose_file_btn = ActionButton(text='File')
        self.choose_file_btn.bind(on_press=self.on_file)
        self.action_view.add_widget(self.choose_file_btn)
        self.action_view.add_widget(self.analysis_btn)
        self.action_bar.add_widget(self.action_view)
        self.top_layout.add_widget(self.action_bar)

        self.calendar = CalendarWidget(size_hint=(1, 0.3))
        self.calendar.bind(current_date=lambda instance, value: self.load_format())
        self.top_layout.add_widget(self.calendar)

        self.scroll_view = ScrollView(size_hint=(1, 0.6))
        self.scroll_view.do_scroll_x = False
        self.scroll_view.do_scroll_y = True
        self.scroll_view_content = GridLayout(size_hint_y=None,
                                              cols=1,
                                              spacing=dp(60),
                                              padding=(0, dp(20), 0, dp(20)))

        self.scroll_view_content.bind(
            minimum_height=lambda instance, value: self.adjust_scroll_view_height(instance, value))
        self.scroll_view.add_widget(self.scroll_view_content)

        self.load_format()

        self.top_layout.add_widget(self.scroll_view)

        self.add_question_button = Button(text='Add Question',
                                          size_hint=(0.3, 0.1),
                                          pos_hint={'center_x': 0.5})
        self.add_question_button.bind(on_press=self.on_add_question)
        self.top_layout.add_widget(self.add_question_button)
        self.add_widget(self.top_layout)

    def adjust_scroll_view_height(self, instance, value):
        instance.height = value + len(self.children) * dp(30)

    def on_analysis_btn(self):
        self.to_ana = not self.to_ana

    def load_format(self):
        self.scroll_view_content.clear_widgets()
        # try if no 'format' key
        try:
            # try if no 'current date' key
            try:
                answers = self.data[self.calendar.get_current_date()]
            except:
                self.data[self.calendar.get_current_date()] = {}
                answers = self.data[self.calendar.get_current_date()]
            for question in self.data['format']:
                try:
                    if question['scheduling'][0] == 'daily':
                        pass
                    elif question['scheduling'][0] == 'weekly':
                        if not self.calendar.compare_day_name(question['scheduling'][1]):
                            continue
                    elif question['scheduling'][0] == 'monthly':
                        if not self.calendar.compare_month_status(question['scheduling'][1]):
                            continue
                except:
                    question['scheduling'] = ['daily', '']
                qw = QuestionWidget(**question)
                self.question_widgets[question['question'][0]] = qw
                # try if no 'question' key
                try:
                    qw.load_answer(answers[question['question'][0]])
                except:
                    answers[question['question'][0]] = {}
                    qw.load_answer(answers[question['question'][0]])
                qw.bind(answer_changed=self.on_answer_change)
                qw.bind(format_changed=self.on_format_change)
                qw.bind(removed=self.on_removed)
                self.scroll_view_content.add_widget(qw)
        except KeyError:
            self.data['format'] = []
        except:
            pass

    def on_file(self, instance):
        content = BoxLayout(orientation='vertical')
        self.popup = Popup(
            title=
            'Choose a directory where to save your data or a data.json file with the correct format',
            content=content,
            auto_dismiss=False)
        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
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
        self.popup.open()

    def on_save_file(self, instance, file_path):
        if os.path.isdir(file_path[0]):
            p = Path(os.path.join(file_path[0], 'data.json'))
            p.touch(exist_ok=False)
            self.f_name = str(p)
        else:
            self.f_name = file_path[0]
        self.config['data_file'] = self.f_name

        self.dump_config = not self.dump_config
        self.dump_data = not self.dump_data
        self.popup.dismiss()

    def on_load_file(self, instance, file_path):
        if os.path.isdir(file_path[0]):
            # Give error hint
            return
        else:
            self.f_name = file_path[0]
        self.config['data_file'] = self.f_name
        self.dump_config = not self.dump_config
        self.load_data = not self.load_data
        self.popup.dismiss()

    def load_data_dic(self, data_dic):
        self.data = data_dic
        print(self.data)
        self.load_format()

    def on_answer_change(self, instance, value):
        self.dump_data = not self.dump_data

    def on_format_change(self, instance, value):
        self.load_format()

    def on_removed(self, instance, value):
        self.data['format'].remove(instance.question_json)
        self.load_format()

    def on_add_question(self, instance):
        self.popup = EditQuestionPopup(title='Add a new question', auto_dismiss=False)
        self.popup.bind(finished=lambda instance, value: self.add_question(instance.question_json))
        self.popup.open()

    def add_question(self, question_json):
        self.data['format'].append(question_json)
        # with open(self.f_name, 'w') as f:
        #     f.write(json.dumps(self.data, indent=4))
        self.dump_data = not self.dump_data
        self.load_format()

    # def on_keyboard_down(self, keyboard, keycode, text, modifiers, who_knows):
    def on_keyboard_down(self, *args):
        if args[1] == 27:
            for widget in App.get_running_app().root_window.children:
                if type(widget) == EditQuestionPopup:
                    widget.on_discard(widget)
                    return True
                elif type(widget) == Popup:
                    widget.dismiss()
                    return True
            if self.screen_manager.current == 'HWYD_ana_screen':
                screen = self.screen_manager.get_screen(self.screen_manager.current)
                screen.to_main = not screen.to_main
                return True
