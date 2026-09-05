#!/usr/bin/env python3
"""The repository and skill copies of .env.example must stay byte-identical."""

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


class EnvExampleTests(unittest.TestCase):
    def test_skill_copy_matches_repository_copy(self) -> None:
        repo_copy = REPO_ROOT / ".env.example"
        skill_copy = REPO_ROOT / "skills" / "ppt-master" / ".env.example"
        self.assertEqual(
            skill_copy.read_bytes(),
            repo_copy.read_bytes(),
            "skills/ppt-master/.env.example drifted from .env.example; edit both",
        )


if __name__ == "__main__":
    unittest.main()
