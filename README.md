# Formbricks Challenge Solution

This project implements the Formbricks challenge: run Formbricks locally, generate realistic data via LLM, and seed it using APIs.

## Setup
1. Clone this repo.
2. Copy `.env.example` to `.env` and fill in your API keys.
3. Install dependencies: `pip install -r requirements.txt`.
4. Ensure Docker is installed.

## Commands
- `python main.py formbricks up`: Start Formbricks locally.
- `python main.py formbricks generate`: Generate data (requires OpenAI key).
- `python main.py formbricks seed`: Seed data (requires Formbricks API key from admin panel).
- `python main.py formbricks down`: Stop Formbricks.

## Docker (Optional)
- Build: `docker build -t formbricks-challenge .`
- Run: `docker run -it --rm -v /var/run/docker.sock:/var/run/docker.sock formbricks-challenge python main.py formbricks <action>`

## Notes
- Wait 5-10 mins after `up` for Formbricks to start.
- Check http://localhost:3000 for the UI.
- API docs: https://formbricks.com/docs/overview/introduction