import os
from datetime import datetime
import kivy

kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scatter import Scatter
from kivy.uix.layout import Layout
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.properties import BooleanProperty
from kivy.metrics import dp, sp
from copy import deepcopy
from kivy.uix.camera import Camera
from plyer import camera
from plyer import accelerometer

from takePhotoPopup import TakePhotoPopup


class QuestionWidget(GridLayout):

    answer_changed = BooleanProperty(True)
    format_changed = BooleanProperty(True)
    removed = BooleanProperty(True)

    def __init__(self, root_dir, **kwargs):
        super(QuestionWidget, self).__init__(cols=1,
                                             size_hint_y=None,
                                             row_default_height=dp(40))
        self.root_dir = root_dir
        self.question_json = kwargs
        self.answer = {}
        self.option_widgets = {}
        self.question_layout = BoxLayout(orientation='horizontal',
                                         size_hint=(1, 0.4))
        self.edit_question_btn = Button(text='edit', size_hint=(0.05, 0.5))
        self.edit_question_btn.bind(
            on_press=lambda instance: self.on_edit_question(instance))
        self.question_layout.add_widget(
            Label(text=self.question_json['question'][0], size_hint=(0.9, 1)))

        self.question_layout.add_widget(self.edit_question_btn)
        self.add_widget(self.question_layout)

        self.inclusive_layout = None
        self.exclusive_layout = None
        self.counter_layout = None
        self.image_layout = None
        self.timer_layout = None
        self.label_cb_layout = None

        for (option_type, option_name) in self.question_json['options']:
            if option_type == 'unconstrained input':
                self.text_input = TextInput(hint_text=option_name,
                                            multiline=True,
                                            size_hint_y=1)
                self.text_input.bind(text=self.create_callback(option_name))
                self.add_widget(self.text_input)
                self.option_widgets[option_name] = self.text_input
                self.answer[option_name] = ""
            if option_type == 'inclusive option':
                if self.inclusive_layout == None:
                    self.inclusive_layout = BoxLayout(orientation='horizontal')
                self.label_cb_layout = BoxLayout(orientation='vertical')
                self.label_cb_layout.add_widget(Label(text=option_name))
                cb = CheckBox()
                cb.bind(active=self.create_callback(option_name))
                self.label_cb_layout.add_widget(cb)
                self.inclusive_layout.add_widget(self.label_cb_layout)
                self.option_widgets[option_name] = cb
                self.answer[option_name] = False
            if option_type == 'exclusive option':
                if self.exclusive_layout == None:
                    self.exclusive_layout = BoxLayout(orientation='horizontal')
                self.label_cb_layout = BoxLayout(orientation='vertical')
                self.label_cb_layout.add_widget(Label(text=option_name))
                cb = CheckBox(group=str(self) +
                              self.question_json['question'][0])
                cb.bind(active=self.create_callback(option_name))
                self.label_cb_layout.add_widget(cb)
                self.exclusive_layout.add_widget(self.label_cb_layout)
                self.option_widgets[option_name] = cb
                self.answer[option_name] = False
            if option_type == 'counter':
                if self.counter_layout == None:
                    self.counter_layout = BoxLayout(orientation='horizontal')

                plus_btn = Button(text='+')
                minus_btn = Button(text='-')
                # count_input = TextInput(text='0.0', input_filter='float', multiline=False)
                count_input = TextInput(multiline=False)
                count_input.bind(text=self.create_callback(option_name))
                plus_btn.bind(on_press=self.create_on_plus(option_name))
                minus_btn.bind(on_press=self.create_on_minus(option_name))
                self.counter_layout.add_widget(plus_btn)
                self.counter_layout.add_widget(count_input)
                self.counter_layout.add_widget(minus_btn)
                self.option_widgets[option_name] = count_input
                self.option_widgets[option_name].text = str(0.0)
                self.answer[option_name] = "0.0"
            if option_type == 'image':
                if self.image_layout == None:
                    self.image_layout = BoxLayout(orientation='horizontal')
                picture_btn = Button(text='Take a picture')
                picture_btn.bind(on_press=self.on_picture_btn)
                self.image_layout.add_widget(picture_btn)
                self.option_widgets[option_name] = picture_btn
                self.answer[option_name] = ['']
            if option_type == 'timer':
                if self.timer_layout == None:
                    self.timer_layout = BoxLayout(orientation='horizontal')

                start_stop_btn = Button(text='Start')
                timer_remove_btn = Button(text='Remove last')
                timer_label = Label(text="")
                timer_label.bind(text=self.create_callback(option_name))
                start_stop_btn.bind(
                    on_press=self.create_on_start_stop(option_name))
                timer_remove_btn.bind(
                    on_press=self.create_on_timer_remove(option_name))
                self.timer_layout.add_widget(timer_label)
                self.timer_layout.add_widget(timer_remove_btn)
                self.timer_layout.add_widget(start_stop_btn)
                self.option_widgets[option_name] = timer_label
                self.answer[option_name] = ['']

        if self.inclusive_layout != None:
            self.add_widget(self.inclusive_layout)
        if self.exclusive_layout != None:
            self.add_widget(self.exclusive_layout)
        if self.counter_layout != None:
            self.add_widget(self.counter_layout)
        if self.image_layout != None:
            self.add_widget(self.image_layout)
        if self.timer_layout != None:
            self.add_widget(self.timer_layout)

    def on_edit_question(self, instance):
        from editQuestionPopup import EditQuestionPopup
        popup = EditQuestionPopup(title='Edit the Question',
                                  auto_dismiss=False,
                                  question_json=self.question_json)
        popup.bind(finished=lambda instance, value: self.
                   on_edit_question_finisehd(popup))
        popup.bind(removed=lambda instance, value: self.on_question_removed())
        popup.open()

    def on_edit_question_finisehd(self, popup):
        self.format_changed = not self.format_changed

    def on_question_removed(self):
        self.removed = not self.removed

    def camera_done(self, e):
        print(e)

    def on_picture_btn(self, instance):
        # camera = AndroidCamera()
        camera.take_picture(on_complete=self.camera_done,
                            filename=f"{self.root_dir} /test.jpg")
        accelerometer.enable()
        print(accelerometer.acceleration)
        camera_popup = TakePhotoPopup(root_dir=self.root_dir)
        camera_popup.open()

    def disable_edit(self):
        self.question_layout.remove_widget(self.edit_question_btn)

    def create_on_plus(self, option_name):
        def on_plus(instance):
            try:
                self.option_widgets[option_name].text = str(
                    float(self.option_widgets[option_name].text) + 1)
            except ValueError:
                if self.option_widgets[option_name].text == '':
                    self.option_widgets[option_name].text = str(1.0)
                else:
                    self.option_widgets[option_name].text = str(0.0)

        return on_plus

    def create_on_minus(self, option_name):
        def on_minus(instance):
            try:
                self.option_widgets[option_name].text = str(
                    float(self.option_widgets[option_name].text) - 1)
            except ValueError:
                if self.option_widgets[option_name].text == '':
                    self.option_widgets[option_name].text = str(-1.0)
                else:
                    self.option_widgets[option_name].text = str(0.0)

        return on_minus

    def create_on_start_stop(self, option_name):
        def on_start_stop(instance):
            if instance.text == 'Start':
                instance.text = 'Stop'
                if self.option_widgets[option_name].text == '':
                    self.option_widgets[option_name].text += "Start: " + str(
                        datetime.now().strftime("%H:%M:%S"))
                else:
                    self.option_widgets[
                        option_name].text += '\n' + "Start: " + str(
                            datetime.now().strftime("%H:%M:%S"))
            elif instance.text == 'Stop':
                instance.text = 'Start'
                self.option_widgets[option_name].text += '\n' + "Stop: " + str(
                    datetime.now().strftime("%H:%M:%S"))

        return on_start_stop

    def create_on_timer_remove(self, option_name):
        def on_timer_remove(instance):
            last_lb_idx = self.option_widgets[option_name].text.rfind('\n')
            if last_lb_idx == -1:
                self.option_widgets[option_name].text = ''
            else:
                self.option_widgets[option_name].text = self.option_widgets[
                    option_name].text[:last_lb_idx]

        return on_timer_remove

    def load_answer(self, answer):
        self.answer = answer
        if self.answer == {}:
            for opts in self.question_json['options']:
                option_type = opts[0]
                option_name = opts[1]
                if type(self.option_widgets[option_name]) == CheckBox:
                    self.option_widgets[option_name].active = False
                    self.answer[option_name] = False
                elif type(self.option_widgets[option_name]) == TextInput:
                    if option_type == 'counter':
                        self.option_widgets[option_name].text = '0.0'
                        self.answer[option_name] = '0.0'
                    else:
                        self.option_widgets[option_name].text = ''
                        self.answer[option_name] = ''

        for key in self.answer:
            try:
                value = answer[key]
                if type(self.option_widgets[key]) == CheckBox:
                    self.option_widgets[key].active = value
                elif type(self.option_widgets[key]) == TextInput:
                    self.option_widgets[key].text = value
                elif type(self.option_widgets[key]) == Label:
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

    def create_callback(self, option_name):
        def callback(instance, value):
            self.answer[option_name] = value
            self.answer_changed = not self.answer_changed

        return callback
