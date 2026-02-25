import sys
import re
from playwright.sync_api import sync_playwright

#auction scraper with deafult search query, can be modified by passing a different query to the function
def scrape_auctions(search_query: str) -> list[dict]:
    auction_details: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = browser.new_page()
        page.goto("https://bringatrailer.com/search/?s=" + search_query)
        # wait for the listing cards container to show up
        try:
                page.wait_for_selector("//div[contains(@class, 'listing-card')]", timeout=10000)
        except Exception:
            print("[warning] listing cards did not appear within timeout")

        # click through pagination (search page) until we reach the end of the results
        while True:
            next_btn = page.locator("//a[contains(@class, 'page-numbers')]")
    
            if next_btn.count() == 0:
                break
    
            next_btn.first.scroll_into_view_if_needed()
            next_btn.first.click()
            page.wait_for_load_state("networkidle")

        # click through pagination (model page) until we reach the end of the results
        while True:
            next_btn = page.locator("//button[contains(@class, 'button-show-more')]")
    
            if next_btn.count() == 0:
                break
    
            next_btn.first.scroll_into_view_if_needed()
            next_btn.first.click()
            page.wait_for_load_state("networkidle")

        previous_auctions = page.locator("//div[contains(@class, 'previous-listings')]")
        if previous_auctions.count() == 0:
            previous_auctions = page.locator("//div[contains(@class, 'listings-container')]")
            if previous_auctions.count() == 0:
                print("could not find auction listings on page, exiting")
                browser.close()
                sys.exit(0)
        # get locator for all auction listing cards
        page.wait_for_load_state("networkidle")
        cards = previous_auctions.locator("//div[contains(@class, 'listing-card')]")

        # debug count (helps diagnose empty output)
        count = cards.count()
        print(f"DEBUG: found {count} listing cards")
        if count == 0:
            print("no auctions to process, exiting")
            browser.close()
            sys.exit(0)
        for i in range(count):
            card = cards.nth(i)
            # the link is stored on the <a> inside the card
            href = card.locator("a").first.get_attribute("href")
            if not href:
                # skip if for some reason we couldn't find the link
                continue

            content_search = context.new_page()
            content_search.goto(href)
            # grab details once the page loads
            title = content_search.locator("//h1[contains(@class, 'post-title')]").inner_text()
            price = content_search.locator("//span[contains(@class, 'info-value')]//strong").text_content()
            locator = content_search.locator("//div[contains(@class, 'essentials')]//li").filter(has_text="Miles")
            miles = locator.first.text_content() if locator.count() else None
            date_sold = content_search.locator("//span[contains(@class, 'date')]").first.inner_text()

            price_fixed = price[price.find("$")+1:]
            price_clean = price_fixed.replace(",", "")
            price_int = int(price_clean) if price_clean else None
            miles_fixed = re.search(r'\(?(\w+)\s+Miles\b', miles)
            if (miles_fixed and "k" in miles_fixed.group(1)):
                miles_clean = miles_fixed.group(1).replace("k", "000")
            elif (miles_fixed and "," in miles_fixed.group(1)):
                miles_clean = miles_fixed.group(1).replace(",", "")
            else:
                miles_clean = miles_fixed.group(1) if miles_fixed else None
            try:
                miles_int = int(miles_clean) if miles_clean else None
            except ValueError:
                miles_int = None
            date_sold_clean = date_sold[date_sold.find("on")+3:]
            auction_details.append({
                "title": title,
                "price": price_int,
                "miles":  miles_int,
                "date_sold": date_sold_clean
            })
            # print progress to console
            print(f"\rProcessing auction {i + 1} of {count}...", end="", flush=True)
            sys.stdout.flush()
            content_search.close()

        browser.close()
        print()  # moves to a fresh line
        print(f"Done! processed {count} auctions")
    return auction_details



#auction_details = scrape_auctions()
#
#for auction in auction_details:
#    print("title: " + auction["title"])
#    print("price: " + str(auction["price"]))
#    print("miles: " + str(auction["miles"]))
#    print("date sold: " + auction["date_sold"] + "\n")