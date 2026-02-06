"""
片段组织分析器

分析小说片段如何组织进入正文，通过文本特征、主题、时间线等维度进行匹配和分类。
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import re
from collections import Counter
from dataclasses import dataclass


@dataclass
class Dialogue:
    """对话信息"""
    text: str
    speaker: Optional[str] = None
    position: int = 0


@dataclass
class DocumentInfo:
    """文档信息"""
    title: str
    content: str
    word_count: int
    paragraph_count: int
    dialogue_count: int
    dialogues: List[Dialogue]
    location: str  # 片段/正文


@dataclass
class MatchScore:
    """匹配分数"""
    document: DocumentInfo
    keyword_overlap: float
    dialogue_similarity: float
    location_match: float
    theme_similarity: float
    total_score: float


class FragmentAnalyzer:
    """片段组织分析器"""

    def __init__(self, jupyterbook_path: str = "data/storage/jupyterbook", output_path: str = "data/storage/write_analysis"):
        """
        初始化分析器

        Args:
            jupyterbook_path: JupyterBook 目录路径
            output_path: 分析报告输出目录路径
        """
        self.jupyterbook_path = Path(jupyterbook_path)
        self.output_path = Path(output_path)
        self.fragments: List[DocumentInfo] = []
        self.main_texts: List[DocumentInfo] = []
        self.documents: Dict[str, DocumentInfo] = {}

        # 创建输出目录
        self.output_path.mkdir(parents=True, exist_ok=True)

        # 从 _toc.yml 加载文档分类
        self.fragment_titles: Set[str] = set()
        self.main_text_titles: Set[str] = set()

        self._load_toc()
        self._load_documents()

    def _load_toc(self):
        """从 _toc.yml 加载文档分类，只提取片段和正文"""
        import yaml

        toc_path = self.jupyterbook_path / "_toc.yml"
        if not toc_path.exists():
            return

        with open(toc_path, 'r', encoding='utf-8') as f:
            toc = yaml.safe_load(f)

        # 解析 YAML，只提取片段和正文的标题
        current_part = None
        for item in toc:
            if isinstance(item, str):
                continue
            elif isinstance(item, dict):
                if 'part' in item:
                    current_part = item['part']
                    # 只处理"片段"和"正文"部分
                    if current_part == '片段':
                        if 'chapters' in item:
                            for chapter in item['chapters']:
                                title = self._extract_title_from_file(chapter.get('file', ''))
                                if title:
                                    self.fragment_titles.add(title)
                    elif current_part == '正文':
                        if 'chapters' in item:
                            for chapter in item['chapters']:
                                title = self._extract_title_from_file(chapter.get('file', ''))
                                if title:
                                    self.main_text_titles.add(title)

    def _extract_title_from_file(self, filename: str) -> Optional[str]:
        """从文件名提取标题"""
        # 移除 .md 后缀
        title = filename.replace('.md', '')
        return title if title else None

    def _load_documents(self):
        """只加载片段和正文，忽略辅助文本"""
        md_files = list(self.jupyterbook_path.glob("*.md"))

        for md_file in md_files:
            if md_file.name == "_toc.yml":
                continue

            title = md_file.stem

            # 只处理在 toc 中明确标记为片段或正文的文档
            if title not in self.fragment_titles and title not in self.main_text_titles:
                continue

            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            doc_info = self._analyze_document(title, content)

            # 根据标题分类
            if title in self.fragment_titles:
                doc_info.location = "片段"
                self.fragments.append(doc_info)
            elif title in self.main_text_titles:
                doc_info.location = "正文"
                self.main_texts.append(doc_info)

            self.documents[title] = doc_info

    def _analyze_document(self, title: str, content: str) -> DocumentInfo:
        """分析单个文档"""
        # 统计段落
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)

        # 统计字数（中文）
        word_count = len(re.sub(r'\s+', '', content))

        # 提取对话
        dialogues = self.extract_dialogues(content)
        dialogue_count = len(dialogues)

        return DocumentInfo(
            title=title,
            content=content,
            word_count=word_count,
            paragraph_count=paragraph_count,
            dialogue_count=dialogue_count,
            dialogues=dialogues,
            location="未知"
        )

    def extract_dialogues(self, text: str) -> List[Dialogue]:
        """
        提取中文文本中的对话

        支持中文引号：" " ' ' 「」 『』
        以及 Unicode 标点：U+201C (") U+201D (") U+2018 (') U+2019 (')
        处理跨段落引号、同一句中多段引号

        Args:
            text: 文本内容

        Returns:
            对话列表
        """
        dialogues = []

        # 中文弯引号 U+201C (" ) 和 U+201D (" )
        left_wavy_double = '\u201c'
        right_wavy_double = '\u201d'
        pattern_wavy_double = re.compile(f'{left_wavy_double}(.*?){right_wavy_double}', re.DOTALL)
        for match in pattern_wavy_double.finditer(text):
            dialogue_text = match.group(1).strip()
            if dialogue_text:
                dialogues.append(Dialogue(text=dialogue_text, position=match.start()))

        # 中文单弯引号 U+2018 (') 和 U+2019 (')
        left_wavy_single = '\u2018'
        right_wavy_single = '\u2019'
        pattern_wavy_single = re.compile(f'{left_wavy_single}(.*?){right_wavy_single}', re.DOTALL)
        for match in pattern_wavy_single.finditer(text):
            dialogue_text = match.group(1).strip()
            if dialogue_text:
                dialogues.append(Dialogue(text=dialogue_text, position=match.start()))

        # ASCII 双引号 "
        pattern_ascii_double = re.compile(r'"([^"]*)"')
        for match in pattern_ascii_double.finditer(text):
            dialogue_text = match.group(1).strip()
            if dialogue_text:
                dialogues.append(Dialogue(text=dialogue_text, position=match.start()))

        # ASCII 单引号 '
        pattern_ascii_single = re.compile(r"'([^']*)'")
        for match in pattern_ascii_single.finditer(text):
            dialogue_text = match.group(1).strip()
            if dialogue_text:
                dialogues.append(Dialogue(text=dialogue_text, position=match.start()))

        # 直角引号 「」
        pattern_corner = re.compile(r'「([^」]*)」')
        for match in pattern_corner.finditer(text):
            dialogue_text = match.group(1).strip()
            if dialogue_text:
                dialogues.append(Dialogue(text=dialogue_text, position=match.start()))

        # 二重直角引号 『』
        pattern_corner_double = re.compile(r'『([^』]*)』')
        for match in pattern_corner_double.finditer(text):
            dialogue_text = match.group(1).strip()
            if dialogue_text:
                dialogues.append(Dialogue(text=dialogue_text, position=match.start()))

        # 去重（避免同一对话被多个模式匹配）
        unique_dialogues = []
        seen = set()
        for d in dialogues:
            key = (d.text, d.position)
            if key not in seen:
                seen.add(key)
                unique_dialogues.append(d)

        # 按位置排序
        unique_dialogues.sort(key=lambda x: x.position)

        return unique_dialogues

    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        提取关键词

        Args:
            text: 文本内容
            top_n: 返回前 N 个关键词

        Returns:
            关键词列表
        """
        # 简单的分词和词频统计（中文）
        # 提取所有中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)

        # 简单的双字词提取
        words = []
        for chars in chinese_chars:
            # 提取双字词
            for i in range(len(chars) - 1):
                word = chars[i:i+2]
                # 过滤常见的停用词
                if word not in {'这个', '那个', '他的', '她的', '他们', '一个', '什么',
                               '不是', '就是', '没有', '可以', '这样', '那样', '还是',
                               '时候', '知道', '觉得', '好像', '真的', '然后', '已经',
                               '只是', '因为', '所以', '但是', '虽然', '可是', '而且'}:
                    words.append(word)

        # 词频统计
        word_freq = Counter(words)

        # 返回高频词
        return [word for word, _ in word_freq.most_common(top_n)]

    def extract_locations(self, text: str) -> List[str]:
        """
        提取地点信息

        Args:
            text: 文本内容

        Returns:
            地点列表
        """
        # 常见地点模式
        location_patterns = [
            r'酒吧', r'咖啡店', r'咖啡厅', r'海边', r'海边散步', r'教室', r'公园', r'阳台',
            r'书房', r'家里', r'餐厅', r'便利店', r'院子', r'院子里的咖啡店',
            r'栈道', r'长椅', r'酒店', r'办公室', r'公司'
        ]

        locations = []
        for pattern in location_patterns:
            if re.search(pattern, text):
                locations.append(pattern)

        return list(set(locations))

    def extract_characters(self, text: str) -> List[str]:
        """
        提取人物信息

        Args:
            text: 文本内容

        Returns:
            人物列表
        """
        # 从代词推断
        characters = []

        # 检测是否有"他"、"她"的叙述
        if '他' in text and '她' in text:
            characters.extend(['男主', '女主'])

        return list(set(characters))

    def calculate_similarity(self, fragment: DocumentInfo, main_text: DocumentInfo) -> MatchScore:
        """
        计算片段与正文的匹配度

        Args:
            fragment: 片段文档
            main_text: 正文文档

        Returns:
            匹配分数
        """
        # 1. 关键词重叠度
        fragment_keywords = set(self.extract_keywords(fragment.content))
        main_text_keywords = set(self.extract_keywords(main_text.content))

        if fragment_keywords and main_text_keywords:
            keyword_overlap = len(fragment_keywords & main_text_keywords) / len(fragment_keywords | main_text_keywords)
        else:
            keyword_overlap = 0.0

        # 2. 对话相似度（基于对话密度）
        fragment_dialogue_density = fragment.dialogue_count / fragment.paragraph_count if fragment.paragraph_count > 0 else 0
        main_text_dialogue_density = main_text.dialogue_count / main_text.paragraph_count if main_text.paragraph_count > 0 else 0
        dialogue_similarity = 1 - abs(fragment_dialogue_density - main_text_dialogue_density)

        # 3. 地点匹配
        fragment_locations = set(self.extract_locations(fragment.content))
        main_text_locations = set(self.extract_locations(main_text.content))

        if fragment_locations and main_text_locations:
            location_match = len(fragment_locations & main_text_locations) / len(fragment_locations | main_text_locations)
        else:
            location_match = 0.0

        # 4. 主题相似度（简单使用关键词重叠）
        theme_similarity = keyword_overlap

        # 综合分数
        total_score = (
            keyword_overlap * 0.3 +
            dialogue_similarity * 0.2 +
            location_match * 0.3 +
            theme_similarity * 0.2
        )

        return MatchScore(
            document=main_text,
            keyword_overlap=keyword_overlap,
            dialogue_similarity=dialogue_similarity,
            location_match=location_match,
            theme_similarity=theme_similarity,
            total_score=total_score
        )

    def find_best_matches(self, fragment: DocumentInfo, top_n: int = 3) -> List[MatchScore]:
        """
        为片段找到最佳匹配的正文

        Args:
            fragment: 片段文档
            top_n: 返回前 N 个匹配结果

        Returns:
            匹配分数列表，按分数降序排列
        """
        scores = []
        for main_text in self.main_texts:
            score = self.calculate_similarity(fragment, main_text)
            scores.append(score)

        # 按总分排序
        scores.sort(key=lambda x: x.total_score, reverse=True)

        return scores[:top_n]

    def analyze_fragment_organization(self) -> Dict:
        """
        分析片段组织策略

        Returns:
            分析结果字典
        """
        results = {
            "summary": {
                "fragment_count": len(self.fragments),
                "main_text_count": len(self.main_texts),
                "total_documents": len(self.documents)
            },
            "fragment_analysis": [],
            "organization_patterns": []
        }

        # 分析每个片段
        for fragment in self.fragments:
            matches = self.find_best_matches(fragment, top_n=3)

            fragment_data = {
                "title": fragment.title,
                "word_count": fragment.word_count,
                "paragraph_count": fragment.paragraph_count,
                "dialogue_count": fragment.dialogue_count,
                "keywords": self.extract_keywords(fragment.content, top_n=5),
                "locations": self.extract_locations(fragment.content),
                "dialogues": [
                    {"text": d.text, "speaker": d.speaker, "position": d.position}
                    for d in fragment.dialogues[:5]
                ] if fragment.dialogues else [],  # 前5条对话示例
                "best_matches": [
                    {
                        "title": match.document.title,
                        "score": round(match.total_score, 3),
                        "keyword_overlap": round(match.keyword_overlap, 3),
                        "location_match": round(match.location_match, 3)
                    }
                    for match in matches if match.total_score > 0
                ]
            }
            results["fragment_analysis"].append(fragment_data)

        # 总结组织模式
        location_based_matches = 0
        keyword_based_matches = 0

        for fragment_data in results["fragment_analysis"]:
            if fragment_data["best_matches"]:
                best_match = fragment_data["best_matches"][0]
                if best_match["location_match"] > 0:
                    location_based_matches += 1
                if best_match["keyword_overlap"] > 0:
                    keyword_based_matches += 1

        results["organization_patterns"] = [
            {
                "pattern": "地点关联",
                "count": location_based_matches,
                "description": "片段与正文通过相同或相关地点连接"
            },
            {
                "pattern": "关键词关联",
                "count": keyword_based_matches,
                "description": "片段与正文通过主题关键词关联"
            }
        ]

        return results

    def print_analysis(self):
        """打印分析结果"""
        results = self.analyze_fragment_organization()

        print("=" * 80)
        print("片段组织分析报告")
        print("=" * 80)
        print()

        # 摘要
        summary = results["summary"]
        print(f"文档总数: {summary['total_documents']}")
        print(f"片段数量: {summary['fragment_count']}")
        print(f"正文数量: {summary['main_text_count']}")
        print()

        # 片段分析
        print("-" * 80)
        print("片段详细分析")
        print("-" * 80)
        print()

        for i, fragment in enumerate(results["fragment_analysis"], 1):
            print(f"{i}. {fragment['title']}")
            print(f"   字数: {fragment['word_count']} | 段落: {fragment['paragraph_count']} | 对话: {fragment['dialogue_count']}")
            print(f"   关键词: {', '.join(fragment['keywords'])}")
            print(f"   地点: {', '.join(fragment['locations']) if fragment['locations'] else '无'}")

            if fragment['dialogues']:
                print(f"   对话示例:")
                for dialogue in fragment['dialogues'][:3]:
                    print(f'     - "{dialogue["text"]}"')

            if fragment['best_matches']:
                print(f"   最佳匹配:")
                for match in fragment['best_matches'][:2]:
                    print(f"     - {match['title']} (总分: {match['score']}, "
                          f"地点: {match['location_match']}, 关键词: {match['keyword_overlap']})")
            else:
                print(f"   最佳匹配: 无")

            print()

        # 组织模式
        print("-" * 80)
        print("组织模式总结")
        print("-" * 80)
        print()

        for pattern in results["organization_patterns"]:
            print(f"{pattern['pattern']}: {pattern['count']} 个片段")
            print(f"  {pattern['description']}")

        print()
        print("=" * 80)

        return results

    def save_report(self, results: Dict, format: str = "both"):
        """
        保存分析报告到文件

        Args:
            results: 分析结果字典
            format: 输出格式 ("json", "yaml", "both")
        """
        import json
        import yaml

        # 保存 JSON 格式
        if format in ["json", "both"]:
            json_path = self.output_path / "fragment_analysis_report.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"JSON 报告已保存: {json_path}")

        # 保存 YAML 格式
        if format in ["yaml", "both"]:
            yaml_path = self.output_path / "fragment_analysis_report.yaml"
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(results, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            print(f"YAML 报告已保存: {yaml_path}")


def main():
    """主函数"""
    analyzer = FragmentAnalyzer()
    results = analyzer.analyze_fragment_organization()
    analyzer.print_analysis()
    analyzer.save_report(results, format="both")


if __name__ == "__main__":
    main()
