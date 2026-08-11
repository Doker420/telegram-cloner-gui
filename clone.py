# channel_cloner_interactive.py
import asyncio
import os
import random
import shutil
from datetime import datetime
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message, Chat, MessageEntity
from pyrogram.enums import ChatType, MessageMediaType, ParseMode
from tqdm import tqdm

# ===================== КОНФИГУРАЦИЯ =====================
API_ID = 1234567           # Получить на my.telegram.org
API_HASH = "ваш_api_хэш"

# Настройки
WORK_DIR = "temp_downloads"  # Папка для временных файлов
BOT_LINK = "https://t.me/your_bot"
HASHTAGS = ["#крипта", "#LTC", "#бонус", "#промокод"]

# Задержки
DELAY_MIN = 2
DELAY_MAX = 8

# ===================== ИНИЦИАЛИЗАЦИЯ =====================
app = Client(
    "session_user",
    api_id=API_ID,
    api_hash=API_HASH,
    workdir=WORK_DIR
)

# Создаём папку для загрузок
Path(WORK_DIR).mkdir(exist_ok=True)

# ===================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====================

def clear_terminal():
    """Очищает терминал"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Красивый заголовок"""
    clear_terminal()
    print("\n" + "="*70)
    print("🔥  TELEGRAM CHANNEL CLONER v3.0  🔥")
    print("="*70)
    print("   ✦ Клонирование частных каналов")
    print("   ✦ Скачивание и перезаливка медиа")
    print("   ✦ Добавление промо-текста")
    print("="*70 + "\n")

async def get_user_channels(client: Client):
    """Получает список всех каналов пользователя"""
    print("📡 Сканирование ваших каналов...\n")
    
    channels = []
    dialogs = client.get_dialogs()
    
    async for dialog in dialogs:
        if dialog.chat.type in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
            # Проверяем права на отправку сообщений
            try:
                chat_info = await client.get_chat(dialog.chat.id)
                channels.append({
                    'id': dialog.chat.id,
                    'title': dialog.chat.title or "Без названия",
                    'username': dialog.chat.username or "приватный",
                    'type': dialog.chat.type,
                    'members': getattr(chat_info, 'members_count', 0),
                    'dialog': dialog
                })
                print(f"   📌 {dialog.chat.title[:40]} (@{dialog.chat.username or 'приватный'})")
            except:
                pass
    
    return channels

async def search_channels(client: Client, query: str):
    """Ищет каналы по названию"""
    all_channels = await get_user_channels(client)
    if not query:
        return all_channels
    
    query_lower = query.lower()
    results = []
    for ch in all_channels:
        if query_lower in ch['title'].lower() or (ch['username'] and query_lower in ch['username'].lower()):
            results.append(ch)
    return results

def display_channels(channels, page=0, per_page=10):
    """Отображает каналы постранично"""
    if not channels:
        print("❌ Каналы не найдены")
        return None
    
    total = len(channels)
    start = page * per_page
    end = min(start + per_page, total)
    
    print(f"\n📋 Найдено каналов: {total}\n")
    print("   #  Название                      Участники  Username")
    print("   " + "-"*70)
    
    for idx in range(start, end):
        ch = channels[idx]
        num = idx + 1
        title = ch['title'][:30].ljust(30)
        members = str(ch['members']).ljust(10)
        username = ch['username']
        print(f"   {num:2}. {title} {members} @{username}")
    
    print("   " + "-"*70)
    
    if total > per_page:
        print(f"\n📄 Страница {page+1}/{((total-1)//per_page)+1}")
        print("   [N] - следующая  [P] - предыдущая  [Q] - выход")
    
    return channels[start:end]

async def select_channel(client: Client):
    """Интерактивный выбор канала с поиском"""
    print_header()
    print("🔍 Выберите канал-источник (откуда клонируем):\n")
    print("   Введите текст для поиска или нажмите Enter для всех")
    query = input("   🔎 Поиск: ").strip()
    
    channels = await search_channels(client, query)
    if not channels:
        print("❌ Каналы не найдены")
        return None
    
    page = 0
    per_page = 10
    
    while True:
        clear_terminal()
        print_header()
        print(f"🔍 Результаты поиска: '{query}'" if query else "📋 Все каналы")
        
        display_channels(channels, page, per_page)
        
        print("\n   Выберите номер канала (1-{}) или".format(len(channels)))
        choice = input("   [N/P - страница, Q - выход]: ").strip()
        
        if choice.lower() == 'q':
            return None
        elif choice.lower() == 'n':
            if (page + 1) * per_page < len(channels):
                page += 1
            continue
        elif choice.lower() == 'p':
            if page > 0:
                page -= 1
            continue
        
        try:
            num = int(choice) - 1
            if 0 <= num < len(channels):
                selected = channels[num]
                print(f"\n✅ Выбран канал: {selected['title']}")
                return selected
            else:
                print("❌ Неверный номер")
                input("Нажмите Enter...")
        except ValueError:
            print("❌ Введите число")
            input("Нажмите Enter...")

