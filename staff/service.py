import uuid
from pathlib import Path

from django.conf import settings


def generate_path(instance, filename: str) -> str:
    """Generate a path for photo upload."""
    ext = Path(filename).suffix
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = Path("staff_photos") / instance.username / unique_filename
    full_path = Path(settings.MEDIA_ROOT) / file_path

    try:
        if full_path.exists():
            full_path.unlink()
    except Exception as e:
        # TODO: Error logging if necessary
        print(f"Error removing file: {e}")

    return str(file_path)
