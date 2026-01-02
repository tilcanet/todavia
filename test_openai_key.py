import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
print(f"Key loaded (len={len(api_key) if api_key else 0})")

if not api_key:
    print("API Key is missing/empty")
    exit(1)

try:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hola"}],
        max_tokens=5
    )
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("Error:", e)
