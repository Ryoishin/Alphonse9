
"""A module for helping ban group join spammers."""

from asyncio import sleep

from requests import get
from telethon.events import ChatAction
from telethon.tl.types import ChannelParticipantsAdmins, Message

from userbot import (
    ANTI_SPAMBOT,
    ANTI_SPAMBOT_SHOUT,
    BOTLOG,
    BOTLOG_CHATID,
    CMD_HELP,
    bot,
)
from userbot.events import is_chat_allowed


@bot.on(ChatAction)
async def ANTI_SPAMBOTS(welcm):
    """Ban a recently joined user if it matches the spammer checking algorithm."""
    try:
        if not ANTI_SPAMBOT:
            return

        if not is_chat_allowed(welcm):
            return

        if welcm.user_joined or welcm.user_added:
            adder = None
            ignore = False
            users = None

            if welcm.user_added:
                ignore = False
                try:
                    adder = welcm.action_message.sender_id
                except AttributeError:
                    return

            async for admin in bot.iter_participants(
                welcm.chat_id, filter=ChannelParticipantsAdmins
            ):
                if admin.id == adder:
                    ignore = True
                    break

            if ignore:
                return

            if welcm.user_joined:
                users_list = hasattr(welcm.action_message.action, "users")
                if users_list:
                    users = welcm.action_message.action.users
                else:
                    users = [welcm.action_message.sender_id]

            await sleep(5)
            spambot = False

            if not users:
                return

            for user_id in users:
                async for message in bot.iter_messages(
                    welcm.chat_id, from_user=user_id
                ):

                    correct_type = isinstance(message, Message)
                    if not message or not correct_type:
                        break

                    join_time = welcm.action_message.date
                    message_date = message.date

                    if message_date < join_time:
                        continue  # The message was sent before the user joined, thus ignore it

                    check_user = await welcm.client.get_entity(user_id)

                    # DEBUGGING. LEAVING IT HERE FOR SOME TIME ###
                    print(f"User Joined: {check_user.first_name} [ID: {check_user.id}]")
                    print(f"Chat: {welcm.chat.title}")
                    print(f"Time: {join_time}")
                    print(f"Message Sent: {message.text}\n\n[Time: {message_date}]")
                    ##############################################

                    try:
                        # https://t.me/combotnews/283
                        cas_url = f"https://api.cas.chat/check?user_id={check_user.id}"
                        r = get(cas_url, timeout=3)
                        data = r.json()
                    except BaseException:
                        print(
                            "CAS check failed, falling back to legacy anti_spambot behaviour."
                        )
                        data = None

                    if data and data["ok"]:
                        reason = f"[Banned by Combot Anti Spam](https://cas.chat/query?u={check_user.id})"
                        spambot = True
                    elif "t.cn/" in message.text:
                        reason = "Match on `t.cn` URLs"
                        spambot = True
                    elif "t.me/joinchat" in message.text:
                        reason = "Potential Promotion Message"
                        spambot = True
                    elif message.fwd_from:
                        reason = "Forwarded Message"
                        spambot = True
                    elif "?start=" in message.text:
                        reason = "Telegram bot `start` link"
                        spambot = True
                    elif "bit.ly/" in message.text:
                        reason = "Match on `bit.ly` URLs"
                        spambot = True
                    else:
                        if (
                            check_user.first_name
                            in (
                                "Bitmex",
                                "Promotion",
                                "Information",
                                "Dex",
                                "Announcements",
                                "Info",
                            )
                            and users.last_name == "Bot"
                        ):
                            reason = "Known spambot"
                            spambot = True

                    if spambot:
                        print(f"Potential Spam Message: {message.text}")
                        await message.delete()
                        break

                    continue  # Check the next messsage

            if spambot:
                chat = await welcm.get_chat()
                admin = chat.admin_rights
                creator = chat.creator
                if not admin and not creator:
                    if ANTI_SPAMBOT_SHOUT:
                        await welcm.reply(
                            "@admins\n"
                            "**Anti spambot detector!\n"
                            "This user matches my algorithms as a spambot!**"
                            f"Reason: {reason}"
                        )
                        kicked = False
                        reported = True
                else:
                    try:

                        await welcm.reply(
                            "**Potential spambot detected!**\n"
                            f"**Reason:** {reason}\n"
                            "Kicking away for now, will log the ID.\n"
                            f"**User:** [{check_user.first_name}](tg://user?id={check_user.id})"
                        )

                        await welcm.client.kick_participant(
                            welcm.chat_id, check_user.id
                        )
                        kicked = True
                        reported = False

                    except BaseException:
                        if ANTI_SPAMBOT_SHOUT:
                            await welcm.reply(
                                "@admins\n"
                                "**Anti spambot detector!\n"
                                "This user matches my algorithms as a spambot!**"
                                f"Reason: {reason}"
                            )
                            kicked = False
                            reported = True

                if BOTLOG and (kicked or reported):
                    await welcm.client.send_message(
                        BOTLOG_CHATID,
                        "#ANTI_SPAMBOT REPORT\n"
                        f"USER: [{check_user.first_name}](tg://user?id={check_user.id})\n"
                        f"USER ID: `{check_user.id}`\n"
                        f"CHAT: {welcm.chat.title}\n"
                        f"CHAT ID: `{welcm.chat_id}`\n"
                        f"REASON: {reason}\n"
                        f"MESSAGE:\n\n{message.text}",
                    )
    except ValueError:
        pass


CMD_HELP.update(
    {
        "anti_spambot": "If enabled in config.env or env var,"
        "\nthis module will ban(or inform the admins of the group about) the"
        "\nspammer(s) if they match the userbot's anti-spam algorithm."
    }
)