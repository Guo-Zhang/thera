# quanttide-feishu

飞书知识库 Python SDK - 文档转换、JupyterBook 生成

## 功能

- 认证管理: 使用 SDK 自动管理 tenant_access_token
- 知识空间节点查询: 获取知识空间下的节点列表和详细信息
- 文档到 JupyterBook 转换: 将飞书文档转换为 Markdown 格式

## 安装

```bash
pip install quanttide-feishu
```

## 使用

```python
from quanttide_feishu import create_lark_client, build_directory_tree

# 创建客户端
client = create_lark_client()

# 构建知识库目录树
tree = build_directory_tree(client, space_id="xxx")
```

## 环境变量

- `FEISHU_APP_ID`: 飞书应用 ID
- `FEISHU_APP_SECRET`: 飞书应用密钥
