import kivy
kivy.require('1.0.6')

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.layout import Layout
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.properties import BooleanProperty
from kivy.metrics import dp, sp
from copy import deepcopy


class QuestionWidget(GridLayout):

    answer_changed = BooleanProperty(True)
    format_changed = BooleanProperty(True)
    removed = BooleanProperty(True)


    def __init__(self, **kwargs):
        super(QuestionWidget, self).__init__(cols=1, size_hint_y=None, row_default_height=dp(40))
        self.question_json = kwargs
        self.answer = {}
        self.option_widgets = {}

        self.question_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.4))
        self.edit_question_btn = Button(text='Edit', size_hint=(0.05, 0.5))
        self.edit_question_btn.bind(on_press=lambda instance: self.on_edit_question(instance))
        self.question_layout.add_widget(Label(text=self.question_json['question'][0], size_hint=(0.9, 1)))

        self.question_layout.add_widget(self.edit_question_btn)
        self.add_widget(self.question_layout)

        self.inclusive_layout = None
        self.exclusive_layout = None
        self.counter_layout = None

        for opts in self.question_json['options']:
            opt = opts[0]
            text = opts[1]
            if opt == 'unconstrained input':
                text_input = TextInput(hint_text=text, multiline = False)
                text_input.bind(text=self.create_callback(text))
                self.add_widget(text_input)
                self.option_widgets[text] = text_input
                self.answer[text] = ""
            if opt == 'inclusive option':
                if self.inclusive_layout == None:
                    self.inclusive_layout = BoxLayout(orientation='horizontal')
                label_cb_layout = BoxLayout(orientation='vertical')
                label_cb_layout.add_widget(Label(text=text))
                cb = CheckBox()
                cb.bind(active=self.create_callback(text))
                label_cb_layout.add_widget(cb)
                self.inclusive_layout.add_widget(label_cb_layout)
                self.option_widgets[text] = cb
                self.answer[text] = False
            if opt == 'exclusive option':
                if self.exclusive_layout == None:
                    self.exclusive_layout = BoxLayout(orientation='horizontal')
                label_cb_layout = BoxLayout(orientation='vertical')
                label_cb_layout.add_widget(Label(text=text))
                cb = CheckBox(group=self.question_json['question'][0])
                cb.bind(active=self.create_callback(text))
                label_cb_layout.add_widget(cb)
                self.exclusive_layout.add_widget(label_cb_layout)
                self.option_widgets[text]=cb
                self.answer[text] = False
            if opt == 'counter':
                if self.counter_layout == None:      
                    self.counter_layout = BoxLayout(orientation='horizontal')
                
                plus_btn = Button(text='+')
                minus_btn = Button(text='-')
                count_input = TextInput(input_filter='float', multiline=False)
                count_input.bind(text=self.create_callback(text))
                plus_btn.bind(on_press=self.create_on_plus(text))
                minus_btn.bind(on_press=self.create_on_minus(text))
                self.counter_layout.add_widget(plus_btn)
                self.counter_layout.add_widget(count_input)
                self.counter_layout.add_widget(minus_btn)
                self.option_widgets[text]=count_input
                self.answer[text] = 0.0


        if self.inclusive_layout != None:
            self.add_widget(self.inclusive_layout)
        if self.exclusive_layout != None:
            self.add_widget(self.exclusive_layout)
        if self.counter_layout != None:
            self.add_widget(self.counter_layout)

        self.answer_changed = not self.answer_changed

    def on_edit_question(self, instance):
        from editQuestionPopup import EditQuestionPopup
        popup = EditQuestionPopup(title='Edit the Question', auto_dismiss=False, question_json=self.question_json)
        popup.bind(finished=lambda instance, value: self.on_edit_question_finisehd(popup))
        popup.bind(removed=lambda instance, value: self.on_question_removed())
        popup.open()

    def on_edit_question_finisehd(self, popup):
        self.format_changed = not self.format_changed

    def on_question_removed(self):
        self.removed = not self.removed

    def disable_edit(self):
        self.question_layout.remove_widget(self.edit_question_btn)

    def create_on_plus(self, text):
        def on_plus(instance):
            try:
                self.option_widgets[text].text = str(float(self.option_widgets[text].text) + 1)
            except ValueError:
                if self.option_widgets[text].text == '':
                    self.option_widgets[text].text=str(1.0)
                else:
                    self.option_widgets[text].text=str(0.0)
        return on_plus
    
    def create_on_minus(self, text):
        def on_minus(instance):
            try:
                self.option_widgets[text].text = str(float(self.option_widgets[text].text) - 1)
            except ValueError:
                if self.option_widgets[text].text == '':
                    self.option_widgets[text].text=str(-1.0)
                else:
                    self.option_widgets[text].text=str(0.0)
        return on_minus

    def load_answer(self, answer):
        self.answer = answer
        if self.answer == {}:
            for opts in self.question_json['options']:
                opt = opts[0]
                text = opts[1]
                if type(self.option_widgets[text]) == CheckBox:
                    self.option_widgets[text].active = False
                    self.answer[text] = False
                elif type(self.option_widgets[text]) == TextInput:
                    self.option_widgets[text].text = ''
                    self.answer[text] = ''

        for key in self.answer:
            try:
                value = answer[key]
                if type(self.option_widgets[key]) == CheckBox:
                    self.option_widgets[key].active = value
                elif type(self.option_widgets[key]) == TextInput:
                    self.option_widgets[key].text = value
            except KeyError:
                # Maybe the option is not there anymore because the question was changed
                try:
                    if type(self.option_widgets[key]) == CheckBox:
                        self.option_widgets[key].active = False
                    elif type(self.option_widgets[key]) == TextInput:
                        self.option_widgets[key].text = ''
                except KeyError:
                    pass

    def clear_answer(self):
        for key in self.option_widgets:                
            w = self.option_widgets[key]
            if type(w) == CheckBox:
                w.active = False
            elif type(w) == TextInput:
                w.text = ''

    def create_callback(self,text):
        def callback(instance, value):
            self.answer[text] = value
            self.answer_changed = not self.answer_changed
        return callback
