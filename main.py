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

import os
import json
from pathlib import Path

from questionWidget import QuestionWidget


class HwydScreen(BoxLayout):

    def __init__(self, **kwargs):
        super(HwydScreen, self).__init__(orientation='vertical')
        self.f_name = 'data.json'
        try:
            with open(self.f_name, 'r') as f:
                try:
                    self.data = json.load(f)
                except:
                    self.data = {}
        except:
            Path(self.f_name).touch()
            self.data = {}

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

        question_txt = TextInput(hint_text='Question')
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

        ok_button.bind(on_press=lambda instance: self.on_okay(question_json))
        discard_button.bind(on_press=popup.dismiss)
        popup.open()
    
    def on_question_txt(self, instance, text, question_json):
        question_json['question'] = text

    def on_okay(self, question_json):
        self.data['format'].append(question_json)


class HWYD(App):

    def build(self):
        root_dir = self.user_data_dir 
        if not os.path.exists(root_dir):
            os.makedirs(root_dir)
        data_file = os.path.join(root_dir, 'data.json')
        p = Path(data_file)
        p.touch(exist_ok=True)
        self.screen = HwydScreen(root_dir = root_dir, data_file=data_file)
        return self.screen

    def on_stop(self):
        self.screen.on_stop()


if __name__=='__main__':
    HWYD().run()