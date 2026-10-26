import sys, os, argparse, json, urllib.request

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
parser.add_argument('--text', required=True, help='Message text')
parser.add_argument('--as-bot', action='store_true', help='Force send as bot')
parser.add_argument('--as-user', action='store_true', help='Force send as userbot')

args = parser.parse_args()

def send_via_bot(chat_id, text, topic=None):
    cid = chat_id
    if str(cid).isdigit() and not str(cid).startswith('-100'):
        cid = int(f"-100{cid}")
    elif str(cid).lstrip('-').isdigit():
        cid = int(cid)
        
    payload = {'chat_id': cid, 'text': text, 'parse_mode': 'Markdown'}
    if topic and topic != 1:
        payload['message_thread_id'] = topic
        
    req = urllib.request.Request(
        f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    urllib.request.urlopen(req)
    print(f"SUCCESS: Sent via Bot to {chat_id} (topic: {topic})")

def send_via_userbot(target, text, topic=None):
    from telethon.sync import TelegramClient
    tgt = target
    if tgt.isdigit() or (tgt.startswith('-') and tgt[1:].isdigit()):
        tgt = int(tgt)
        
    with TelegramClient('userbot_session', API_ID, API_HASH) as client:
        peer = client.get_input_entity(tgt)
        if topic:
            client.send_message(peer, text, reply_to=topic)
        else:
            client.send_message(peer, text)
        print(f"SUCCESS: Sent via Userbot to {target} (topic: {topic})")

is_group_or_storage = (str(args.to) == str(STORAGE_ID) or str(args.to).startswith('-100') or str(args.to) == f"-100{STORAGE_ID}")

if args.as_user:
    send_via_userbot(args.to, args.text, args.topic)
elif args.as_bot or is_group_or_storage:
    send_via_bot(args.to, args.text, args.topic)
else:
    send_via_userbot(args.to, args.text, args.topic)
