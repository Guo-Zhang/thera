"""
知识域单元测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from thera.domain.knowl import (
    DocType,
    classify_doc_type,
    load_articles,
    tfidf_similarity,
    jaccard_similarity,
    keyword_similarity,
    embedding_similarity,
    build_similarity_report,
    export_html,
    KnowlDomain,
)
from thera.__main__ import Thera


class TestClassifyDocType:
    def test_classify_outline_by_path(self):
        path = Path("/docs/提纲/test.md")
        assert classify_doc_type(path) == DocType.OUTLINE

    def test_classify_outline_by_filename(self):
        path = Path("/docs/test/提纲.md")
        assert classify_doc_type(path) == DocType.OUTLINE

    def test_classify_draft_by_path(self):
        path = Path("/docs/初稿/test.md")
        assert classify_doc_type(path) == DocType.DRAFT

    def test_classify_draft_by_filename(self):
        path = Path("/docs/test/初稿.md")
        assert classify_doc_type(path) == DocType.DRAFT

    def test_classify_other(self):
        path = Path("/docs/other/test.md")
        assert classify_doc_type(path) == DocType.OTHER


class TestLoadArticles:
    def test_load_articles_basic(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        (docs_dir / "test1.md").write_text(
            "# Test Article\n\nContent here", encoding="utf-8"
        )
        (docs_dir / "test2.md").write_text(
            "# Another Article\n\nMore content", encoding="utf-8"
        )

        articles, doc_types = load_articles(docs_dir)

        assert len(articles) == 2
        assert "test1" in articles
        assert "test2" in articles
        assert articles["test1"]["title"] == "Test Article"
        assert articles["test1"]["content"] == "# Test Article\n\nContent here"
        assert articles["test1"]["doc_type"] == DocType.OTHER

    def test_load_articles_skip_special_files(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        (docs_dir / "test.md").write_text("# Test", encoding="utf-8")
        (docs_dir / "_private.md").write_text("# Private", encoding="utf-8")
        (docs_dir / "feishu_wiki_directory.json").write_text("{}", encoding="utf-8")

        articles, _ = load_articles(docs_dir)

        assert len(articles) == 1
        assert "test" in articles

    def test_load_articles_with_doc_type(self, tmp_path):
        docs_dir = tmp_path / "docs"
        outline_dir = docs_dir / "提纲"
        outline_dir.mkdir(parents=True)

        (outline_dir / "story.md").write_text(
            "# Story Outline\n\nOutline content", encoding="utf-8"
        )

        articles, doc_types = load_articles(docs_dir)

        assert len(articles) == 1
        assert articles["story"]["doc_type"] == DocType.OUTLINE
        assert "story" in doc_types[DocType.OUTLINE]


class TestTfidfSimilarity:
    def test_tfidf_similarity_same_texts(self):
        texts = ["hello world", "hello world"]
        sim_matrix = tfidf_similarity(texts)

        assert sim_matrix.shape == (2, 2)
        assert np.isclose(sim_matrix[0][1], 1.0)

    def test_tfidf_similarity_different_texts(self):
        texts = ["hello world", "foo bar baz"]
        sim_matrix = tfidf_similarity(texts)

        assert sim_matrix.shape == (2, 2)
        assert sim_matrix[0][1] < 1.0


class TestJaccardSimilarity:
    def test_jaccard_identical(self):
        text = "hello world"
        result = jaccard_similarity(text, text)
        assert result == 1.0

    def test_jaccard_different(self):
        result = jaccard_similarity("abc", "xyz")
        assert result == 0.0

    def test_jaccard_partial(self):
        result = jaccard_similarity("hello world", "hello there")
        assert 0.0 < result < 1.0

    def test_jaccard_empty(self):
        result = jaccard_similarity("", "hello")
        assert result == 0.0


class TestKeywordSimilarity:
    def test_keyword_identical(self):
        text = "hello world test"
        result = keyword_similarity(text, text)
        assert result == 1.0

    def test_keyword_no_overlap(self):
        result = keyword_similarity("hello", "world")
        assert result == 0.0

    def test_keyword_partial(self):
        result = keyword_similarity("hello world test", "hello world foo")
        assert 0.0 < result < 1.0


class TestEmbeddingSimilarity:
    def test_embedding_same_vectors(self):
        embeddings = np.array([[1.0, 0.0], [1.0, 0.0]])
        sim_matrix = embedding_similarity(embeddings)
        assert sim_matrix.shape == (2, 2)
        assert np.isclose(sim_matrix[0][1], 1.0)

    def test_embedding_orthogonal(self):
        embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])
        sim_matrix = embedding_similarity(embeddings)
        assert np.isclose(sim_matrix[0][1], 0.0)


class TestBuildSimilarityReport:
    def test_build_similarity_report_basic(self):
        import numpy as np

        sim_results = {
            "names": ["doc1", "doc2"],
            "similarities": {
                "jaccard": np.array([[1.0, 0.5], [0.5, 1.0]]),
                "keyword": np.array([[1.0, 0.3], [0.3, 1.0]]),
                "tfidf": np.array([[1.0, 0.4], [0.4, 1.0]]),
                "embedding": np.array([[1.0, 0.6], [0.6, 1.0]]),
            },
        }

        report = build_similarity_report(sim_results)

        assert "# 文本相似度分析报告" in report
        assert "doc1" in report
        assert "doc2" in report
        assert "jaccard" in report
        assert "TF-IDF" in report

    def test_build_similarity_report_top_pairs(self):
        import numpy as np

        sim_results = {
            "names": ["a", "b", "c"],
            "similarities": {
                "jaccard": np.array(
                    [[1.0, 0.9, 0.1], [0.9, 1.0, 0.2], [0.1, 0.2, 1.0]]
                ),
                "keyword": np.array(
                    [[1.0, 0.8, 0.1], [0.8, 1.0, 0.2], [0.1, 0.2, 1.0]]
                ),
                "tfidf": np.array([[1.0, 0.7, 0.1], [0.7, 1.0, 0.2], [0.1, 0.2, 1.0]]),
                "embedding": np.array(
                    [[1.0, 0.6, 0.1], [0.6, 1.0, 0.2], [0.1, 0.2, 1.0]]
                ),
            },
        }

        report = build_similarity_report(sim_results)

        assert "Top相似对" in report or "Top" in report
        assert "a <-> b" in report


class TestExportHtml:
    def test_export_html_basic(self, tmp_path):
        md_path = tmp_path / "test.md"
        html_path = tmp_path / "test.html"

        md_content = """# Title

