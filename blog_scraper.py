import asyncio
import random
import time
import csv
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Helper to save data
def save_to_csv(data):
    # This uses 'utf-8-sig' so Excel can read it perfectly
    with open('reddit_data.csv', mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(data)

async def scan_article_full_text(page, article_url, keywords):
    try:
        print(f"      > Scanning: {article_url[:50]}...")
        await page.goto(article_url, wait_until="domcontentloaded", timeout=45000)
        
        for _ in range(6):
            await page.mouse.wheel(0, 1200)
            await asyncio.sleep(2) 
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        container = soup.find('div', {'class': 'caas-body'}) or soup.find('article') or soup.find('main')

        if container:
            paragraphs = container.find_all('p')
            full_text = "\n\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20])
            
            matches = [k for k in keywords if k.lower() in full_text.lower()]
            if matches:
                save_to_csv(['Blog/News', article_url, "|".join(matches), full_text, "N/A"])
                print(f"      🔥 Saved Match!")
                return True
    except Exception as e:
        print(f"      ⚠️ Error: {e}")
    return False

async def main():
    MY_KEYWORDS = ["credit", "debit", "card", "interest", "tax", "dividend", "fees"]
    hubs = [
        "https://ca.finance.yahoo.com/",
        "https://news.google.com/search?q=financial%20products",
        "https://seekingalpha.com/search?q=financial%20products"
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0")
        page = await context.new_page()

        for hub_url in hubs:
            print(f"\n--- HUB: {hub_url} ---")
            await page.goto(hub_url, wait_until="domcontentloaded")
            for _ in range(4):
                await page.mouse.wheel(0, 3000)
                await asyncio.sleep(4)
            
            hrefs = await page.eval_on_selector_all("a", "elements => elements.map(e => e.href)")
            links = list(set([h for h in hrefs if any(x in h for x in ["/news/", "/article/", "/mkt-news/"])]))

            for link in links[:8]:
                await scan_article_full_text(page, link, MY_KEYWORDS)
                await asyncio.sleep(random.uniform(5, 10))

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())