import kivy

kivy.require('1.0.6') 
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from calendar_ui import CalendarWidget
from kivy.utils import platform
from kivy.uix.actionbar import ActionBar, ActionGroup, ActionView, ActionButton, ActionOverflow, ActionPrevious
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView, FileChooser
from kivy.utils import platform
import os
import json
from pathlib import Path

from questionWidget import QuestionWidget
if platform == 'android':
    from android.storage import app_storage_path, primary_external_storage_path, secondary_external_storage_path
    from android.permissions import request_permissions, Permission

class HwydScreen(BoxLayout):

    def __init__(self, **kwargs):
        super(HwydScreen, self).__init__(orientation='vertical')
        self.config_file = kwargs['config_file']
        with open(self.config_file, 'r') as f:
            try:
                self.config = json.load(f)
            except:
                self.config = {}
        try:
            self.f_name = self.config['data_file']
        except:
            self.f_name = 'data.json'
            self.config['data_file'] = 'data.json'
            with open(self.config_file, 'w') as f:
                f.write(json.dumps(self.config, indent=4))

        print(self.config)

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




        self.calendar = CalendarWidget()
        self.calendar.bind(current_date=self.on_calendar_touch)
        self.add_widget(self.calendar)

        # try if no 'format' key 
        try:
            # try if no 'current date' key
            try:
                answers = self.data[self.calendar.get_current_date()].copy()
            except:
                answers = {}
            self.question_widgets = {}
            for question in self.data['format']:
                qw = QuestionWidget(**question)
                qw.bind(changed=self.on_question_change)
                self.question_widgets[question['question']] = qw
                # try if no 'question' key
                try:
                    qw.load_answer(answers[question['question']])
                except:
                    qw.clear_answer()
                self.add_widget(qw)
        except:
            self.data['format'] = []
        


        self.add_question_button = Button(text='Add Question')
        self.add_question_button.bind(on_press=self.add_question)
        self.add_widget(self.add_question_button)

    def on_file(self, instance):
        content = BoxLayout(orientation='vertical')
        popup = Popup(title = 'Choose a directory where to save your data or a data.json file with the correct format', content=content, auto_dismiss=False)
        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
            file_chooser = FileChooserListView(path=primary_external_storage_path(), dirselect=True, multiselect=False)
        else:
            file_chooser = FileChooserListView(path='/', dirselect=True, multiselect=False)
        load_file_btn = Button(text='Save', size_hint=(0.3, 0.1), pos_hint={'center_x' : 0.5})
        load_file_btn.bind(on_press=lambda instance: self.on_load_file(instance, popup, file_chooser.selection))
        content.add_widget(file_chooser)
        content.add_widget(load_file_btn)
        popup.open()

    def on_load_file(self, instance, popup, file_path):
        if os.path.isdir(file_path[0]):
            p = Path(os.path.join(file_path[0], 'data.json'))
            p.touch(exist_ok=False)
            self.f_name = str(p)
        else:
            self.f_name = file_path[0]
        self.config['data_file'] = self.f_name
        with open(self.config_file, 'w') as f:
            f.write(json.dumps(self.config, indent=4))
        popup.dismiss()


    def on_stop(self):
        with open(self.f_name, 'w') as f:
            f.write(json.dumps(self.data, indent=4))
    
    def on_calendar_touch(self, instance, value):
        # try if no 'current date' key
        try:
            answers = self.data[self.calendar.get_current_date()].copy()
        except KeyError:
            self.data[self.calendar.get_current_date()] = {}
            answers = self.data[self.calendar.get_current_date()].copy()
        for question in self.question_widgets:
            qw = self.question_widgets[question]
            # try if no 'question' key
            if answers != {}:
                try:
                    answer = answers[question].copy()
                    qw.load_answer(answers[question])
                except KeyError:
                    qw.clear_answer()
            else:
                qw.clear_answer()

    def on_question_change(self, instance, value):
        try:
            date_data = self.data[self.calendar.get_current_date()].copy()
        except KeyError:
            date_data = {}
        date_data[instance.question] = instance.answer.copy()
        self.data[self.calendar.get_current_date()] = date_data.copy()
        with open(self.f_name, 'w') as f:
            f.write(json.dumps(self.data, indent=4))

    def add_question(self, instance):
        content = BoxLayout(orientation='vertical')
        question_json = {'question' : "", 'options' : []}

        question_txt = TextInput(hint_text='Question', multiline=False)
        question_txt.bind(text=lambda instance, txt: self.on_question_txt(instance, txt, question_json))

        answer_layout = GridLayout(cols=2)
        unconstrained_txt = TextInput(hint_text='Unconstrained Answer')
        unconstrained_btn = Button(text='Add')
        unconstrained_btn.bind(on_press=lambda instance: question_json['options'].append(['unconstrained input', unconstrained_txt.text]))
        exclusive_opt_txt = TextInput(hint_text='Exclusive Option')
        exclusive_opt_btn = Button(text='Add')
        exclusive_opt_btn.bind(on_press=lambda instance: question_json['options'].append(['exclusive option', exclusive_opt_txt.text]))
        inclusive_opt_txt = TextInput(hint_text='Inclusive Option')
        inclusive_opt_btn = Button(text='Add')
        inclusive_opt_btn.bind(on_press=lambda instance: question_json['options'].append(['inclusive option', inclusive_opt_txt.text]))
        answer_layout.add_widget(unconstrained_txt)
        answer_layout.add_widget(unconstrained_btn)
        answer_layout.add_widget(exclusive_opt_txt)
        answer_layout.add_widget(exclusive_opt_btn)
        answer_layout.add_widget(inclusive_opt_txt)
        answer_layout.add_widget(inclusive_opt_btn)

        button_layout = BoxLayout(orientation='horizontal')
        ok_button = Button(text='OK', size_hint=(0.2, 0.2))
        discard_button = Button(text='Discard', size_hint=(0.2, 0.2))
        button_layout.add_widget(ok_button)
        button_layout.add_widget(discard_button)

        content.add_widget(question_txt)
        content.add_widget(answer_layout)
        content.add_widget(button_layout)

        popup = Popup(title = 'Add a new question', content=content, auto_dismiss=False)

        ok_button.bind(on_press=lambda instance: self.on_okay(question_json, popup))
        discard_button.bind(on_press=popup.dismiss)
        popup.open()
    
    def on_question_txt(self, instance, text, question_json):
        question_json['question'] = text

    def on_okay(self, question_json, popup):
        self.data['format'].append(question_json)
        popup.dismiss()


class HWYD(App):

    def build(self):
        root_dir = self.user_data_dir 
        if not os.path.exists(root_dir):
            os.makedirs(root_dir)
        config_file = os.path.join(root_dir, 'config.json')
        p = Path(config_file)
        p.touch(exist_ok=True)
        self.screen = HwydScreen(root_dir = root_dir, config_file=config_file)
        return self.screen

    def on_stop(self):
        self.screen.on_stop()


if __name__=='__main__':
    HWYD().run()