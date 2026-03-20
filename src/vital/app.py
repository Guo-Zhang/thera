from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager

from vital.screens import HomeScreen


class VitalApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "BlueGray"
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        return sm
