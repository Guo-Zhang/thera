from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from vital.screens import HomeScreen, SubmodulesScreen


class VitalApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(SubmodulesScreen(name="submodules"))
        return sm
