from telegram import Update
from telegram.ext import ContextTypes
from keyboards import get_back_to_menu_keyboard, get_main_keyboard
from config import TELEGRAPH_HELP_LINK, TERMS_OF_USE

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"❓ Нужна помощь?\n\nПерейдите по ссылке для подробной инструкции:\n{TELEGRAPH_HELP_LINK}",
        reply_markup=get_back_to_menu_keyboard()
    )

async def terms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        TERMS_OF_USE,
        reply_markup=get_back_to_menu_keyboard()
    )

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🏠 Главное меню\n\nВыберите действие:",
        reply_markup=get_main_keyboard()
    )