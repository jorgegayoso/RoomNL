# Roommatch Auto-Apply Bot

Monitors [roommatch.nl](https://www.roommatch.nl) for new student housing listings and automatically applies to rooms that match your criteria.

## Quick Start

```bash
# 1. Install dependencies
pip install selenium webdriver-manager requests beautifulsoup4

# 2. Set up your credentials
cp .env.example .env
# Edit .env with your Roommatch login + email settings

# 3. Configure filters in main.py (price, keywords, cities, etc.)

# 4. Run
python main.py
```

You'll also need Chrome installed for the Selenium-based application step.

## Environment Variables

| Variable | Description |
|---|---|
| `ROOMMATCH_USERNAME` | Your roommatch.nl / ROOM.nl email |
| `ROOMMATCH_PASSWORD` | Your roommatch.nl / ROOM.nl password |
| `SMTP_USERNAME` | Gmail address for sending notifications |
| `SMTP_PASSWORD` | Gmail [app password](https://myaccount.google.com/apppasswords) (not your regular password) |
| `NOTIFY_EMAIL` | Email address to receive notifications |

### Gmail App Password

Gmail won't let you log in with your regular password from a script. You need to generate an **app password** instead:

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (you'll need 2FA enabled on your Google account first)
2. Create a new app password — Google will give you a 16-character code like `abcd efgh ijkl mnop`
3. Put that code in your `.env` as `SMTP_PASSWORD`

## How It Works

The bot runs a continuous loop with four components:

- **`listings.py`** — Fetches current room listings from the Roommatch API filtered by region and student profile. Can also be run standalone (`python listings.py`) to browse what's available.
- **`main.py`** — The main monitor. Polls the API every few seconds, compares against known listings, and when a new room appears that matches your filters (price range, keywords, city, room type), triggers an application.
- **`bot.py`** — Uses Selenium to open Chrome, log in via ROOM.nl SSO, navigate to the room page, and click the "Reageer" (apply) button. There's also `apply.py` which does the same thing via raw HTTP requests instead of a browser.
- **`notifier.py`** — Sends you an email after each application attempt (success or failure) with the room details.

### Configuration

Edit the `CONFIG` dict at the top of `main.py` to set your filters:

```python
CONFIG = {
    "check_interval_seconds": 5,
    "max_price": 750,
    "required_keywords": ["amsterdam", "studio"],
    "excluded_keywords": ["shared"],
    "auto_apply": True,
    "send_email_notifications": True,
    # ...
}
```

### Test Mode

To test without hitting the live API for the initial fetch:

```bash
python listings.py          # saves roommatch_listings.json
python main.py --test       # loads that file as baseline, then polls API for new ones
```
