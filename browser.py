import os
import time
import asyncio
from playwright.sync_api import sync_playwright

class SocialMediaAutomationWorker:
    def __init__(self, user_data_dir: str = "./playwright_profile"):
        self.user_data_dir = user_data_dir
        self._playwright = None
        self._browser = None

    def _sync_initialize(self):
        if not self._browser:
            os.makedirs(self.user_data_dir, exist_ok=True)
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                args=["--start-maximized"]
            )

    def _sync_close(self):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def _sync_execute_post(self, platform: str, content: str, media_url: str | None = None):
        self._sync_initialize()
        page = self._browser.new_page()
        try:
            if platform.lower() == "twitter":
                page.goto("https://x.com/compose/post", timeout=60000)
                page.wait_for_selector("div[aria-label='Post text']", timeout=15000)
                page.click("div[aria-label='Post text']")
                page.keyboard.type(content)
                time.sleep(1)
                page.click("button[data-testid='tweetButton']", timeout=5000)
                time.sleep(3)
            elif platform.lower() == "linkedin":
                page.goto("https://www.linkedin.com/feed/", timeout=60000)
                time.sleep(3)
        finally:
            page.close()

    async def initialize(self):
        await asyncio.to_thread(self._sync_initialize)

    async def close(self):
        await asyncio.to_thread(self._sync_close)

    async def execute_post(self, platform: str, content: str, media_url: str | None = None):
        await asyncio.to_thread(self._sync_execute_post, platform, content, media_url)

automation_worker = SocialMediaAutomationWorker()