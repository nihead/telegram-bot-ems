#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

import logging
import os

from dotenv import load_dotenv
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, CallbackContext
from pocketbase import PocketBase
from services import Db
import asyncio
from threading import Thread
import time


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

#Keyboards
kb_i_o = [
        [
            InlineKeyboardButton("IN", callback_data='IN'),
            InlineKeyboardButton("OUT", callback_data='OUT')
        ]
    ]
kb_o = [
        [
            InlineKeyboardButton("OUT", callback_data='OUT')
        ]
    ]


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    username = update.message.chat.full_name
    cid = update.message.chat.id
    welcome = f"""
    <b>WELCOME TO EMS FOOTBALL TEAM MAKER BOT!</b>
    
Salaam! {username},
Please answer all question and wait for Approvals From Our Teams!!
THANK YOU!
    """
    await update.message.reply_text(
        text=welcome,
        parse_mode='HTML'
    )
    await update.message.reply_html(
        rf"What is your name?",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("keep thinking!")


async def team_maker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    m = update.message.text.split('\n')

    f_msg= f"""
    <u>Team List</u>
<b>{m[1]}</b>
    
<i>Interested Press IN</i>
    """

    await update.message.reply_text(
        f_msg,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(kb_i_o)
    )

# Define a function to handle button press events
async def inline_button(update: Update, context) -> None:
    query = update.callback_query
    user = query.from_user  # Get the user who pressed the button
    username = user.username or user.first_name
    current_message = query.message.text
    chat_id = query.message.chat.id


    # Determine which button was pressed
    if query.data == 'IN':
        new_message = f"{current_message}\n{username} is: {query.data}"
        suc = await add_to_db(chat_id)
        if suc:
            await query.edit_message_text(text=new_message, reply_markup=InlineKeyboardMarkup(kb_i_o))
        else:
            alert = await query.message.reply_text("May be you are on list")
            print(alert.chat_id)
            # pythoncom.CoInitialize()
            Thread(target=delete_alert, daemon=True, args=(alert,)).start()
            # Thread(target=delete_message_in_thread, args=(
            #     context.bot,  # The bot instance
            #     alert.chat_id,  # The chat ID of the sent message
            #     alert.message_id  # The message ID of the sent message
            # )).start()

        # await query.edit_message_text(text="You pressed: IN")
    elif query.data == 'OUT':
        await query.edit_message_text(text="You pressed: OUT")

    await query.answer()


async def delete_message_in_thread(bot, chat_id, message_id):
    # Sleep for 5 seconds
    time.sleep(5)
    # Delete the message (this will run in a separate thread)
    await bot.delete_message(chat_id=chat_id, message_id=message_id)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)


def delete_alert(alert):
    time.sleep(3)
    alert.delete()

async def add_to_db(tid):
    pb = Db()
    if pb.on_list(tid) == 0:
        suc = pb.add_to_team(tid)
        print("New player saved")
        return True if suc else False

async def on_list(tid=498123938) -> int:
    tid = tid
    pb = PocketBase(os.environ['pb'])

    p = pb.collection('team').get_list(1,20,{"filter": f'tid = {tid} && active = true'})
    return p.total_items



def main() -> None:
    """Start the bot."""
    load_dotenv()

    # Create the Application and pass it your bot's token.
    # application = Application.builder().token(os.environ["TOKEN"]).build()
    application = Application.builder().token(os.environ["TOKEN"]).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("team", team_maker))
    application.add_handler(CallbackQueryHandler(inline_button))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
