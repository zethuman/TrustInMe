from flask import Flask, request
import requests
from flask import Response
import bot
import json
import settings


app = Flask(__name__)

# TOKEN = settings.TOKEN

# https://api.telegram.org/bot1237617532:AAFWXqQsjg2DqA-jWg9QWnhOCT3fJ2ZDE3U/getMe
# https://api.telegram.org/bot1237617532:AAFWXqQsjg2DqA-jWg9QWnhOCT3fJ2ZDE3U/setWebhook?url=https://16020371.ngrok.io/

def write_json(data, filename='response.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def send_message(chat_id, text):
    method = "sendMessage"
    token = TOKEN
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)


@app.route('/', methods=['POST', 'GET'])
def receive_update():
    if request.method == "POST":
        print(request.json)
        chat_id = request.json["message"]["chat"]["id"]
        send_message(chat_id, "pong")
    return {"ok": True}


if __name__ == '__main__':
    app.run()
