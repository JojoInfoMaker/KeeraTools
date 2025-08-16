import requests
import json
from time import sleep

# Base URL for Flathub AppStream data
BASE_URL = "https://flathub.org/api/v1/apps"

# Output file
OUTPUT_FILE = "flathub_apps.json"

def get_all_apps():
    print("Fetching the list of all apps...")
    response = requests.get(BASE_URL)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch apps: {response.status_code}")
    return response.json()

def fetch_app_details(app_id):
    url = f"https://flathub.org/api/v2/appstream/{app_id}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Warning: Could not fetch {app_id}")
        return None
    return response.json()

def main():
    apps = get_all_apps()
    all_app_data = []

    for app in apps:
        app_id = app['app_id']
        print(f"Fetching metadata for {app_id}...")
        details = fetch_app_details(app_id)
        if details:
            # Extract the categories
            categories = details.get("categories", [])
            all_app_data.append({
                "app_id": app_id,
                "name": details.get("name"),
                "summary": details.get("summary"),
                "categories": categories
            })
        sleep(0.1)  # Be polite to Flathub servers

    # Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_app_data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_app_data)} apps to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
