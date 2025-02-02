from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
print(f"API Key: {os.getenv('OPENAI_API_KEY')}")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ])
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")