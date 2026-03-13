import os
import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load from .env explicitly
load_dotenv()

async def run():
    # Fetch values directly inside the script
    cf_id = os.environ.get("CF_ACCESS_CLIENT_ID")
    cf_secret = os.environ.get("CF_ACCESS_CLIENT_SECRET")
    
    if not cf_id or not cf_secret:
        print("ERROR: CF_ACCESS_CLIENT_ID or CF_ACCESS_CLIENT_SECRET not set in .env.")
        return

    async with async_playwright() as p:
        headers = {
            "CF-Access-Client-ID": cf_id,
            "CF-Access-Client-Secret": cf_secret,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        print(f"Testing with ID: {cf_id[:8]}...")
        
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(extra_http_headers=headers)
        page = await context.new_page()
        
        # Listen to requests
        page.on("request", lambda request: print(f">> Request: {request.url} | Header ID Present: {bool(request.headers.get('cf-access-client-id'))}"))
        
        response = await page.goto("https://staging.spencerscooking.uk/home")
        
        print(f"Final URL: {page.url}")
        print(f"Status: {response.status}")
        
        if "cloudflareaccess.com" in page.url:
            print("FAILED: Redirected to Cloudflare Login")
        else:
            print("SUCCESS: Content reached!")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
