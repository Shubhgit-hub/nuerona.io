import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import openai
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
FORMBRICKS_REPO = "https://github.com/formbricks/formbricks.git"
FORMBRICKS_DIR = Path("formbricks")
GENERATED_DATA_FILE = Path("generated_data.json")
BASE_URL = "http://localhost:3000"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FORMBRICKS_API_KEY = os.getenv("FORMBRICKS_API_KEY")

def check_dependencies():
    """Ensure required env vars and tools are available."""
    if not OPENAI_API_KEY:
        raise ValueError("Set OPENAI_API_KEY in .env or environment.")
    if not FORMBRICKS_API_KEY:
        raise ValueError("Set FORMBRICKS_API_KEY in .env or environment. Generate from Formbricks admin after 'up'.")
    if subprocess.run(["docker", "--version"], capture_output=True).returncode != 0:
        raise RuntimeError("Docker is required.")

def up():
    """Run Formbricks locally using Docker Compose."""
    check_dependencies()
    if not FORMBRICKS_DIR.exists():
        print("Cloning Formbricks repo...")
        subprocess.run(["git", "clone", FORMBRICKS_REPO], check=True)
    os.chdir(FORMBRICKS_DIR)
    print("Starting Formbricks with Docker Compose...")
    subprocess.run(["docker-compose", "up", "-d"], check=True)
    print("Formbricks is running at http://localhost:3000. Wait 5-10 minutes for it to fully start.")

def down():
    """Stop and clean up Formbricks."""
    if not FORMBRICKS_DIR.exists():
        print("Formbricks not found. Nothing to stop.")
        return
    os.chdir(FORMBRICKS_DIR)
    print("Stopping Formbricks...")
    subprocess.run(["docker-compose", "down"], check=True)
    print("Formbricks stopped and cleaned up.")

def generate():
    """Generate realistic data using OpenAI and save to JSON."""
    check_dependencies()
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = """
    Generate realistic data for seeding Formbricks. Output as valid JSON with two keys:
    - "surveys": An array of 5 unique surveys. Each survey has:
      - "name": A string title.
      - "questions": An array of 3-5 questions. Each question is an object with "type" (e.g., "multipleChoiceSingle", "openText"), "headline" (string), and for multipleChoice, "choices" (array of strings).
      - "responses": An array of at least 1 realistic response. Each response is an object with "data" (object mapping question IDs to answers, e.g., {"q1": "Answer"}).
    - "users": An array of 10 unique users. Each user has:
      - "name": String.
      - "email": Unique string.
      - "role": Either "Manager" or "Owner".
    Make it look like an actively used system: varied, realistic content (e.g., customer feedback, product surveys).
    Ensure the JSON is parseable.
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    try:
        data = json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}")
    
    with open(GENERATED_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Data generated and saved to {GENERATED_DATA_FILE}.")

def seed():
    """Seed Formbricks with generated data using APIs."""
    if not GENERATED_DATA_FILE.exists():
        raise FileNotFoundError("Run 'generate' first.")
    
    with open(GENERATED_DATA_FILE) as f:
        data = json.load(f)
    
    headers = {"Authorization": f"Bearer {FORMBRICKS_API_KEY}", "Content-Type": "application/json"}
    
    # Health check: Ensure Formbricks is up
    print("Checking if Formbricks is ready...")
    for _ in range(10):  # Retry up to 10 times
        try:
            resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
            if resp.status_code == 200:
                break
        except requests.RequestException:
            pass
        print("Formbricks not ready yet. Retrying in 10 seconds...")
        time.sleep(10)
    else:
        raise RuntimeError("Formbricks is not responding. Ensure 'up' completed and wait longer.")
    
    # Seed users
    print("Seeding users...")
    for user in data["users"]:
        resp = requests.post(f"{BASE_URL}/api/management/users", json=user, headers=headers)
        if resp.status_code != 201:
            print(f"Failed to create user {user['email']}: {resp.text}")
        else:
            print(f"Created user: {user['name']}")
    
    # Seed surveys and responses
    print("Seeding surveys and responses...")
    for survey in data["surveys"]:
        # Create survey
        survey_payload = {"name": survey["name"], "questions": survey["questions"]}
        resp = requests.post(f"{BASE_URL}/api/management/surveys", json=survey_payload, headers=headers)
        if resp.status_code != 201:
            print(f"Failed to create survey {survey['name']}: {resp.text}")
            continue
        survey_id = resp.json()["id"]
        print(f"Created survey: {survey['name']} (ID: {survey_id})")
        
        # Submit responses via Client API (no auth needed)
        for response in survey["responses"]:
            resp = requests.post(f"{BASE_URL}/api/client/surveys/{survey_id}/responses", json=response)
            if resp.status_code != 201:
                print(f"Failed to submit response for survey {survey_id}: {resp.text}")
            else:
                print(f"Submitted response for survey {survey_id}")

def main():
    parser = argparse.ArgumentParser(description="Formbricks Challenge CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    formbricks_parser = subparsers.add_parser("formbricks")
    formbricks_sub = formbricks_parser.add_subparsers(dest="action", required=True)
    
    formbricks_sub.add_parser("up")
    formbricks_sub.add_parser("down")
    formbricks_sub.add_parser("generate")
    formbricks_sub.add_parser("seed")
    
    args = parser.parse_args()
    
    if args.command == "formbricks":
        if args.action == "up":
            up()
        elif args.action == "down":
            down()
        elif args.action == "generate":
            generate()
        elif args.action == "seed":
            seed()

if __name__ == "__main__":
    main()