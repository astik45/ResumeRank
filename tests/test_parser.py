import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.parser import extract_text_from_pdf


class TestResumeParser:
    def test_extract_text_from_nonexistent_file(self):
        with pytest.raises((FileNotFoundError, Exception)):
            extract_text_from_pdf("nonexistent_file.pdf")

    def test_parser_handles_empty_file(self, tmp_path):
        empty_file = tmp_path / "empty.pdf"
        empty_file.write_bytes(b"")
        result = extract_text_from_pdf(str(empty_file))
        assert result is not None

    def test_parser_output_is_string(self, temp_resume_file):
        result = extract_text_from_pdf(temp_resume_file)
        assert isinstance(result, str)
