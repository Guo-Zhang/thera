"""vital 应用测试"""

from vital.app import VitalApp


def test_app_creation():
    """测试 VitalApp 能否正常创建"""
    app = VitalApp()
    assert app is not None
    assert app.name == "vital"


def test_home_screen():
    """测试 HomeScreen 能否正常创建"""
    from vital.screens import HomeScreen

    screen = HomeScreen(name="home")
    assert screen is not None
    assert screen.name == "home"
