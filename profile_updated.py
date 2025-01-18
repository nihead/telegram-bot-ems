from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, MessageHandler, Filters, ContextTypes, ConversationHandler, CommandHandler
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

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    query.answer()

    await query.edit_message_text(text="See you next time!")
    return ConversationHandler.END

def profile_update_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("profile_update", ask_name)],
        states={
            ASK_NAME: [MessageHandler(Filters.text & ~Filters.command, ask_so)],
            ASK_SO: [MessageHandler(Filters.text & ~Filters.command, ask_nickname)],
            ASK_NICKNAME: [MessageHandler(Filters.text & ~Filters.command, ask_mobile)],
            ASK_MOBILE: [MessageHandler(Filters.text & ~Filters.command, ask_save)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern="^cancel$"),
            MessageHandler(Filters.text, cancel),
        ],
    )
