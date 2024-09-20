import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()


DENSER_RETRIEVER_API_KEY = os.getenv("DENSER_RETRIEVER_API_KEY")
RETRIEVER_ID = os.getenv("RETRIEVER_ID")


headers = {
    "Authorization": f"Bearer {DENSER_RETRIEVER_API_KEY}",
    "content-type": "application/json",
}

json_data = {
    "query": "How do I get the number of tokens used by the LLM, along with the completion?",
    "id": RETRIEVER_ID,
    "k": 4,
}

response = requests.post(
    "https://retriever.denser.ai/api/retrievers/retrieve",
    headers=headers,
    json=json_data,
)

with open("test_denser_retriever_output.json", "w") as f:
    json.dump(
        {
            "user_query": json_data["query"],
            "denser_retriever_api_response": response.json(),
        },
        f,
        indent=4,
    )
