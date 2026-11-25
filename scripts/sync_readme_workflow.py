"""Sync the workflow status table in README from the generated workflow reference."""

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "WORKFLOW.md"
README = ROOT / "README.md"
START = "<!-- WORKFLOW_TABLE_START -->"
END = "<!-- WORKFLOW_TABLE_END -->"
SECTION = "## Statuses and allowed outgoing transitions"


def generated_table(source_text):
    section = source_text.split(SECTION, 1)[1]
    lines = []
    for line in section.splitlines():
        if line.startswith("|"):
            lines.append(line)
        elif lines:
            break
    if len(lines) < 3:
        raise ValueError("The workflow status table was not found in docs/WORKFLOW.md")
    return "\n".join(lines)


def synced_readme(readme_text, table):
    start = readme_text.index(START) + len(START)
    end = readme_text.index(END, start)
    return readme_text[:start] + "\n\n" + table + "\n\n" + readme_text[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if README is out of sync")
    args = parser.parse_args()
    current = README.read_text(encoding="utf-8")
    expected = synced_readme(current, generated_table(SOURCE.read_text(encoding="utf-8")))
    if args.check:
        if current != expected:
            raise SystemExit("README workflow table is stale; run python scripts/sync_readme_workflow.py")
        print("README workflow table is current.")
    else:
        README.write_text(expected, encoding="utf-8")
        print("Updated README workflow table from docs/WORKFLOW.md.")


if __name__ == "__main__":
    main()
