import os, sys, asyncio, json, subprocess
from datetime import datetime, timezone, timedelta

if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

os.chdir(r'D:\Dev\Bots\Telegram\NovaAssistant')

# Read .env if present
if os.path.exists('.env'):
    try:
        with open('.env', 'r', encoding='utf-8') as f_env:
            for line in f_env:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()
    except Exception:
        pass

from telethon import TelegramClient, events, functions, types
from google import genai

API_ID = int(os.environ.get('TG_API_ID', '0'))
API_HASH = os.environ.get('TG_API_HASH', '')
CHANNEL_ID = int(os.environ.get('TG_STORAGE_CHANNEL_ID', '0'))
DIGEST_TOPIC_ID = int(os.environ.get('TG_DIGEST_TOPIC_ID', '37'))
LOG_FILE = r'D:\Dev\Bots\Telegram\NovaAssistant\live_events.log'
STATE_FILE = r'D:\Dev\Bots\Telegram\NovaAssistant\last_digest_date.txt'

client = TelegramClient('userbot_session', API_ID, API_HASH)

def log_event(text):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {text}\n"
    if sys.stdout is not None:
        try:
            print(line, end='', flush=True)
        except Exception:
            pass
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass

def is_antigravity_open():
    try:
        res = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Antigravity.exe", "/NH"], capture_output=True, text=True, timeout=3)
        return "Antigravity.exe" in res.stdout
    except Exception:
        return False

def show_toast(title, message):
    try:
        clean_title = title.replace('"', '`"')
        clean_msg = message.replace('"', '`"').replace('\n', ' ')
        ps_cmd = (
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
            "$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
            "$textNodes = $template.GetElementsByTagName('text'); "
            f"$textNodes.Item(0).AppendChild($template.CreateTextNode(\"{clean_title}\")) | Out-Null; "
            f"$textNodes.Item(1).AppendChild($template.CreateTextNode(\"{clean_msg}\")) | Out-Null; "
            "$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
            "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Telegram Assistant').Show($toast);"
        )
        subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd])
    except Exception as e:
        log_event(f"Error showing toast: {e}")

# 1. LIVE DM LISTENER
@client.on(events.NewMessage(incoming=True))
async def handle_incoming(event):
    if event.is_private:
        sender = await event.get_sender()
        if not getattr(sender, 'bot', False):
            user = getattr(sender, 'username', '') or ''
            name = f"{getattr(sender, 'first_name', '') or ''} {getattr(sender, 'last_name', '') or ''}".strip()
            text_preview = event.raw_text or ''
            log_event(f"[TG_INCOMING_DM] SENDER_ID:{sender.id} | USER:@{user} | NAME:{name} | TEXT:{text_preview}")
            
            # Show toast only if Antigravity is currently open
            if is_antigravity_open():
                toast_title = f"🔔 Telegram: {name or user or 'Новое сообщение'}"
                toast_body = text_preview[:120] if text_preview else "[Медиа / файл]"
                show_toast(toast_title, toast_body)

# 2. AI-POWERED DIGEST WITH GEMINI FLASH
def generate_ai_digest(today_str, dev_items, game_items):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None
    try:
        ai_client = genai.Client(api_key=api_key)
        
        dev_text = ""
        for i, item in enumerate(dev_items[:30], 1):
            dev_text += f"[{i}] Канал: {item['channel']} | Ссылка: {item['link']}\nТекст: {item['text'][:400]}\n\n"
            
        game_text = ""
        for i, item in enumerate(game_items[:20], 1):
            game_text += f"[{i}] Канал: {item['channel']} | Ссылка: {item['link']}\nТекст: {item['text'][:400]}\n\n"

        prompt = f"""Ты — персональный ИИ-ассистент Грави. Ниже собраны посты из Telegram-каналов за последние 24 часа.
Твоя задача — составить сочный, интересный и полезный вечерний дайджест за {today_str} для программиста и геймера Вани.

Требования к оформлению:
1. Заголовок: 📰 **ЕЖЕДНЕВНАЯ ВЫЖИМКА ЗА {today_str}**
2. Раздел: 💻 **РАЗРАБОТКА И НЕЙРОСЕТИ (Dev & AI)**
   - Выбери топ-3..5 самых важных новостей (новые модели ИИ, релизы фреймворков, крутые фичи, полезные тулзы).
   - Для каждого пункта укажи:
     • **Название темы / новости** (жирным)
       Суть новости в 1-2 ёмких предложениях.
       🔗 [Ссылка на пост](URL_ИЗ_ПОСТА)
3. Раздел: 🎮 **ИГРЫ И ГЕЙМДЕВ**
   - Выбери топ-2..4 ключевых события (анонсы, даты релизов, крупные трейлеры или события).
   - Формат аналогичный (краткая суть + ссылка на пост).
4. Завершение:
   ════════════════════════════════════════
   💡 *Все каналы отмечены как прочитанные. Следующий дайджест завтра вечером!*

ВАЖНО:
- Отсекай рекламу, казино, крипту, спам и мелкие мемы.
- Ссылки на посты бери ТОЧНО из исходного текста (не выдумывай несуществующие ссылки).
- Пиши живо, по делу, без канцелярита.

Исходные посты Dev & AI:
{dev_text if dev_text else "Сегодня новых постов нет."}

Исходные посты Игры:
{game_text if game_text else "Сегодня новых постов нет."}
"""
        response = ai_client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
        )
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        log_event(f"Gemini API generation error: {e}")
    return None

