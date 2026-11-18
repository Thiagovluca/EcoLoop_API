"""
API REST (Flask) do projeto EcoLoop - GS CitizenTech.

Disponibiliza os dois modelos treinados nos notebooks:
  - POST /prever/vazamento : classificação (risco de vazamento de água)
  - POST /prever/consumo   : regressão (consumo mensal de energia em kWh)
  - GET  /                 : página web para testar os modelos

Observação: os modelos foram treinados com dados FICTÍCIOS (sintéticos).
"""
import os
import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.json.ensure_ascii = False  # mostra acentos normalmente no JSON

# Caminho dos modelos (relativo a este arquivo, funciona local e no Render)
PASTA = os.path.dirname(os.path.abspath(__file__))
modelo_vazamento = joblib.load(os.path.join(PASTA, "modelos", "modelo_classificacao.pkl"))
modelo_consumo = joblib.load(os.path.join(PASTA, "modelos", "modelo_regressao.pkl"))

# Campos esperados por cada modelo, NA MESMA ORDEM do treino.
# Formato: nome do campo -> (valor mínimo, valor máximo, precisa ser inteiro?)
CAMPOS_VAZAMENTO = {
    "hora_do_dia": (0, 23, True),
    "dia_da_semana": (0, 6, True),
    "volume_consumido_na_ultima_hora": (0, 10000, False),
    "imovel_ocupado": (0, 1, True),
}

CAMPOS_CONSUMO = {
    "historico_consumo_mes_anterior": (0, 100000, False),
    "tamanho_imovel_m2": (1, 100000, False),
    "numero_pessoas": (1, 100, True),
    "temperatura_media_mensal": (-50, 60, False),
}


def validar_entrada(dados, campos):
    """Confere se o JSON tem todos os campos, com números válidos e dentro dos limites.
    Retorna (DataFrame com 1 linha, None) se estiver tudo certo, ou (None, mensagem de erro)."""
    if not isinstance(dados, dict):
        return None, "Envie um JSON (objeto) com os campos: " + ", ".join(campos)

    linha = {}
    for nome, (minimo, maximo, inteiro) in campos.items():
        if nome not in dados:
            return None, f"Campo obrigatório ausente: '{nome}'"

        valor = dados[nome]
        if isinstance(valor, bool):
            valor = int(valor)  # true/false vira 1/0
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            return None, f"O campo '{nome}' deve ser numérico"

        if valor < minimo or valor > maximo:
            return None, f"O campo '{nome}' deve estar entre {minimo} e {maximo}"
        if inteiro and valor != int(valor):
            return None, f"O campo '{nome}' deve ser um número inteiro"

        linha[nome] = int(valor) if inteiro else valor

    # DataFrame com as colunas na ordem do treino
    return pd.DataFrame([linha], columns=list(campos)), None


@app.route("/", methods=["GET"])
def pagina_inicial():
    """Página web simples para testar os dois modelos pelo navegador."""
    return render_template("index.html")


@app.route("/api", methods=["GET"])
def info_api():
    return jsonify({
        "projeto": "EcoLoop - GS CitizenTech",
        "descricao": "API de IA para reduzir o desperdício de água e energia",
        "aviso": "Modelos treinados com dados fictícios (sintéticos)",
        "endpoints": {
            "GET /saude": "verifica se a API está no ar",
            "POST /prever/vazamento": {"campos": list(CAMPOS_VAZAMENTO)},
            "POST /prever/consumo": {"campos": list(CAMPOS_CONSUMO)},
        },
    })


@app.route("/saude", methods=["GET"])
def saude():
    return jsonify({"status": "ok"})


@app.route("/prever/vazamento", methods=["POST"])
def prever_vazamento():
    dados = request.get_json(silent=True)
    entrada, erro = validar_entrada(dados, CAMPOS_VAZAMENTO)
    if erro:
        return jsonify({"erro": erro}), 400

    classe = int(modelo_vazamento.predict(entrada)[0])
    probabilidade = float(modelo_vazamento.predict_proba(entrada)[0][1])

    if classe == 1:
        mensagem = "ALERTA: risco de vazamento de água"
    else:
        mensagem = "Consumo dentro do esperado"

    return jsonify({
        "houve_vazamento": classe,
        "probabilidade_vazamento": round(probabilidade, 4),
        "mensagem": mensagem,
    })


@app.route("/prever/consumo", methods=["POST"])
def prever_consumo():
    dados = request.get_json(silent=True)
    entrada, erro = validar_entrada(dados, CAMPOS_CONSUMO)
    if erro:
        return jsonify({"erro": erro}), 400

    previsao = float(modelo_consumo.predict(entrada)[0])

    return jsonify({
        "consumo_previsto_kwh": round(previsao, 2),
    })


if __name__ == "__main__":
    # Execução local. No Render quem inicia a API é o gunicorn (veja o README).
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=False)
