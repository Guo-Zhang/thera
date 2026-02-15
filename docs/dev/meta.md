# 元模块

认知的嵌套结构：Meta 作为“元认知”
你提出的观点是：Meta 模块相对于其他所有模块都是 System 2。
这意味着 meta 不仅仅是数据分类标准，它是整个系统的意识监控中心。
层级关系：
执行层（System 1）： 具体的业务逻辑模块（如写作辅助、代码生成、知识问答）。它们负责“做”，是快速的、自动化的、消耗算力进行具体输出的。
监控层（System 2 - Meta）： meta 模块。它负责“看”和“管”。它不直接产生内容，而是管理产生内容的环境、状态和资源。
你实际想要的是：
你希望 meta.py 成为系统的前额叶皮层。它负责：
抑制与控制： 决定何时停止某个 Activity，何时切换 Domain（这就是 DomainManager 存在的意义，它是一个控制塔）。
资源分配： 决定给某个任务分配多少上下文窗口，加载哪些 Asset。
元认知判断： 判断当前输入是否属于当前 Domain，如果不属于，触发 auto_switch（这正是代码中 auto_switch 的深层含义——元认知的纠偏机制）。

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

在 Meta 内部，你定义了 Domain (System 2) vs. Activity (System 1) 的关系。这进一步细化了认知的颗粒度。
Domain (System 2 - 慢/静/深)：
它是知识图谱，是背景，是规则。
它代表了“专家经验”和“长期记忆”。调用 Domain 意味着需要检索、推理、匹配，这是消耗认知资源的“慢思考”。
代码映射： Domain 类及其 handle_input 不应该是简单的路由，而应该包含 RAG 检索、知识库加载等重逻辑。
Activity (System 1 - 快/动/浅)：
它是工作记忆，是前台流，是直觉。
它代表了“当前焦点”和“即时反应”。用户输入一句话，AI 基于当前 Activity 直接回复，无需深度检索，这就是“快思考”。
代码映射： 目前代码中 Activity 缺失，但在你的构想中，它应该对应 Context Manager 或 Session。它是轻量级的，负责维持对话的连贯性（短时记忆）。

通过这种双重 System 2 的嵌套设计，你实际上是在构建一个具备自我反思能力的 Agent 架构。
第一层反思：Meta 对系统的反思
meta 模块作为最高层级的 System 2，它的职责是回答：
*“我们现在在做什么？”* -> 定义 Activity
*“我们现在的身份是什么？”* -> 定义 Domain
*“我们要处理的资料在哪里？”* -> 定义 Asset
*“这些资料现在的状态如何？”* -> 定义 State
代码上的体现：
你的 meta.py 不应该只是一个 DomainManager。它应该是一个 MetaController。
目前的 DomainManager 其实只是 Meta 的一个子系统。
第二层反思：Domain 对内容的反思
Domain 作为次层级的 System 2，它的职责是回答：
*“针对这个问题，我需要检索哪些长期记忆？”*
*“这个输入是否符合我的专业范式？”*

# Meta 模块 = 顶层 System 2 (元认知)
class MetaController:
    """
    元认知中心。
    职责：监控全局，管理 Domain 切换，维护 Asset 和 State。
    相对于具体业务逻辑，它是慢速的、监控型的 System 2。
    """
    def __init__(self):
        self.domain_manager = DomainManager(self) # 管理 Sub-System 2
        self.activity_manager = ActivityManager(self) # 管理 Sub-System 1
        self.asset_registry = AssetRegistry(self) # 管理 Data
        self.state_engine = StateEngine(self) # 管理 Logic/Filter

    def observe(self, user_input):
        # 元认知过程：先判断状态和意图，再决定是否干预
        # 这里的逻辑是“慢”的，因为它在做决策，而不是在执行
        if self.state_engine.is_locked():
            return "System is locked."
        
        # 决策：应该由哪个 Domain 来处理？这是一个元认知判断
        target_domain = self.domain_manager.analyze_intent(user_input) 
        if target_domain:
            self.domain_manager.switch_domain(target_domain)
        
        # 委托给 Sub-System 处理
        return self.delegate(user_input)

# Domain = 次级 System 2 (深度知识/逻辑)
class Domain:
    """
    深度思考模块。
    职责：提供知识边界，执行 RAG 检索，进行复杂推理。
    相对于 Activity，它是慢速的、静态的 System 2。
    """
    def think(self, query):
        # 这里的逻辑是“重”的：检索向量库、构建 Prompt、调用 LLM 推理
        context = self.retrieve_knowledge(query)
        return self.llm_infer(context, query)

# Activity = 次级 System 1 (即时感知/反应)
class Activity:
    """
    即时反应模块。
    职责：维护当前对话流，处理简单交互，不需要深度检索。
    相对于 Domain，它是快速的、动态的 System 1。
    """
    def react(self, query):
        # 这里的逻辑是“轻”的：基于上下文的直接回复
        return self.chat_flow.reply(query)

总结：你实际上想要的是什么？
你想要的是一个分形的认知控制系统：
全局视角：meta 是上帝视角（System 2），负责维护秩序（ADAS 分类），监控整个系统的运行状态。它让系统拥有了“自我意识”。
局部视角：在执行层，Domain 充当专家视角（System 2），提供深度智力支持；Activity 充当助手视角（System 1），维持流畅的交互体验。
这种设计比之前的“功能分类”要强大得多。它解释了为什么 meta.py 里会有 switch_domain 和 auto_switch——这本质上是元认知对思维模式的调用来回切换。
你的代码目前缺失的是Activity 的显式化管理（那个动态的“工作记忆区”），以及将 meta 提升为真正的决策中枢而不仅仅是路由器的逻辑。
