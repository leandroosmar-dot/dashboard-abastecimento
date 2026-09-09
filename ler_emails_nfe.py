"""
Script: ler_emails_nfe.py
Objetivo: conectar na caixa de e-mail (Outlook/M365), procurar mensagens com
XML de NFe anexado, baixar esses XMLs para uma pasta local e marcar as
mensagens já processadas (para não baixar a mesma nota duas vezes).

COMO USAR
---------
1. Preencha as variáveis EMAIL_USUARIO e EMAIL_SENHA abaixo (ou, melhor
   ainda, defina como variáveis de ambiente - veja a nota de segurança).
2. Rode: python3 ler_emails_nfe.py
3. Os XMLs baixados vão para a pasta ./notas_xml

SE DER ERRO DE AUTENTICAÇÃO (muito comum em contas M365 corporativas)
-----------------------------------------------------------------------
A Microsoft está desativando a "autenticação básica" (usuário + senha direto)
para IMAP em contas corporativas. Se aparecer erro tipo "AUTHENTICATE failed"
ou "basic auth is disabled", você tem duas saídas:
  a) Pedir para o administrador de TI da empresa habilitar IMAP com
     "Autenticação Básica" (ou SMTP AUTH) especificamente para essa caixa.
  b) (Caminho mais robusto e recomendado a médio prazo) Trocar esse script
     para usar a Microsoft Graph API com OAuth2, que é o método oficial e
     moderno de acessar e-mails do M365. Se quiser, eu monto essa versão
     depois - é um pouco mais trabalhosa de configurar (precisa registrar
     um "app" no Azure AD), mas é o caminho definitivo para produção.

SEGURANÇA
---------
Nunca deixe a senha escrita direto no código em um projeto real.
Prefira definir como variável de ambiente:
    export EMAIL_SENHA="sua_senha_aqui"
e trocar a linha abaixo para: EMAIL_SENHA = os.environ["EMAIL_SENHA"]
"""

import imaplib
import email
import os
from email.header import decode_header

# ============ CONFIGURAÇÃO ============
IMAP_SERVER = "outlook.office365.com"
IMAP_PORT = 993

EMAIL_USUARIO = os.environ.get("EMAIL_USUARIO", "leandro.osmar@portoex.com.br")
EMAIL_SENHA = os.environ.get("EMAIL_SENHA")

if not EMAIL_SENHA:
    print("ERRO: a senha não foi definida.")
    print("No cmd, antes de rodar este script, digite (troque pela sua senha nova):")
    print('    set EMAIL_SENHA=sua_senha_nova_aqui')
    print("Depois, sem fechar o cmd, rode de novo: python3 ler_emails_nfe.py")
    raise SystemExit(1)

PASTA_DESTINO = "notas_xml"          # onde os XMLs baixados serão salvos
ARQUIVO_PROCESSADOS = "processados.txt"  # guarda quais e-mails já foram baixados
# =======================================


def carregar_processados():
    """Lê a lista de IDs de e-mail já processados, para não baixar de novo."""
    if not os.path.exists(ARQUIVO_PROCESSADOS):
        return set()
    with open(ARQUIVO_PROCESSADOS, "r") as f:
        return set(linha.strip() for linha in f)


def marcar_como_processado(msg_id):
    with open(ARQUIVO_PROCESSADOS, "a") as f:
        f.write(msg_id + "\n")


def conectar_email():
    print(f"Conectando em {IMAP_SERVER}...")
    conn = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    conn.login(EMAIL_USUARIO, EMAIL_SENHA)
    print("Conectado com sucesso.")
    return conn


def baixar_xmls_anexados():
    os.makedirs(PASTA_DESTINO, exist_ok=True)
    processados = carregar_processados()

    conn = conectar_email()
    conn.select("INBOX")  # pode trocar por outra pasta, ex: "NotasFiscais"

    # Busca todos os e-mails (você pode trocar para buscar só os não lidos,
    # trocando 'ALL' por 'UNSEEN')
    status, dados = conn.search(None, "ALL")
    ids_emails = dados[0].split()

    print(f"{len(ids_emails)} e-mails encontrados na caixa. Verificando anexos...")

    novos = 0
    for eid in ids_emails:
        eid_str = eid.decode()
        if eid_str in processados:
            continue  # já processado antes, pula

        status, msg_data = conn.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        tem_xml = False
        for parte in msg.walk():
            nome_arquivo = parte.get_filename()
            if nome_arquivo:
                nome_decodificado = decode_header(nome_arquivo)[0][0]
                if isinstance(nome_decodificado, bytes):
                    nome_decodificado = nome_decodificado.decode(errors="ignore")

                if nome_decodificado.lower().endswith(".xml"):
                    caminho_salvar = os.path.join(PASTA_DESTINO, nome_decodificado)
                    with open(caminho_salvar, "wb") as f:
                        f.write(parte.get_payload(decode=True))
                    print(f"  [OK] Baixado: {nome_decodificado}")
                    tem_xml = True
                    novos += 1

        marcar_como_processado(eid_str)

    conn.logout()
    print(f"\nConcluído. {novos} novo(s) XML(s) baixado(s) em ./{PASTA_DESTINO}")


if __name__ == "__main__":
    baixar_xmls_anexados()
