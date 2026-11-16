import sys, os, argparse, json, urllib.request, time, socket, ssl
from http.client import RemoteDisconnected

if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load .env
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()

API_ID = int(os.environ.get('TG_API_ID', '0'))
API_HASH = os.environ.get('TG_API_HASH', '')
STORAGE_ID = int(os.environ.get('TG_STORAGE_CHANNEL_ID', '0'))
BOT_TOKEN = os.environ.get('TG_BOT_TOKEN', '')

parser = argparse.ArgumentParser(description="Smart Telegram sender: Bot for groups/topics, Userbot for personal DMs")
parser.add_argument('--to', default=str(STORAGE_ID), help='Target username or group ID')
parser.add_argument('--topic', type=int, default=None, help='Topic ID in forum supergroup')
parser.add_argument('--text', default='', help='Message text or caption')
parser.add_argument('--file', default=None, help='Path to file to send')
parser.add_argument('--as-bot', action='store_true', help='Force send as bot')
parser.add_argument('--as-user', action='store_true', help='Force send as userbot')
parser.add_argument('--pin', action='store_true', help='Pin message after sending')

def _do_bot_request(endpoint, payload, max_retries=4):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/{endpoint}'
    data = json.dumps(payload).encode('utf-8')
    
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            return urllib.request.urlopen(req, timeout=20)
        except urllib.error.HTTPError:
            # Application-level Telegram HTTP errors (like 400 Bad Request) are re-raised to allow fallback logic
            raise
        except (ConnectionResetError, urllib.error.URLError, ssl.SSLError, RemoteDisconnected, socket.timeout, TimeoutError, OSError) as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(1.2 * attempt)
            else:
                break
    raise last_err

def send_via_bot(chat_id, text, topic=None, pin=False):
    cid = chat_id
    if str(cid).isdigit() and not str(cid).startswith('-100'):
        cid = int(f"-100{cid}")
    elif str(cid).lstrip('-').isdigit():
        cid = int(cid)
        
    # Telegram max message length is 4096 chars
    chunks = []
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            chunks.append(text[i:i+4000])
    else:
        chunks = [text]

    for chunk in chunks:
        payload = {'chat_id': cid, 'text': chunk, 'parse_mode': 'Markdown'}
        if topic and topic != 1:
            payload['message_thread_id'] = topic

        try:
            res = _do_bot_request('sendMessage', payload)
            res_data = json.loads(res.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            # If markdown entity parsing failed, fallback to plain text without parse_mode
            if 'parse entities' in err_body.lower() or 'bad request' in err_body.lower():
                payload.pop('parse_mode', None)
                try:
                    res = _do_bot_request('sendMessage', payload)
                    res_data = json.loads(res.read().decode('utf-8'))
                except urllib.error.HTTPError as e2:
                    err_body2 = e2.read().decode('utf-8', errors='ignore')
                    print(f"ERROR: Telegram Bot API failed: {err_body2}", file=sys.stderr)
                    raise
            else:
                print(f"ERROR: Telegram Bot API failed: {err_body}", file=sys.stderr)
                raise

        print(f"SUCCESS: Sent via Bot to {chat_id} (topic: {topic})")
        
        msg_id = res_data.get('result', {}).get('message_id')
        if pin and msg_id:
            try:
                pin_payload = {'chat_id': cid, 'message_id': msg_id}
                _do_bot_request('pinChatMessage', pin_payload)
                print(f"PINNED: Message {msg_id} pinned in {chat_id}")
            except Exception as e:
                print(f"WARNING: Could not pin message: {e}")

def send_file_via_bot(chat_id, file_path, caption='', topic=None):
    import requests
    cid = chat_id
    if str(cid).isdigit() and not str(cid).startswith('-100'):
        cid = int(f"-100{cid}")
    elif str(cid).lstrip('-').isdigit():
        cid = int(cid)
        
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument'
    data = {'chat_id': cid}
    if caption:
        data['caption'] = caption
    if topic and topic != 1:
        data['message_thread_id'] = topic
        
    for attempt in range(1, 4):
        try:
            with open(file_path, 'rb') as f:
                res = requests.post(url, data=data, files={'document': f}, timeout=30)
            if res.ok:
                print(f"SUCCESS: Sent file via Bot to {chat_id} (topic: {topic})")
                return
            else:
                print(f"ERROR: Failed to send file: {res.text}")
                return
        except Exception as e:
            if attempt < 3:
                time.sleep(1.5 * attempt)
            else:
                print(f"ERROR: Failed to send file due to network error: {e}")

def send_via_userbot(target, text, topic=None, pin=False, file_path=None):
    from telethon.sync import TelegramClient
    import shutil
    tgt = target
    if tgt.isdigit() or (tgt.startswith('-') and tgt[1:].isdigit()):
        tgt = int(tgt)
        
    use_temp = False
    temp_file = 'userbot_cli.session'
    try:
        client = TelegramClient('userbot_session', API_ID, API_HASH)
        client.start()
    except Exception as e:
        if 'locked' in str(e).lower() and os.path.exists('userbot_session.session'):
            shutil.copy2('userbot_session.session', temp_file)
            use_temp = True
            client = TelegramClient('userbot_cli', API_ID, API_HASH)
            client.start()
        else:
            raise

    try:
        peer = client.get_input_entity(tgt)
        if file_path:
            msg = client.send_file(peer, file_path, caption=text, reply_to=topic if topic else None)
        else:
            msg = client.send_message(peer, text, reply_to=topic if topic else None)
        print(f"SUCCESS: Sent via Userbot to {target} (topic: {topic})")
        if pin and msg:
            try:
                client.pin_message(peer, msg)
                print(f"PINNED: Message pinned in {target}")
            except Exception as e:
                print(f"WARNING: Could not pin message: {e}")
    finally:
        client.disconnect()
        if use_temp and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass

if __name__ == '__main__':
    args = parser.parse_args()
    is_group_or_storage = (str(args.to) == str(STORAGE_ID) or str(args.to).startswith('-100') or str(args.to) == f"-100{STORAGE_ID}")

    if args.file:
        if args.as_user:
            send_via_userbot(args.to, args.text, args.topic, args.pin, file_path=args.file)
        elif args.as_bot or is_group_or_storage:
            send_file_via_bot(args.to, args.file, args.text, args.topic)
        else:
            send_via_userbot(args.to, args.text, args.topic, args.pin, file_path=args.file)
    else:
        if args.as_user:
            send_via_userbot(args.to, args.text, args.topic, args.pin)
        elif args.as_bot or is_group_or_storage:
            send_via_bot(args.to, args.text, args.topic, args.pin)
        else:
            send_via_userbot(args.to, args.text, args.topic, args.pin)
