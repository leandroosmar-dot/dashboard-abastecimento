"""
processar_notas.py
Varre a pasta de XMLs baixados (notas_xml/), extrai os dados de cada nota
usando o extrator.py, e salva tudo consolidado em base_abastecimentos.csv.
"""

import os
import glob
import pandas as pd
from extrator import extrair_dados_nfe

PASTA_XML = "notas_xml"
ARQUIVO_SAIDA = "base_abastecimentos.csv"

PLACAS_EXCLUIDAS = {"HWP5C65", "FRP3J31", "LXV8E52", "HBN8A85"}


def processar():
    arquivos = glob.glob(os.path.join(PASTA_XML, "*.xml"))
    if not arquivos:
        print(f"Nenhum XML encontrado em ./{PASTA_XML}.")
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

    # IMPORTANTE: format="mixed" evita que o pandas "trave" num unico
    # formato de data inferido da primeira linha e descarte (NaT) linhas
    # com formato ligeiramente diferente (ex: "T" vs espaco separando
    # data e hora), o que zerava a data de notas novas silenciosamente.
    df["data_emissao"] = pd.to_datetime(df["data_emissao"], errors="coerce", utc=True, format="mixed")
    df["ano"] = df["data_emissao"].dt.year
    df["mes"] = df["data_emissao"].dt.month
    df["dia"] = df["data_emissao"].dt.date

    df = df.drop_duplicates(subset=["arquivo"])

    duplicadas = df[df.get("duplicado", False) == True]
    if len(duplicadas) > 0:
        print(f"\n{len(duplicadas)} nota(s) ignorada(s) por serem resumo duplicado de outra nota:")
        for a in duplicadas["arquivo"]:
            print(f"  - {a}")
    df = df[df.get("duplicado", False) != True].drop(columns=["duplicado"], errors="ignore")

    sem_litros = df[df["litros"].isna() | (df["litros"] == 0)]
    if len(sem_litros) > 0:
        print(f"\n{len(sem_litros)} nota(s) ignorada(s) por nao terem litros de combustivel:")
        for a in sem_litros["arquivo"]:
            print(f"  - {a}")
    df = df[~(df["litros"].isna() | (df["litros"] == 0))]

    df = df[~df["placa"].isin(PLACAS_EXCLUIDAS)]

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

    sem_placa = df[df["placa"].isna()]
    if len(sem_placa) > 0:
        print(f"\nAtencao: {len(sem_placa)} nota(s) sem placa identificada.")


if __name__ == "__main__":
    processar()
