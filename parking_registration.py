import time
from datetime import datetime, date
from utils import logger
import asyncio
from playwright.async_api import async_playwright, Error as PWError
from playwright.async_api import TimeoutError


_browser = {"pw": None, "inst": None, "lock": asyncio.Lock()}

CHROME_ARGS = [
    "--no-sandbox",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--no-zygote",
    "--disable-setuid-sandbox",
]


class RegistrationProcessor:
    def __init__(self, profile: dict, is_test_mode: bool):
        self.profile = profile
        self.is_test_mode = is_test_mode

    def fill_out_registration(self):
        logger.info("starting registration form processing")
        image_path = asyncio.get_event_loop().run_until_complete(self.run_flow())
        logger.info(f"registration complete, image path: {image_path}")
        return image_path

    async def _launch_browser(self):
        _browser["pw"] = await async_playwright().start()
        _browser["inst"] = await _browser["pw"].chromium.launch(
            headless=True, args=CHROME_ARGS
        )

    async def get_browser(self):
        # Single-writer init/reinit
        async with _browser["lock"]:
            b = _browser["inst"]
            if b is None or not b.is_connected():
                # (Re)launch
                await self._launch_browser()
                return _browser["inst"]

            # Health-check with a throwaway context/page (fast)
            try:
                ctx = await b.new_context()
                p = await ctx.new_page()
                await p.close()
                await ctx.close()
                return b
            except PWError:
                # Browser is stale/crashed → relaunch
                try:
                    await b.close()
                except Exception:
                    pass
                try:
                    if _browser["pw"]:
                        await _browser["pw"].stop()
                except Exception:
                    pass
                _browser.update({"pw": None, "inst": None})
                await self._launch_browser()
                return _browser["inst"]

    async def run_flow(self):
        url = "https://parkingpermitsofamerica.com/"

        # create Chromium browser instance
        logger.info("getting Chromium browser")
        browser = await self.get_browser()
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(15_000)
        page.set_default_navigation_timeout(20_000)
        try:
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()

            # Set headers
            await page.set_extra_http_headers(
                {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                }
            )

            # 1) navigate
            logger.info(f"navigating to url: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # 2) click 'Register Here'
            logger.info("clicking the 'Register Here' button")
            async with page.expect_navigation():
                await page.click("text=Register Here")

            # 3) type in registration code input
            logger.info("inputting MLCRVP code")
            code_input = page.locator("#codeInput")
            await code_input.wait_for(state="visible")  # visible in the viewport
            time.sleep(1)

            await code_input.type("MLCRVP", delay=30)  # simulate human typing
            await page.click("text=Verify Code")

            # 4) wait until the 'Select' button is visible then click it
            logger.info("clicking the 'Select' button")
            await page.wait_for_selector("text=Select")
            await page.click("text=Select")
            time.sleep(1)

            # 5) type in registration inputs
            logger.info("inputting permit details")
            license_plate_input = page.locator(
                "[name='PermitDetails.LicensePlateNumber']"
            )
            await license_plate_input.wait_for(state="visible")
            await license_plate_input.type(self.profile.get("licensePlate"), delay=10)
            await page.locator(
                "[name='PermitDetails.LicensePlateState']"
            ).select_option(self.profile.get("state"))
            await page.locator("[name='PermitDetails.VehicleYear']").type(
                self.profile.get("year"), delay=10
            )
            await page.locator("[name='PermitDetails.VehicleMake']").type(
                self.profile.get("make"), delay=10
            )
            await page.locator("[name='PermitDetails.VehicleModel']").type(
                self.profile.get("model"), delay=10
            )
            await page.locator("[name='PermitDetails.VehicleColor']").select_option(
                self.profile.get("color")
            )

            await page.locator("[name='PermitDetails.FirstName']").type(
                self.profile.get("firstName"), delay=10
            )
            await page.locator("[name='PermitDetails.LastName']").type(
                self.profile.get("lastName"), delay=10
            )
            await page.locator("[name='PermitDetails.ResidentVisiting']").type(
                "Kuzie Chambers", delay=10
            )
            await page.locator("[name='PermitDetails.ApartmentVisiting']").type(
                "440", delay=10
            )
            await page.locator("[name='PermitDetails.PhoneNumber']").type(
                self.profile.get("phoneNumber"), delay=10
            )
            await page.locator("[name='PermitDetails.Email']").type(
                "kuzie.chambers@gmail.com", delay=10
            )

            # 6) click the 'Proceed to Confirmation' button
            logger.info("clicking 'Proceed to Confirmation' button")
            await page.click("text=Proceed to Confirmation")
            time.sleep(1)

            # 7) wait until the user agreement checkbox is visible then click it
            logger.info("clicking the user agreement checkbox")
            confirm_checkbox = page.locator("[name='UserAgreed']")
            try:
                await confirm_checkbox.wait_for(state="visible")
            except TimeoutError:
                logger.info("car appears to already be registered")
                return None
            await confirm_checkbox.click()
            time.sleep(1)

            # 8) wait until the 'Confirm and Submit Permit' button is visible then click it
            logger.info("clicking the 'Confirm and Submit Permit' button")
            if not self.is_test_mode:
                confirm_button = page.locator("text=Confirm and Submit Permit")
                await confirm_button.click()
            else:
                logger.info("TEST MODE ENABLED, SKIPPING SUBMITTING")
            time.sleep(1)

            # take screenshot
            current_time = datetime.now()
            image_name = (
                f"screenshot_{self.profile.get('firstName')}_{date.today()}_{current_time.hour}-"
                f"{current_time.minute}-{current_time.second}.png"
            )
            logger.info(f"taking screenshot, path: /tmp/{image_name}")
            await page.locator("main").screenshot(path=f"/tmp/{image_name}")
            logger.info("screenshot created")

        finally:
            # Only close the *context*, never the global browser
            await context.close()

        return image_name
