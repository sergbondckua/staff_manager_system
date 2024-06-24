import hashlib
import hmac
import time
import uuid
from pathlib import Path
from typing import Any

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


def check_telegram_auth(data: dict[str, Any], bot_token: str) -> bool:
    """
    Checks Telegram user authentication.
    This function verifies if the provided data is authentic using the Telegram bot token.
    """
    # Get the authentication date
    auth_date = data.get("auth_date")
    if not auth_date:
        return False

    # Check if more than 24 hours have passed since authentication
    current_time = int(time.time())
    if current_time - int(auth_date) > 86400:  # 24 hours
        return False

    # Get the hash for verification
    check_hash = data.pop("hash", None)
    if not check_hash:
        return False

    # Create the data check string from sorted keys and values
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    print(data_check_string)

    # Compute the secret key using the bot token
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    # Compute the hash using the secret key and data check string
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    # Return the result of comparing the calculated hash with the provided hash
    print(secret_key)
    return calculated_hash == check_hash
