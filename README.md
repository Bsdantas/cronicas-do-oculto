# Crônicas do Oculto: Sombras de São Paulo

App de RPG em Streamlit ambientado no submundo sobrenatural de São Paulo.

## Recursos

- Criação de personagens Bruxos, Lobisomens e Vampiros.
- Ficha com atributos, 27 habilidades, poderes, vantagens e defeitos.
- Aventura com diálogos no estilo visual novel.
- Inventário de itens e pistas, códex de NPCs e diário de quests.
- Rolador de dados d10 e acompanhamento de recursos de cada natureza.

## Executar localmente

Com Python 3.11 ou superior instalado, abra um terminal na pasta do projeto:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

No macOS ou Linux, ative o ambiente com `source .venv/bin/activate`.

O app abre no navegador, normalmente em `http://localhost:8501`.

As informações da partida ficam na sessão do Streamlit. Não há armazenamento permanente de fichas ou progresso.

## Arquivos

- `app.py`: aplicação principal.
- `requirements.txt`: dependência para execução.

Os PDFs locais em `livros/` não são versionados nem necessários para executar o app.

Instruções de instalação e execução: [documentação oficial do Streamlit](https://docs.streamlit.io/get-started/installation/command-line).
