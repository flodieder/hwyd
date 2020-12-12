import kivy

kivy.require('1.0.6')
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


class EditQuestionPopup(Popup):

    finished = BooleanProperty(True)
    removed = BooleanProperty(True)

    def __init__(self, **kwargs):
        self.content = GridLayout(cols=1, row_default_height=dp(40))
        try:
            self.old_question_json = deepcopy(kwargs['question_json'])
            self.question_json = kwargs['question_json']
        except KeyError:
            self.question_json = {'question': [''], 'options': [], 'scheduling': ['daily', '']}

        self.scheduling_layout = BoxLayout(orientation='horizontal', size_hint_y=0.01)
        scheduling_scheme = self.question_json['scheduling'][0]
        schedule_spinner = Spinner(text=scheduling_scheme,
                                   values=('daily', 'weekly', 'monthly'),
                                   size_hint=(1, 1))
        if scheduling_scheme == 'daily':
            self.second_schedule_spinner = Spinner(text='', size_hint=(1, 1))
        elif scheduling_scheme == 'weekly':
            self.second_schedule_spinner = Spinner(values=('Monday', 'Tuesday', 'Wednesday',
                                                           'Thursday', 'Friday', 'Saturday',
                                                           'Sunday'))
            self.second_schedule_spinner.text = self.question_json['scheduling'][1]
        elif scheduling_scheme == 'monthly':
            self.second_schedule_spinner = Spinner(values=('Start', 'Mid', 'End'))
            self.second_schedule_spinner.text = self.question_json['scheduling'][1]
        self.second_schedule_spinner.bind(text=self.on_second_schedule_spinner)
        schedule_spinner.bind(text=lambda instance, txt: self.on_schedule_spinner(instance, txt))
        self.scheduling_layout.add_widget(schedule_spinner)
        self.scheduling_layout.add_widget(self.second_schedule_spinner)
        self.content.add_widget(self.scheduling_layout)

        self.content.add_widget(Label(text='Preview:', size_hint=(1, 0.01)))

        self.qw = QuestionWidget(**self.question_json)
        self.qw.disable_edit()
        self.qw.size_hint_y = 0.1
        self.content.add_widget(self.qw)

        question_txt = TextInput(hint_text='Question', multiline=False, size_hint_y=0.05)
        if self.question_json['question'][0] != "":
            question_txt.text = self.question_json['question'][0]
        question_txt.bind(text=lambda instance, txt: self.on_question_txt(instance, txt))

        answer_layout = GridLayout(cols=3, size_hint_y=0.3)

        unconstrained_txt = TextInput(hint_text='Unconstrained Answer')
        unconstrained_add_btn = Button(text='Add')
        unconstrained_add_btn.bind(on_press=lambda instance: self.on_add_question_opt_added(
            instance, 'unconstrained input', unconstrained_txt.text))
        unconstrained_remove_btn = Button(text='Remove')
        unconstrained_remove_btn.bind(on_press=lambda instance: self.on_remove_question_opt_added(
            instance, 'unconstrained input'))

        exclusive_opt_txt = TextInput(hint_text='Exclusive Option')
        exclusive_opt_add_btn = Button(text='Add')
        exclusive_opt_add_btn.bind(on_press=lambda instance: self.on_add_question_opt_added(
            instance, 'exclusive option', exclusive_opt_txt.text))
        exclusive_opt_remove_btn = Button(text='Remove')
        exclusive_opt_remove_btn.bind(on_press=lambda instance: self.on_remove_question_opt_added(
            instance, 'exclusive option'))

        inclusive_opt_txt = TextInput(hint_text='Inclusive Option')
        inclusive_opt_add_btn = Button(text='Add')
        inclusive_opt_add_btn.bind(on_press=lambda instance: self.on_add_question_opt_added(
            instance, 'inclusive option', inclusive_opt_txt.text))
        inclusive_opt_remove_btn = Button(text='Remove')
        inclusive_opt_remove_btn.bind(on_press=lambda instance: self.on_remove_question_opt_added(
            instance, 'inclusive option'))

        counter_txt = TextInput(hint_text='Counter')
        counter_add_btn = Button(text='Add')
        counter_add_btn.bind(on_press=lambda instance: self.on_add_question_opt_added(
            instance, 'counter', counter_txt.text))
        counter_remove_btn = Button(text='Remove')
        counter_remove_btn.bind(
            on_press=lambda instance: self.on_remove_question_opt_added(instance, 'counter'))

        answer_layout.add_widget(unconstrained_txt)
        answer_layout.add_widget(unconstrained_add_btn)
        answer_layout.add_widget(unconstrained_remove_btn)
        answer_layout.add_widget(exclusive_opt_txt)
        answer_layout.add_widget(exclusive_opt_add_btn)
        answer_layout.add_widget(exclusive_opt_remove_btn)
        answer_layout.add_widget(inclusive_opt_txt)
        answer_layout.add_widget(inclusive_opt_add_btn)
        answer_layout.add_widget(inclusive_opt_remove_btn)
        answer_layout.add_widget(counter_txt)
        answer_layout.add_widget(counter_add_btn)
        answer_layout.add_widget(counter_remove_btn)

        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.05)
        ok_button = Button(text='OK', size_hint=(0.2, 1))
        ok_button.bind(on_press=lambda instance: self.on_okay())
        discard_button = Button(text='Discard', size_hint=(0.2, 1))
        discard_button.bind(on_press=self.on_discard)
        remove_button = Button(text='Remove', size_hint=(0.2, 1))
        remove_button.bind(on_press=self.on_remove)
        button_layout.add_widget(ok_button)
        button_layout.add_widget(discard_button)
        button_layout.add_widget(remove_button)

        self.content.add_widget(question_txt)
        self.content.add_widget(answer_layout)
        self.content.add_widget(button_layout)

        super(EditQuestionPopup, self).__init__(title=kwargs['title'],
                                                content=self.content,
                                                auto_dismiss=kwargs['auto_dismiss'])

    def on_question_txt(self, instance, text):
        self.question_json['question'][0] = text
        self.refresh_question_widget()

    def on_schedule_spinner(self, instance, value):
        self.question_json['scheduling'][0] = value
        if value == 'daily':
            self.scheduling_layout.remove_widget(self.second_schedule_spinner)
            self.second_schedule_spinner = Spinner(text='', size_hint=(1, 1))
            self.second_schedule_spinner.bind(text=self.on_second_schedule_spinner)
            self.scheduling_layout.add_widget(self.second_schedule_spinner)
        elif value == 'weekly':
            self.scheduling_layout.remove_widget(self.second_schedule_spinner)
            self.second_schedule_spinner = Spinner(values=('Monday', 'Tuesday', 'Wednesday',
                                                           'Thursday', 'Friday', 'Saturday',
                                                           'Sunday'))
            self.second_schedule_spinner.bind(text=self.on_second_schedule_spinner)
            self.second_schedule_spinner.text = 'Monday'
            self.scheduling_layout.add_widget(self.second_schedule_spinner)
        elif value == 'monthly':
            self.scheduling_layout.remove_widget(self.second_schedule_spinner)
            self.second_schedule_spinner = Spinner(values=('Start', 'Mid', 'End'))
            self.second_schedule_spinner.bind(text=self.on_second_schedule_spinner)
            self.second_schedule_spinner.text = 'Start'
            self.scheduling_layout.add_widget(self.second_schedule_spinner)
        self.refresh_question_widget()

    def on_second_schedule_spinner(self, instance, value):
        if len(self.question_json['scheduling']) > 1:
            self.question_json['scheduling'].pop()
        self.question_json['scheduling'].append(value)
        self.refresh_question_widget()

    def refresh_question_widget(self):
        self.content.remove_widget(self.qw)
        self.qw = QuestionWidget(**self.question_json)
        self.qw.disable_edit()
        self.qw.size_hint_y = 0.1
        self.content.add_widget(self.qw, index=3)

    def on_remove_question_opt_added(self, instance, option_type):
        # Remove the last option that matches the type that should be removed
        for o in reversed(self.question_json['options']):
            if o[0] == option_type:
                self.question_json['options'].remove(o)
                self.refresh_question_widget()
                return

    def on_add_question_opt_added(self, instance, option_type, option_text):
        self.question_json['options'].append([option_type, option_text])
        self.refresh_question_widget()

    def on_okay(self):
        self.finished = not self.finished
        self.dismiss()

    def on_discard(self, instance):
        try:
            self.question_json['question'][0] = self.old_question_json['question'][0]
            self.question_json['options'].clear()
            for option in self.old_question_json['options']:
                self.question_json['options'].append(option)
        except AttributeError as err:
            pass
        self.dismiss()

    def on_remove(self, instance):
        self.removed = not self.removed
        self.dismiss()