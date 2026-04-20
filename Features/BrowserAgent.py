import asyncio
import os
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from Features.Face.Mouth import speak

class BrowserAgent:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.context = None

    async def _start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )

    async def _stop(self):
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def execute_task(self, url, actions):
        """
        Actions: list of {'type': 'click'|'type'|'wait'|'scrape', 'selector': '...', 'value': '...'}
        """
        await self._start()
        page = await self.context.new_page()
        await stealth_async(page)
        
        try:
            speak(f"Executive Assistant navigating to {url}")
            await page.goto(url, wait_until="networkidle")
            
            for action in actions:
                a_type = action.get('type')
                selector = action.get('selector')
                value = action.get('value')
                
                if a_type == 'click':
                    await page.click(selector)
                elif a_type == 'type':
                    await page.fill(selector, value)
                elif a_type == 'wait':
                    await page.wait_for_timeout(action.get('ms', 2000))
                elif a_type == 'scrape':
                    content = await page.inner_text(selector)
                    print(f"[BrowserAgent] Scraped: {content}")
            
            speak("Task executed successfully on the digital portal.")
            return True
        except Exception as e:
            speak(f"Browser Agent failure: {str(e)}")
            return False
        finally:
            await self._stop()

    def run_task(self, url, actions):
        """Synchronous wrapper for async execution"""
        return asyncio.run(self.execute_task(url, actions))

browser_agent = BrowserAgent()
