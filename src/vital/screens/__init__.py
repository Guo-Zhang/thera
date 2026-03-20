from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.metrics import dp

from vital.screens.submodules import SubmodulesScreen


class HomeScreen(Screen):
    """主页 - 导航入口"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))

        # 标题
        layout.add_widget(
            Label(text="vital", font_size=dp(48), size_hint_y=None, height=dp(80))
        )

        # 导航按钮
        btn_submodules = Button(
            text="子模块总览",
            size_hint_y=None,
            height=dp(50),
            on_press=self.goto_submodules,
        )
        layout.add_widget(btn_submodules)

        # 占位
        layout.add_widget(Label())

        self.add_widget(layout)

    def goto_submodules(self, instance):
        """跳转到子模块页面"""
        self.manager.current = "submodules"


__all__ = ["HomeScreen", "SubmodulesScreen"]
