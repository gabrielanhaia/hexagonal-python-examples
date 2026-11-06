"""Measure the five variants in architectures/.

Standard library only. Run from anywhere inside the repository:

    python3 architectures/measure.py

Per variant it reports the production code (everything outside
tests/): .py files, non-blank non-comment lines, classes and
Protocols. It also counts test functions, and lists the files
the "a booking may not exceed 4 hours" commit touched, read
from git.
"""

import ast
import hashlib
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
VARIANTS = (
    "layered",
    "hexagonal",
    "onion",
    "clean",
    "vertical_slice",
)
RULE_SUBJECT = "a booking may not exceed 4 hours"
SKIP = {".venv", "__pycache__", ".import_linter_cache"}


@dataclass
class Count:
    files: int = 0
    lines: int = 0
    classes: int = 0
    protocols: int = 0
    tests: int = 0
    touched: list[str] = field(default_factory=list)


def python_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.py")
        if not SKIP.intersection(path.relative_to(root).parts)
    )


def code_lines(source: str) -> int:
    return sum(
        1
        for line in source.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def is_protocol(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Subscript):
            base = base.value
        name = getattr(base, "id", getattr(base, "attr", ""))
        if name == "Protocol":
            return True
    return False


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(HERE), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def touched_by_rule(variant: str) -> list[str]:
    log = git(
        "log",
        "--format=%H %s",
        "--",
        f":(top)architectures/{variant}",
    )
    for line in log.splitlines():
        commit, _, subject = line.partition(" ")
        if subject.endswith(RULE_SUBJECT):
            names = git("show", "--name-only", "--format=", commit)
            prefix = f"architectures/{variant}/"
            return sorted(
                name.removeprefix(prefix)
                for name in names.split()
                if name.startswith(prefix)
            )
    return []


def measure(variant: str) -> Count:
    root = HERE / variant
    count = Count(touched=touched_by_rule(variant))
    for path in python_files(root):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if "tests" in path.relative_to(root).parts:
            count.tests += sum(
                1
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef)
                and node.name.startswith("test_")
            )
            continue
        count.files += 1
        count.lines += code_lines(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                count.classes += 1
                count.protocols += is_protocol(node)
    return count


def scenario_digests() -> set[str]:
    return {
        hashlib.sha256(
            (HERE / v / "tests" / "test_scenarios.py").read_bytes()
        ).hexdigest()[:12]
        for v in VARIANTS
    }


def main() -> int:
    counts = {variant: measure(variant) for variant in VARIANTS}
    header = (
        "variant",
        "files",
        "lines",
        "classes",
        "protos",
        "tests",
        "touched",
    )
    print("{:<15}{:>7}{:>7}{:>9}{:>8}{:>7}{:>9}".format(*header))
    for variant, c in counts.items():
        print(
            f"{variant:<15}{c.files:>7}{c.lines:>7}{c.classes:>9}"
            f"{c.protocols:>8}{c.tests:>7}{len(c.touched):>9}"
        )
    print()
    print("files, lines, classes, protos: production code only")
    print("(tests/ excluded); lines are non-blank, non-comment.")
    print("touched: files changed by the max-length rule commit.")
    for variant, c in counts.items():
        print()
        print(f"{variant}:")
        for name in c.touched:
            print(f"  {name}")
    digests = scenario_digests()
    print()
    if len(digests) == 1:
        print(
            f"tests/test_scenarios.py identical in all five "
            f"(sha256 {digests.pop()})"
        )
        return 0
    print("tests/test_scenarios.py DIFFERS between variants")
    return 1


if __name__ == "__main__":
    sys.exit(main())
