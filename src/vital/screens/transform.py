"""模糊进清晰出 - 转换过程可视化"""

from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp

from vital.data import (
    load_raw_journal,
    load_episode,
    get_available_dates,
    get_tense_label,
    get_event_type_label,
)

FONT_NAME = "Chinese"


class TransformScreen(Screen):
    """模糊进清晰出 - 转换过程可视化"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dates = get_available_dates()
        self.current_date = self.dates[0] if self.dates else None
        self.build_ui()

    def build_ui(self):
        """构建界面"""
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        # 标题
        title = Label(
            text="模糊进清晰出",
            font_size=dp(24),
            font_name=FONT_NAME,
            size_hint_y=None,
            height=dp(40),
        )
        root.add_widget(title)

        # 日期选择
        date_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )

        btn_prev = Button(
            text="<",
            font_name=FONT_NAME,
            size_hint_x=0.2,
            on_press=self.prev_date,
        )
        self.date_label = Label(
            text=self.current_date or "无数据",
            font_size=dp(16),
            font_name=FONT_NAME,
            size_hint_x=0.6,
        )
        btn_next = Button(
            text=">",
            font_name=FONT_NAME,
            size_hint_x=0.2,
            on_press=self.next_date,
        )

        date_bar.add_widget(btn_prev)
        date_bar.add_widget(self.date_label)
        date_bar.add_widget(btn_next)
        root.add_widget(date_bar)

        # 两栏内容
        content = BoxLayout(orientation="horizontal", spacing=dp(10))

        # 原始输入
        raw_box = self._create_column("原始输入", "[模糊]")
        self.raw_content = raw_box.children[0]  # ScrollView
        content.add_widget(raw_box)

        # 提炼后
        episode_box = self._create_column("提炼后", "[结构化]")
        self.episode_content = episode_box.children[0]
        content.add_widget(episode_box)

        root.add_widget(content)

        self.add_widget(root)
        self.refresh_content()

    def _create_column(self, title: str, subtitle: str) -> BoxLayout:
        """创建单列"""
        box = BoxLayout(orientation="vertical", spacing=dp(5))

        # 列标题
        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(50))
        header.add_widget(
            Label(
                text=title,
                font_size=dp(16),
                font_name=FONT_NAME,
                bold=True,
            )
        )
        header.add_widget(
            Label(
                text=subtitle,
                font_size=dp(12),
                font_name=FONT_NAME,
                color=(0.6, 0.6, 0.6, 1),
            )
        )
        box.add_widget(header)

        # 内容区域
        scroll = ScrollView()
        content_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(5),
            padding=dp(5),
        )
        content_layout.bind(minimum_height=content_layout.setter("height"))
        scroll.add_widget(content_layout)
        box.add_widget(scroll)

        return box

    def _get_content_layout(self, scroll: ScrollView):
        """获取 ScrollView 中的 content layout"""
        return scroll.children[0]

    def prev_date(self, instance):
        """切换到前一个日期"""
        if not self.dates or not self.current_date:
            return

        idx = self.dates.index(self.current_date)
        if idx < len(self.dates) - 1:
            self.current_date = self.dates[idx + 1]
            self.refresh_content()

    def next_date(self, instance):
        """切换到后一个日期"""
        if not self.dates or not self.current_date:
            return

        idx = self.dates.index(self.current_date)
        if idx > 0:
            self.current_date = self.dates[idx - 1]
            self.refresh_content()

    def refresh_content(self):
        """刷新内容"""
        if not self.current_date:
            return

        self.date_label.text = self.current_date

        # 清空内容
        self._get_content_layout(self.raw_content).clear_widgets()
        self._get_content_layout(self.episode_content).clear_widgets()

        # 加载原始日志
        raw_text = load_raw_journal(self.current_date)
        if raw_text:
            raw_label = Label(
                text=raw_text,
                font_size=dp(12),
                font_name=FONT_NAME,
                halign="left",
                valign="top",
                size_hint_y=None,
                text_size=(dp(300), None),
            )
            raw_label.bind(texture_size=raw_label.setter("size"))
            self._get_content_layout(self.raw_content).add_widget(raw_label)

        # 加载提炼后事件记忆
        episodes = load_episode(self.current_date)
        for ep in episodes:
            item = self._create_episode_item(ep)
            self._get_content_layout(self.episode_content).add_widget(item)

    def _create_episode_item(self, episode: dict) -> BoxLayout:
        """创建单个事件记忆项"""
        item = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(80),
            padding=dp(5),
        )

        # 标题
        title_label = Label(
            text=episode.get("title", ""),
            font_size=dp(14),
            font_name=FONT_NAME,
            bold=True,
            halign="left",
            size_hint_y=None,
            height=dp(20),
        )
        title_label.bind(size=title_label.setter("text_size"))
        item.add_widget(title_label)

        # 描述
        desc_label = Label(
            text=episode.get("description", ""),
            font_size=dp(11),
            font_name=FONT_NAME,
            halign="left",
            size_hint_y=None,
            height=dp(40),
            color=(0.4, 0.4, 0.4, 1),
        )
        desc_label.bind(size=desc_label.setter("text_size"))
        item.add_widget(desc_label)

        # 标签
        tense = get_tense_label(episode.get("tense", ""))
        event_type = get_event_type_label(episode.get("type", ""))
        tag_label = Label(
            text=f"{tense} | {event_type}",
            font_size=dp(10),
            font_name=FONT_NAME,
            halign="left",
            size_hint_y=None,
            height=dp(15),
            color=(0.6, 0.6, 0.6, 1),
        )
        tag_label.bind(size=tag_label.setter("text_size"))
        item.add_widget(tag_label)

        return item
