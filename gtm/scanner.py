"""AST-based detection of LLM call sites in a Python codebase.

The scanner walks every .py file and emits a CallSite for each spot worth
migrating to BAML. Five patterns are recognized:

    openai            openai.chat.completions.create(...) and async
    instructor        instructor.patch(...) / .from_openai(...) and the
                      response_model= kwarg downstream
    langchain_parser  PydanticOutputParser / StructuredOutputParser usage
    raw_json_after    json.loads(...) immediately following an LLM call
    anthropic_tools   anthropic.messages.create(..., tools=...)

Match policy is conservative: false positives are cheap (we just skip them
later if the translator can't make sense of them), but missing a real call
costs trust. So we lean toward attribute-name pattern matching rather than
strict type inference.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path


PATTERN_TYPES = (
    "openai",
    "instructor",
    "langchain_parser",
    "raw_json_after",
    "anthropic_tools",
)


@dataclass
class CallSite:
    """A single LLM call site detected in source code."""

    file: str  # repo-relative path
    line: int
    pattern_type: str
    raw_snippet: str
    surrounding_context: str  # roughly +/- 5 lines, for translator context
    inferred_schema: str | None = None  # nearby Pydantic class def, if any
    model_name: str | None = None
    retry_logic_present: bool = False
    notes: list[str] = field(default_factory=list)

    def display_id(self) -> str:
        return f"{self.file}:{self.line}"


def _attr_chain(node: ast.AST) -> str:
    """Render a dotted attribute chain. obj.foo.bar -> 'obj.foo.bar'."""
    parts: list[str] = []
    cur: ast.AST | None = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))


def _get_kwarg(call: ast.Call, name: str) -> ast.AST | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _literal_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _snippet(source: str, lineno: int, end_lineno: int | None) -> str:
    """Extract the source text for a node, by line number."""
    lines = source.splitlines()
    start = max(lineno - 1, 0)
    end = (end_lineno or lineno)
    return "\n".join(lines[start:end])


def _context_window(source: str, lineno: int, before: int = 5, after: int = 8) -> str:
    lines = source.splitlines()
    start = max(lineno - 1 - before, 0)
    end = min(lineno + after, len(lines))
    chunk = lines[start:end]
    return "\n".join(chunk)


def _has_retry_decorator(func_node: ast.FunctionDef | ast.AsyncFunctionDef | None) -> bool:
    """Detect @retry, @backoff, @tenacity.retry decorators on the containing func."""
    if func_node is None:
        return False
    for deco in func_node.decorator_list:
        name = _attr_chain(deco.func) if isinstance(deco, ast.Call) else _attr_chain(deco)
        if not name:
            continue
        low = name.lower()
        if "retry" in low or "backoff" in low or "tenacity" in low:
            return True
    return False


class _LLMCallVisitor(ast.NodeVisitor):
    """Single-pass visitor that emits a list of CallSites."""

    def __init__(self, source: str, rel_path: str, pydantic_classes: dict[str, str]):
        self.source = source
        self.rel_path = rel_path
        # name -> source text of the class def, for inferred_schema lookups
        self.pydantic_classes = pydantic_classes
        self.sites: list[CallSite] = []
        # stack of enclosing function defs (for retry-decorator lookup)
        self._func_stack: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        # recent LLM call lines per scope, for raw_json_after detection
        self._recent_llm_lines: list[int] = []

    # --- function-scope tracking -----------------------------------------

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter_func(node)
        self.generic_visit(node)
        self._exit_func()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter_func(node)
        self.generic_visit(node)
        self._exit_func()

    def _enter_func(self, node):
        self._func_stack.append(node)
        self._recent_llm_lines.append(-1)

    def _exit_func(self):
        self._func_stack.pop()
        self._recent_llm_lines.pop()

    @property
    def _enclosing_func(self):
        return self._func_stack[-1] if self._func_stack else None

    # --- call detection --------------------------------------------------

    def visit_Call(self, node: ast.Call) -> None:
        # Pattern precedence: instructor > openai. A call that passes
        # response_model= is definitionally an instructor-style call even
        # if the chain reads .chat.completions.create — we don't want to
        # emit two sites for the same source line.
        instructor_match = self._is_instructor_call(node)
        if instructor_match:
            self._emit_instructor(node)
        elif self._is_openai_call(node):
            self._emit_openai(node)
        if self._is_anthropic_tool_call(node):
            self._emit_anthropic_tools(node)
        if self._is_langchain_parser(node):
            self._emit_langchain_parser(node)
        if self._is_json_loads(node):
            self._maybe_emit_raw_json_after(node)

        self.generic_visit(node)

    # --- pattern checks --------------------------------------------------

    def _is_openai_call(self, node: ast.Call) -> bool:
        # openai.chat.completions.create / client.chat.completions.create
        # async variants land at the same attribute chain. Also catch the newer
        # `.beta.chat.completions.parse` (structured outputs with Pydantic
        # response_format) and `.responses.create`.
        if not isinstance(node.func, ast.Attribute):
            return False
        chain = _attr_chain(node.func)
        return (
            chain.endswith(".chat.completions.create")
            or chain.endswith(".chat.completions.parse")
            or chain.endswith(".responses.create")
            or chain.endswith(".responses.parse")
        )

    def _is_instructor_call(self, node: ast.Call) -> bool:
        # instructor.patch(...) / instructor.from_openai(...) -- and any
        # .create call that passes response_model=
        if isinstance(node.func, ast.Attribute):
            chain = _attr_chain(node.func)
            if chain.startswith("instructor."):
                return True
            if (chain.endswith(".chat.completions.create") or chain.endswith(".create")) and _get_kwarg(node, "response_model") is not None:
                return True
        if isinstance(node.func, ast.Name) and node.func.id == "instructor":
            return True
        return False

    def _is_anthropic_tool_call(self, node: ast.Call) -> bool:
        if not isinstance(node.func, ast.Attribute):
            return False
        chain = _attr_chain(node.func)
        if not chain.endswith(".messages.create"):
            return False
        return _get_kwarg(node, "tools") is not None

    def _is_langchain_parser(self, node: ast.Call) -> bool:
        # PydanticOutputParser(pydantic_object=X) or StructuredOutputParser.from_response_schemas(...)
        if isinstance(node.func, ast.Name):
            return node.func.id in {"PydanticOutputParser", "StructuredOutputParser"}
        if isinstance(node.func, ast.Attribute):
            chain = _attr_chain(node.func)
            return any(p in chain for p in ("PydanticOutputParser", "StructuredOutputParser"))
        return False

    def _is_json_loads(self, node: ast.Call) -> bool:
        if not isinstance(node.func, ast.Attribute):
            return False
        chain = _attr_chain(node.func)
        return chain in {"json.loads", "orjson.loads"}

    # --- emitters --------------------------------------------------------

    def _emit_openai(self, node: ast.Call) -> None:
        model = _literal_str(_get_kwarg(node, "model"))
        site = self._build_site(node, "openai", model_name=model)
        # response_format can be either {"type": "json_object"} or a Pydantic
        # class (with the newer .parse() pattern). When it's a class name we
        # can reach back into the scanned BaseModel registry for the schema.
        rf = _get_kwarg(node, "response_format")
        if rf is not None:
            schema_name = self._extract_class_name(rf)
            if schema_name and schema_name in self.pydantic_classes:
                site.inferred_schema = self.pydantic_classes[schema_name]
                site.notes.append(f"response_format={schema_name}")
            else:
                site.notes.append("uses response_format=")
        if _get_kwarg(node, "tools") is not None:
            site.notes.append("uses tools=")
        self.sites.append(site)
        if node.lineno is not None and self._recent_llm_lines:
            self._recent_llm_lines[-1] = node.lineno

    def _emit_instructor(self, node: ast.Call) -> None:
        model = _literal_str(_get_kwarg(node, "model"))
        site = self._build_site(node, "instructor", model_name=model)
        rm = _get_kwarg(node, "response_model")
        if rm is not None:
            schema_name = self._extract_class_name(rm)
            if schema_name and schema_name in self.pydantic_classes:
                site.inferred_schema = self.pydantic_classes[schema_name]
                site.notes.append(f"response_model={schema_name}")
            elif schema_name:
                site.notes.append(f"response_model={schema_name} (class def not found in scanned files)")
        self.sites.append(site)
        if node.lineno is not None and self._recent_llm_lines:
            self._recent_llm_lines[-1] = node.lineno

    def _emit_anthropic_tools(self, node: ast.Call) -> None:
        model = _literal_str(_get_kwarg(node, "model"))
        site = self._build_site(node, "anthropic_tools", model_name=model)
        self.sites.append(site)
        if node.lineno is not None and self._recent_llm_lines:
            self._recent_llm_lines[-1] = node.lineno

    def _emit_langchain_parser(self, node: ast.Call) -> None:
        site = self._build_site(node, "langchain_parser")
        # PydanticOutputParser(pydantic_object=X)
        po = _get_kwarg(node, "pydantic_object")
        if po is not None:
            schema_name = self._extract_class_name(po)
            if schema_name and schema_name in self.pydantic_classes:
                site.inferred_schema = self.pydantic_classes[schema_name]
                site.notes.append(f"pydantic_object={schema_name}")
        self.sites.append(site)

    def _maybe_emit_raw_json_after(self, node: ast.Call) -> None:
        if not self._recent_llm_lines:
            return
        last_llm_line = self._recent_llm_lines[-1]
        if last_llm_line < 0:
            return
        # Heuristic: json.loads within ~6 lines after the last LLM call in
        # this function counts as a raw-parse pattern worth migrating.
        if 0 < (node.lineno - last_llm_line) <= 6:
            site = self._build_site(node, "raw_json_after")
            site.notes.append(f"follows LLM call at line {last_llm_line}")
            self.sites.append(site)

    # --- helpers ---------------------------------------------------------

    def _build_site(self, node: ast.Call, pattern: str, model_name: str | None = None) -> CallSite:
        snippet = _snippet(self.source, node.lineno, node.end_lineno)
        context = _context_window(self.source, node.lineno)
        retry = _has_retry_decorator(self._enclosing_func)
        return CallSite(
            file=self.rel_path,
            line=node.lineno,
            pattern_type=pattern,
            raw_snippet=snippet,
            surrounding_context=context,
            model_name=model_name,
            retry_logic_present=retry,
        )

    def _extract_class_name(self, node: ast.AST) -> str | None:
        # Bare Name: response_model=MyModel
        if isinstance(node, ast.Name):
            return node.id
        # Attribute: response_model=schemas.MyModel  -> 'MyModel'
        if isinstance(node, ast.Attribute):
            return node.attr
        # List[MyModel] / Optional[MyModel] -> peel the subscript
        if isinstance(node, ast.Subscript):
            return self._extract_class_name(node.slice)
        return None


def _collect_pydantic_classes(tree: ast.Module, source: str) -> dict[str, str]:
    """Find class defs that inherit BaseModel and return name -> source text."""
    found: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        base_names: list[str] = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                base_names.append(b.id)
            elif isinstance(b, ast.Attribute):
                base_names.append(b.attr)
        if any(bn in {"BaseModel", "pydantic.BaseModel"} for bn in base_names):
            found[node.name] = _snippet(source, node.lineno, node.end_lineno)
    return found


def scan_file(path: Path, repo_root: Path) -> list[CallSite]:
    """Scan a single Python file and return any LLM call sites found."""
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    pydantic_classes = _collect_pydantic_classes(tree, source)
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    visitor = _LLMCallVisitor(source, rel, pydantic_classes)
    visitor.visit(tree)
    return visitor.sites


# Directory and filename patterns we skip during repo walks.
_SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    "site-packages",
    ".tox",
    ".idea",
    ".vscode",
}


def scan_repo(repo_root: Path) -> list[CallSite]:
    """Walk a repo root and return CallSites across every .py file."""
    sites: list[CallSite] = []
    for path in repo_root.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        sites.extend(scan_file(path, repo_root))
    return sites
