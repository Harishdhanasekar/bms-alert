"""
BookMyShow Booking-Open Alert
------------------------------
Checks whether a given movie has booking open in a given city on BookMyShow,
optionally filtered to specific theater name(s), and sends a push notification
via ntfy.sh the moment it detects a change.

Designed to be run repeatedly (e.g. every 5 minutes via GitHub Actions cron).
State is persisted in state.json so you only get alerted once per new theater,
not on every run.
"""

import json
import os
import re
import sys
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

# ----------------------------- CONFIG ---------------------------------------
# Edit these to match what you're tracking.

MOVIE_NAME = "Jana Nayagan"
CITY_SLUG = "chennai"          # BookMyShow's URL slug for the city

# Leave THEATER_KEYWORDS empty ( [] ) to get alerted the moment ANY theater
# in the city opens booking for this movie. Add substrings (case-insensitive)
# to restrict alerts to specific theaters, e.g.:
# THEATER_KEYWORDS = ["Sathyam", "Rohini", "Luxe"]
THEATER_KEYWORDS = []

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
STATE_FILE = Path(__file__).parent / "state.json"

MOVIES_LISTING_URL = f"https://in.bookmyshow.com/explore/movies-{CITY_SLUG}"
# -----------------------------------------------------------------------------


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"movie_found": False, "notified_theaters": []}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def send_ntfy(title: str, message: str, priority: str = "high") -> None:
    if not NTFY_TOPIC:
        print("[WARN] NTFY_TOPIC not set — skipping push notification.")
        print(f"       Would have sent: {title} — {message}")
        return
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": priority,
                "Tags": "movie_camera,bell",
            },
            timeout=15,
        )
        print(f"[OK] Sent ntfy alert: {title}")
    except Exception as e:
        print(f"[ERROR] Failed to send ntfy alert: {e}")


def find_movie_url(page) -> str | None:
    """Search the city's movie listing page for a link matching MOVIE_NAME."""
    page.goto(MOVIES_LISTING_URL, timeout=45000, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)  # let client-side rendering settle

    links = page.eval_on_selector_all(
        "a[href*='/movies/']",
        "els => els.map(e => ({href: e.href, text: e.innerText}))",
    )

    target = MOVIE_NAME.lower().replace(" ", "")
    for link in links:
        text = (link.get("text") or "").lower().replace(" ", "")
        href = (link.get("href") or "").lower()
        if target in text or target in href.replace("-", ""):
            return link["href"]
    return None


def get_theaters_with_shows(page, movie_url: str) -> list[str]:
    """
    Visit the movie page and try to reach the 'buy tickets' venue list.
    Returns a list of theater/venue names that currently have showtimes.
    """
    page.goto(movie_url, timeout=45000, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # If there's a "Book tickets" CTA, click it — BMS often needs this to
    # reveal the date/venue picker rather than just a synopsis page.
    try:
        book_btn = page.locator("text=/book tickets/i").first
        if book_btn.is_visible(timeout=3000):
            book_btn.click()
            page.wait_for_timeout(3000)
    except Exception:
        pass

    # Venue names on BMS venue-listing pages are typically inside elements
    # with class names containing "venue" — this selector is intentionally
    # broad since BMS changes its markup periodically.
    venue_texts = page.eval_on_selector_all(
        "[class*='venue' i], [class*='Venue' i]",
        "els => els.map(e => e.innerText).filter(Boolean)",
    )

    # Clean and dedupe short venue-name-looking strings
    theaters = []
    seen = set()
    for t in venue_texts:
        name = t.strip().split("\n")[0].strip()
        if 3 < len(name) < 80 and name not in seen:
            seen.add(name)
            theaters.append(name)

    return theaters


def main():
    state = load_state()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-IN",
        )
        page = context.new_page()

        try:
            movie_url = find_movie_url(page)
        except Exception as e:
            print(f"[ERROR] Could not load movie listing page: {e}")
            browser.close()
            sys.exit(1)

        if not movie_url:
            print(f"[INFO] '{MOVIE_NAME}' not yet listed in {CITY_SLUG}. Will keep checking.")
            browser.close()
            return

        if not state["movie_found"]:
            state["movie_found"] = True
            send_ntfy(
                f"{MOVIE_NAME} is now listed!",
                f"{MOVIE_NAME} has appeared on BookMyShow {CITY_SLUG.title()}. Checking for showtimes...",
            )

        try:
            theaters = get_theaters_with_shows(page, movie_url)
        except Exception as e:
            print(f"[ERROR] Could not load theater list: {e}")
            browser.close()
            save_state(state)
            return

        browser.close()

    print(f"[INFO] Found {len(theaters)} theater(s) with listed shows.")

    # Filter to theaters of interest
    if THEATER_KEYWORDS:
        matched = [
            t for t in theaters
            if any(kw.lower() in t.lower() for kw in THEATER_KEYWORDS)
        ]
    else:
        matched = theaters

    new_theaters = [t for t in matched if t not in state["notified_theaters"]]

    if new_theaters:
        theater_list = "\n".join(f"• {t}" for t in new_theaters)
        send_ntfy(
            f"🎬 Booking OPEN: {MOVIE_NAME}",
            f"Tickets are now bookable at:\n{theater_list}\n\nBook fast: {movie_url}",
        )
        state["notified_theaters"] = list(set(state["notified_theaters"] + new_theaters))
    else:
        print("[INFO] No new matching theaters since last check.")

    save_state(state)


if __name__ == "__main__":
    main()
