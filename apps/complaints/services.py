import hashlib
import io
import uuid

from PIL import Image, ImageOps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
ALLOWED_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
private_storage = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=None)


def store_citizen_image(upload):
    if upload.size > MAX_UPLOAD_BYTES:
        raise ValidationError("Photo must be 8 MB or smaller.")
    raw = upload.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValidationError("Photo must be 8 MB or smaller.")
    try:
        with Image.open(io.BytesIO(raw)) as opened:
            if opened.format not in ALLOWED_FORMATS:
                raise ValidationError("Upload a JPEG, PNG or WebP image.")
            if opened.width * opened.height > MAX_IMAGE_PIXELS:
                raise ValidationError("Photo dimensions are too large.")
            image_format = opened.format
            opened.verify()
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in ALLOWED_FORMATS:
                raise ValidationError("Upload a JPEG, PNG or WebP image.")
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValidationError("Photo dimensions are too large.")
            clean = ImageOps.exif_transpose(image).convert("RGB")
            display_max_edge = getattr(settings, "EVIDENCE_DISPLAY_MAX_EDGE", 1600)
            if not isinstance(display_max_edge, int) or display_max_edge < 1:
                raise ValidationError("EVIDENCE_DISPLAY_MAX_EDGE must be a positive integer.")
            clean.thumbnail((display_max_edge, display_max_edge), Image.Resampling.LANCZOS)
            display_buffer = io.BytesIO()
            clean.save(display_buffer, format="JPEG", quality=88, optimize=True, exif=b"")
            thumbnail = clean.copy()
            thumbnail.thumbnail((320, 320), Image.Resampling.LANCZOS)
            thumbnail_buffer = io.BytesIO()
            thumbnail.save(thumbnail_buffer, format="JPEG", quality=82, optimize=True, exif=b"")
    except (OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError("The uploaded photo is invalid or too large to process.") from exc

    token = uuid.uuid4().hex
    extension = ALLOWED_FORMATS[image_format]
    original_path = private_storage.save(f"original/{token}.{extension}", ContentFile(raw))
    saved_paths = [original_path]
    try:
        display_path = private_storage.save(f"display/{token}.jpg", ContentFile(display_buffer.getvalue()))
        saved_paths.append(display_path)
        thumbnail_path = private_storage.save(f"thumbnail/{token}.jpg", ContentFile(thumbnail_buffer.getvalue()))
        saved_paths.append(thumbnail_path)
    except Exception:
        delete_private_files(saved_paths)
        raise
    return original_path, display_path, thumbnail_path, hashlib.sha256(raw).hexdigest()


def delete_private_files(paths):
    for path in paths:
        if path:
            private_storage.delete(path)
