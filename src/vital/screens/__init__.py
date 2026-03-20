from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivy.uix.boxlayout import BoxLayout


class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20)
        layout.add_widget(MDLabel(text="vital", halign="center", font_style="H2"))
        self.add_widget(layout)
