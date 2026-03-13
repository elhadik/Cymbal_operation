import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda err: print(f"JS ERROR: {err}"))
        
        await page.goto("http://localhost:8080")
        await page.click("button#start-btn")
        await asyncio.sleep(2)
        
        await page.evaluate("""() => {
            ws.send(JSON.stringify({ type: 'order_parsed', medicine: 'Insulin', aisle: 'Aisle 2' }));
            window._checklistPending = true;
            window._pendingWidgetDrop = true;
            audioQueue.push({type: 'signal', name: 'show_widget'});
            playNextAudio();
        }""")
        
        await asyncio.sleep(1)
        # click first widget btn
        await page.evaluate("finishChecklist()")
        
        await asyncio.sleep(1)
        # click second widget btn
        await page.evaluate("finishChecklist()")
        
        await asyncio.sleep(8)
        
        map_rendered = await page.evaluate("document.querySelectorAll('#map-confirm-btn').length > 0")
        print(f"MAP RENDERED: {map_rendered}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
