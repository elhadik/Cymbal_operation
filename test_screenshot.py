import asyncio
from playwright.async_api import async_playwright
import time

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        
        await page.goto("http://localhost:8080")
        await page.wait_for_selector("button#start-btn:not([disabled])")
        await page.click("button#start-btn")
        await asyncio.sleep(2)
        
        print("Triggering pathfinder directly...")
        await page.evaluate("""() => {
            ws.send(JSON.stringify({
                clientContent: {
                    turns: [{
                        parts: [{text: "User clicked: Added both items to package. Please run pathfinder analysis now."}]
                    }]
                }
            }));
        }""")
        
        print("Waiting for Pathfinder analysis...")
        # Wait until pathfinder map actually renders in transcript box
        try:
            await page.wait_for_selector('iframe[src*="google.com/maps"]', timeout=30000)
            print("Map rendered successfully!")
        except Exception as e:
            print("Map did not render within 30 seconds.")
            
        await page.screenshot(path="/usr/local/google/home/elhadik/.gemini/jetski/brain/659befbc-92d3-4fc2-bde3-e212d1606d15/final_map_in_chat.png", full_page=True)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
