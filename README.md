# Simuradar

AST-based Python code duplication detection.

## Why AST?

Simuradar uses Python's built-in `ast` module—no external parser dependencies. This means:

- **Zero parser dependencies** — Only standard library + output formatters
- **Native Python version alignment** — The AST parser IS your Python interpreter. No parser/ runtime version mismatches
- **Automatic updates** — When Python adds new syntax `match` (like in 3.10 or improved f-strings in 3.12), Simuradar gets it for free
- **No third-party parser edge cases** — External parsers may diverge from CPython's behavior. We use the real thing

## Installation

```bash
pip install .
# or with uv
uv pip install .
```

## Usage

```bash
simuradar /path/to/project
```

Options:
- `--engine {apted,jaccard,jaccard-norm}` — Similarity algorithm (default: jaccard)
- `--threshold 0.8` — Similarity threshold 0.0-1.0 (default: 0.8)
- `--output {rich,json}` — Output format (default: rich)

## How It Works

1. **Parse** — Walk the target directory, extract code fragments (functions, classes, modules) using Python's `ast` module
2. **Normalize** — Optional: strip comments, normalize whitespace (not yet implemented)
3. **Compare** — Run selected similarity algorithm against all fragment pairs
4. **Report** — Group similar fragments and display results

## Engines

| Engine | Description | Complexity |
|--------|-------------|------------|
| `apted` | Tree edit distance (APTED) | O(n³) — Slow but accurate |
| `jaccard` | Node type Jaccard similarity | O(n²) — Fast |
| `jaccard-norm` | Jaccard + subtree patterns | O(n²) — Balanced |

## Requirements

- Python 3.12+
- cyclopts (CLI)
- rich (terminal output)
- apted (optional, for apted engine)
