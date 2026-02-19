"""
飞书知识库 API
"""

from typing import Any, Dict, List, Optional


def list_space_nodes(
    client: Any, space_id: str, parent_node_token: Optional[str] = None
):
    """获取知识空间子节点列表"""
    from lark_oapi.api.wiki.v2 import ListSpaceNodeRequest

    request = ListSpaceNodeRequest.builder().space_id(space_id).page_size(50)

    if parent_node_token:
        request.parent_node_token(parent_node_token)

    response = client.wiki.v2.space_node.list(request.build())

    if not response.success():
        raise Exception(f"failed to get space nodes: {response.code} {response.msg}")

    return response.data


def build_directory_tree(
    client: Any,
    space_id: str,
    parent_node_token: Optional[str] = None,
    save_docs: bool = True,
) -> List[Dict[str, Any]]:
    """递归构建知识库目录树结构"""
    nodes = []
    page_token = None

    while True:
        result = list_space_nodes(client, space_id, parent_node_token, page_token)

        if result and result.items:
            for item in result.items:
                node_info = {
                    "node_token": item.node_token,
                    "obj_token": item.obj_token,
                    "obj_type": item.obj_type,
                    "title": item.title,
                    "has_child": item.has_child or False,
                    "node_create_time": item.node_create_time,
                    "children": [],
                }

                if save_docs and item.obj_type == "docx" and item.obj_token:
                    save_document_content(item.obj_token, item.title, client)

                if item.has_child:
                    node_info["children"] = build_directory_tree(
                        client, space_id, item.node_token, save_docs
                    )

                nodes.append(node_info)

        if result.has_more and result.page_token:
            page_token = result.page_token
        else:
            break

    return nodes


def save_document_content(obj_token: str, title: str, client: Any) -> None:
    """获取并保存文档内容"""
    from lark_oapi.api.docx.v1 import ListDocumentBlockRequest

    page_token = None
    block_dict = {}

    while True:
        request = (
            ListDocumentBlockRequest.builder().document_id(obj_token).page_size(100)
        )

        if page_token:
            request.page_token(page_token)

        response = client.docx.v1.document_block.list(request.build())

        if not response.success():
            return

        if response.data and response.data.items:
            for block in response.data.items:
                block_dict[block.block_id] = block_to_dict(block)

        if response.data.has_more and response.data.page_token:
            page_token = response.data.page_token
        else:
            break

    doc_data = {
        "title": title,
        "obj_token": obj_token,
        "blocks": list(block_dict.values()),
    }

    safe_title = "".join(
        c for c in title if c.isalnum() or c in (" ", "-", "_")
    ).strip()
    if not safe_title:
        safe_title = f"doc_{obj_token}"

    print(f"  Saved: {title} ({len(block_dict)} blocks)")


def block_to_dict(block) -> dict:
    """将 block 对象转换为字典"""
    from .converter import style_to_dict

    data = {
        "block_id": block.block_id,
        "block_type": block.block_type,
        "parent_id": getattr(block, "parent_id", None),
        "children": getattr(block, "children", None),
    }

    if block.text is not None:
        data["text"] = {
            "style": style_to_dict(getattr(block.text, "style", None)),
            "elements": [],
        }
        if hasattr(block.text, "elements") and block.text.elements:
            for elem in block.text.elements:
                elem_data = {"type": getattr(elem, "type", None)}
                if hasattr(elem, "text_run"):
                    elem_data["text_run"] = {
                        "content": getattr(elem.text_run, "content", None),
                        "style": style_to_dict(getattr(elem.text_run, "style", None)),
                    }
                data["text"]["elements"].append(elem_data)

    return data
