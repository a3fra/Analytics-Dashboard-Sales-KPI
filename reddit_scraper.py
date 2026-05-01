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

async def scrape_full_post(page, post_url, keywords):
    try:
        await page.goto(post_url, wait_until="commit", timeout=60000)
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3) 
        
        for i in range(3):
            await page.mouse.wheel(0, 3000)
            await asyncio.sleep(random.uniform(1.0, 2.0)) 
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        body_container = soup.find('shreddit-post')
        full_body = "\n".join([p.get_text().strip() for p in body_container.find_all('p')]) if body_container else ""
        
        comment_elements = soup.find_all('shreddit-comment')
        all_comments = [c.find('div', {'slot': 'comment'}).get_text(separator=' ').strip() 
                        for c in comment_elements if c.find('div', {'slot': 'comment'})]

        search_space = (full_body + " " + " ".join(all_comments)).lower()
        matches = [k for k in keywords if k.lower() in search_space]
        
        if matches:
            save_to_csv(['Reddit', post_url, "|".join(matches), full_body, " || ".join(all_comments)])
            print(f"   >>> Saved: {post_url.split('/')[-2]}")
            return True
    except Exception as e:
        print(f"   ⚠️ Error: {e}")
    return False

async def main():
    MY_KEYWORDS = ["credit", "debit", "card", "interest", "etf", "tax", "dividend", "fees"]
    subreddits = [
        "https://www.reddit.com/r/Economics/",
        "https://www.reddit.com/r/PersonalFinanceCanada/",
        "https://www.reddit.com/r/investing/"
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        for sub_url in subreddits:
            print(f"\n--- SUBREDDIT: {sub_url} ---")
            await page.goto(sub_url, wait_until="domcontentloaded")
            await asyncio.sleep(12) # Time for manual captcha/login
            
            await page.reload(wait_until="commit")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(5)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            posts = soup.find_all('shreddit-post', limit=5)
            links = ["https://www.reddit.com" + p.get('permalink') for p in posts if p.get('permalink')]

            for link in links:
                await scrape_full_post(page, link, MY_KEYWORDS)
                await asyncio.sleep(random.uniform(2, 4))

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())