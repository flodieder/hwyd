import os
from datetime import datetime
from copy import deepcopy
import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
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
from kivy.uix.camera import Camera
from kivy.graphics import Rotate, PushMatrix, PopMatrix


class TakePhotoPopup(Popup):

    def __init__(self, root_dir, **kwargs):
        self.root_dir = root_dir
        try:
            self.camera_layout = FloatLayout()
            # self.camera_layout.canvas.add(PushMatrix())
            # self.camera_layout.canvas.add(Rotate(center=(100, 100), angle=60))
            self.camera = Camera(size_hint=(1, 1), pos=(100, 100))
            self.camera_layout.add_widget(self.camera)
            # self.camera_layout.canvas.add(PopMatrix())
        except (TypeError, ModuleNotFoundError):
            self.camera_layout = FloatLayout()
            self.camera_layout.canvas.add(PushMatrix())
            self.camera_layout.canvas.add(Rotate(origin=(20, 20), angle=50))
            label = Label(text='Not implemented', pos=(20, 20))
            print(label.center)
            self.camera_layout.add_widget(label)
            self.camera_layout.canvas.add(PopMatrix())
            # self.camera.canvas.before.add(Rotate(angle=60))

        take_photo_btn = Button(text='Take Photo', height=40, size_hint=(0.5, 1))
        take_photo_btn.bind(on_press=self.create_on_take_picture_btn())
        camera_exit_btn = Button(text='Exit', height=40, size_hint=(0.5, 1))
        camera_exit_btn.bind(on_press=lambda instance: self.dismiss())
        camera_btn_layout = GridLayout(cols=2, size_hint=(1, 0.25))
        camera_btn_layout.add_widget(take_photo_btn)
        camera_btn_layout.add_widget(camera_exit_btn)
        self.content = GridLayout(cols=1)
        self.content.add_widget(self.camera_layout)
        self.content.add_widget(camera_btn_layout)

        super(TakePhotoPopup, self).__init__(title='WHO KNOWS?', content=self.content)

    def create_on_take_picture_btn(self):
        def on_take_picture_btn(instance):
            print(self.root_dir)
            print(os.path.dirname(self.root_dir))
            print(self.camera.texture)
            print(self.question_json['question'])
            picture_path = os.path.join(os.path.dirname(self.root_dir), self.question_json['question'][0])
            if not os.path.isdir(picture_path):
                os.makedirs(picture_path)
            picture_path = os.path.join(picture_path, datetime.now().strftime("%d_%m_%Y__%H_%M_%S.jpg"))
            self.camera.texture.save(picture_path)
        return on_take_picture_btn
