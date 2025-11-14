from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def clients(connected_clients):
    kb = InlineKeyboardBuilder()
    for client_id in connected_clients.keys():
        kb.add(InlineKeyboardButton(text=client_id, callback_data=f'client_{client_id}'))
    return kb


def client(client_id):
    return InlineKeyboardBuilder().row(
        InlineKeyboardButton(text='Shutdown', callback_data=f'cmd_shutdown_{client_id}'),
        InlineKeyboardButton(text='Reboot', callback_data=f'cmd_reboot_{client_id}'),
        InlineKeyboardButton(text='Lock Screen', callback_data=f'cmd_lock_{client_id}'),
        width=2
    )
