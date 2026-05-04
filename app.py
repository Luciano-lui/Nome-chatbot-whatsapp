from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
CLIENT_TOKEN = os.getenv("CLIENT_TOKEN")


def enviar_whatsapp(numero, mensagem):
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"

    headers = {
        "Client-Token": CLIENT_TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "phone": numero,
        "message": mensagem
    }

    requests.post(url, json=payload, headers=headers)


@app.route("/", methods=["GET"])
def home():
    return "Bot online!"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    numero = data.get("phone")
    mensagem = data.get("text", {}).get("message", "").lower().strip()

    if mensagem in ["oi", "olá", "ola", "menu", "bom dia", "boa tarde", "boa noite"]:
        resposta = """
Olá! 👋
Como posso ajudar?

Digite uma opção:

1 - Horário de atendimento
2 - Endereço
3 - Preços
4 - Falar com atendente
"""

    elif mensagem == "1":
        resposta = "Nosso horário de atendimento é de segunda a sexta, das 8h às 18h."

    elif mensagem == "2":
        resposta = "Nosso endereço é: Rua Exemplo, 123 - Centro."

    elif mensagem == "3":
        resposta = "Nossos preços começam a partir de R$ 50,00."

    elif mensagem == "4":
        resposta = "Certo! Um atendente vai te chamar em breve."

    else:
        resposta = """
Não entendi sua mensagem 😅

Digite MENU para ver as opções disponíveis.
"""

    if numero:
        enviar_whatsapp(numero, resposta)

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)