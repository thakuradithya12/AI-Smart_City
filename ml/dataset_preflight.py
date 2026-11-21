"""Validate owner-provided image folders before any training or evaluation."""

import argparse
import csv
import hashlib
from pathlib import Path, PurePosixPath

from PIL import Image

DATA_CATEGORIES = ("pothole", "garbage", "drainage", "streetlight", "other")
MODEL_CATEGORIES = frozenset({"pothole", "garbage", "drainage", "streetlight"})
ALLOWED_FORMATS = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
}
MAX_IMAGE_PIXELS = 40_000_000
MANIFEST_COLUMNS = {"path", "group_id"}


def audit_dataset(root):
    """Return a privacy-minimal summary and errors; never modify source images."""
    root = Path(root).resolve()
    errors = []
    image_paths = {}
    counts = {category: {"images": 0, "groups": 0} for category in DATA_CATEGORIES}

    if not root.is_dir():
        return counts, ["Dataset root is missing or is not a directory."]

    for category in DATA_CATEGORIES:
        category_root = root / category
        if not category_root.is_dir():
            errors.append(f"Required category folder is missing: {category}.")
            continue
        for path in category_root.rglob("*"):
            if path.is_symlink():
                errors.append(f"Symlinks are not allowed in category: {category}.")
                continue
            if not path.is_file():
                continue
            expected_format = ALLOWED_FORMATS.get(path.suffix.lower())
            if expected_format is None:
                errors.append(f"Unsupported file type in category: {category}.")
                continue
            try:
                with Image.open(path) as image:
                    actual_format = image.format
                    image.verify()
                with Image.open(path) as image:
                    width, height = image.size
                    if width * height > MAX_IMAGE_PIXELS:
                        errors.append(f"Image exceeds the pixel limit in category: {category}.")
                        continue
                    image.load()
                if actual_format != expected_format:
                    errors.append(f"File extension does not match image content in category: {category}.")
                    continue
            except (Image.DecompressionBombError, OSError, ValueError):
                errors.append(f"Unreadable or unsafe image in category: {category}.")
                continue

            try:
                relative_path = path.resolve(strict=True).relative_to(root).as_posix()
            except (OSError, ValueError):
                errors.append(f"Image path escapes the dataset root in category: {category}.")
                continue
            digest_builder = hashlib.sha256()
            with path.open("rb") as image_file:
                for chunk in iter(lambda: image_file.read(1024 * 1024), b""):
                    digest_builder.update(chunk)
            digest = digest_builder.hexdigest()
            image_paths[relative_path] = (category, digest)

    for category in DATA_CATEGORIES:
        counts[category]["images"] = sum(
            image_category == category for image_category, _ in image_paths.values()
        )

    manifest_path = root / "manifest.csv"
    if not manifest_path.is_file():
        errors.append("manifest.csv is required with path and group_id columns.")
        return counts, errors

    manifest_entries = {}
    try:
        with manifest_path.open(newline="", encoding="utf-8-sig") as manifest_file:
            reader = csv.DictReader(manifest_file)
            if reader.fieldnames != ["path", "group_id"]:
                errors.append("manifest.csv must contain exactly path and group_id columns.")
            else:
                for row in reader:
                    raw_path = (row.get("path") or "").replace("\\", "/")
                    relative_path = PurePosixPath(raw_path)
                    group_id = (row.get("group_id") or "").strip()
                    if relative_path.is_absolute() or ".." in relative_path.parts or not raw_path:
                        errors.append("Manifest paths must be relative and remain inside the dataset root.")
                        continue
                    normalized_path = relative_path.as_posix()
                    if not group_id:
                        errors.append("Every image must have a non-empty group_id.")
                        continue
                    if normalized_path in manifest_entries:
                        errors.append("Each image must appear once in manifest.csv.")
                        continue
                    manifest_entries[normalized_path] = group_id
    except (OSError, UnicodeError, csv.Error):
        errors.append("manifest.csv could not be read as valid UTF-8 CSV.")

    if errors and not manifest_entries:
        return counts, errors

    if set(manifest_entries) != set(image_paths):
        errors.append("manifest.csv paths must exactly match the validated image files.")

    digest_groups = {}
    groups_by_category = {category: set() for category in DATA_CATEGORIES}
    for relative_path in set(manifest_entries) & set(image_paths):
        category, digest = image_paths[relative_path]
        group_id = manifest_entries[relative_path]
        prior_group = digest_groups.setdefault(digest, group_id)
        if prior_group != group_id:
            errors.append("Byte-identical images must share one group_id to prevent split leakage.")
        groups_by_category[category].add(group_id)

    for category in DATA_CATEGORIES:
        counts[category]["groups"] = len(groups_by_category[category])

    return counts, errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Preflight owner-provided AI evaluation photos.")
    parser.add_argument("root", nargs="?", default=Path(__file__).parent / "data")
    args = parser.parse_args(argv)
    counts, errors = audit_dataset(args.root)
    for category, summary in counts.items():
        use = "model candidate" if category in MODEL_CATEGORIES else "evaluation only; no model output"
        print(f"{category}: {summary['images']} images, {summary['groups']} groups ({use})")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print("Dataset preflight failed; no training or evaluation was run.")
        return 1
    print("Dataset preflight passed; this does not evaluate model quality.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
