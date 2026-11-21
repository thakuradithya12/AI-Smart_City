import csv

from PIL import Image

from ml.dataset_preflight import audit_dataset, main


def make_dataset(tmp_path, images):
    for category in ("pothole", "garbage", "drainage", "streetlight", "other"):
        (tmp_path / category).mkdir()
    manifest_rows = []
    for relative_path, group_id, color in images:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (12, 10), color=color).save(path, format="JPEG")
        manifest_rows.append({"path": relative_path, "group_id": group_id})
    with (tmp_path / "manifest.csv").open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=("path", "group_id"))
        writer.writeheader()
        writer.writerows(manifest_rows)
    return tmp_path


def test_preflight_accepts_valid_grouped_owner_photos(tmp_path):
    root = make_dataset(
        tmp_path,
        [("pothole/road-a.jpg", "session-a", "black"), ("other/scene-b.jpg", "session-b", "white")],
    )

    counts, errors = audit_dataset(root)

    assert errors == []
    assert counts["pothole"] == {"images": 1, "groups": 1}
    assert counts["other"] == {"images": 1, "groups": 1}


def test_preflight_rejects_missing_group_manifest(tmp_path):
    (tmp_path / "pothole").mkdir(parents=True)
    Image.new("RGB", (4, 4)).save(tmp_path / "pothole" / "image.jpg")

    counts, errors = audit_dataset(tmp_path)

    assert counts["pothole"]["images"] == 1
    assert any("manifest.csv is required" in error for error in errors)


def test_preflight_rejects_traversal_path(tmp_path):
    root = make_dataset(tmp_path, [("pothole/road-a.jpg", "session-a", "black")])
    with (root / "manifest.csv").open("a", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=("path", "group_id"))
        writer.writerow({"path": "../outside.jpg", "group_id": "session-a"})

    _, errors = audit_dataset(root)

    assert any("must be relative" in error for error in errors)


def test_preflight_rejects_corrupt_image_and_reports_no_training(tmp_path, capsys):
    root = make_dataset(tmp_path, [("pothole/road-a.jpg", "session-a", "black")])
    (root / "pothole" / "road-a.jpg").write_bytes(b"not an image")

    result = main([str(root)])
    output = capsys.readouterr().out

    assert result == 1
    assert "Unreadable or unsafe image" in output
    assert "no training or evaluation was run" in output


def test_preflight_rejects_identical_image_in_multiple_groups(tmp_path):
    root = make_dataset(
        tmp_path,
        [("pothole/road-a.jpg", "session-a", "black"), ("pothole/road-b.jpg", "session-b", "black")],
    )

    _, errors = audit_dataset(root)

    assert any("must share one group_id" in error for error in errors)
