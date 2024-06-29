import hashlib
import hmac
import json
import logging
import time
from datetime import datetime
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


def compute_hmac_hash(params: dict[str, Any], secret: str) -> str:
    """Compute the HMAC hash for the given params."""

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )
    secret_key = hashlib.sha256(secret.encode()).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    return computed_hash


async def make_api_request(
    method: str, endpoint: str, **params: Any
) -> Optional[dict]:
    """Make API requests."""

    url = f"{env.str('STAFF_API_URL')}/{endpoint}/"
    headers = {"Content-Type": "application/json"}
    params["hash"] = compute_hmac_hash(params, env.str("BOT_TOKEN"))

    # Fetch JSON data
    async with aiohttp.ClientSession() as session:
        try:
            async with session.request(
                method, url, json=params, headers=headers
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as client_error:
            logger.error("Error fetching data: %s", client_error)
        except Exception as general_error:
            logger.error("An error occurred: %s", general_error)
        return None


@dp.message(Command(commands=["start"]))
async def send_welcome(message: Message):
    """Send a welcome message when the /start command is received."""
    await message.answer("Hi!\nI'm your Leave Request Bot!")


@dp.message(Command(commands=["my_leaves"]))
async def my_leaves(message: Message):
    """Handle the /my_leaves command and send the user's leave requests."""

    params = {
        "telegram_id": message.from_user.id,
        "auth_date": int(time.time()),
    }

    leave_requests = await make_api_request("GET", "leave-requests", **params)
    response = (
        "No leave requests found."
        if not leave_requests
        else "Your Leave Requests:\n\n"
        + "\n".join(
            f"Start Date: {leave['start_date']}, End Date: {leave['end_date']}, Status: {leave['status']}"
            for leave in leave_requests
        )
    )

    await message.answer(response)


@dp.message(Command(commands=["new_vacation"]))
async def new_vacation(message: Message, state: FSMContext):
    """Initiate the vacation request process."""

    params = {"telegram_id": message.from_user.id}
    is_employee = await make_api_request(
        "GET", "leave-requests/telegram_is_employee", **params
    )
    if not is_employee.get("status"):
        await message.answer(
            "You are not an employee or not yet registered, please contact your manager."
        )
        return

    await message.answer("Please enter the start date (DD.MM.YYYY):")
    await state.set_state(VacationForm.start_date)


@dp.message(VacationForm.start_date, F.text)
async def process_start_date(message: Message, state: FSMContext):
    try:
        start_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        if start_date < datetime.now().date():
            await message.answer(
                "Start date cannot be later than current date\n\n"
                "Please enter the end date:"
            )
            return
        await state.update_data(start_date=start_date)
        await message.answer("Please enter the end date (DD.MM.YYYY):")
        await state.set_state(VacationForm.end_date)
    except ValueError:
        await message.reply(
            "Invalid date format. Please enter a date in the format DD.MM.YYYY:"
        )


@dp.message(VacationForm.end_date, F.text)
async def process_end_date(message: Message, state: FSMContext):
    data = await state.get_data()
    start_date = data["start_date"]

    try:
        end_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        if start_date >= end_date:
            await message.answer(
                "End date cannot be earlier than start date.\n\n"
                "Please enter the end date:"
            )
            return
        await state.update_data(end_date=end_date)
        await message.answer("Please enter a comment:")
        await state.set_state(VacationForm.comment)
    except ValueError:
        await message.reply(
            "Invalid date format. Please enter a date in the format DD.MM.YYYY:"
        )


@dp.message(VacationForm.comment, F.text)
async def process_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)

    # Receive a list of vacation types
    leave_types = await make_api_request("GET", "leave-type", **{})

    # Create a message with a list of vacation types
    leave_types_message = "\n".join(
        f"{leave_type['id']}. {leave_type['title']}"
        for leave_type in leave_types
    )
    await message.answer(
        f"Please enter the leave type (number):\n{leave_types_message}"
    )
    await state.set_state(VacationForm.leave_type)


@dp.message(VacationForm.leave_type, F.text)
async def process_leave_type(message: Message, state: FSMContext):
    # Receive a list of vacation types
    valid_leave_types = [
        num["id"] for num in await make_api_request("GET", "leave-type")
    ]
    try:
        leave_type = int(message.text)
        # Correctness check leave_type
        if leave_type not in valid_leave_types:
            await message.answer(
                "Wrong type of leave. Please enter a valid leave type."
            )
            return
    except ValueError:
        await message.answer(
            "Incorrect input. Please enter a numeric leave type:"
        )
        return

    await state.update_data(leave_type=int(message.text))

    data = await state.get_data()
    params = {
        "telegram_id": message.from_user.id,
        "auth_date": int(time.time()),
        "start_date": data["start_date"].strftime("%Y-%m-%d"),
        "end_date": data["end_date"].strftime("%Y-%m-%d"),
        "comment": data["comment"],
        "leave_type": data["leave_type"],
    }

    # Create vacation form and save
    new_vacation_request = await make_api_request(
        "POST", "leave-requests", **params
    )
    # Send for approval
    await make_api_request(
        "POST",
        f"leave-requests/{new_vacation_request['id']}/save_and_submit",
        **params,
    )
    response = json.dumps(new_vacation_request, indent=4, ensure_ascii=False)

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