## Section

Some content
"""
        md_path.write_text(md_content, encoding="utf-8")

        export_html(md_path, html_path)

        assert html_path.exists()
        html_content = html_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html_content
        assert "<title>" in html_content
        assert "Title" in html_content


class TestKnowlDomain:
    def test_domain_creation(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = KnowlDomain(app)
        assert domain.name == "knowl"
        assert domain.description == "知识工程域 - 知识图谱、RAG"

    def test_handle_input_basic(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = KnowlDomain(app)
        result = domain.handle_input("hello")
        assert "[Knowl] hello" in result

    def test_handle_input_discover(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = KnowlDomain(app)
        with patch.object(domain, "_run_discovery", return_value="Test"):
            result = domain.handle_input("/discover")
            assert result == "Test"

    def test_on_activate(self, capsys):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = KnowlDomain(app)
        domain.on_activate()
        captured = capsys.readouterr()
        assert "Activated: knowl" in captured.out

    def test_on_deactivate(self, capsys):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = KnowlDomain(app)
        domain.on_deactivate()
        captured = capsys.readouterr()
        assert "Deactivated: knowl" in captured.out

    def test_auto_switch_to_think(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = KnowlDomain(app)
        result = domain.auto_switch("/think 分析这个故事")
        assert result is not None
        assert result.value == "think"

    def test_auto_switch_to_write(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = KnowlDomain(app)
        result = domain.auto_switch("/write 开始写作")
        assert result is not None
        assert result.value == "write"

    def test_auto_switch_no_match(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = KnowlDomain(app)
        result = domain.auto_switch("今天天气真好")
        assert result is None


class TestLLMFunctions:
    @patch("thera.infra.llm.create_client")
    def test_llm_chat_str(self, mock_create_client):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client

        from thera.infra.llm import chat_str

        result = chat_str("Hello", system_prompt="You are helpful")
        assert result == "Test response"

        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][1]["role"] == "user"
        assert call_kwargs["messages"][1]["content"] == "Hello"

    @patch("thera.infra.llm.create_client")
    def test_llm_stream(self, mock_create_client):
        mock_client = MagicMock()

        def mock_generator():
            chunk1 = MagicMock()
            chunk1.choices = [MagicMock()]
            chunk1.choices[0].delta.content = "Hello "
            chunk1.choices[0].delta.reasoning_content = None
            yield chunk1

            chunk2 = MagicMock()
            chunk2.choices = [MagicMock()]
            chunk2.choices[0].delta.content = "world"
            chunk2.choices[0].delta.reasoning_content = None
            yield chunk2

        mock_client.chat.completions.create.return_value = mock_generator()
        mock_create_client.return_value = mock_client

        from thera.infra.llm import stream

        result = list(stream("Hello"))
        assert "Hello" in result[0]
        assert "world" in result[1]

    def test_json_request(self):
        from thera.infra.llm import json_request

        prompt = '请以 JSON 格式输出 {"hello": "world"}，只输出 JSON'
        result = json_request(prompt)
        assert isinstance(result, dict)
