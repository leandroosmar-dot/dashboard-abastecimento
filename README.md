# Dashboard de Abastecimento por Placa

Lê automaticamente as notas fiscais (XML) de abastecimento que chegam por
e-mail, extrai placa, motorista, km e média de consumo, e mostra tudo num
dashboard online: km rodado (dia/mês/ano) e média de consumo por placa.

## Como o projeto funciona (fluxo)

```
E-mail (Outlook/M365)
      │  ler_emails_nfe.py  (baixa os XMLs anexados)
      ▼
notas_xml/*.xml
      │  processar_notas.py  (extrai os dados de cada nota)
      ▼
base_abastecimentos.csv
      │  dashboard.py  (Streamlit)
      ▼
Dashboard online
```

## Arquivos do projeto

- `ler_emails_nfe.py` — conecta no e-mail e baixa os XMLs anexados
- `extrator.py` — lê um XML e extrai placa, motorista, km, média etc.
- `processar_notas.py` — processa todos os XMLs baixados e monta a base de dados (CSV)
- `dashboard.py` — o dashboard (Streamlit)
- `requirements.txt` — lista de bibliotecas necessárias

## Passo a passo para rodar na sua máquina

1. Instale o Python (https://python.org) se ainda não tiver.
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Abra `ler_emails_nfe.py` e preencha seu e-mail e senha (de preferência
   usando variável de ambiente — veja o comentário no topo do arquivo).
4. Rode, nesta ordem:
   ```
   python3 ler_emails_nfe.py
   python3 processar_notas.py
   streamlit run dashboard.py
   ```
5. Uma aba do navegador vai abrir com o dashboard, em `http://localhost:8501`.

## Como subir no GitHub

1. Crie um repositório novo no GitHub (pode ser privado, já que lida com
   dados da empresa).
2. **Antes de subir, remova a senha do código** — deixe só o placeholder,
   como já está no `ler_emails_nfe.py` enviado.
3. Crie um arquivo `.gitignore` com este conteúdo, para nunca subir dados
   sensíveis ou temporários sem querer:
   ```
   notas_xml/
   base_abastecimentos.csv
   processados.txt
   __pycache__/
   ```
4. Suba os arquivos:
   ```
   git init
   git add .
   git commit -m "Primeira versão do dashboard de abastecimento"
   git remote add origin <link_do_seu_repositorio>
   git push -u origin main
   ```

## Como colocar o dashboard online (Streamlit Community Cloud)

1. Acesse https://share.streamlit.io e entre com sua conta do GitHub.
2. Clique em "New app", escolha o repositório e o arquivo `dashboard.py`.
3. Clique em "Deploy" — em alguns minutos você recebe um link público
   (algo como `https://seuapp.streamlit.app`).

**Atenção com um ponto importante:** o dashboard online lê o arquivo
`base_abastecimentos.csv`. Como esse arquivo foi colocado no `.gitignore`
(por conter dados da empresa), ele **não vai existir automaticamente** no
GitHub. Você tem duas opções:

- **Mais simples (para começar):** remova `base_abastecimentos.csv` do
  `.gitignore` e suba/atualize esse arquivo manualmente no GitHub sempre
  que quiser atualizar o dashboard (rodando o processamento local e
  commitando o CSV atualizado).
- **Mais robusta (automação de verdade):** trocar o CSV por um banco de
  dados na nuvem (ex: Supabase ou Postgres gratuito), que o
  `processar_notas.py` atualiza automaticamente rodando num servidor com
  agendamento (cron), e o `dashboard.py` lê direto da internet, sempre
  atualizado, sem precisar mexer no GitHub toda vez. Posso te ajudar a
  montar essa versão depois que a versão simples estiver funcionando.

## Próximos passos sugeridos

- Testar com mais notas de postos diferentes e ajustar `extrator.py` se
  algum posto não for reconhecido (o script avisa quando isso acontece).
- Automatizar a leitura de e-mail com agendamento (cron), em vez de rodar
  manualmente.
- Migrar do CSV para um banco de dados na nuvem, para o dashboard ficar
  sempre atualizado sozinho.
