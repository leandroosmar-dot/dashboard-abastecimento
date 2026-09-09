"""
dashboard.py
Dashboard de abastecimento por placa: km rodado (dia/mês/ano) e média de
consumo (km/l) por placa (dia/mês/ano).

Como rodar localmente:
    pip install streamlit pandas plotly
    streamlit run dashboard.py

Como colocar online:
    1. Suba esta pasta inteira num repositório do GitHub.
    2. Entre em https://share.streamlit.io, conecte sua conta do GitHub.
    3. Escolha o repositório e o arquivo dashboard.py.
    4. Pronto — você recebe um link público (algo como
       https://seuapp.streamlit.app) que qualquer um pode acessar.

IMPORTANTE: o dashboard lê o arquivo base_abastecimentos.csv, gerado pelo
processar_notas.py. Ele PRECISA estar na mesma pasta (ou você adapta o
código para ler de um banco de dados online — veja nota no final do
projeto sobre isso).
"""

import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Dashboard de Abastecimento", layout="wide")

ARQUIVO_DADOS = "base_abastecimentos.csv"


@st.cache_data
def carregar_dados():
    df = pd.read_csv(ARQUIVO_DADOS, parse_dates=["data_emissao", "dia"])
    return df


st.title("🚛 Dashboard de Abastecimento por Placa")

try:
    df = carregar_dados()
except FileNotFoundError:
    st.error(
        f"Não encontrei o arquivo {ARQUIVO_DADOS}. "
        "Rode ler_emails_nfe.py e depois processar_notas.py antes de abrir o dashboard."
    )
    st.stop()

# ============ FILTROS (barra lateral) ============
st.sidebar.header("Filtros")

placas_disponiveis = sorted(df["placa"].dropna().unique())
placas_selecionadas = st.sidebar.multiselect(
    "Placa(s)", placas_disponiveis, default=placas_disponiveis
)

periodo = st.sidebar.radio("Agrupar por", ["Dia", "Mês", "Ano"], index=1)

df_filtrado = df[df["placa"].isin(placas_selecionadas)] if placas_selecionadas else df

# Define a coluna de agrupamento conforme o período escolhido
if periodo == "Dia":
    df_filtrado["periodo"] = df_filtrado["dia"].dt.strftime("%d/%m/%Y")
elif periodo == "Mês":
    df_filtrado["periodo"] = df_filtrado["data_emissao"].dt.strftime("%m/%Y")
else:
    df_filtrado["periodo"] = df_filtrado["data_emissao"].dt.strftime("%Y")

# ============ MÉTRICAS GERAIS (topo) ============
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de abastecimentos", len(df_filtrado))
col2.metric("Km rodado total", f"{df_filtrado['km_rodado'].sum():,.0f} km")
col3.metric("Litros totais", f"{df_filtrado['litros'].sum():,.1f} L")
media_geral = df_filtrado["media_km_l"].mean()
col4.metric("Média geral (km/l)", f"{media_geral:,.2f}" if pd.notna(media_geral) else "—")

st.divider()

# ============ KM RODADO POR PERÍODO E PLACA ============
st.subheader(f"Km rodado por placa — agrupado por {periodo.lower()}")

km_por_periodo = (
    df_filtrado.groupby(["periodo", "placa"])["km_rodado"]
    .sum()
    .reset_index()
    .sort_values("periodo")
)

fig_km = px.bar(
    km_por_periodo, x="periodo", y="km_rodado", color="placa",
    barmode="group", labels={"km_rodado": "Km rodado", "periodo": periodo}
)
st.plotly_chart(fig_km, use_container_width=True)

# ============ MÉDIA DE CONSUMO POR PLACA ============
st.subheader(f"Média de consumo (km/l) por placa — agrupado por {periodo.lower()}")

media_por_periodo = (
    df_filtrado.groupby(["periodo", "placa"])["media_km_l"]
    .mean()
    .reset_index()
    .sort_values("periodo")
)

fig_media = px.line(
    media_por_periodo, x="periodo", y="media_km_l", color="placa",
    markers=True, labels={"media_km_l": "Média (km/l)", "periodo": periodo}
)
st.plotly_chart(fig_media, use_container_width=True)

# ============ TABELA DETALHADA ============
st.subheader("Notas detalhadas")
colunas_exibir = [
    "data_emissao", "placa", "motorista", "posto", "combustivel",
    "litros", "valor_total", "km_anterior", "km_atual", "km_rodado", "media_km_l",
]
st.dataframe(
    df_filtrado[colunas_exibir].sort_values("data_emissao", ascending=False),
    use_container_width=True,
)

# Aviso sobre notas sem placa reconhecida
sem_placa = df[df["placa"].isna()]
if len(sem_placa) > 0:
    st.warning(
        f"{len(sem_placa)} nota(s) não tiveram a placa reconhecida automaticamente "
        "(provavelmente de um posto com formato de texto diferente). "
        "Veja o arquivo de log do processar_notas.py."
    )
