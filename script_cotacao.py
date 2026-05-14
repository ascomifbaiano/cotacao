import os
import sys
import requests
import json
import numpy as np
from weasyprint import HTML

# Captura os itens enviados pelo GitHub Actions
input_itens = os.getenv("LISTA_ITENS", "")
LISTA_DE_COMPRAS = [i.strip() for i in input_itens.split(",") if i.strip()]

if not LISTA_DE_COMPRAS:
    print("Nenhum item fornecido para cotação.")
    sys.exit(0)

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

BASE_CNPJ = {
    "magazineluiza.com.br": "47.960.950/0001-21",
    "mercadolivre.com.br": "03.361.252/0001-34",
    "kabum.com.br": "05.570.714/0001-59",
    "amazon.com.br": "15.436.940/0001-03",
    "fastshop.com.br": "43.708.379/0001-10",
    "casasbahia.com.br": "33.041.260/0652-90"
}

def extrair_dominio(url):
    try:
        from urllib.parse import urlparse
    except ImportError:
        from urlparse import urlparse
    parsed_uri = urlparse(url)
    return '{uri.netloc}'.format(uri=parsed_uri).replace('www.', '')

def buscar_precos_serper(produto):
    url = "https://google.serper.dev/shopping"
    payload = json.dumps({"q": produto, "gl": "br", "hl": "pt-br"})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=payload)
        return response.json().get("shopping", [])
    except Exception as e:
        print(f"Erro ao buscar {produto}: {e}")
        return []

dados_relatorio = []

for item in LISTA_DE_COMPRAS:
    print(f"Pesquisando: {item}...")
    ofertas = buscar_precos_serper(item)
    
    lojas_vistas = set()
    ofertas_filtradas = []
    
    for of in ofertas:
        link_direto = of.get("link")
        dominio = extrair_dominio(link_direto)
        
        if dominio not in lojas_vistas:
            lojas_vistas.add(dominio)
            preco_raw = of.get("price", "0").replace("R$", "").replace(".", "").replace(",", ".").strip()
            
            try:
                preco_float = float(preco_raw)
            except ValueError:
                continue
                
            cnpj = BASE_CNPJ.get(dominio, "Verificar no site")
            
            ofertas_filtradas.append({
                "loja": of.get("merchant", dominio),
                "cnpj": cnpj,
                "link": link_direto,
                "preco_texto": f"R$ {preco_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "preco_float": preco_float
            })
            
        if len(ofertas_filtradas) == 3:
            break
            
    if len(ofertas_filtradas) >= 1:
        precos = [o["preco_float"] for o in ofertas_filtradas]
        media_preco = np.mean(precos)
        
        dados_relatorio.append({
            "produto": item,
            "ofertas": ofertas_filtradas,
            "media": f"R$ {media_preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "menor": f"R$ {min(precos):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "maior": f"R$ {max(precos):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        })

# Gerar HTML
html_dinamico = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page { size: A4; margin: 18mm 15mm; }
        body { font-family: Arial, sans-serif; color: #2d3748; font-size: 10pt; }
        .header { background-color: #1a365d; color: white; padding: 15px; margin-bottom: 20px; border-radius: 4px; }
        .section { margin-bottom: 30px; border-left: 4px solid #2b6cb0; padding-left: 10px; page-break-inside: avoid; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th { background-color: #f7fafc; padding: 8px; text-align: left; border-bottom: 2px solid #cbd5e0; }
        td { padding: 8px; border-bottom: 1px solid #e2e8f0; }
        .summary { background-color: #ebf8ff; padding: 10px; text-align: right; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="header"><h2>Relatório de Cotação de Preços</h2></div>
"""

for item in dados_relatorio:
    html_dinamico += f"""
    <div class="section">
        <h3>{item['produto']}</h3>
        <table>
            <tr><th>Loja</th><th>CNPJ</th><th>Link</th><th>Preço</th></tr>
    """
    for of in item['ofertas']:
        html_dinamico += f"<tr><td><b>{of['loja']}</b></td><td>{of['cnpj']}</td><td><a href='{of['link']}' style='color:#2b6cb0;'>Acessar</a></td><td>{of['preco_texto']}</td></tr>"
    
    html_dinamico += f"""
        </table>
        <div class="summary">
            <b>Menor:</b> {item['menor']} | <b>Maior:</b> {item['maior']} | <b style="color:#2f855a;">Média Estimada: {item['media']}</b>
        </div>
    </div>
    """

html_dinamico += "</body></html>"

with open("relatorio_final.html", "w", encoding="utf-8") as f:
    f.write(html_dinamico)

HTML("relatorio_final.html").write_pdf("relatorio_final.pdf")
print("PDF gerado com sucesso!")
