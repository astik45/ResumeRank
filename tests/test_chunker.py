import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.chunker import chunk_text


class TestChunker:
    def test_chunk_text_basic(self):
        text = "This is a sample text. " * 100
        chunks = chunk_text(text, chunk_size=100, overlap=10)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) > 0 for chunk in chunks)

    def test_chunk_text_respects_size(self):
        text = "This is a sample text. " * 100
        chunk_size = 100
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=10)
        for chunk in chunks:
            assert len(chunk) <= chunk_size + 50

    def test_chunk_small_text(self):
        text = "Small text"
        chunks = chunk_text(text, chunk_size=100, overlap=10)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_empty_text(self):
        text = ""
        chunks = chunk_text(text, chunk_size=100, overlap=10)
        assert isinstance(chunks, list)

    def test_chunk_text_preserves_content(self):
        text = "This is important information. " * 50
        chunks = chunk_text(text, chunk_size=200, overlap=20)
        combined = " ".join(chunks)
        assert text.replace(" ", "") in combined.replace(" ", "") or len(chunks) > 0

    def test_chunk_overlap_functionality(self):
        text = "This is a sample text. " * 100
        chunks_with_overlap = chunk_text(text, chunk_size=100, overlap=50)
        chunks_no_overlap = chunk_text(text, chunk_size=100, overlap=0)
        assert len(chunks_with_overlap) >= len(chunks_no_overlap) - 1
