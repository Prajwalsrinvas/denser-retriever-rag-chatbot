import json
from typing import List

import requests


def fetch_groq_models(api_key: str) -> List[str]:
    response = requests.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    if response.status_code == 200:
        models_data = response.json()
        # Write to JSON file
        with open("groq_models.json", "w") as f:
            json.dump(models_data, f, indent=4)

        return models_data
    else:
        raise Exception(f"Failed to fetch models: {response.status_code}")


if __name__ == "__main__":
    import os

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")

    models = fetch_groq_models(api_key)
    print(f"Fetched and saved {len(models['data'])} models")
