#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

import logging
import os
from tkinter.font import names

from dotenv import load_dotenv
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, \
    CallbackContext, ChatMemberHandler
from telegram.constants import ChatAction, ParseMode
from pocketbase import PocketBase

# import bot
from examples.errorhandlerbot import error_handler
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

# Keyboards
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

qid = 0


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
This bot is ....!!
THANK YOU!
    """
    await update.message.reply_text(
        text=welcome,
        parse_mode=ParseMode.HTML
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("keep thinking!")


async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /alert is issued."""
    await update.message.delete()
    msg = update.message.text.strip('/alert')
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=f"<pre>Notification</pre>\n\nmsg",
        parse_mode='HTML'
    )


async def team_maker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    m = update.message.text.strip('/team').strip().split('\n')
    u_name = update.effective_user.full_name

    try:
        mp = int(m[-2])
        mr = int(m[-1])
        desc = '\n'.join(m[:-2])
    except Exception as e:
        mp = 14
        mr = 2
        desc = "Kulhun @ Male' city Council\nFrom <b>19:00</b> to <b>20:00</b>"


    f_msg = f"""
{'<u>Team List</u>'.center(50,'~')}
{desc}
---------------------
<u><b>ONTEAM</b></u>
---------------------
    """

    pb_db = Db()
    await update.message.delete()
    if pb_db.active_seesion():
        f_msg = """<b>An active team listing session is currently in progress.</b>
Please try again later.

Thank you for your patience."""

        await context.bot.send_message(chat_id=update.message.chat_id, text=f_msg, parse_mode="HTML")

    else:
        # create kulhun
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"<b>{u_name}</b>, Started Team listing session\nMax players = {mp}\nMax reserved = {mr}",
            parse_mode="HTML",
        )
        # Add user restrction
        # await restrict_all(update, context)

        await asyncio.sleep(2)

        k = await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f_msg,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(kb_i_o)
        )
        pb_db.create_kulhun(update.message.from_user.id, desc, k.message_id, mp, mr)


# Define a function to handle button press events
async def inline_button(update: Update, context) -> None:
    query = update.callback_query
    user = query.from_user  # Get the user who pressed the button
    username = f"{user.first_name} {user.last_name if user.last_name else ''}"
    current_message = query.message.text
    chat_id = query.from_user.id

    await context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)

    # Determine which button was pressed
    try:
        if query.data == 'IN':
            # saving
            suc, on_team, no_players, total_players = await add_to_db(chat_id, query, context)

            if suc:
                pb_db = Db()
                team_list = pb_db.team_list()
                # get descrption from kulhun
                desc = pb_db.pb.collection('kulhun').get_list(1, 30, {"filter": 'completed = false'}).items[
                    0].description
                team_msg = f"""
{'<u>Team List</u>'.center(50,'~')}
<i>{desc}</i>
---------------------
<u><b>ONTEAM</b></u>
---------------------
{team_list}
"""

                await query.edit_message_text(text=team_msg, reply_markup=InlineKeyboardMarkup(kb_i_o),
                                              parse_mode=ParseMode.HTML)
                if no_players + 1 == total_players:
                    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(kb_o))
                await query.answer(
                    text=f"{username}\nAdded to Team list",
                    show_alert=True
                )
            else:
                await query.answer(
                    text=f"{username}\nYou are Already on the list",
                    show_alert=True
                )

            # await query.edit_message_text(text="You pressed: IN")
        elif query.data == 'OUT':

            pb_db = Db()
            if pb_db.on_list(chat_id) > 0:

                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"{username}  takes his name off the list.",
                    parse_mode=ParseMode.HTML
                )
                await query.answer(
                    text=f"{username}\nRemoved from Team list",
                    show_alert=True
                )
                # await query.edit_message_reply_markup(reply_markup=None)
                await query.delete_message()

                # mark user out from list & updating from reserved
                suc = pb_db.off_list(chat_id)

                # recreate team list
                if suc:
                    print("Making team list")
                    team_list = pb_db.team_list()
                    # get descrption from kulhun
                    desc = pb_db.pb.collection('kulhun').get_list(1, 20, {"filter": 'completed = false'}).items[
                        0].description
                    team_msg = f"""
{'<u>Team List</u>'.center(50,'~')}
<i>{desc}</i>
---------------------
<u><b>ONTEAM</b></u>
---------------------
{team_list}
"""

                    new_list = await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=team_msg,
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(kb_i_o)
                    )

                    # update new message id
                    pb_db.pb.collection('kulhun').update(
                        pb_db.pb.collection('kulhun').get_list(1, 20, {"filter": 'completed = false'}).items[0].id,
                        {"message_id": new_list.message_id})



            else:
                await query.answer(
                    text=f"{username}\nYou are not on the list",
                    show_alert=True
                )


    except Exception as e:
        await on_error(context, "inline Query", e)

    finally:
        await query.answer()


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    if Db().active_seesion():
        await update.message.delete()
        alert = await update.message.reply_text("Ongoing Team polling\nNot allowed send messages")
        await asyncio.sleep(2)
        await alert.delete()
    else:
        pass


