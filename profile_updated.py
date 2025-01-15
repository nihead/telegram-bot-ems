from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, MessageHandler, Filters, ContextTypes
from telegram.constants import ParseMode, ChatAction


ASK_NAME, ASK_SO,  ASK_NICKNAME, ASK_MOBILE, ASK_SAVE = range(5)


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pass

async def ask_so(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pass    

async def ask_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pass

async def ask_mobile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pass    

async def ask_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pass



