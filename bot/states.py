from aiogram.fsm.state import State, StatesGroup


class LoginStates(StatesGroup):
    waiting_for_contact = State()
    waiting_for_username = State()
    waiting_for_password = State()


class QuickEntryStates(StatesGroup):
    waiting_for_entry_type = State()
    waiting_for_shift = State()
    waiting_for_record_date = State()
    waiting_for_liters = State()
    waiting_for_finance_category = State()
    waiting_for_finance_amount = State()
    waiting_for_finance_currency = State()
    waiting_for_finance_source = State()
    waiting_for_finance_date = State()
    waiting_for_finance_note = State()
