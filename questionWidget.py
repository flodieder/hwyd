import kivy
kivy.require('1.0.6')

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.layout import Layout
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import BooleanProperty

class QuestionWidget(BoxLayout):

    changed = BooleanProperty(True)


    def __init__(self, **kwargs):
        super(QuestionWidget, self).__init__(orientation='vertical')

        self.inclusive_layout = None
        self.exclusive_layout = None

        self.question = kwargs['question']
        self.options = kwargs['options']
        self.answer = {}
        self.option_widgets = {}

        self.add_widget(Label(text=self.question, pos_hint={'left': 1}))
        for opts in self.options:
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
                self.inclusive_layout.add_widget(Label(text=text))
                cb = CheckBox()
                cb.bind(active=self.create_callback(text))
                self.inclusive_layout.add_widget(cb)
                self.option_widgets[text] = cb
                self.answer[text] = False
            if opt == 'exclusive option':
                if self.exclusive_layout == None:
                    self.exclusive_layout = BoxLayout(orientation='horizontal')
                self.exclusive_layout.add_widget(Label(text=text))
                cb = CheckBox(group=self.question)
                cb.bind(active=self.create_callback(text))
                self.exclusive_layout.add_widget(cb)
                self.option_widgets[text]=cb
                self.answer[text] = False

        if self.inclusive_layout != None:
            self.add_widget(self.inclusive_layout)
        if self.exclusive_layout != None:
            self.add_widget(self.exclusive_layout)

    def load_answer(self, answer):
        for key in self.answer:
            try:
                value = answer[key]
                if type(self.option_widgets[key]) == CheckBox:
                    self.option_widgets[key].active = value
                elif type(self.option_widgets[key]) == TextInput:
                    self.option_widgets[key].text = value
            except KeyError:
                if type(self.option_widgets[key]) == CheckBox:
                    self.option_widgets[key].active = False
                elif type(self.option_widgets[key]) == TextInput:
                    self.option_widgets[key].text = self.option_widgets[key].hint_text

    def clear_answer(self):
        for key in self.option_widgets:                
            w = self.option_widgets[key]
            if type(w) == CheckBox:
                w.active = False
            elif type(w) == TextInput:
                w.text = w.hint_text

    def create_callback(self,text):
        def callback(instance, value):
            self.answer[text] = value
            self.changed = not self.changed
        return callback
