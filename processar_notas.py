"""
processar_notas.py
Varre a pasta de XMLs baixados (notas_xml/), extrai os dados de cada nota
usando o extrator.py, e salva tudo consolidado em base_abastecimentos.csv.

Rode este script depois de ler_emails_nfe.py, sempre que quiser atualizar
os dados do dashboard.
"""

import os
import glob
import pandas as pd
from extrator import extrair_dados_nfe

PASTA_XML = "notas_xml"
ARQUIVO_SAIDA = "base_abastecimentos.csv"


def processar():
    arquivos = glob.glob(os.path.join(PASTA_XML, "*.xml"))
    if not arquivos:
        print(f"Nenhum XML encontrado em ./{PASTA_XML}. Rode ler_emails_nfe.py primeiro.")
        return

    print(f"Processando {len(arquivos)} arquivo(s) XML...")
    linhas = []
    erros = 0
    for caminho in arquivos:
        try:
            dados = extrair_dados_nfe(caminho)
            linhas.append(dados)
        except Exception as e:
            print(f"  [ERRO] Falha ao processar {caminho}: {e}")
            erros += 1

    if not linhas:
        print("Nenhuma nota processada com sucesso.")
        return

    df = pd.DataFrame(linhas)

    # Converte a data para tipo data de verdade e cria colunas dia/mes/ano
    df["data_emissao"] = pd.to_datetime(df["data_emissao"], errors="coerce", utc=True)
    df["ano"] = df["data_emissao"].dt.year
    df["mes"] = df["data_emissao"].dt.month
    df["dia"] = df["data_emissao"].dt.date

    # Remove duplicatas (caso o mesmo XML seja processado mais de uma vez)
    df = df.drop_duplicates(subset=["arquivo"])

    # --- Recalcula km_rodado e media a partir do historico de cada placa ---
    # Em vez de confiar no "km anterior" / "media" que cada posto escreve (e
    # que muitos nem informam), calculamos comparando com o abastecimento
    # anterior da MESMA placa nesta nossa propria base. Isso funciona igual
    # para qualquer posto, independente do formato de texto dele.
    df = df.sort_values(["placa", "data_emissao"]).reset_index(drop=True)

    km_rodado_calc = []
    media_calc = []
    for placa, grupo in df.groupby("placa", dropna=False):
        km_anterior_calc = None
        for idx in grupo.index:
            km_atual = df.at[idx, "km_atual"]
            litros = df.at[idx, "litros"]

            if km_atual is not None and pd.notna(km_atual) and km_anterior_calc is not None:
                rodado = km_atual - km_anterior_calc
            elif pd.notna(df.at[idx, "km_anterior"]) and km_atual is not None and pd.notna(km_atual):
                # Primeiro abastecimento dessa placa na nossa base: usa o
                # "km anterior" do proprio posto, se ele informou.
                rodado = km_atual - df.at[idx, "km_anterior"]
            else:
                rodado = None

            km_rodado_calc.append((idx, rodado))
            if rodado is not None and litros and pd.notna(litros) and litros > 0:
                media_calc.append((idx, rodado / litros))
            else:
                media_calc.append((idx, None))

            if km_atual is not None and pd.notna(km_atual):
                km_anterior_calc = km_atual

    km_map = dict(km_rodado_calc)
    media_map = dict(media_calc)
    df["km_rodado"] = df.index.map(km_map)
    df["media_km_l"] = df.index.map(media_map)

    df.to_csv(ARQUIVO_SAIDA, index=False)
    print(f"Base salva em {ARQUIVO_SAIDA} — {len(df)} nota(s), {erros} erro(s).")

    # Aviso sobre notas sem placa/km reconhecidos, para você revisar o padrão
    sem_placa = df[df["placa"].isna()]
    if len(sem_placa) > 0:
        print(f"\nAtenção: {len(sem_placa)} nota(s) sem placa identificada. Arquivos:")
        for a in sem_placa["arquivo"]:
            print(f"  - {a}")


if __name__ == "__main__":
    processar()
