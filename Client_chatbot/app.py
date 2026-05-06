from flask import Flask, request, jsonify
import requests
import os
import time
from threading import Thread

app = Flask(__name__)

ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
CLIENT_TOKEN = os.getenv("CLIENT_TOKEN")

TEMPO_ENCERRAMENTO = 180  # 3 minutos
conversas = {}

# Número da psicóloga (quem atende manualmente)
NUMERO_PSICOLOGA = os.getenv("NUMERO_PSICOLOGA")  # ex: 5531985061117


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


def monitorar_inatividade():
    while True:
        agora = time.time()
        for numero, dados in list(conversas.items()):
            tempo_parado = agora - dados["ultima_mensagem"]
            if tempo_parado >= TEMPO_ENCERRAMENTO and not dados["encerrado"]:
                enviar_whatsapp(
                    numero,
                    "Como não houve novas mensagens, este atendimento foi encerrado automaticamente. "
                    "Para começar novamente, digite MENU."
                )
                conversas[numero]["encerrado"] = True
                conversas[numero]["modo_humano"] = False  # reseta ao encerrar
        time.sleep(10)


Thread(target=monitorar_inatividade, daemon=True).start()


@app.route("/", methods=["GET"])
def home():
    return "Bot online!"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("WEBHOOK Z-API:", data)

    numero_remetente = data.get("phone")
    from_me = data.get("fromMe", False)  # True = mensagem enviada pela psicóloga
    mensagem = data.get("text", {}).get("message", "").lower().strip()

    # ── Mensagem enviada PELA psicóloga (atendimento humano) ──
    if from_me and numero_remetente:
        if numero_remetente not in conversas:
            conversas[numero_remetente] = {
                "ultima_mensagem": time.time(),
                "encerrado": False,
                "modo_humano": False
            }
        # Ativa modo humano e atualiza tempo
        conversas[numero_remetente]["modo_humano"] = True
        conversas[numero_remetente]["ultima_mensagem"] = time.time()
        conversas[numero_remetente]["encerrado"] = False
        print(f"Modo humano ATIVADO para {numero_remetente}")
        return jsonify({"status": "modo humano ativo"})

    # ── Mensagem recebida DO cliente ──
    if numero_remetente:
        if numero_remetente not in conversas:
            conversas[numero_remetente] = {
                "ultima_mensagem": time.time(),
                "encerrado": False,
                "modo_humano": False
            }

        conversas[numero_remetente]["ultima_mensagem"] = time.time()

        # Se estiver em modo humano, bot fica silencioso
        if conversas[numero_remetente].get("modo_humano"):
            print(f"Modo humano ativo — bot silencioso para {numero_remetente}")
            return jsonify({"status": "modo humano — bot silencioso"})

        # Se conversa foi encerrada, reseta
        if conversas[numero_remetente].get("encerrado"):
            conversas[numero_remetente]["encerrado"] = False
            conversas[numero_remetente]["modo_humano"] = False

    # ── Respostas automáticas do bot ──
    if mensagem in ["oi", "olá", "ola", "menu", "bom dia", "boa tarde", "boa noite"]:
        resposta = """Olá, bem vindo! 👋
Esse contato é da Psicóloga Lilian Félix.
Como posso ajudar?

Digite uma opção:

1 - Horário de atendimento
2 - Informações sobre a sessão
3 - Valor da sessão
4 - Falar com a/o Psicóloga(o)
5 - Agendar sessão
6 - Outros assuntos"""

    elif mensagem == "1":
        resposta = "Nosso horário de atendimento é de segunda a sexta, das 9h às 17h."

    elif mensagem == "2":
        resposta = "O atendimento é apenas online. Cada sessão tem duração de 45 minutos."

    elif mensagem == "3":
        resposta = "O valor da sessão é R$ 300,00."

    elif mensagem == "4":
        resposta = "Certo! Deixe sua mensagem e responderei assim que possível."
        # Ativa modo humano após opção 4
        if numero_remetente:
            conversas[numero_remetente]["modo_humano"] = True

    elif mensagem == "5":
        resposta = "OK! Informe sua disponibilidade que verificarei a agenda e entrarei em contato."

    elif mensagem == "6":
        resposta = "OK! Informe o assunto que deseja tratar que entrarei em contato."

    else:
        resposta = "Não entendi sua mensagem 😅\n\nDigite MENU para ver as opções disponíveis."

    if numero_remetente:
        enviar_whatsapp(numero_remetente, resposta)

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
