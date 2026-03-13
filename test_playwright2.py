import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        
        # Intercept websocket frames
        page.on("websocket", lambda ws: ws.on("framereceived", lambda frame: print(f"WS RAW RECV: {frame.payload[0:150]}")))

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
        await page.evaluate("finishChecklist()")
        
        await asyncio.sleep(1)
        await page.evaluate("finishChecklist()")
        
        await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
