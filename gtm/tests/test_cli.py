"""Tests for cli.py URL/path resolution helpers — no subprocess calls."""

from __future__ import annotations

from pathlib import Path

import pytest

from baml_scout.cli import _is_github_url, _repo_name_from_url


class TestIsGithubUrl:
    @pytest.mark.parametrize("url", [
        "https://github.com/owner/repo",
        "https://github.com/owner/repo.git",
        "http://github.com/owner/repo",
        "git@github.com:owner/repo.git",
    ])
    def test_recognizes_github_urls(self, url):
        assert _is_github_url(url) is True

    @pytest.mark.parametrize("not_url", [
        "./local/path",
        "/abs/path",
        "owner/repo",
        "https://gitlab.com/owner/repo",
        "https://example.com/owner/repo",
        "file.py",
        "",
    ])
    def test_rejects_non_github(self, not_url):
        assert _is_github_url(not_url) is False


class TestRepoNameFromUrl:
    @pytest.mark.parametrize("url,expected", [
        ("https://github.com/owner/repo", "repo"),
        ("https://github.com/owner/repo.git", "repo"),
        ("https://github.com/owner/repo/", "repo"),
        ("git@github.com:owner/repo.git", "repo"),
        ("https://github.com/owner/multi-word-repo", "multi-word-repo"),
    ])
    def test_extracts_repo_name(self, url, expected):
        assert _repo_name_from_url(url) == expected
