import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load .env if present
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()

API_ID = int(os.environ.get('TG_API_ID', '0'))
API_HASH = os.environ.get('TG_API_HASH', '')

from telethon.sync import TelegramClient

if len(sys.argv) < 3:
    print("Usage: python send_reply.py <target_peer> <message>")
    sys.exit(1)

target = sys.argv[1]
if target.isdigit() or (target.startswith('-') and target[1:].isdigit()):
    target = int(target)

message = " ".join(sys.argv[2:])

with TelegramClient('userbot_session', API_ID, API_HASH) as client:
    try:
        peer = client.get_input_entity(target)
        client.send_message(peer, message)
        print(f"SUCCESS: Message delivered to {target}!")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
