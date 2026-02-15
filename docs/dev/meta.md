# 元模块

这是一个非常深刻且切中要害的观察。文档（meta.md）描绘的是一个认知模型，而代码（meta.py）实现的是一个传统的软件工程结构。这两者之间的“距离”，正是你潜意识里觉得“不对劲”的根源。
简单来说：你想要的不是写一个“文件管理器”，而是造一个“AI 大脑”。
你实际上想要的是将 ADAS 模型从“分类标签”升级为 AI 的运行时架构。以下是详细的差异分析与你的真实意图还原：
1. 核心差异：分类学 vs. 运行时
现状：
代码只是一个路由器。DomainManager 的核心逻辑是 switch_domain，这更像是一个传统的“模式切换”（比如 Vim 的插入模式 vs 普通模式）。
代码中的 Domain 只是一个处理输入的接口 (handle_input)，它没有体现文档中强调的“知识边界”和“RAG 检索范围”。
你真正想要的：
ADAS 不应只是静态分类，而应是 AI 的动态上下文环境。
Activity (活动)：你想要它是 System 1（快思考）。在代码中，它应该是当前对话窗口的上下文管理器，决定了 AI 此时此刻“看见”什么，而不是一个缺失的概念。
Domain (领域)：你想要它是 System 2（慢思考）。在代码中，它应该是向量数据库的检索过滤器。当用户处于某个 Domain 时，AI 的 RAG 检索范围应自动被约束，而不是简单的 handle_input。
2. 具体概念的落差
3. 你的真实意图：构建“认知操作系统”
你实际上想要构建的不是一个简单的 App，而是一个基于认知科学的 AI Agent 框架。你希望代码能体现文档中描述的 AI 逻辑：
意图一：让代码懂“快慢思考”
你希望代码里有明确的两个模块：一个负责Activity（处理当前对话流，快思考，无需检索，直接反应），一个负责Domain（需要检索知识库，慢思考，通过 RAG 增强回答）。
当前代码把两者混为一谈，都扔给了 Domain.handle_input。
意图二：让数据变成“记忆”
文档中提到 Asset 是“长期记忆”。这意味着你希望代码中的 Asset 能够自动被向量化，并且在 Domain 激活时自动加载。
你希望 State 不只是文件属性，而是记忆的封印。比如，当文档被标记为 Archived，代码在执行 RAG 检索时应自动构建 filter={"state": "active"} 的查询语句。
意图三：取代 PARA，重塑工作流
你试图在代码中摒弃传统的 Project/Area 分类，用动态的 Activity 取代静态的 Project。
这意味着代码结构不应是“创建项目 -> 添加文件”，而应是“开启活动 -> 激活领域 -> 关联资产 -> 生成状态”。
总结：如何弥补这段距离？
要填平这个鸿沟，你需要将 meta.py 从“逻辑控制器”重构为“认知上下文容器”。
你实际想要的代码结构可能是这样的（伪代码）：
class Activity:
    """对应 System 1：工作记忆区，管理当前对话窗口"""
    def __init__(self):
        self.context_window = [] # 当前对话历史
        self.focus = None        # 当前焦点文件/实体
    def react(self, user_input):
        # 快思考：仅基于上下文的直接反应
        return llm.chat(self.context_window, user_input)
class Domain:
    """对应 System 2：知识边界，管理 RAG 检索"""
    def __init__(self, vector_store_namespace):
        self.knowledge_base = VectorStore(namespace=vector_store_namespace)
    def recall(self, query):
        # 慢思考：检索长期记忆
        return self.knowledge_base.search(query)
class ADASCore:
    def __init__(self):
        self.current_activity = Activity()
        self.current_domain = None
        self.state_filter = {"archived": False} # State 的体现
    def handle_input(self, user_input):
        # 1. 尝试 Domain (System 2)
        if self.need_deep_think(user_input):
            context = self.current_domain.recall(user_input, filter=self.state_filter)
            return llm.chat_with_context(context, user_input)
        # 2. 默认 Activity (System 1)
        return self.current_activity.react(user_input)
结论：
你实际上想要的是将文档中的“AI 逻辑”落地为具体的“数据流控制”。你现在的代码只是搭了架子（类和枚举），但缺失了灵魂（如何利用 Activity/Domain/State 来控制 LLM 的 Input/Output 和 RAG 行为）。你想要的是一个能理解“我现在在做什么”并据此自动调整“大脑运作模式”的智能系统。
