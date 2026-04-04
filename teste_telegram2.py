import requests
import os

# Coloca os valores direto aqui para testar sem .env
TOKEN   = "8034041185:AAG9QnslYrI5B9OObWM5MJBoQ1IxCLB5ClU"
CHAT_ID = "1177725958"

r = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json={"chat_id": CHAT_ID, "text": "✅ Teste direto funcionando!"}
)
print(r.status_code, r.json())