"""
测试 cli.py 模块
"""
import unittest
from unittest.mock import patch
from io import StringIO

from src.thera.cli import TheraCLI


class TestTheraCLI(unittest.TestCase):
    """测试 TheraCLI 类"""
    
    def setUp(self):
        """测试前的设置"""
        self.cli = TheraCLI()
        # 捕获标准输出
        self.stdout = StringIO()
        self.patcher = patch('sys.stdout', self.stdout)
        self.patcher.start()
    
    def tearDown(self):
        """测试后的清理"""
        self.patcher.stop()
    
    def test_intro_and_prompt(self):
        """测试欢迎信息和提示符"""
        self.assertIn("欢迎使用", self.cli.intro)
        self.assertEqual("thera> ", self.cli.prompt)
    
    def test_empty_line(self):
        """测试空行处理"""
        initial_output = self.stdout.getvalue()
        self.cli.emptyline()
        self.assertEqual(initial_output, self.stdout.getvalue())
    
    def test_exit_command(self):
        """测试退出命令"""
        result = self.cli.do_exit("")
        self.assertTrue(result)
        self.assertIn("再见", self.stdout.getvalue())
    
    def test_quit_command(self):
        """测试quit命令"""
        result = self.cli.do_quit("")
        self.assertTrue(result)
        self.assertIn("再见", self.stdout.getvalue())
    
    def test_eof_command(self):
        """测试EOF（Ctrl-D/Ctrl-Z）处理"""
        result = self.cli.do_EOF("")
        self.assertTrue(result)
        self.assertIn("再见", self.stdout.getvalue())
    
    @patch('importlib.metadata.version')
    def test_version_command(self, mock_version):
        """测试version命令"""
        # 模拟版本号
        mock_version.return_value = "0.1.0"
        
        self.cli.do_version("")
        output = self.stdout.getvalue()
        self.assertIn("Thera version 0.1.0", output)
    
    @patch('importlib.metadata.version')
    def test_version_command_error(self, mock_version):
        """测试version命令出错情况"""
        # 模拟版本获取失败
        mock_version.side_effect = Exception("测试异常")
        
        self.cli.do_version("")
        output = self.stdout.getvalue()
        self.assertIn("无法获取版本信息", output)


if __name__ == '__main__':
    unittest.main()