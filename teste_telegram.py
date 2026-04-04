import requests
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

print(f"Token: {token[:10]}..." if token else "Token: 8651484956:AAEXsVP14-TfoYYcK4lXraLZl7cF202gLXU!")
print(f"Chat ID: {chat_id}" if chat_id else "Chat ID: 1177725958!")

url = f"https://api.telegram.org/bot{token}/sendMessage"
r = requests.post(url, json={"chat_id": chat_id, "text": "✅ Teste do bot funcionando!"})
print(f"Status: {r.status_code}")
print(f"Resposta: {r.json()}")

