"""Unit tests for scanner.py — AST detection against in-memory fixtures.

These tests write tiny Python files to a tmp dir and call `scan_file` /
`scan_repo`. They don't touch the network, don't shell out, and don't
need an LLM key — they're the fastest regression-safety net we have for
the pattern-matching layer.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from baml_scout.scanner import (
    PATTERN_TYPES,
    iter_python_files,
    scan_file,
    scan_repo,
)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return tmp_path


def _write(repo: Path, rel: str, body: str) -> Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dedent(body), encoding="utf-8")
    return p


def test_pattern_types_locked():
    """Lock the public pattern type tuple — any change is a breaking API shift."""
    assert PATTERN_TYPES == (
        "openai", "instructor", "langchain_parser", "raw_json_after", "anthropic_tools",
    )


def test_detects_openai_chat_completions(repo):
    p = _write(repo, "app.py", '''
        from openai import OpenAI
        client = OpenAI()

        def summarize(text):
            return client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": text}],
            )
    ''')
    sites = scan_file(p, repo)
    assert len(sites) == 1
    s = sites[0]
    assert s.pattern_type == "openai"
    assert s.model_name == "gpt-4o-mini"


def test_detects_instructor_via_response_model(repo):
    p = _write(repo, "app.py", '''
        from pydantic import BaseModel

        class User(BaseModel):
            name: str
            age: int

        def extract(text):
            return client.chat.completions.create(
                model="gpt-4o-mini",
                response_model=User,
                messages=[{"role": "user", "content": text}],
            )
    ''')
    sites = scan_file(p, repo)
    # response_model= takes precedence over openai detection — exactly one site.
    assert len(sites) == 1
    assert sites[0].pattern_type == "instructor"
    # The Pydantic class is in the same file so the scanner should infer it.
    assert sites[0].inferred_schema is not None
    assert "class User" in sites[0].inferred_schema


def test_detects_anthropic_tools(repo):
    p = _write(repo, "app.py", '''
        import anthropic

        def call():
            return anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                tools=[{"name": "get_weather"}],
                messages=[{"role": "user", "content": "weather?"}],
            )
    ''')
    sites = scan_file(p, repo)
    types = {s.pattern_type for s in sites}
    assert "anthropic_tools" in types


def test_detects_langchain_pydantic_output_parser(repo):
    p = _write(repo, "app.py", '''
        from langchain.output_parsers import PydanticOutputParser
        from pydantic import BaseModel

        class Answer(BaseModel):
            text: str

        parser = PydanticOutputParser(pydantic_object=Answer)
    ''')
    sites = scan_file(p, repo)
    assert any(s.pattern_type == "langchain_parser" for s in sites)


def test_detects_raw_json_after_llm_call(repo):
    p = _write(repo, "app.py", '''
        import json

        def go(client):
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "x"}],
            )
            data = json.loads(resp.choices[0].message.content)
            return data
    ''')
    sites = scan_file(p, repo)
    patterns = [s.pattern_type for s in sites]
    assert "openai" in patterns
    assert "raw_json_after" in patterns


def test_skips_unparseable_file(repo):
    p = _write(repo, "broken.py", "def oops(:\n   nope\n")
    # SyntaxError → empty result, not a crash.
    assert scan_file(p, repo) == []


def test_iter_python_files_skips_venv_and_caches(repo):
    _write(repo, "good.py", "x = 1\n")
    _write(repo, ".venv/lib/site-packages/bad.py", "x = 1\n")
    _write(repo, "node_modules/pkg/also_bad.py", "x = 1\n")
    _write(repo, "__pycache__/cached.py", "x = 1\n")

    found = sorted(p.name for p in iter_python_files(repo))
    assert found == ["good.py"]


def test_scan_repo_handles_empty(repo):
    assert scan_repo(repo) == []


def test_scan_repo_traverses_subdirs(repo):
    _write(repo, "a/foo.py", '''
        client.chat.completions.create(model="gpt-4o", messages=[])
    ''')
    _write(repo, "b/bar.py", '''
        client.chat.completions.create(model="gpt-4o", messages=[])
    ''')
    sites = scan_repo(repo)
    assert len(sites) == 2
    files = {s.file for s in sites}
    # Repo-relative, forward-slash-normalized for cross-platform consistency.
    assert files == {"a/foo.py", "b/bar.py"}
