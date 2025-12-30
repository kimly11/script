import asyncio
import os
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError, SessionPasswordNeededError, InviteHashInvalidError, InviteHashExpiredError
from telethon.tl.types import User, Channel, Chat
import re

class TelegramService:
    def __init__(self, api_id, api_hash, session_name="invite_session"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.is_running = False
        self.logs = []
        self.stats = {"successful": 0, "skipped": 0, "errors": 0}
        self.invited_file = "invited.txt"
        self.invited_cache = self._load_invited()

    def _load_invited(self):
        if not os.path.exists(self.invited_file):
            return set()
        with open(self.invited_file, "r") as f:
            return set(f.read().splitlines())

    def _save_invited(self, user_id):
        self.invited_cache.add(str(user_id))
        with open(self.invited_file, "a", encoding="utf-8") as f:
            f.write(str(user_id) + "\n")

    def _log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        if len(self.logs) > 100:
            self.logs.pop(0)
        try:
            print(log_entry)
        except UnicodeEncodeError:
            # Fallback for Windows console that doesn't support emojis
            print(log_entry.encode('ascii', 'replace').decode('ascii'))

    async def connect(self):
        if not self.client.is_connected():
            await self.client.connect()

    async def is_authorized(self):
        return await self.client.is_user_authorized()

    async def send_code(self, phone):
        return await self.client.send_code_request(phone)

    async def sign_in(self, phone, code, hash, password=None):
        try:
            if password:
                await self.client.sign_in(password=password)
            else:
                await self.client.sign_in(phone, code, phone_code_hash=hash)
            return True
        except SessionPasswordNeededError:
            return "2FA_REQUIRED"
        except Exception as e:
            self._log(f"Sign in error: {e}")
            return False

    async def stop(self):
        self.is_running = False
        self._log("Stopping invitation process...")

    async def _get_entity(self, link):
        """Resolves a link (public or private) to a Telegram entity."""
        link = link.strip()
        
        # Check if it's a private invite link (e.g., t.me/+... or t.me/joinchat/...)
        private_match = re.search(r'(?:t\.me/|telegram\.me/)(?:\+|joinchat/)([\w-]+)', link)
        if private_match:
            hash = private_match.group(1)
            try:
                # Try to import/join the invite
                await self.client(ImportChatInviteRequest(hash))
                self._log(f"Successfully joined group via invite link: {hash}")
            except Exception as e:
                err_str = str(e)
                if "USER_ALREADY_PARTICIPANT" in err_str:
                    self._log(f"Already a participant of the group: {hash}")
                    # Try to get entity anyway to return it
                else:
                    self._log(f"Error joining/checking invite link {hash}: {err_str}")
            
            # After joining or if already participant, try to resolve the entity
            try:
                check = await self.client(CheckChatInviteRequest(hash))
                if hasattr(check, 'chat'):
                    return check.chat
            except:
                pass
            
            # After joining or if already participant, we might still need to find the entity
            # This is tricky for private groups, usually the above works or we browse dialogs
            async for dialog in self.client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    # This is inefficient but sometimes necessary to find the right entity
                    # for private groups we just joined.
                    pass
            
            # Fallback to get_entity which might work if already joined
            return await self.client.get_entity(link)

        # For public links or usernames
        return await self.client.get_entity(link)

    async def start_inviting(self, source_group, target_group, delay=40):
        if self.is_running:
            return
        
        self.is_running = True
        self._log(f"Starting invitation: {source_group} -> {target_group}")
        
        try:
            source = await self._get_entity(source_group)
            target = await self._get_entity(target_group)
            
            users = await self.client.get_participants(source)
            self._log(f"Found {len(users)} users in source group")

            for user in users:
                if not self.is_running:
                    break
                
                if str(user.id) in self.invited_cache:
                    self.stats["skipped"] += 1
                    continue

                try:
                    await self.client(InviteToChannelRequest(
                        channel=target,
                        users=[user]
                    ))
                    self._log(f"✅ Invited: {user.id}")
                    self._save_invited(user.id)
                    self.stats["successful"] += 1
                    await asyncio.sleep(delay)

                except UserPrivacyRestrictedError:
                    self._log(f"❌ Privacy restricted for user {user.id}")
                    self.stats["errors"] += 1
                    await asyncio.sleep(5)

                except FloodWaitError as e:
                    self._log(f"⏳ Flood wait: {e.seconds} seconds")
                    await asyncio.sleep(e.seconds)

                except Exception as e:
                    self._log(f"❌ Error inviting {user.id}: {e}")
                    self.stats["errors"] += 1
                    await asyncio.sleep(10)

        except Exception as e:
            self._log(f"Fatal error in invitation loop: {e}")
        finally:
            self.is_running = False
            self._log("Invitation process finished.")
