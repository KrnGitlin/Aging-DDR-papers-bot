# SciPaper Bot

A two-part bot that:

1. Posts weekly highlights of newly released papers to Twitter (X) based on your keywords.
2. Publishes a GitHub Pages website listing papers from newest to oldest with filtering by keyword.

Inspired by public paper feeds like accounts similar to Pha_Tran_Papers and open-source ideas like Scitify, but implemented from scratch here.

## Features

- Source: arXiv feed via public API (extensible to others later)
- Keywords and categories configurable in `config.yaml`
- Weekly Twitter posting with duplicate protection
- Static website (no backend) hosted via GitHub Pages
- JSON data generated at `site/data/papers.json`

## Quickstart (Windows PowerShell)

1. Create and activate a virtual environment (optional but recommended):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Configure keywords and settings in `config.yaml` (defaults included).

4. Generate paper data locally:

```powershell
python .\scripts\update_papers.py --write
```

5. Open the static site by using a simple server (optional):

```powershell
# Python 3.x
python -m http.server -d .\site 8000
# Visit http://localhost:8000
```

## Twitter (X) setup

Important: Never share your account password. Use API keys/tokens from the Twitter developer portal.

1) Create a Twitter app and enable User OAuth 1.0a.
2) Obtain these credentials:
	 - `TWITTER_API_KEY`
	 - `TWITTER_API_SECRET`
	 - `TWITTER_ACCESS_TOKEN`
	 - `TWITTER_ACCESS_TOKEN_SECRET`

Local run options:

- Option A: Use a `.env` file (recommended locally)
	- Copy `.env.example` to `.env` and paste your values.
	- The scripts auto-load `.env`.

- Option B: Set environment variables in PowerShell:
	```powershell
	$env:TWITTER_API_KEY = "<your_api_key>"
	$env:TWITTER_API_SECRET = "<your_api_secret>"
	$env:TWITTER_ACCESS_TOKEN = "<your_access_token>"
	$env:TWITTER_ACCESS_TOKEN_SECRET = "<your_access_token_secret>"
	```

Dry run (no posting):
```powershell
& ".\.venv\Scripts\python.exe" ".\scripts\post_to_twitter.py" --days 7 --max 5 --dry-run
```

Enable real posting:
- In `config.yaml`, set `twitter.enabled: true` and `twitter.dry_run: false`.
- Then run:
```powershell
& ".\.venv\Scripts\python.exe" ".\scripts\post_to_twitter.py" --days 7 --max 5
```

## GitHub Pages

This repo includes a GitHub Actions workflow to:
- Run the paper updater on a schedule
- Commit the updated `site/data/papers.json`
- Deploy the `site/` folder to GitHub Pages

You’ll need to:
- Push this repo to GitHub
- Enable Pages in your repo settings (Build and deployment: GitHub Actions)
## Publish to GitHub and set secrets

1) Initialize git locally (already done below if you used the one-click setup) and create a repo on GitHub (e.g., `scipaper-bot`).
2) Add the remote and push:
	 - Set your origin URL: `git remote add origin https://github.com/<you>/scipaper-bot.git`
	 - Set default branch to `main` if needed: `git branch -M main`
	 - Push: `git push -u origin main`
3) In GitHub → Settings → Secrets and variables → Actions, add:
	 - `TWITTER_API_KEY`
	 - `TWITTER_API_SECRET`
	 - `TWITTER_ACCESS_TOKEN`
	 - `TWITTER_ACCESS_TOKEN_SECRET`

Then enable Pages for the repo (build via GitHub Actions).

## Enable tweeting safely

- Verify credentials locally first:
	```powershell
	& ".\.venv\Scripts\python.exe" ".\scripts\check_twitter_auth.py"
	```
- When ready, toggle in `config.yaml`:
	- `twitter.enabled: true`
	- `twitter.dry_run: false`
- For a one-off bioRxiv post you can run:
	```powershell
	& ".\.venv\Scripts\python.exe" ".\scripts\post_to_twitter.py" --days 60 --max 1 --source bioRxiv --live-biorxiv
	```


### Auto-tweet workflow

This repo includes `.github/workflows/tweet-weekly.yml` which:
- Refreshes `site/data/papers.json`
- Posts up to 5 tweets for the last 7 days

Before it can post, add these Repository Secrets in GitHub (Settings ➜ Secrets and variables ➜ Actions):
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_TOKEN_SECRET`

Control posting with `config.yaml`:
- `twitter.enabled: true` to allow posting in CI
- `twitter.dry_run: false` for real tweets (leave true to log-only)

## Configuration (`config.yaml`)

- `keywords`: List of strings to match in title or abstract
- `categories`: arXiv categories (e.g., `cs.CL`, `cs.LG`)
- `days_back`: How many days back to keep
- `max_results`: Max results fetched per keyword (fetched broadly then filtered by date)
- `site_data_path`: Where the JSON is written for the website
- `twitter`: Enable/disable, max posts, hashtags, dry-run

## Notes

- arXiv API returns Atom feeds; we parse with `feedparser`.
- We filter locally by date range. arXiv doesn’t natively support arbitrary date ranges in the query.
- Respect arXiv’s rate limits; this code avoids excessive requests and deduplicates by ID.
- Local `.env` is for development only. Don’t commit your `.env` file.

## Roadmap

- Add support for more sources (Semantic Scholar, Papers with Code)
- Topic pages per keyword with pre-rendered HTML
- RSS output for each keyword
