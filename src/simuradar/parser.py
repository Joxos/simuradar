"""AST parsing and code fragment extraction."""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class CodeFragment:
    """Represents a code fragment (function or class)."""

    file_path: Path
    name: str
    fragment_type: str  # "function" or "class"
    start_line: int
    end_line: int
    ast_node: ast.AST
    source_code: str

    @property
    def size(self) -> int:
        """Number of AST nodes in this fragment."""
        return sum(1 for _ in ast.walk(self.ast_node))

    @property
    def lines(self) -> tuple[int, int]:
        """Line range as a tuple."""
        return (self.start_line, self.end_line)


class Parser:
    """Parse Python files and extract code fragments."""

    # AST node types that represent extractable fragments
    FRAGMENT_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

    def parse_file(self, file_path: Path) -> Iterator[CodeFragment]:
        """Parse a single Python file and yield code fragments."""
        try:
            source = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            raise ValueError(f"Failed to read {file_path}: {e}")

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            raise ValueError(f"Syntax error in {file_path}: {e}")

        # Extract top-level functions and classes
        for node in tree.body:
            if isinstance(node, self.FRAGMENT_TYPES):
                # Get source code for this fragment
                fragment_source = ast.get_source_segment(source, node)
                if fragment_source is None:
                    # Fallback: manually slice source
                    lines = source.splitlines(keepends=True)
                    fragment_source = "".join(lines[node.lineno - 1 : node.end_lineno])

                yield CodeFragment(
                    file_path=file_path,
                    name=node.name,
                    fragment_type="function"
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    else "class",
                    start_line=node.lineno,
                    end_line=node.end_lineno,
                    ast_node=node,
                    source_code=fragment_source,
                )

    def parse_directory(self, directory: Path) -> Iterator[CodeFragment]:
        """Parse all Python files in a directory recursively."""
        for py_file in directory.rglob("*.py"):
            # Skip __pycache__ and hidden directories
            if "__pycache__" in py_file.parts or any(
                p.startswith(".") for p in py_file.parts
            ):
                continue

            try:
                yield from self.parse_file(py_file)
            except ValueError as e:
                # Skip files that can't be parsed
                print(f"Warning: {e}")
                continue

    def collect_fragments(self, path: Path, min_size: int = 5) -> list[CodeFragment]:
        """Collect all fragments from a path, filtering by minimum size."""
        # Resolve to absolute path to avoid relative path issues
        # (e.g., '../dir' parts include '..' which starts with '.')
        path = path.resolve()
        if path.is_file():
            fragments = list(self.parse_file(path))
        elif path.is_dir():
            fragments = list(self.parse_directory(path))
        else:
            raise ValueError(f"Path does not exist: {path}")

        # Filter by minimum size
        return [f for f in fragments if f.size >= min_size]
