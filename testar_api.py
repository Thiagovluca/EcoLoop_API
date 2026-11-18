"""Testa a API (local ou no Render) usando só a biblioteca padrão.
Uso:  python testar_api.py http://127.0.0.1:5000
      python testar_api.py https://SEU-APP.onrender.com
"""
import json
import sys
import urllib.error
import urllib.request

url_base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:5000"


def chamar(caminho, dados=None):
    corpo = json.dumps(dados).encode("utf-8") if dados is not None else None
    req = urllib.request.Request(url_base + caminho, data=corpo,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as erro:
        return erro.code, json.loads(erro.read())


print("GET /saude ->", chamar("/saude"))
print("Vazamento (madrugada, imóvel vazio, 120 L) ->", chamar("/prever/vazamento", {
    "hora_do_dia": 3, "dia_da_semana": 2,
    "volume_consumido_na_ultima_hora": 120, "imovel_ocupado": 0}))
print("Vazamento (tarde, imóvel ocupado, 40 L) ->", chamar("/prever/vazamento", {
    "hora_do_dia": 15, "dia_da_semana": 2,
    "volume_consumido_na_ultima_hora": 40, "imovel_ocupado": 1}))
print("Consumo ->", chamar("/prever/consumo", {
    "historico_consumo_mes_anterior": 150, "tamanho_imovel_m2": 80,
    "numero_pessoas": 3, "temperatura_media_mensal": 25}))
print("Erro esperado (campo faltando) ->", chamar("/prever/consumo", {"tamanho_imovel_m2": 80}))