async def add_to_db(tid, query, context):

    pb = Db()
    no_players = pb.no_players()
    max_players = pb.max_players()
    max_reserves = pb.max_reserved()
    total_players = max_players + max_reserves
    print(no_players, max_players, max_reserves, total_players)

    # players limit check
    if pb.on_list(tid) == 0:

        if no_players < total_players:
            if no_players < max_players:
                if pb.add_to_team(tid, True):
                    print("New player saved")
                    # return succeeded , on_team, no_players, t_player
                    return True, True, no_players, total_players
            else:
                if pb.add_to_team(tid, False):
                    print("New player saved")
                    # return succeeded , on_team, no_players
                    return True, False, no_players, total_players
        else:
            print("Max players reached")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Max players reached",
                parse_mode=ParseMode.HTML
            )
            try:

                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup(kb_o))
                # return succeeded , on_team, no_players
                return False, False, no_players, total_players
            except Exception as e:
                print(e)
            return False, False, no_players, total_players
    else:
        print("on List")
        return False, False, no_players, total_players

    # async def on_list(tid=498123938) -> int:
    tid = tid
    pb = PocketBase(os.environ['pb'])

    p = pb.collection('team').get_list(1, 20, {"filter": f'tid = {tid} && active = true'})
    return p.total_items


async def completed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /completed is issued."""
    await update.message.delete()
    info = await context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Ending team listing session.",
        parse_mode=ParseMode.HTML
    )
    pb_db = Db()
    if pb_db.active_seesion():
        # remove inline keyboard from privious listing with message id from kulhun
        try:
            message_id = pb_db.pb.collection('kulhun').get_list(1, 20, {"filter": 'completed = false'}).items[
                0].message_id
            print(update.effective_chat.id)
            print(update.message.chat_id)
            await context.bot.edit_message_reply_markup(
                chat_id=update.effective_chat.id,
                message_id=message_id,
                reply_markup=None
            )
        except Exception as e:
            await on_error(context, "completed", e)

        # mark active session as completed
        pb_db.pb.collection('kulhun').update(
            pb_db.pb.collection('kulhun').get_list(1, 20, {"filter": 'completed = false'}).items[0].id,
            {"completed": True})
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            text="<b>Marking Attendance..</b>",
            message_id=info.message_id,
            parse_mode=ParseMode.HTML
        )

        # mark attended as true on all team
        pb_db.all_attended()

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            text="<b>Team Listing Ended</b>",
            message_id=info.message_id,
            parse_mode=ParseMode.HTML
        )
    else:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            text="<b>No Active <i>Polling</i></b>",
            message_id=info.message_id,
            parse_mode=ParseMode.HTML
        )

async def end_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /completed is issued."""
    await update.message.delete()

    pb_db = Db()
    if pb_db.active_seesion():
        # remove inline keyboard from privious listing with message id from kulhun
        try:
            info = await context.bot.send_message(
                chat_id=update.message.chat_id,
                text="<b>Ending.. Polling Session</b>",
                parse_mode="HTML"
            )

            message_id = pb_db.pb.collection('kulhun').get_list(1, 20, {"filter": 'completed = false'}).items[
                0].message_id

            await context.bot.edit_message_reply_markup(
                chat_id=update.effective_chat.id,
                message_id=message_id,
                reply_markup=None
            )

            await context.bot.edit_message_text(
                chat_id=info.chat_id,
                message_id=info.message_id,
                text="Please be present"
            )

        except Exception as e:
            await on_error(context, "completed", e)

    else:
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="No active team listing session is currently in progress.",
            parse_mode="HTML"
        )

    # await info.delete()


