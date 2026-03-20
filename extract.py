#!/usr/bin/env python3
"""
extract.py — Extract 30 player fields from screenshots and append to xlsx.

Usage:
    # Batch — process all images in a directory (default)
    python extract.py assets/screens/ assets/ScoutDecisionPlayerImport.xlsx

    # Single player
    python extract.py assets/screens/ assets/ScoutDecisionPlayerImport.xlsx --file 1.jpg

    # Flags
    --file <name>   Process a single image file inside the screens directory
    --dry-run       Print extracted data without writing to xlsx
    --verbose       Show Gemini prompt and raw response
"""

import argparse
import os
import sys

from gemini_client import extract_fields
from position_mapper import convert_fields, load_map
from xlsx_manager import HEADERS, append_row, reset_rows

_POSITION_MAP = load_map()

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def print_summary(filename: str, data: dict) -> None:
    print("\n" + "=" * 56)
    print(f"  {filename}")
    print("=" * 56)
    for header in HEADERS:
        value = data.get(header) or data.get(header.split("(")[0].strip())
        label = header.split("(")[0].strip()
        display = str(value) if value is not None else "—"
        print(f"  {label:<42} {display}")
    print("=" * 56)


def process(image_path: str, output: str, dry_run: bool, verbose: bool, use_fallback: bool = False) -> bool:
    print(f"\nSending {os.path.basename(image_path)} to Gemini...")
    try:
        data = extract_fields(image_path, verbose=verbose, use_fallback=use_fallback)
        data = convert_fields(data, _POSITION_MAP)
    except EnvironmentError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    print_summary(os.path.basename(image_path), data)

    if dry_run:
        print("  [dry-run] Row not written.")
    else:
        append_row(output, data)
        print(f"  Row appended to: {output}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Extract player data from screenshots into xlsx."
    )
    parser.add_argument("screens_dir", help="Directory containing screenshots.")
    parser.add_argument("output", help="Path to the output .xlsx file.")
    parser.add_argument("--file", metavar="FILENAME", help="Process a single image inside screens_dir.")
    parser.add_argument("--dry-run", action="store_true", help="Print extracted data without writing to xlsx.")
    parser.add_argument("--verbose", action="store_true", help="Show Gemini prompt and raw response.")
    parser.add_argument("--reset", action="store_true", help="Delete all data rows below the header, then exit.")
    parser.add_argument("--fallback", action="store_true", help=f"Skip primary model and use fallback directly.")
    args = parser.parse_args()

    if args.reset:
        reset_rows(args.output)
        sys.exit(0)

    if not os.path.isdir(args.screens_dir):
        print(f"Error: Directory not found: {args.screens_dir}", file=sys.stderr)
        sys.exit(1)

    # Single file mode
    if args.file:
        image_path = os.path.join(args.screens_dir, args.file)
        if not os.path.isfile(image_path):
            print(f"Error: File not found: {image_path}", file=sys.stderr)
            sys.exit(1)
        ok = process(image_path, args.output, args.dry_run, args.verbose, args.fallback)
        sys.exit(0 if ok else 1)

    # Batch mode
    images = sorted([
        f for f in os.listdir(args.screens_dir)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
    ])

    if not images:
        print(f"No images found in {args.screens_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(images)} image(s) in {args.screens_dir}")
    failed = []
    for filename in images:
        image_path = os.path.join(args.screens_dir, filename)
        ok = process(image_path, args.output, args.dry_run, args.verbose, args.fallback)
        if not ok:
            failed.append(filename)

    print(f"\nDone: {len(images) - len(failed)}/{len(images)} processed successfully.")
    if failed:
        print("Failed:", ", ".join(failed))
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
