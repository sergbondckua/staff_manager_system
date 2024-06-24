import hashlib
import hmac
import logging
import time
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import aiohttp
from environs import Env

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read environment variables
env = Env()
env.read_env()

# Initialize bot and dispatcher
bot = Bot(token=env.str("BOT_TOKEN"))
dp = Dispatcher()


def compute_hash(payload: dict[str, Any], secret: str) -> str:
    """Compute the HMAC hash for the given payload."""
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(payload.items())
    )
    secret_key = hashlib.sha256(secret.encode()).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    return computed_hash


async def fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
):
    """
    Fetch JSON data from the given URL using the provided session, payload, and headers.
    """
    try:
        async with session.get(url, json=payload, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching leave requests: %s", e)
    except aiohttp.HttpProcessingError as e:
        logger.error(f"HTTP error occurred: %s", e)
    except Exception as e:
        logger.error(f"An error occurred: %s", e)
    return None


async def fetch_requests(telegram_id: int, auth_date: int, **kwargs):
    """Fetch leave requests from the staff API."""

    url = f"{env.str('STAFF_API_URL')}/leave-requests/"
    headers = {"Content-Type": "application/json"}
    payload = {
        "telegram_id": telegram_id,
        "auth_date": auth_date,
        **kwargs,
    }
    payload["hash"] = compute_hash(payload, env.str("BOT_TOKEN"))
    logger.info(payload)

    async with aiohttp.ClientSession() as session:
        return await fetch_json(session, url, payload, headers)


@dp.message(Command(commands=["start"]))
async def send_welcome(message: Message):
    """Send a welcome message when the /start command is received."""
    await message.answer("Hi!\nI'm your Leave Request Bot!")


@dp.message(Command(commands=["new_vacation"]))
async def new_vacation(message: Message):
    """Handle the /my_leaves command and send the user's leave requests."""

    telegram_id = message.from_user.id
    auth_date = int(time.time())
    start_date = "2024-08-15"
    end_date = "2024-08-20"
    comment = "hook"
    leave_type = 1

    new_vac = await fetch_requests(
        telegram_id,
        auth_date,
        start_date=start_date,
        end_date=end_date,
        leave_type=leave_type,
        comment=comment,
    )
    response = new_vac

    await message.answer(str(response))


@dp.message(Command(commands=["my_leaves"]))
async def my_leaves(message: Message):
    """Handle the /my_leaves command and send the user's leave requests."""

    telegram_id = message.from_user.id
    auth_date = int(time.time())

    leaves = await fetch_requests(telegram_id, auth_date)
    response = (
        "No leave requests found."
        if not leaves
        else "Your Leave Requests:\n\n"
        + "\n".join(
            f"Start Date: {leave['start_date']}, End Date: {leave['end_date']}, Status: {leave['status']}"
            for leave in leaves
        )
    )

    await message.answer(response)


async def main():
    """Start the bot."""
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())