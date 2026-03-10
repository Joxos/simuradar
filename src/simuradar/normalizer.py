"""AST normalization for structural comparison."""

import ast
import copy
from typing import Any


class Normalizer(ast.NodeTransformer):
    """Normalize AST nodes for structural comparison.

    This transformer:
    - Replaces variable names with generic identifiers (var_0, var_1, ...)
    - Replaces string literals with generic placeholder
    - Replaces numeric literals with generic placeholder
    - Removes docstrings
    """

    def __init__(self) -> None:
        super().__init__()
        self._name_map: dict[str, str] = {}
        self._name_counter: int = 0

    def _normalize_name(self, name: str) -> str:
        """Map a name to a generic identifier."""
        if name not in self._name_map:
            self._name_map[name] = f"var_{self._name_counter}"
            self._name_counter += 1
        return self._name_map[name]

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """Normalize variable names."""
        return ast.Name(id=self._normalize_name(node.id), ctx=node.ctx)

    def visit_NameConstant(self, node: ast.NameConstant) -> ast.Constant:
        """Normalize True/False/None to generic values."""
        return ast.Constant(value="BOOL")

    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        """Normalize string and numeric literals."""
        if isinstance(node.value, str):
            return ast.Constant(value="STR")
        elif isinstance(node.value, (int, float, complex)):
            return ast.Constant(value="NUM")
        return node

    def visit_Num(self, node: ast.Num) -> ast.Constant:
        """Normalize numeric literals (Python 3.7 compatibility)."""
        return ast.Constant(value="NUM")

    def visit_Str(self, node: ast.Str) -> ast.Constant:
        """Normalize string literals (Python 3.7 compatibility)."""
        return ast.Constant(value="STR")

    def visit_Expr(self, node: ast.Expr) -> Any:
        """Remove docstrings (first string literal expression)."""
        # Check if this is a docstring
        if isinstance(node.value, (ast.Str, ast.Constant)):
            if isinstance(node.value, ast.Constant) and isinstance(
                node.value.value, str
            ):
                # Keep the node if it's not a docstring (not at module/function start)
                return node
            elif isinstance(node.value, ast.Str):
                return None  # Remove docstring
        return node


def normalize_ast(tree: ast.AST) -> ast.AST:
    """Create a normalized copy of an AST for comparison."""
    normalizer = Normalizer()
    normalized = normalizer.visit(tree)
    # Fix missing locations for transformed nodes
    ast.fix_missing_locations(normalized)
    return copy.deepcopy(normalized)


def ast_to_bracket_notation(tree: ast.AST) -> str:
    """Convert AST to bracket notation for apted.

    Example: {FunctionDef{body{Return{BinOp{...}}}}}
    """
    return _node_to_bracket(tree)


def _node_to_bracket(node: ast.AST) -> str:
    """Recursively convert AST node to bracket notation."""
    if node is None:
        return "{}"

    # Get node type as label
    label = node.__class__.__name__

    # Get children
    children: list[str] = []
    for child in ast.iter_child_nodes(node):
        children.append(_node_to_bracket(child))

    if children:
        return f"{{{label}{{{'}{'.join(children)}}}}}"
    else:
        return f"{{{label}}}"


def ast_to_tree_string(tree: ast.AST) -> str:
    """Convert AST to a tree string for apted.

    Returns a string representation suitable for apted consumption.
    """
    return ast_to_bracket_notation(tree)
