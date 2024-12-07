from flask import Flask, jsonify, request, send_file
import random
import time
import manager
import payment
import requests
import base64
import hashlib
import os
from multiprocessing import Process
from registro import main


app = Flask(__name__)

dashboard_data = {
    "botsActive": 0,
    "usersCount": 0,
    "salesCount": 0
}

debug = True

@app.route('/', methods=['GET'])
def home():
    """
    Retorna os dados do dashboard.
    """
    # Simulação de alterações dinâmicas nos dados
    dashboard_data['botsActive'] = len(manager.get_all_active_bots())
    dashboard_data['usersCount'] = '?'
    dashboard_data['salesCount'] = len(manager.get_payments_by_status('paid'))
    return send_file('./templates/terminal.html')




@app.route('/dashboard-data', methods=['GET'])
def get_dashboard_data():
    dashboard_data['botsActive'] = len(manager.get_all_active_bots())
    dashboard_data['usersCount'] = '?'
    dashboard_data['salesCount'] = len(manager.get_payments_by_status('paid'))
    return jsonify(dashboard_data)



@app.route('/terminal', methods=['POST'])
def terminal():
    """
    Processa comandos enviados pelo terminal.
    """
    data = request.get_json()
    command = data.get('command', '').strip()
    if not command:
        return jsonify({"response": "Comando vazio. Digite algo para enviar."}), 400

    # Simulação de resposta ao comando
    response = f"Comando '{command}' recebido com sucesso. Processado às {time.strftime('%H:%M:%S')}."
    return jsonify({"response": response})


@app.route('/webhook/pp/<bot_id>/<chat_id>', methods=['POST'])
def webhook(bot_id, chat_id):
    if request.content_type == 'application/json':
        data = request.get_json()
    elif request.content_type == 'application/x-www-form-urlencoded':
        data = request.form.to_dict()
    else:
        print("[ERRO] Tipo de conteúdo não suportado")  # Log de erro para tipo de conteúdo não suportado
        return jsonify({"error": "Unsupported Media Type"}), 415

    if not data:
        print("[ERRO] Dados JSON ou Form Data inválidos")  # Log de erro para dados inválidos
        return jsonify({"error": "Invalid JSON or Form Data"}), 400
    print(f"[DEBUG] Webhook recebido: {data}")  # Log para verificar dados do webhook
    transaction_id = data.get("id").lower()
    # Carrega o mapeamento de pagamentos do bot específico
    bot = manager.get_bot_by_id(bot_id)
    # Verifica o status do pagamento
    if data.get('status', '').lower() == 'paid':
        print(transaction_id + ' Pago')
        manager.update_payment_status(transaction_id, 'paid')
    else:
        print("[ERRO] Status do pagamento não é 'paid'")  # Log para status diferente de "paid"

    return jsonify({"status": "success"})
keys = {}


@app.route('/key', methods=['GET'])
def get_key():
    bot_id = request.args.get('bot_id')
    key = request.args.get('key')
    if key and bot_id:
        keys[bot_id] = key
        return 'Chave recebida', 200
    else:
        return 'Chave incompleta', 400

@app.route('/callback', methods=['GET'])
def callback():
    """
    Endpoint para receber o webhook de redirecionamento do Mercado Pago.
    """
    # Obter o authorization_code da query string
    TOKEN_URL = "https://api.mercadopago.com/oauth/token"

    authorization_code = request.args.get('code')
    bot_id = request.args.get('state')

    if not authorization_code:
        return jsonify({"error": "Authorization code not provided"}), 400

    try:
        # Dados para a troca de tokens
        
        payload = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": authorization_code,
            "redirect_uri": IP_DA_VPS+'/callback',  # A mesma configurada no Mercado Pago
            "state":bot_id,
            "code_verifier":keys[bot_id]
        }
        
        # Fazer a requisição para obter o token
        response = requests.post(TOKEN_URL, data=payload)
        response_data = response.json()

        if response.status_code == 200:
            # Sucesso - Retorna o access token
            access_token = response_data.get("access_token")
            print(access_token)
            manager.update_bot_payment(bot_id, {'type':"MP", 'token':access_token})
            return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Token Cadastrado</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: #333;
        }
        .container {
            background-color: #fff;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 20px 30px;
            text-align: center;
            max-width: 400px;
        }
        .container h1 {
            color: #4caf50;
            font-size: 24px;
            margin-bottom: 10px;
        }
        .container p {
            font-size: 16px;
            margin-bottom: 20px;
        }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            font-size: 14px;
            color: #fff;
            background-color: #4caf50;
            text-decoration: none;
            border-radius: 4px;
            transition: background-color 0.3s ease;
        }
        .btn:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Token Cadastrado com Sucesso!</h1>
        <p>O seu token Mercado Pago está pronto para uso.</p>
      
    </div>
</body>
</html>
"""
        else:
            # Erro na troca de tokens
            return jsonify({"error": response_data}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


CLIENT_ID = "4160833868783446"
CLIENT_SECRET = "GODqR68FqsUOL7JcurhKrNAScjqZ9GVa"
IP_DA_VPS = 'http://54.255.240.75/'


if __name__ == '__main__':


    app.run(debug=True, host='0.0.0.0', port=4040)



#DEV BY <GL>