from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

META_TOKEN = os.getenv("META_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "psi_chatbot_123")


def enviar_whatsapp(numero, mensagem):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": mensagem}
    }

    response = requests.post(url, headers=headers, json=payload, timeout=15)
    print("ENVIO META:", response.status_code, response.text)


@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    verify_token = os.getenv("VERIFY_TOKEN", "psi_chatbot_123")

    if mode == "subscribe" and token == verify_token:
        return challenge, 200

    return "Token inválido", 403


@app.route("/webhook", methods=["POST"])
def receber_mensagem():
    data = request.json
    print("WEBHOOK META:", data)

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return jsonify({"status": "sem mensagem"}), 200

        mensagem = value["messages"][0]
        numero = mensagem["from"]

        texto = ""
        if mensagem.get("type") == "text":
            texto = mensagem["text"]["body"].lower().strip()

        if texto in ["oi", "olá", "ola", "menu", "bom dia", "boa tarde", "boa noite"]:
            resposta = """Olá! 👋
Como posso ajudar?

Digite uma opção:

1 - Horário de atendimento
2 - Informações sobre a sessão
3 - Valor da sessão
4 - Falar com a/o Psicóloga(o)
5 - Agendar sessão
6 - Outros assuntos"""
        elif texto == "1":
            resposta = "Nosso horário de atendimento é de segunda a sexta, das 9h às 17h."
        elif texto == "2":
            resposta = "O atendimento é apenas online. Cada sessão tem duração de 45 minutos."
        elif texto == "3":
            resposta = "O valor da sessão é R$ 300,00."
        elif texto == "4":
            resposta = "Certo! A/o Psicóloga(o) vai te chamar em breve."
        elif texto == "5":
            resposta = "Ok! Informe sua disponibilidade que verificarei a agenda e entrarei em contato."
        elif texto == "6":
            resposta = "Ok! Informe o assunto que deseja tratar que entrarei em contato."
        else:
            resposta = "Não entendi sua mensagem 😅\n\nDigite MENU para ver as opções disponíveis."

        enviar_whatsapp(numero, resposta)

    except Exception as e:
        print("ERRO WEBHOOK:", str(e))

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