async def get_channel_messages(client: Client, channel_id, limit=None):
    """Получает все сообщения из канала с первого по порядку"""
    print(f"\n📥 Загрузка сообщений из канала...")
    
    messages = []
    async for message in client.get_chat_history(channel_id, limit=limit):
        messages.append(message)
    
    # Сортируем от старых к новым
    messages.reverse()
    
    print(f"✅ Загружено {len(messages)} сообщений")
    return messages

async def download_media(message: Message, client: Client):
    """Скачивает медиафайл и возвращает путь"""
    try:
        if message.media:
            # Скачиваем с прогрессом
            file_path = await client.download_media(
                message,
                file_name=f"{WORK_DIR}/{message.id}_",
                progress=print_progress
            )
            return file_path
    except Exception as e:
        print(f"⚠️ Ошибка скачивания: {e}")
    return None

def print_progress(current, total):
    """Прогресс скачивания"""
    if total > 0:
        percent = current * 100 / total
        bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
        print(f"\r   📥 Загрузка: [{bar}] {percent:.1f}%", end="")

async def clone_message(client: Client, source_msg: Message, target_chat_id: str, index: int, total: int):
    """Клонирует сообщение с перезаливкой медиа"""
    try:
        # Формируем текст с промо
        text = source_msg.text or source_msg.caption or ""
        if text:
            promo = f"\n\n🚀 {BOT_LINK}\n" + " ".join(HASHTAGS)
            text = text + promo
        else:
            text = "🚀 " + BOT_LINK + "\n" + " ".join(HASHTAGS)
        
        # Обработка медиа
        media_type = source_msg.media
        
        if media_type == MessageMediaType.PHOTO:
            file_path = await download_media(source_msg, client)
            if file_path:
                await client.send_photo(
                    target_chat_id,
                    file_path,
                    caption=text,
                    parse_mode=ParseMode.HTML
                )
                os.remove(file_path)
            else:
                await client.send_message(target_chat_id, text)
                
        elif media_type == MessageMediaType.VIDEO:
            file_path = await download_media(source_msg, client)
            if file_path:
                await client.send_video(
                    target_chat_id,
                    file_path,
                    caption=text,
                    parse_mode=ParseMode.HTML,
                    supports_streaming=True
                )
                os.remove(file_path)
            else:
                await client.send_message(target_chat_id, text)
                
        elif media_type == MessageMediaType.DOCUMENT:
            file_path = await download_media(source_msg, client)
            if file_path:
                await client.send_document(
                    target_chat_id,
                    file_path,
                    caption=text,
                    parse_mode=ParseMode.HTML
                )
                os.remove(file_path)
            else:
                await client.send_message(target_chat_id, text)
                
        elif media_type == MessageMediaType.VOICE:
            file_path = await download_media(source_msg, client)
            if file_path:
                await client.send_voice(target_chat_id, file_path, caption=text)
                os.remove(file_path)
            else:
                await client.send_message(target_chat_id, text)
                
        elif media_type == MessageMediaType.VIDEO_NOTE:
            file_path = await download_media(source_msg, client)
            if file_path:
                await client.send_video_note(target_chat_id, file_path)
                await client.send_message(target_chat_id, text)
                os.remove(file_path)
            else:
                await client.send_message(target_chat_id, text)
                
        elif media_type == MessageMediaType.STICKER:
            # Стикеры копируем по file_id
            await client.send_sticker(target_chat_id, source_msg.sticker.file_id)
            if text:
                await client.send_message(target_chat_id, text)
                
        elif media_type == MessageMediaType.ANIMATION:
            # GIF
            file_path = await download_media(source_msg, client)
            if file_path:
                await client.send_animation(
                    target_chat_id,
                    file_path,
                    caption=text,
                    parse_mode=ParseMode.HTML
                )
                os.remove(file_path)
            else:
                await client.send_message(target_chat_id, text)
                
        else:
            # Просто текст
            await client.send_message(
                target_chat_id,
                text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        
        # Прогресс
        print(f"✅ [{index}/{total}] Пост склонирован")
        
        # Задержка
        delay = random.uniform(DELAY_MIN, DELAY_MAX)
        await asyncio.sleep(delay)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка клонирования поста {source_msg.id}: {e}")
        return False

async def clear_channel(client: Client, channel_id: str, limit=None):
    """Очищает канал от старых сообщений"""
    print(f"\n🗑️  Очистка канала...")
    
    deleted = 0
    async for message in client.get_chat_history(channel_id, limit=limit):
        try:
            await message.delete()
            deleted += 1
            if deleted % 10 == 0:
                print(f"   Удалено {deleted} сообщений...")
            await asyncio.sleep(0.3)
        except:
            pass
    
    print(f"✅ Удалено {deleted} сообщений")
    return deleted

# ===================== ОСНОВНАЯ ФУНКЦИЯ =====================

async def main():
    """Главная функция с интерактивным выбором"""
    async with app:
        print_header()
        print("🔑 Подключение к аккаунту...")
        
        # Проверяем сессию
        try:
            me = await app.get_me()
            print(f"✅ Подключено: @{me.username} ({me.first_name})\n")
        except:
            print("❌ Ошибка авторизации!")
            return
        
        # 1. Выбираем канал-источник
        print("="*70)
        print("📌 ШАГ 1: ВЫБОР КАНАЛА-ИСТОЧНИКА")
        print("   (откуда будем брать посты)")
        print("="*70)
        
        source_channel = await select_channel(app)
        if not source_channel:
            print("❌ Операция отменена")
            return
        
        # 2. Выбираем канал-цель (куда клонируем)
        print("\n" + "="*70)
        print("📌 ШАГ 2: ВЫБОР КАНАЛА-ЦЕЛИ")
        print("   (куда будем клонировать посты)")
        print("="*70)
        
        target_channel = await select_channel(app)
        if not target_channel:
            print("❌ Операция отменена")
            return
        
        # 3. Подтверждение
        print("\n" + "="*70)
        print("📌 ШАГ 3: ПОДТВЕРЖДЕНИЕ")
        print("="*70)
        
        print(f"\n📡 ИСТОЧНИК: {source_channel['title']}")
        print(f"🎯 ЦЕЛЬ: {target_channel['title']}")
        print(f"\n🏷️  Хэштеги: {' '.join(HASHTAGS)}")
        print(f"🔗 Ссылка на бота: {BOT_LINK}")
        print(f"\n⚠️  ВНИМАНИЕ: Все сообщения в канале-цели будут УДАЛЕНЫ!")
        
        confirm = input("\nПродолжить? (yes/NO): ")
        if confirm.lower() != "yes":
            print("❌ Отменено")
            return
        
        # 4. Загружаем сообщения из источника
        print("\n" + "="*70)
        print("📌 ШАГ 4: ЗАГРУЗКА СООБЩЕНИЙ")
        print("="*70)
        
        source_messages = await get_channel_messages(app, source_channel['id'])
        if not source_messages:
            print("❌ Нет сообщений в канале-источнике!")
            return
        
        # 5. Очищаем целевой канал
        print("\n" + "="*70)
        print("📌 ШАГ 5: ОЧИСТКА КАНАЛА-ЦЕЛИ")
        print("="*70)
        
        await clear_channel(app, target_channel['id'])
        
        # 6. Клонируем сообщения
        print("\n" + "="*70)
        print("📌 ШАГ 6: КЛОНИРОВАНИЕ СООБЩЕНИЙ")
        print("="*70)
        
        total = len(source_messages)
        successful = 0
        
        for i, msg in enumerate(tqdm(source_messages, desc="Клонирование"), 1):
            success = await clone_message(app, msg, target_channel['id'], i, total)
            if success:
                successful += 1
        
        # 7. Итог
        print("\n" + "="*70)
        print("📊 РЕЗУЛЬТАТ")
        print("="*70)
        print(f"\n✅ Успешно склонировано: {successful}/{total} сообщений")
        print(f"🎯 Канал: {target_channel['title']}")
        print(f"🏷️  Добавлены хэштеги: {' '.join(HASHTAGS)}")
        print(f"🔗 Ссылка на бота: {BOT_LINK}")
        print("\n✅ Готово!")

# ===================== ЗАПУСК =====================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    finally:
        # Очистка временных файлов
        if os.path.exists(WORK_DIR):
            shutil.rmtree(WORK_DIR)
        print("\n👋 До свидания!")