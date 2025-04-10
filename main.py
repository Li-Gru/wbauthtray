import objc
import os
import re
import yaml
import asyncio
import time
import httpx
import pyperclip
import rumps
import platform
import threading
from pathlib import Path
from pprint import pprint as print
from desktop_notifier import DEFAULT_SOUND, DesktopNotifier, Urgency

if platform.system() == "Darwin":
    from rubicon.objc.eventloop import EventLoopPolicy
    asyncio.set_event_loop_policy(EventLoopPolicy())

AUTH_POLL_URL = "https://wbx-bell-v3.wildberries.ru/shard-proxy/api/v3/notice/get"
TOKEN_REGEX = r'[0-9]{5,6}'


class WBAuthTrayApp(rumps.App):
    def __init__(self):
        super().__init__("WB", icon=None)
        self.config = self.load_config()
        self.notifier = DesktopNotifier(app_name="WB Auth")
        self.loop = None
        self.tasks = []

    def run(self):
        threading.Thread(target=self.start_event_loop, daemon=False).start()
        super().run()

    def start_event_loop(self, sender=None):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.monitor(sender))
        finally:
            for task in self.tasks:
                task.cancel()
            self.tasks.clear()

    def load_config(self):
        config_paths = []
        home = str(Path.home())
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
        if not xdg_config_home:
            xdg_config_home = os.path.join(home, '.config')
        filenames = ['wbauth.yaml', 'wbauth.yml']
        dirs = [xdg_config_home, os.path.join(xdg_config_home, 'wbauth'), home]
        config_paths = [
            os.path.join(xdg_config_home, 'wbauth', 'config.yaml'),
            os.path.join(xdg_config_home, 'wbauth', 'config.yml'),
            os.path.join(home, '.wbauth.yaml'),
            os.path.join(home, '.wbauth.yml')]
        config_paths.extend([os.path.join(d, f) for d in dirs for f in filenames])

        for path in config_paths:
            if os.path.isfile(path):
                try:
                    with open(path, 'r') as file:
                        return yaml.safe_load(file)
                except yaml.YAMLError as e:
                    print(f"[YAML ERROR] {e}")
        return None

    @rumps.clicked("Auth - Wait messaage")
    def auth_wait_handler(self, sender):
        if not self.loop:
            asyncio.run_coroutine_threadsafe(self.notify('ERROR', "Event loop not started yet."), self.loop)
            return
        if not self.config or 'wbauth' not in self.config:
            asyncio.run_coroutine_threadsafe(self.notify('ERROR', "No valid config found"), self.loop)
            return
        sender.state = not sender.state
        if sender.state:
            pyperclip.copy(self.config['wbauth'].get('phone', ''))
            self.tasks.append(self.loop.create_task(self.poll_for_token(sender)))

    @rumps.clicked("Auth - Last message")
    def auth_last_handler(self, _):
        if not self.config or 'wbauth' not in self.config:
            asyncio.run_coroutine_threadsafe(self.notify('ERROR', "No valid config found"), self.loop)
            return
        try:
            with httpx.Client(timeout=httpx.Timeout(3.0)) as client:
                token = self.config['wbauth']['token']
                headers = {'Authorization': f'Bearer {token}'}
                response = client.post(AUTH_POLL_URL, headers=headers)
                response.raise_for_status()
                data = response.json()
                if 'error' in data:
                    asyncio.run_coroutine_threadsafe(self.notify('ERROR', data['error']), self.loop)
                elif 'payload' in data:
                    payload = sorted(data['payload'], key=lambda d: d['dt'])
                    while payload:
                        item = payload.pop()
                        if re.search(TOKEN_REGEX, item['text']):
                            asyncio.run_coroutine_threadsafe(self.notify(item['title'], item['text']), self.loop)
                            break
        except httpx.HTTPError as e:
            print(f"[HTTP ERROR] {e}")
        except Exception as e:
            print(f"[ERROR] {e}")

    async def monitor(self, sender=None):
        while True:
            await asyncio.sleep(0.1)

    async def poll_for_token(self, sender):
        if not self.config or 'wbauth' not in self.config:
            print("No valid config found")
            return
        last_time = round(time.time() * 1_000_000_000)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
                while sender.state:
                    try:
                        token = self.config['wbauth']['token']
                        headers = {'Authorization': f'Bearer {token}'}
                        response = await client.post(AUTH_POLL_URL, headers=headers)
                        response.raise_for_status()
                        data = response.json()

                        if 'error' in data:
                            await self.notify('ERROR', data['error'], sender)
                        elif 'payload' in data:
                            for item in data['payload']:
                                if item['dt'] > last_time:
                                    last_time = item['dt']
                                    await self.notify(item['title'], item['text'], sender)
                                    break
                    except httpx.HTTPError as e:
                        print(f"[HTTP ERROR] {e}")
                    except Exception as e:
                        print(f"[ERROR] {e}")

                    await asyncio.sleep(5)
        finally:
            await asyncio.sleep(1)

    async def notify(self, title, text, sender=None):
        if not title or not text:
            return
        token_match = re.search(TOKEN_REGEX, text)
        token = token_match.group(0) if token_match else None
        description = re.sub(TOKEN_REGEX, '*****', text)

        if token:
            pyperclip.copy(token)
            if sender is not None:
                sender.state = False

        def copy_to_clipboard():
            if token:
                pyperclip.copy(token)
                if sender is not None:
                    sender.state = False

        if not token and "error" not in title.lower():
            return

        await self.notifier.send(
            title=title,
            message=description,
            urgency=Urgency.Critical,
            sound=DEFAULT_SOUND,
            on_clicked=copy_to_clipboard
        )
        await asyncio.sleep(1)


if __name__ == "__main__":
    WBAuthTrayApp().run()
