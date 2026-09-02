from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".R", ".md", ".txt", ".csv", ".json", ".example", ".gitignore"}


class RepositoryHygieneTests(unittest.TestCase):
    def test_no_oversized_files(self):
        oversized = [path for path in ROOT.rglob("*") if path.is_file() and path.stat().st_size >= 100 * 1024 * 1024]
        self.assertEqual(oversized, [])

    def test_no_machine_specific_paths_or_literal_secrets(self):
        findings = []
        secret_patterns = [re.compile(r"sk-[A-Za-z0-9_-]{10,}"), re.compile(r"MC-[A-Za-z0-9_-]{10,}")]
        unix_home_marker = "/" + "Users" + "/"
        windows_home_pattern = re.compile(r"[A-Za-z]:" + re.escape("\\Users\\"))
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            if path.suffix not in TEXT_SUFFIXES and path.name not in {".gitignore"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if unix_home_marker in text or windows_home_pattern.search(text):
                findings.append(f"absolute path: {path.relative_to(ROOT)}")
            if any(pattern.search(text) for pattern in secret_patterns):
                findings.append(f"literal secret: {path.relative_to(ROOT)}")
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
