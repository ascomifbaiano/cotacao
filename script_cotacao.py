import os
import sys

# Captura a lista enviada pelo HTML via GitHub Actions
input_itens = os.getenv("LISTA_ITENS", "")
LISTA_DE_COMPRAS = [i.strip() for i in input_itens.split(",") if i.strip()]

if not LISTA_DE_COMPRAS:
    print("Nenhum item fornecido.")
    sys.exit(0)
