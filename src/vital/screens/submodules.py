"""子模块总览页面"""

from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp

from vital.data import (
    load_submodules,
    get_submodules_by_category,
    get_category_label,
)


class SubmodulesScreen(Screen):
    """子模块总览页面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.submodules = load_submodules()
        self.current_filter = None
        self.build_ui()

    def build_ui(self):
        """构建界面"""
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        # 标题
        title = Label(
            text="子模块总览",
            font_size=dp(24),
            size_hint_y=None,
            height=dp(40),
        )
        root.add_widget(title)

        # 过滤按钮
        filter_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )

        btn_all = Button(text="全部", on_press=lambda x: self.apply_filter(None))
        btn_procedural = Button(
            text="程序型", on_press=lambda x: self.apply_filter("procedural")
        )
        btn_declarative = Button(
            text="陈述型", on_press=lambda x: self.apply_filter("declarative")
        )

        filter_bar.add_widget(btn_all)
        filter_bar.add_widget(btn_procedural)
        filter_bar.add_widget(btn_declarative)
        root.add_widget(filter_bar)

        # 子模块列表容器
        self.list_container = ScrollView()
        self.list_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(5),
        )
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        self.list_container.add_widget(self.list_layout)
        root.add_widget(self.list_container)

        # 底部统计
        self.count_label = Label(
            text=self._get_count_text(),
            size_hint_y=None,
            height=dp(30),
        )
        root.add_widget(self.count_label)

        self.add_widget(root)
        self.refresh_list()

    def _get_count_text(self) -> str:
        """获取统计文本"""
        filtered = get_submodules_by_category(self.submodules, self.current_filter)
        return f"共 {len(filtered)} 个子模块"

    def apply_filter(self, category: str):
        """应用分类过滤"""
        self.current_filter = category
        self.refresh_list()

    def refresh_list(self):
        """刷新子模块列表"""
        self.list_layout.clear_widgets()
        filtered = get_submodules_by_category(self.submodules, self.current_filter)

        for sub in filtered:
            item = self._create_item(sub)
            self.list_layout.add_widget(item)

        self.count_label.text = self._get_count_text()

    def _create_item(self, sub: dict) -> BoxLayout:
        """创建单个子模块项"""
        item = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(60),
            padding=dp(8),
        )

        # 名称和分类
        header = BoxLayout(orientation="horizontal")
        name_label = Label(
            text=sub.get("name", ""),
            font_size=dp(16),
            bold=True,
            halign="left",
            size_hint_x=0.6,
        )
        name_label.bind(size=name_label.setter("text_size"))

        category_text = get_category_label(sub.get("category", ""))
        if sub.get("type"):
            category_text += f" - {sub['type']}"
        elif sub.get("grid"):
            category_text += f" - {sub['grid']}"

        category_label = Label(
            text=category_text,
            font_size=dp(12),
            halign="right",
            size_hint_x=0.4,
        )
        category_label.bind(size=category_label.setter("text_size"))

        header.add_widget(name_label)
        header.add_widget(category_label)
        item.add_widget(header)

        # 路径和描述
        desc = sub.get("description", "")
        path = sub.get("path", "")
        info_label = Label(
            text=f"{path} | {desc}",
            font_size=dp(12),
            halign="left",
            color=(0.6, 0.6, 0.6, 1),
        )
        info_label.bind(size=info_label.setter("text_size"))
        item.add_widget(info_label)

        return item
