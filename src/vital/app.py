from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.text import LabelBase

from vital.screens import HomeScreen, SubmodulesScreen

# 中文字体配置
CHINESE_FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

# 注册中文字体
LabelBase.register(name="Chinese", fn_regular=CHINESE_FONT_PATH)


class VitalApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(SubmodulesScreen(name="submodules"))
        return sm
