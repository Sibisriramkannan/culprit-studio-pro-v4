"""Shared fixtures and mock providers for the test suite.

Mock providers allow testing the pipeline without paid API access.
"""
from __future__ import annotations

import os, sys, json, tempfile, shutil
from pathlib import Path
from typing import Any

import pytest

# Ensure the app package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Use a temporary .env for tests so real keys don't leak
os.environ.setdefault("GEMINI_API_KEY", "test-key-not-real")
os.environ.setdefault("OUTPUT_DIR", tempfile.mkdtemp(prefix="culprit_test_"))
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="culprit_data_"))
os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp(prefix="culprit_upload_"))


@pytest.fixture(scope="session", autouse=True)
def cleanup_tmp():
    """Remove temp test directories after the full test session."""
    yield
    for d in [os.environ.get("OUTPUT_DIR", ""), os.environ.get("DATA_DIR", ""), os.environ.get("UPLOAD_DIR", "")]:
        if d and Path(d).exists():
            shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def tmp_job_dir(tmp_path):
    """Return a temporary job directory."""
    d = tmp_path / "job-test"
    d.mkdir()
    return d


@pytest.fixture
def sample_plan():
    """Return a minimal valid video plan dict."""
    return {
        "title": "Test Story",
        "description": "A test story for unit tests.",
        "hashtags": ["#test"],
        "character_bible": "A friendly test panda.",
        "scenes": [
            {
                "scene": 1,
                "narration": "Hello, this is scene one.",
                "caption": "Scene 1",
                "visual_prompt": "A test panda in a lab.",
                "motion_prompt": "Panda waves hello.",
                "camera": "gentle push-in",
                "foreground_text": "Scene 1",
                "duration": 5,
            },
            {
                "scene": 2,
                "narration": "Now we are in scene two.",
                "caption": "Scene 2",
                "visual_prompt": "The panda explores a forest.",
                "motion_prompt": "Panda walks forward slowly.",
                "camera": "slow tracking shot",
                "foreground_text": "Scene 2",
                "duration": 5,
            },
        ],
    }


@pytest.fixture
def tamil_scenes():
    """Return scenes with Tamil narration for Unicode testing."""
    return [
        {"scene": 1, "narration": "வணக்கம், இது ஒரு சோதனை காட்சி.", "caption": "வணக்கம்"},
        {"scene": 2, "narration": "பாண்டா காட்டில் நடக்கிறது.", "caption": "பாண்டா"},
    ]
