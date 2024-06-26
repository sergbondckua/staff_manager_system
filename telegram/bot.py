import hashlib
import hmac
import logging
import time
from typing import Any, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
import aiohttp
from environs import Env

from telegram.state import VacationForm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read environment variables
env = Env()
env.read_env()

# Initialize bot and dispatcher
bot = Bot(
    token=env.str("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
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


async def fetch_requests(method: str, **payloads: Any) -> Optional[dict]:
    """Fetch requests from the staff API."""

    url = f"{env.str('STAFF_API_URL')}/leave-requests/"
    headers = {"Content-Type": "application/json"}
    payloads["hash"] = compute_hash(payloads, env.str("BOT_TOKEN"))

    # Fetch JSON data
    async with aiohttp.ClientSession() as session:
        try:
            async with session.request(
                method, url, json=payloads, headers=headers
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error("Error fetching data: %s", e)
        except aiohttp.HttpProcessingError as e:
            logger.error("HTTP error occurred: %s", e)
        except Exception as e:
            logger.error("An error occurred: %s", e)
        return None


@dp.message(Command(commands=["start"]))
async def send_welcome(message: Message):
    """Send a welcome message when the /start command is received."""
    await message.answer("Hi!\nI'm your Leave Request Bot!")


@dp.message(Command(commands=["my_leaves"]))
async def my_leaves(message: Message):
    """Handle the /my_leaves command and send the user's leave requests."""

    payloads = {
        "telegram_id": message.from_user.id,
        "auth_date": int(time.time()),
    }

    leaves = await fetch_requests("GET", **payloads)
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


@dp.message(Command(commands=["new_vacation"]))
async def new_vacation(message: Message, state: FSMContext):
    """Initiate the vacation request process."""
    await message.answer("Please enter the start date (YYYY-MM-DD):")
    await state.set_state(VacationForm.start_date)


@dp.message(VacationForm.start_date, F.text)
async def process_start_date(message: Message, state: FSMContext):
    await state.update_data(start_date=message.text)
    await message.answer("Please enter the end date (YYYY-MM-DD):")
    await state.set_state(VacationForm.end_date)


@dp.message(VacationForm.end_date, F.text)
async def process_end_date(message: Message, state: FSMContext):
    await state.update_data(end_date=message.text)
    await message.answer("Please enter a comment:")
    await state.set_state(VacationForm.comment)


@dp.message(VacationForm.comment, F.text)
async def process_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await message.answer("Please enter the leave type (number):")
    await state.set_state(VacationForm.leave_type)


@dp.message(VacationForm.leave_type, F.text)
async def process_leave_type(message: Message, state: FSMContext):
    await state.update_data(leave_type=int(message.text))

    data = await state.get_data()
    payloads = {
        "telegram_id": message.from_user.id,
        "auth_date": int(time.time()),
        "start_date": data["start_date"],
        "end_date": data["end_date"],
        "comment": data["comment"],
        "leave_type": data["leave_type"],
    }

    new_vac = await fetch_requests("POST", **payloads)
    response = "\n".join(str(new_vac).split(","))

    await message.answer(
        f"<pre><code class='language-json'>{response}</code></pre>"
    )
    await state.clear()


async def main():
    """Start the bot."""
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
