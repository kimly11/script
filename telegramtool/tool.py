import asyncio
import os
from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError
import re

api_id = 33238695
api_hash = "1a0c36b4f211274c65a9733df5df65a7"

client = TelegramClient("invite_session", api_id, api_hash)

SOURCE_GROUP = "https://t.me/sourcegroup"
TARGET_GROUP = "https://t.me/+Q1hgZoM529Y5MjVl"

DELAY = 40
INVITED_FILE = "invited.txt"

def load_invited():
    if not os.path.exists(INVITED_FILE):
        return set()
    with open(INVITED_FILE, "r") as f:
        return set(f.read().splitlines())

def save_invited(user_id):
    with open(INVITED_FILE, "a") as f:
        f.write(str(user_id) + "\n")

async def get_entity(client, link):
    link = link.strip()
    private_match = re.search(r'(?:t\.me/|telegram\.me/)(?:\+|joinchat/)([\w-]+)', link)
    if private_match:
        hash = private_match.group(1)
        try:
            await client(ImportChatInviteRequest(hash))
            print(f"✅ Joined group via invite link: {hash}")
        except Exception as e:
            if "USER_ALREADY_PARTICIPANT" not in str(e):
                try:
                    print(f"❌ Error join link {hash}: {e}")
                except UnicodeEncodeError:
                    print(f"Error join link {hash}: {str(e).encode('ascii', 'replace').decode('ascii')}")
    return await client.get_entity(link)

async def main():
    await client.start()
    print("✅ Logged in")

    source = await get_entity(client, SOURCE_GROUP)
    target = await get_entity(client, TARGET_GROUP)

    invited = load_invited()
    print(f"📂 Already invited: {len(invited)} users")

    users = await client.get_participants(source)
    print(f"👥 Found {len(users)} users")

    for user in users:
        if str(user.id) in invited:
            print(f"⏭ Skipped (already invited): {user.id}")
            continue

        try:
            await client(InviteToChannelRequest(
                channel=target,
                users=[user]
            ))
            print(f"✅ Invited: {user.id}")
            save_invited(user.id)
            await asyncio.sleep(DELAY)

        except UserPrivacyRestrictedError:
            print("❌ Privacy restricted")
            await asyncio.sleep(10)

        except FloodWaitError as e:
            print(f"⏳ Flood wait {e.seconds}s")
            await asyncio.sleep(e.seconds)

        except Exception as e:
            print("❌ Error:", e)
            await asyncio.sleep(20)

asyncio.run(main())
