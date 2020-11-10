import kivy

kivy.require('1.0.6') 
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
from kivy.utils import platform
from kivy.core.window import Window
from kivy.metrics import dp, sp
import os
import json
from pathlib import Path

from questionWidget import QuestionWidget
from editQuestionPopup import EditQuestionPopup
if platform == 'android':
    from android.storage import app_storage_path, primary_external_storage_path, secondary_external_storage_path
    from android.permissions import request_permissions, Permission

Window.softinput_mode='below_target'

class HwydScreen(BoxLayout):

    def __init__(self, **kwargs):
        super(HwydScreen, self).__init__(orientation='vertical', spacing=dp(10))
        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
        
        if not os.path.exists(kwargs['root_dir']):
            os.makedirs(kwargs['root_dir'])
        self.config_file = os.path.join(kwargs['root_dir'], 'config.json')
        p = Path(self.config_file)
        p.touch(exist_ok=True)

        with open(self.config_file, 'r') as f:
            try:
                self.config = json.load(f)
            except:
                self.config = {}
        try:
            self.f_name = self.config['data_file']
        except KeyError:
            self.f_name = 'data.json'
            self.config['data_file'] = 'data.json'
            with open(self.config_file, 'w') as f:
                f.write(json.dumps(self.config, indent=4))

        try:
            with open(self.f_name, 'r') as f:
                try:
                    self.data = json.load(f)
                except:
                    self.data = {}
        except:
            Path(self.f_name).touch()
            self.data = {}
        
        action_bar = ActionBar(pos_hint={'top':1.3})
        action_view = ActionView()
        action_previous = ActionPrevious(with_previous=False)
        action_view.add_widget(action_previous)
        choose_file_btn = ActionButton(text='File')
        choose_file_btn.bind(on_press=self.on_file)
        action_view.add_widget(choose_file_btn)
        action_bar.add_widget(action_view)
        self.add_widget(action_bar)

        self.calendar = CalendarWidget(size_hint=(1, 0.3))
        self.calendar.bind(current_date=self.on_calendar_touch)
        self.add_widget(self.calendar)

        self.scroll_view = ScrollView(size_hint=(1, 0.6))
        self.scroll_view.do_scroll_x=False
        self.scroll_view.do_scroll_y=True

        self.load_format() 

        self.add_widget(self.scroll_view)

        self.add_question_button = Button(text='Add Question', size_hint=(0.3, 0.1), pos_hint={'center_x' : 0.5})
        self.add_question_button.bind(on_press=self.on_add_question)
        self.add_widget(self.add_question_button)

    def adjust_scroll_view_height(self, instance, value):
        instance.height = value + len(self.children)*dp(10)

    def load_format(self):
        self.scroll_view.clear_widgets()
        scroll_view_content = GridLayout(size_hint_y=None,cols = 1, spacing=dp(60), padding=(0, dp(20), 0, dp(20)))
        scroll_view_content.bind(minimum_height=lambda instance, value: self.adjust_scroll_view_height(instance, value))

        # try if no 'format' key 
        try:
            # try if no 'current date' key
            try:
                answers = self.data[self.calendar.get_current_date()]
            except:
                self.data[self.calendar.get_current_date()] = {}
                answers = self.data[self.calendar.get_current_date()]
            self.question_widgets = {}
            for question in self.data['format']:
                qw = QuestionWidget(**question)
                qw.bind(answer_changed=self.on_answer_change)
                qw.bind(format_changed=self.on_format_change)
                qw.bind(removed=self.on_removed)
                self.question_widgets[question['question'][0]] = qw
                # try if no 'question' key
                try:
                    qw.load_answer(answers[question['question'][0]])
                except:
                    answers[question['question'][0]] = {}
                    qw.load_answer(answers[question['question'][0]])
                scroll_view_content.add_widget(qw)
        except KeyError:
            self.data['format'] = []
        except:
            pass
        self.scroll_view.add_widget(scroll_view_content)
        
    def on_file(self, instance):
        content = BoxLayout(orientation='vertical')
        popup = Popup(title = 'Choose a directory where to save your data or a data.json file with the correct format', content=content, auto_dismiss=False)
        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
            file_chooser = FileChooserListView(path=primary_external_storage_path(), dirselect=True, multiselect=False)
        else:
            file_chooser = FileChooserListView(path='/', dirselect=True, multiselect=False)
        button_layout = BoxLayout(orientation='horizontal', spacing=dp(20), size_hint=(1, 0.2))
        load_file_btn = Button(text='Load', size_hint=(0.1, 1), pos_hint={'center_x' : 0.25})
        load_file_btn.bind(on_press=lambda instance: self.on_load_file(instance, popup, file_chooser.selection))
        save_file_btn = Button(text='Save', size_hint=(0.1, 1), pos_hint={'center_x' : 0.75})
        save_file_btn.bind(on_press=lambda instance: self.on_save_file(instance, popup, file_chooser.selection))
        button_layout.add_widget(load_file_btn)
        button_layout.add_widget(save_file_btn)
        content.add_widget(file_chooser)
        content.add_widget(button_layout)
        popup.open()

    def on_save_file(self, instance, popup, file_path):
        if os.path.isdir(file_path[0]):
            p = Path(os.path.join(file_path[0], 'data.json'))
            p.touch(exist_ok=False)
            self.f_name = str(p)
        else:
            self.f_name = file_path[0]
        self.config['data_file'] = self.f_name
        with open(self.config_file, 'w') as f:
            f.write(json.dumps(self.config, indent=4))
        with open(self.f_name, 'w') as f:
            f.write(json.dumps(self.data, indent=4))
        popup.dismiss()

    def on_load_file(self, instance, popup, file_path):
        if os.path.isdir(file_path[0]):
            # Give error hint
            return
        else:
            self.f_name = file_path[0]
        self.config['data_file'] = self.f_name
        with open(self.config_file, 'w') as f:
            f.write(json.dumps(self.config, indent=4))
        with open(self.f_name, 'r') as f:
            try:
                self.data = json.load(f)
            except:
                self.data = {}
        popup.dismiss()
        self.load_format()


    def on_stop(self):
        with open(self.f_name, 'w') as f:
            f.write(json.dumps(self.data, indent=4))
    
    def on_calendar_touch(self, instance, value):
        # try if no 'current date' key
        try:
            answers = self.data[self.calendar.get_current_date()]
        except KeyError:
            self.data[self.calendar.get_current_date()] = {}
            answers = self.data[self.calendar.get_current_date()]
        for question in self.question_widgets:
            qw = self.question_widgets[question]
            # try if no 'question' key
            try:
                qw.load_answer(answers[question])
            except KeyError as error:
                answers[qw.question_json['question'][0]] = {} 
                qw.load_answer(answers[qw.question_json['question'][0]])

    def on_answer_change(self, instance, value):
        with open(self.f_name, 'w') as f:
            f.write(json.dumps(self.data, indent=4))

    def on_format_change(self, instance, value):
        self.load_format()

    def on_removed(self, instance, value):
        self.data['format'].remove(instance.question_json)
        self.load_format()

    def on_add_question(self, instance):
        popup = EditQuestionPopup(title = 'Add a new question', auto_dismiss=False) 
        popup.bind(finished=lambda instance, value: self.add_question(instance.question_json))
        popup.open()

    def add_question(self, question_json):
        self.data['format'].append(question_json)
        with open(self.f_name, 'w') as f:
            f.write(json.dumps(self.data, indent=4))
        self.load_format()


class HWYD(App):

    def build(self):
        root_dir = self.user_data_dir 
        self.screen = HwydScreen(root_dir = root_dir)
        return self.screen

    def on_stop(self):
        self.screen.on_stop()


if __name__=='__main__':
    HWYD().run()