async def run_daily_digest():
    log_event("Starting automatic daily digest generation...")
    try:
        filters = await client(functions.messages.GetDialogFiltersRequest())
        f11 = next((f for f in filters.filters if getattr(f, 'id', None) == 11), None) # Dev & AI
        f12 = next((f for f in filters.filters if getattr(f, 'id', None) == 12), None) # Игры
        
        dev_peers = list(f11.include_peers) if f11 else []
        game_peers = list(f12.include_peers) if f12 else []
        
        since_date = datetime.now(timezone.utc) - timedelta(hours=24)
        
        dev_items = []
        game_items = []
        
        async def harvest(peers, target_list):
            for p in peers:
                try:
                    ent = await client.get_entity(p)
                    title = getattr(ent, 'title', None) or 'Без названия'
                    username = getattr(ent, 'username', None)
                    msgs = await client.get_messages(ent, limit=10)
                    for m in msgs:
                        if m.date and m.date > since_date and m.text and len(m.text.strip()) > 35:
                            t = m.text.strip()
                            if any(bad in t.lower() for bad in ['скидка', 'промокод', 'казино', 'crypto', 'реклама', 'партнерский']):
                                continue
                            link = f"https://t.me/{username}/{m.id}" if username else f"https://t.me/c/{ent.id}/{m.id}"
                            target_list.append({
                                'channel': title,
                                'text': t,
                                'link': link
                            })
                    # Mark channel read
                    try:
                        await client(functions.channels.ReadHistoryRequest(channel=ent, max_id=0))
                    except Exception:
                        pass
                except Exception:
                    pass

        await harvest(dev_peers, dev_items)
        await harvest(game_peers, game_items)
        
        today_str = datetime.now().strftime('%d.%m.%Y')
        
        # 1. Try AI-generated digest
        text = generate_ai_digest(today_str, dev_items, game_items)
        
        # 2. Fallback if AI not available
        if not text:
            text = f"📰 **ЕЖЕДНЕВНАЯ ВЫЖИМКА ЗА {today_str}**\n════════════════════════════════════════\n\n"
            text += "💻 **РАЗРАБОТКА И НЕЙРОСЕТИ (Dev & AI):**\n\n"
            if dev_items:
                seen_snippets = set()
                count = 0
                for item in dev_items:
                    snippet = item['text'][:120]
                    if snippet not in seen_snippets:
                        seen_snippets.add(snippet)
                        count += 1
                        preview = item['text'][:250].replace('\n', ' ')
                        text += f"• **{item['channel']}**\n  {preview}...\n  🔗 [Ссылка на пост]({item['link']})\n\n"
                        if count >= 4:
                            break
            else:
                text += "• Сегодня без крупных обновлений.\n\n"
                
            text += "────────────────────────────────────────\n"
            text += "🎮 **ИГРЫ И ГЕЙМДЕВ:**\n\n"
            if game_items:
                seen_snippets = set()
                count = 0
                for item in game_items:
                    snippet = item['text'][:120]
                    if snippet not in seen_snippets:
                        seen_snippets.add(snippet)
                        count += 1
                        preview = item['text'][:250].replace('\n', ' ')
                        text += f"• **{item['channel']}**\n  {preview}...\n  🔗 [Ссылка на пост]({item['link']})\n\n"
                        if count >= 3:
                            break
            else:
                text += "• В игровых каналах сегодня тихо.\n\n"
                
            text += "════════════════════════════════════════\n"
            text += "💡 *Все каналы отмечены как прочитанные. Следующий дайджест завтра!*"
        
        # Post to Telegram topic 37
        channel_ent = await client.get_entity(CHANNEL_ID)
        await client.send_message(channel_ent, text, reply_to=DIGEST_TOPIC_ID)
        
        # Save state
        today_key = datetime.now().strftime('%Y-%m-%d')
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            f.write(today_key)
            
        log_event(f"Daily digest successfully posted and channels marked as read for {today_key}!")
    except Exception as e:
        log_event(f"Error in run_daily_digest: {e}")

# 3. BACKGROUND SCHEDULER LOOP
async def scheduler_loop():
    while True:
        try:
            now_local = datetime.now()
            today_key = now_local.strftime('%Y-%m-%d')
            
            last_date = ""
            if os.path.exists(STATE_FILE):
                try:
                    with open(STATE_FILE, 'r', encoding='utf-8') as f:
                        last_date = f.read().strip()
                except Exception:
                    pass
                    
            # Trigger between 21:30 and 23:59 if not run today
            if now_local.hour >= 21 and last_date != today_key:
                await run_daily_digest()
        except Exception as e:
            log_event(f"Error in scheduler_loop: {e}")
            
        await asyncio.sleep(300)

async def main():
    log_event("NovaAssistant Service started. Live listener & Scheduler active.")
    asyncio.create_task(scheduler_loop())
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        with client:
            client.loop.run_until_complete(main())
    except Exception as e:
        import traceback
        with open(r'D:\Dev\Bots\Telegram\NovaAssistant\crash.log', 'w', encoding='utf-8') as f_crash:
            traceback.print_exc(file=f_crash)
