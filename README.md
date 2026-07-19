# BookMyShow Booking-Open Alert — Jana Nayagan (Chennai)

Pings your phone the moment ticket booking opens for **Jana Nayagan** in
**Chennai** on BookMyShow, using free push notifications (ntfy) and a free
GitHub Actions cron job (runs every 5 minutes, no server needed).

## 1. Get the ntfy app on your phone

- Android: [ntfy on Play Store](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
- iPhone: [ntfy on App Store](https://apps.apple.com/us/app/ntfy/id1625396347)

Open the app → tap **+** to subscribe to a topic → type a topic name that's
**hard to guess** (anyone who knows the topic name can send to it), e.g.:

```
harish-jananayagan-alert-83x2
```

Use that exact string in step 3 below.

## 2. Push this folder to a new GitHub repo

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/bms-alert.git
git push -u origin main
```

Make the repo **private** (Settings → General → Danger Zone) since it will
contain a small state file tracking what's been checked — nothing
sensitive, but no reason to make it public.

## 3. Add your ntfy topic as a GitHub secret

In your repo: **Settings → Secrets and variables → Actions → New repository
secret**

- Name: `NTFY_TOPIC`
- Value: the topic string you picked in step 1 (e.g. `harish-jananayagan-alert-83x2`)

## 4. Enable the workflow

Go to the **Actions** tab in your repo — GitHub sometimes needs you to click
"I understand my workflows, go ahead and enable them" the first time. Then
click **Check BookMyShow Booking Status → Run workflow** to trigger it once
manually and confirm it works.

From then on it runs automatically every 5 minutes.

## Customizing

Open `monitor.py` and edit the config block at the top:

- `MOVIE_NAME` — change if you want to track a different film
- `CITY_SLUG` — BookMyShow's city slug, e.g. `"chennai"`, `"bengaluru"`, `"mumbai"`
- `THEATER_KEYWORDS` — leave as `[]` to get alerted for **any** theater in
  the city, or add substrings to restrict to specific theaters, e.g.:
  ```python
  THEATER_KEYWORDS = ["Sathyam", "Rohini Silver Screens", "PVR Luxe"]
  ```

## Important things to know

- **BookMyShow has no public API.** This script loads their real pages with
  a headless browser (Playwright) and reads the rendered content — the same
  way your own browser would see it. This is inherently more fragile than
  an API integration: if BookMyShow changes their page layout, the script's
  selectors may need a small update.
- **Anti-bot protection.** Sites like BookMyShow often run bot-detection
  (e.g. Akamai). Running every 5 minutes from GitHub's shared IP ranges is
  usually fine for a low-frequency personal check, but if you start seeing
  the workflow consistently fail to load the page, that's likely why —
  the fix is typically to reduce frequency or add delays, not to try to
  defeat the protection.
- **Use for personal tracking only.** This checks a public page the same
  way your browser does; it doesn't log in, doesn't touch payment flows,
  and doesn't attempt to book anything automatically — it only tells you
  when to go book it yourself.
- **First-run behavior:** the very first successful run will send you a
  notification when the movie itself first appears on BookMyShow (even
  before showtimes are listed), then a second, separate alert once your
  target theater(s) actually have bookable showtimes.

## Manual test locally (optional)

```bash
pip install -r requirements.txt
playwright install --with-deps chromium
NTFY_TOPIC=harish-jananayagan-alert-83x2 python monitor.py
```
