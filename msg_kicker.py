
# -*- coding: utf-8 -*-
# Модуль для Hikka Userbot
# Автор: Ваше Имя

from datetime import datetime, timedelta
from telethon.tl.functions.channels import GetParticipantsRequest, EditBannedRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsSearch
from .. import loader, utils  # Импорты Hikka

@loader.tds
class MsgKickerMod(loader.Module):
    """Модуль для подсчета сообщений и удаления неактивных участников"""

    strings = {"name": "MsgKicker"}

    async def msgcountcmd(self, message):
        """Считает количество сообщений участников в чате.
Использование: .msgcount"""
        chat_id = utils.get_chat_id(message)
        await message.edit("Считаю сообщения участников...")

        participants = await self._client(GetParticipantsRequest(
            channel=chat_id,
            filter=ChannelParticipantsSearch(''),
            offset=0,
            limit=1000,
            hash=0
        ))

        counts = {}
        async for msg in self._client.iter_messages(chat_id):
            if msg.sender_id not in counts:
                counts[msg.sender_id] = 0
            counts[msg.sender_id] += 1

        result = "Количество сообщений участников:\n"
        for user in participants.users:
            result += f"- {user.first_name or user.id}: {counts.get(user.id, 0)} сообщений\n"

        await message.edit(result)

    async def kicatcmd(self, message):
        """Удаляет участников, не писавших в чат указанное количество дней.
Использование: .kicat <дни>"""
        args = utils.get_args(message)
        if not args or not args[0].isdigit():
            await message.edit("Укажите количество дней! Пример: .kicat 7")
            return

        days = int(args[0])
        chat_id = utils.get_chat_id(message)
        await message.edit(f"Ищу участников, не писавших {days} дней...")

        participants = await self._client(GetParticipantsRequest(
            channel=chat_id,
            filter=ChannelParticipantsSearch(''),
            offset=0,
            limit=1000,
            hash=0
        ))

        now = datetime.utcnow()
        threshold = now - timedelta(days=days)
        kicked = 0

        for user in participants.users:
            if user.bot or user.status is None:  # Пропускаем ботов и неизвестный статус
                continue

            last_seen = getattr(user.status, "was_online", None)
            if last_seen and last_seen < threshold:
                try:
                    await self._client(EditBannedRequest(
                        channel=chat_id,
                        participant=user.id,
                        banned_rights=ChatBannedRights(until_date=None, view_messages=True)
                    ))
                    kicked += 1
                except Exception as e:
                    await message.reply(f"Ошибка при исключении {user.id}: {str(e)}")

        await message.edit(f"Удалено {kicked} участников за неактивность {days} дней.")
