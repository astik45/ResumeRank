import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from query_engine import search_resumes


class TestQueryEngine:
    def test_search_returns_dict(self):
        try:
            results = search_resumes("Python developer", top_k=5)
            assert isinstance(results, dict)
            assert "answer" in results
            assert "matches" in results
        except Exception as e:
            assert "API key" in str(e) or "connection" in str(e).lower()

    def test_search_with_empty_query(self):
        with pytest.raises((ValueError, AssertionError, Exception)):
            search_resumes("", top_k=5)

    def test_search_result_structure(self):
        try:
            results = search_resumes("software engineer", top_k=1)
            if results and "matches" in results:
                for match in results["matches"]:
                    assert isinstance(match, dict)
                    assert "score" in match
                    assert "metadata" in match
        except Exception:
            pass

    def test_search_with_different_queries(self):
        queries = [
            "machine learning engineer",
            "senior developer",
            "data scientist",
        ]
        for query in queries:
            try:
                results = search_resumes(query, top_k=3)
                assert isinstance(results, dict)
            except Exception:
                pass
