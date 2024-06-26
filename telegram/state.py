from aiogram.fsm.state import State, StatesGroup


class VacationForm(StatesGroup):
    """State class representing a Vacation."""

    start_date = State()
    end_date = State()
    comment = State()
    leave_type = State()
