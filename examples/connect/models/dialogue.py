"""
"""


class Dialogue:
    """
    慢思考模式的对话系统
    """

    def __init__(self) -> None:
        self.context = ""

    def update_context(context: str, human_message: str) -> str:
        """
        更新语境
        """
        pass


    def generate_message(context: str, human_message: str) -> str:
        """
        生成消息
        """
        pass



def main() -> None:
    """
    主函数
    """
    print("欢迎来到慢思考模式的对话系统！")
    human_message = input("请输入你的问题：")
    conversation = Dialogue()
    context = conversation.update_context("", human_message)
    conversation.generate_message(context, human_message)


if __name__ == "__main__":
    main()
