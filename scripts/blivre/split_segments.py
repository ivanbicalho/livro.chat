#!/usr/bin/env python3
"""Applies deterministic speaker/segment edits to public/api/pt-br/blivre/**/*.json
files, driven by a JSON "patch" describing one or more operations.

Usage:
    python3 scripts/split_segments.py <patch.json> [--dry-run]

Patch file shape:
{
  "operations": [
    {
      "file": "public/api/pt-br/blivre/genesis/1.json",
      "book": "genesis",      # optional sanity check
      "chapter": 1,           # optional sanity check
      "verse": 3,
      "segments": [
        { "speaker": "narrator", "text": "E disse Deus:" },
        { "speaker": "god", "text": "Haja luz;" },
        { "speaker": "narrator", "text": "e houve luz." }
      ]
    },
    {
      "file": "public/api/pt-br/blivre/genesis/2.json",
      "verse": 23,
      "action": "setSpeaker",
      "segmentIndex": 0,      # omit if verse has exactly one segment
      "speaker": "adam"
    }
  ]
}

A single operation object (without the "operations" wrapper) is also accepted
for one-off edits.

"split" (default action when "segments" is present) replaces a verse's
segments array entirely. Before writing, the script verifies the joined text
of the new segments matches the joined text of the old segments (ignoring
quote characters and whitespace differences), so no words are accidentally
lost or duplicated. Pass "force": true on the operation to allow an
intentional text change (e.g. dropping a redundant "(disse ela)" attribution
aside) - a warning is printed showing the diff.

"setSpeaker" only relabels the speaker of an existing segment (or the verse's
single segment) without touching any text.
"""

import argparse
import json
import re
import sys
from pathlib import Path

QUOTE_CHARS = re.compile(r"[\u201C\u201D\u00AB\u00BB\u2018\u2019\"']")
WHITESPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    text = QUOTE_CHARS.sub("", text)
    text = WHITESPACE.sub(" ", text)
    return text.strip()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")


def find_verse(data: dict, verse_number: int, file_path: str) -> dict:
    for verse in data["verses"]:
        if verse["verse"] == verse_number:
            return verse
    raise ValueError(f"Verse {verse_number} not found in {file_path}")


def apply_split(data: dict, op: dict) -> None:
    verse = find_verse(data, op["verse"], op["file"])
    old_norm = normalize(" ".join(s["text"] for s in verse["segments"]))
    new_norm = normalize(" ".join(s["text"] for s in op["segments"]))

    if old_norm != new_norm:
        message = "\n".join(
            [
                f"Text mismatch in {op['file']} verse {op['verse']}:",
                f"  OLD: {old_norm}",
                f"  NEW: {new_norm}",
            ]
        )
        if not op.get("force"):
            raise ValueError(f"{message}\nUse \"force\": true on the operation to override.")
        print(f"[forced change]\n{message}", file=sys.stderr)

    verse["segments"] = [{"speaker": s["speaker"], "text": s["text"]} for s in op["segments"]]


def apply_set_speaker(data: dict, op: dict) -> None:
    verse = find_verse(data, op["verse"], op["file"])
    segment_index = op.get("segmentIndex")
    if segment_index is not None:
        try:
            segment = verse["segments"][segment_index]
        except IndexError:
            raise ValueError(
                f"Segment index {segment_index} not found in verse {op['verse']} of {op['file']}"
            )
        segment["speaker"] = op["speaker"]
        return

    if len(verse["segments"]) != 1:
        raise ValueError(
            f"Verse {op['verse']} in {op['file']} has {len(verse['segments'])} segments; "
            f"specify \"segmentIndex\""
        )
    verse["segments"][0]["speaker"] = op["speaker"]


def apply_operation(data: dict, op: dict) -> None:
    if op.get("book") and data.get("book") != op["book"]:
        raise ValueError(f"Book mismatch in {op['file']}: expected \"{op['book']}\", found \"{data.get('book')}\"")
    if op.get("chapter") is not None and data.get("chapter") != op["chapter"]:
        raise ValueError(f"Chapter mismatch in {op['file']}: expected {op['chapter']}, found {data.get('chapter')}")

    action = op.get("action") or ("split" if "segments" in op else "setSpeaker")
    if action == "split":
        apply_split(data, op)
    elif action == "setSpeaker":
        apply_set_speaker(data, op)
    else:
        raise ValueError(f"Unknown action \"{action}\" for {op['file']} verse {op['verse']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply deterministic speaker/segment edits to blivre JSON files.")
    parser.add_argument("patch", help="Path to a JSON patch file")
    parser.add_argument("--dry-run", action="store_true", help="Do not write any files")
    args = parser.parse_args()

    patch = load_json(Path(args.patch))
    operations = patch["operations"] if isinstance(patch, dict) and "operations" in patch else [patch]

    files_by_path: dict[Path, dict] = {}
    for op in operations:
        file_path = Path(op["file"]).resolve()
        if file_path not in files_by_path:
            files_by_path[file_path] = load_json(file_path)
        apply_operation(files_by_path[file_path], op)

    for file_path, data in files_by_path.items():
        if args.dry_run:
            print(f"[dry-run] would write {file_path}")
        else:
            save_json(file_path, data)
            print(f"Updated {file_path}")


if __name__ == "__main__":
    main()
