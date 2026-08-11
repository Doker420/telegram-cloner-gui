import asyncio
import os
import random
import shutil
from pathlib import Path
from pyrogram import Client
from pyrogram.errors import (
    SessionPasswordNeeded,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    FloodWait,
    ApiIdInvalid,
)
from pyrogram.enums import ChatType, MessageMediaType, ParseMode


class ClonerEngine:
    def __init__(self, api_id, api_hash, sessions_dir, workdir="temp_downloads"):
        self.api_id = int(api_id) if api_id else 0
        self.api_hash = str(api_hash) if api_hash else ""
        self.sessions_dir = Path(sessions_dir)
        self.workdir = Path(workdir)
        self.workdir.mkdir(exist_ok=True)
        self._clients = {}
        self._cancel = {}

    async def _get_client(self, session_name, proxy=None):
        if session_name in self._clients:
            return self._clients[session_name]
        client = Client(
            str(self.sessions_dir / session_name),
            api_id=self.api_id,
            api_hash=self.api_hash,
            workdir=str(self.sessions_dir),
            proxy=proxy,
        )
        self._clients[session_name] = client
        return client

    async def ensure_connected(self, session_name, proxy=None):
        client = await self._get_client(session_name, proxy)
        if not getattr(client, "is_connected", False):
            await client.connect()
        try:
            await client.get_me()
            return {"ok": True}
        except SessionPasswordNeeded:
            return {"ok": True, "need_password": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def send_code(self, session_name, phone_number, proxy=None):
        client = await self._get_client(session_name, proxy)
        await client.connect()
        sent = await client.send_code(phone_number)
        return {"phone_code_hash": sent.phone_code_hash}

    async def sign_in(self, session_name, phone_number, code, phone_code_hash, proxy=None):
        client = await self._get_client(session_name, proxy)
        try:
            await client.sign_in(phone_number, phone_code_hash, code)
            me = await client.get_me()
            return {
                "ok": True,
                "user": {
                    "id": me.id,
                    "first_name": me.first_name,
                    "username": getattr(me, "username", None) or "",
                },
            }
        except SessionPasswordNeeded:
            return {"ok": False, "need_password": True}
        except (PhoneCodeInvalid, PhoneCodeExpired) as e:
            return {"ok": False, "error": f"Неверный код: {e}"}
        except FloodWait as e:
            return {"ok": False, "error": f"Flood wait {e.value}s"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def check_password(self, session_name, password, proxy=None):
        client = await self._get_client(session_name, proxy)
        try:
            await client.check_password(password)
            me = await client.get_me()
            return {
                "ok": True,
                "user": {
                    "id": me.id,
                    "first_name": me.first_name,
                    "username": getattr(me, "username", None) or "",
                },
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def get_dialogs(self, session_name, proxy=None):
        client = await self._get_client(session_name, proxy)
        if not getattr(client, "is_connected", False):
            await client.connect()
        result = []
        try:
            async for dialog in client.get_dialogs():
                if dialog.chat.type in (ChatType.CHANNEL, ChatType.SUPERGROUP):
                    chat_info = await client.get_chat(dialog.chat.id)
                    result.append(
                        {
                            "id": dialog.chat.id,
                            "title": dialog.chat.title or "Без названия",
                            "username": dialog.chat.username or "",
                            "type": str(dialog.chat.type),
                            "members": getattr(chat_info, "members_count", 0),
                        }
                    )
        except Exception:
            pass
        return result

    async def start_clone(self, session_name, source_id, target_ids, options, event_cb=None):
        client = await self._get_client(session_name, options.get("proxy"))
        if not getattr(client, "is_connected", False):
            await client.connect()

        cancel = asyncio.Event()
        self._cancel[session_name] = cancel

        limit = options.get("limit", 0) or None
        source_messages = []
        async for msg in client.get_chat_history(source_id, limit=limit):
            source_messages.append(msg)
        source_messages.reverse()
        total = len(source_messages)

        if total == 0:
            self._cancel.pop(session_name, None)
            return {"ok": True, "total": 0, "success": 0, "failed": 0, "cancelled": False}

        clear_target = options.get("clear_target", True)
        add_promo = options.get("add_promo", True)
        bot_link = options.get("bot_link", "")
        hashtags = options.get("hashtags", [])
        delay_min = float(options.get("delay_min", 2))
        delay_max = float(options.get("delay_max", 8))

        success = 0
        failed = 0

        for target_id in target_ids:
            if cancel.is_set():
                break

            if clear_target:
                if event_cb:
                    event_cb("log", f"Очистка цели {target_id}...")
                async for msg in client.get_chat_history(target_id, limit=None):
                    if cancel.is_set():
                        break
                    try:
                        await msg.delete()
                    except Exception:
                        pass

            for i, msg in enumerate(source_messages, 1):
                if cancel.is_set():
                    break
                try:
                    text = msg.text or msg.caption or ""
                    if text and add_promo:
                        text = text + f"\n\n🚀 {bot_link}\n" + " ".join(hashtags)
                    elif not text and add_promo:
                        text = f"🚀 {bot_link}\n" + " ".join(hashtags)

                    media_type = msg.media
                    sent = False

                    if media_type == MessageMediaType.PHOTO:
                        path = await client.download_media(
                            msg, file_name=str(self.workdir / f"{msg.id}_")
                        )
                        if path:
                            await client.send_photo(
                                target_id,
                                path,
                                caption=text,
                                parse_mode=ParseMode.HTML,
                            )
                            os.remove(path)
                            sent = True
                    elif media_type == MessageMediaType.VIDEO:
                        path = await client.download_media(
                            msg, file_name=str(self.workdir / f"{msg.id}_")
                        )
                        if path:
                            await client.send_video(
                                target_id,
                                path,
                                caption=text,
                                parse_mode=ParseMode.HTML,
                                supports_streaming=True,
                            )
                            os.remove(path)
                            sent = True
                    elif media_type == MessageMediaType.DOCUMENT:
                        path = await client.download_media(
                            msg, file_name=str(self.workdir / f"{msg.id}_")
                        )
                        if path:
                            await client.send_document(
                                target_id,
                                path,
                                caption=text,
                                parse_mode=ParseMode.HTML,
                            )
                            os.remove(path)
                            sent = True
                    elif media_type == MessageMediaType.VOICE:
                        path = await client.download_media(
                            msg, file_name=str(self.workdir / f"{msg.id}_")
                        )
                        if path:
                            await client.send_voice(target_id, path, caption=text)
                            os.remove(path)
                            sent = True
                    elif media_type == MessageMediaType.VIDEO_NOTE:
                        path = await client.download_media(
                            msg, file_name=str(self.workdir / f"{msg.id}_")
                        )
                        if path:
                            await client.send_video_note(target_id, path)
                            if text:
                                await client.send_message(target_id, text)
                            os.remove(path)
                            sent = True
                    elif media_type == MessageMediaType.STICKER:
                        await client.send_sticker(target_id, msg.sticker.file_id)
                        if text:
                            await client.send_message(target_id, text)
                        sent = True
                    elif media_type == MessageMediaType.ANIMATION:
                        path = await client.download_media(
                            msg, file_name=str(self.workdir / f"{msg.id}_")
                        )
                        if path:
                            await client.send_animation(
                                target_id,
                                path,
                                caption=text,
                                parse_mode=ParseMode.HTML,
                            )
                            os.remove(path)
                            sent = True
                    else:
                        await client.send_message(
                            target_id,
                            text,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True,
                        )
                        sent = True

                    if sent:
                        success += 1
                    else:
                        failed += 1

                    if event_cb:
                        event_cb(
                            "progress",
                            {
                                "index": i,
                                "total": total,
                                "target": target_id,
                                "success": success,
                                "failed": failed,
                            },
                        )

                    delay = random.uniform(delay_min, delay_max)
                    try:
                        await asyncio.wait_for(cancel.wait(), timeout=delay)
                    except asyncio.TimeoutError:
                        pass
                except Exception as e:
                    failed += 1
                    if event_cb:
                        event_cb("error", str(e))

        self._cancel.pop(session_name, None)
        return {
            "ok": True,
            "total": total,
            "success": success,
            "failed": failed,
            "cancelled": cancel.is_set(),
        }

    def cancel(self, session_name):
        ev = self._cancel.get(session_name)
        if ev:
            ev.set()

    async def close(self, session_name):
        client = self._clients.pop(session_name, None)
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
        self._cancel.pop(session_name, None)

    async def close_all(self):
        for name in list(self._clients.keys()):
            await self.close(name)