async def relist(update: Update, context: ContextTypes.DEFAULT_TYPE, fun=False) -> None:
    # deleting command
    print("relisting")
    if not fun:
        await update.message.delete()

    gid = update.effective_chat.id
    # creating pocketbase instance
    pb_db = Db()

    try:
        kulhun = pb_db.pb.collection('kulhun').get_first_list_item(filter= 'completed = false')

        try:
            message_id = kulhun.message_id

            print(message_id)

            await context.bot.delete_message(
                chat_id=gid,
                message_id=int(message_id)
            )

        except Exception as e:
            await on_error(context, "relisting", e)

        try:

            # recreate team list
            # gid = -1001912301677
            team_list = pb_db.team_list()
            # get descrption from kulhun
            desc = kulhun.description
            team_msg = f"""
{'<u>Team List</u>'.center(50,'~')}
<i>{desc}</i>
---------------------
<u><b>ONTEAM</b></u>
---------------------
{team_list}
"""

            new_list = await context.bot.send_message(
                chat_id=gid,
                text=team_msg,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(kb_i_o)
            )

            # update new message id
            pb_db.pb.collection('kulhun').update(
                pb_db.pb.collection('kulhun').get_list(1, 20, {"filter": 'completed = false'}).items[0].id,
                {"message_id": new_list.message_id})

        except Exception as e:
            await on_error(context, "Relisting error\n", e)
    except Exception as e:
        await context.bot.send_message(
            chat_id=gid,
            text="No active team listing session is currently in progress.",
            parse_mode="HTML"
        )

        await on_error(context, "creating kulhun", e)


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for new_member in update.message.new_chat_members:
        # Send a welcome message to the group
        uid = update.message.new_chat_members[0].id
        print(new_member.id)
        print(uid)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Welcome {new_member.full_name} to the group!"
        )
        # Save new member
        save = Db().insert_new_player(uid, new_member.full_name)
        print(save)


# Function to trigger when a bot is added to a group
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("new Group added")
    allowed_gid = Db().get_gids()
    gid = update.my_chat_member.chat.id
    print(gid)
    print(update.effective_chat.id)
    # Leave the group
    if gid in allowed_gid:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Im at Your service, let me mange Team list"
        )
        await context.bot.send_message(
            chat_id=498123938,
            text=f"Allowed group Added\nGroup id = {gid}"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"SORRY!\nYou are not Subscriber"
        )
        await context.bot.leave_chat(chat_id=gid)
        await context.bot.send_message(
            chat_id=498123938,
            text=f"New group add Alerted\nGroup id = {gid}"
        )


async def restrict_all(update: Update, context:ContextTypes.DEFAULT_TYPE) -> None:
    try:
        permissions = ChatPermissions(
            can_send_messages=False,
            can_pin_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_send_photos=False,
            can_send_videos=False
        )
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            permissions=permissions
        )
    except Exception as e:
        await on_error(context, "restrictor", e)


async def unknown_command(update: Update, context:ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.delete()
    pb_db = Db()
    u_name = pb_db.pb.collection('players').get_first_list_item(filter=f'tid={update.effective_user.id}')
    print(f"name: {u_name.u_name}")
    permissions = ChatPermissions(
        can_send_messages=False,
        can_pin_messages=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
        can_send_photos=False,
        can_send_videos=False
    )

    print(update.effective_chat.id)
    print(update.effective_user.id)

    await on_error(context, "unknown", update)

    await context.bot.restrict_chat_member(
        chat_id=update.effective_chat.id,
        user_id=update.effective_user.id,
        permissions=permissions
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="<i>Please Contact One of Group admin to regain Group permissions</i>",
        parse_mode=ParseMode.HTML
    )

    await asyncio.sleep(3)

    if pb_db.active_seesion():
        print("calling for relist")
        await relist(update, context, True)


async def _is_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is an admin"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    try:
        user = await context.bot.get_chat_member(chat_id, user_id)
        is_admin = user.status in ['creator', 'administrator']

        if not is_admin:
            await update.message.reply_text("Only administrators can use this command.")

        return is_admin
    except Exception:
        await update.message.reply_text("Failed to verify Member status.")
        return False




async def on_error(context, fun, msg) -> None:
    await context.bot.send_message(
        chat_id=498123938,
        text=f"Error while exc {fun}\n{msg}"
    )


def main() -> None:
    """Start the bot."""
    load_dotenv()

    # Create the Application and pass it your bot's token.
    # application = Application.builder().token(os.environ["TOKEN"]).build()
    application = Application.builder().token(os.environ["TOKEN"]).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("alert", alert_command))
    application.add_handler(CommandHandler("team", team_maker))
    application.add_handler(CommandHandler("completed", completed))
    application.add_handler(CommandHandler("relist", relist))
    application.add_handler(CommandHandler("endlist", end_list))

    #Unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    application.add_handler(CallbackQueryHandler(inline_button))
    application.add_handler(ChatMemberHandler(new_member, ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
