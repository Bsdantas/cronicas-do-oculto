import streamlit as st
import random
import json
import os
import requests

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

SAVES_FILE = "save_game.json"
PASTA_LIVROS = "livros"

# ==============================================================================
# CARREGAMENTO AUTOMÁTICO DOS LIVROS (PDFs e TXTs)
# ==============================================================================
@st.cache_resource
def carregar_regras_dos_livros():
    texto_total = ""
    if os.path.exists(PASTA_LIVROS):
        for arquivo in os.listdir(PASTA_LIVROS):
            caminho = os.path.join(PASTA_LIVROS, arquivo)
            try:
                if arquivo.lower().endswith(".txt") or arquivo.lower().endswith(".md"):
                    with open(caminho, "r", encoding="utf-8") as f:
                        texto_total += f"\n--- FONTE: {arquivo} ---\n" + f.read()[:15000]
                elif arquivo.lower().endswith(".pdf") and pypdf:
                    leitor = pypdf.PdfReader(caminho)
                    texto_pdf = ""
                    for pag in leitor.pages[:20]:
                        extraido = pag.extract_text()
                        if extraido:
                            texto_pdf += extraido + "\n"
                    texto_total += f"\n--- FONTE: {arquivo} ---\n" + texto_pdf[:25000]
            except Exception as e:
                print(f"Erro ao ler {arquivo}: {e}")
    return texto_total

LORE_DOS_LIVROS = carregar_regras_dos_livros()

def carregar_todos_saves():
    if os.path.exists(SAVES_FILE):
        try:
            with open(SAVES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salvar_todos_saves(dados):
    with open(SAVES_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

st.set_page_config(
    page_title="Crônicas do Oculto: Sombras de SP",
    page_icon="🌘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS: MMO Dark & Visual Novel & OOC
st.markdown("""
    <style>
        .main { background-color: #0b0d11; color: #e6e6e6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        section[data-testid="stSidebar"] { background-color: #11141c; border-right: 1px solid #232936; }
        
        .mmo-card {
            background: linear-gradient(145deg, #161b26 0%, #1c152b 100%);
            border: 1px solid #4a286c;
            border-radius: 12px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 6px 20px rgba(0,0,0,0.6);
            transition: transform 0.2s;
            margin-bottom: 18px;
        }
        .mmo-card:hover { transform: translateY(-4px); border-color: #a855f7; }
        .mmo-avatar { width: 100px; height: 100px; border-radius: 50%; border: 3px solid #8b5cf6; margin-bottom: 10px; object-fit: cover; }
        
        .mmo-slot-empty {
            background-color: rgba(22, 27, 38, 0.4);
            border: 2px dashed #4b5563;
            border-radius: 12px;
            padding: 40px 20px;
            text-align: center;
            margin-bottom: 18px;
        }
        .mmo-plus { font-size: 2.8em; color: #9ca3af; margin-bottom: 8px; }
        
        /* Visual Novel */
        .vn-box {
            background: linear-gradient(135deg, #131722 0%, #1a1528 100%);
            border: 1px solid #4a286c;
            border-left: 5px solid #9d50e6;
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 18px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.6);
        }
        .vn-name { font-size: 1.2em; font-weight: bold; color: #d8b4fe; }
        .vn-action { font-style: italic; color: #a1a1aa; margin: 8px 0; }
        .vn-dialogue { font-size: 1.05em; color: #ffffff; line-height: 1.5; }
        .vn-prompt { color: #facc15; font-weight: bold; margin-top: 12px; text-transform: uppercase; font-size: 0.88em; }
        
        /* Card OOC (Off-Game) */
        .ooc-box {
            background-color: #171324;
            border: 1px dashed #c084fc;
            border-left: 4px solid #a855f7;
            border-radius: 8px;
            padding: 14px 18px;
            margin: 12px 0;
            color: #e2e8f0;
        }
        
        .roll-card {
            background-color: #171d29;
            border-left: 4px solid #60a5fa;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 12px 0;
        }
        .stButton>button { width: 100%; border-radius: 6px; background-color: #3b1d5a; color: white; border: 1px solid #8b5cf6; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

HAB_FISICAS = ["Armas Brancas", "Armas de Fogo", "Atletismo", "Briga", "Condução", "Furtividade", "Ladronagem", "Ofícios", "Sobrevivência"]
HAB_SOCIAIS = ["Empatia com Animais", "Empatia", "Etiqueta", "Intimidação", "Liderança", "Manha", "Performance", "Persuasão", "Subterfúgio"]
HAB_MENTAIS = ["Ciência", "Erudição", "Finanças", "Investigação", "Medicina", "Ocultismo", "Percepção", "Política", "Tecnologia"]
TODAS_HABILIDADES = HAB_FISICAS + HAB_SOCIAIS + HAB_MENTAIS
TODOS_ATRIBUTOS = ["Força", "Destreza", "Vigor", "Carisma", "Manipulação", "Autocontrole", "Inteligência", "Raciocínio", "Determinação"]

todos_saves = carregar_todos_saves()

if "id_ativo" not in st.session_state:
    st.session_state.id_ativo = None
if "modo_criacao" not in st.session_state:
    st.session_state.modo_criacao = False

# ==============================================================================
# MOTOR DE GERAÇÃO DE IMAGEM COM GEMINI
# ==============================================================================
def gerar_imagem_com_gemini(prompt_descricao):
    gemini_key = st.secrets.get("GEMINI_API_KEY", "")
    if not gemini_key or not genai:
        return None
    try:
        genai.configure(api_key=gemini_key)
        model = genai.ImageGenerationModel("imagen-3.0-generate-002")
        result = model.generate_images(
            prompt=f"Dark fantasy, gothic urban, World of Darkness style, São Paulo night, gritty cinematic portrait, 8k: {prompt_descricao}",
            number_of_images=1,
            aspect_ratio="1:1"
        )
        for img in result.images:
            return img._pil_image
    except Exception as e:
        print(f"Erro ao gerar imagem no Gemini: {e}")
        return None

# ==============================================================================
# MOTOR VENICE AI (SUPORTE A IN-GAME E OFF-GAME OOC)
# ==============================================================================
def narrar_acao_venice(comando_jogador, personagem, historico_recente):
    venice_key = st.secrets.get("VENICE_API_KEY", "")
    venice_url = st.secrets.get("VENICE_BASE_URL", "https://api.venice.ai/api/v1")
    
    if not venice_key:
        return {
            "tipo": "narrativa",
            "npc": "Mestre do Oculto",
            "acao": "Observa a garoa de São Paulo esperando a chave da Venice AI.",
            "fala": "A chave da Venice AI não foi configurada nos Secrets (.streamlit/secrets.toml). Configure-a para que a IA narre sua aventura!",
            "pergunta": "O que você faz?"
        }

    # Verifica se o jogador está falando em OFF-GAME (OOC:)
    eh_ooc = comando_jogador.strip().lower().startswith("ooc:") or comando_jogador.strip().lower().startswith("[ooc]")

    if eh_ooc:
        # Prompt exclusivo para responder dúvidas e regras
        prompt_sistema = f"""
Você é o Mestre/Narrador do RPG 'Crônicas do Oculto: Sombras de São Paulo'.
O jogador está falando FORA DO PERSONAGEM (Out of Character / OOC) para tirar dúvidas de regras, pedir informações sobre o que o personagem dele saberia, ou pedir esclarecimentos da cena.

REGRAS E LORE DOS LIVROS NA PASTA 'LIVROS':
{LORE_DOS_LIVROS[:9000]}

DADOS DO PERSONAGEM:
- Nome: {personagem['nome']} ({personagem['natureza']})
- Conceito: {personagem['conceito']}
- Atributos e Habilidades: {personagem['atributos']} | {personagem['habilidades']}

INSTRUÇÕES PARA RESPOSTA OOC:
1. Responda ESTRITAMENTE em formato JSON com 2 chaves:
   "tipo": "ooc"
   "fala": "Sua resposta direta, cordial e explicativa como Mestre, esclarecendo as regras do livro, o que os sentidos dele percebem ou sugerindo qual teste ele pode fazer."
2. Seja claro, prestativo e imparcial como um bom Mestre de mesa de RPG.
"""
    else:
        # Prompt normal de narrativa dramática
        prompt_sistema = f"""
Você é o Mestre do RPG 'Crônicas do Oculto: Sombras de São Paulo'.
Ambiente: Fantasia urbana sombria em São Paulo, dark romance, perigo noturno, vampiros, lobisomens, bruxaria e o Véu.

CONHECIMENTO DOS LIVROS DE REGRAS (PASTA LIVROS):
{LORE_DOS_LIVROS[:9000]}

PROTAGONISTA:
- Nome: {personagem['nome']} ({personagem['natureza']})
- Linhagem/Tradição: {personagem['tradic']}
- Bairro: {personagem['bairro']}
- Conceito: {personagem['conceito']}
- História: {personagem['historia']}

INSTRUÇÕES OBRIGATÓRIAS:
1. Responda ESTRITAMENTE em formato JSON com 4 chaves:
   "tipo": "narrativa",
   "npc": Nome do personagem falando (ou 'Narrador'),
   "acao": Descrição atmosférica da cena ou ação do NPC (estilo dark romance / mistério urbano),
   "fala": Diálogo do NPC ou a consequência direta do que aconteceu,
   "pergunta": Sempre termine com "O QUE VOCÊ FAZ?"
2. Jamais tome decisões pelo jogador. Respeite as regras dos livros da pasta 'livros'.
"""

    try:
        headers = {"Authorization": f"Bearer {venice_key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b",
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"{comando_jogador}"}
            ],
            "response_format": {"type": "json_object"}
        }
        r = requests.post(f"{venice_url}/chat/completions", headers=headers, json=payload, timeout=25)
        res_data = r.json()
        conteudo = json.loads(res_data["choices"][0]["message"]["content"])
        if eh_ooc:
            conteudo["tipo"] = "ooc"
            conteudo["pergunta_jogador"] = comando_jogador
        else:
            conteudo["tipo"] = "narrativa"
        return conteudo
    except Exception as e:
        return {
            "tipo": "narrativa",
            "npc": "Mestre (Aviso)",
            "acao": "As sombras da metrópole tremeluzem.",
            "fala": f"Erro de conexão com o narrador: {str(e)}",
            "pergunta": "O que você faz?"
        }

# ==============================================================================
# TELA 1: SELEÇÃO DE PERSONAGENS (ESTILO MMO)
# ==============================================================================
if st.session_state.id_ativo is None and not st.session_state.modo_criacao:
    st.title("Crônicas do Oculto 🌘")
    st.subheader("Seleção de Personagens • Sombras de São Paulo")
    
    if LORE_DOS_LIVROS:
        st.success(f"📚 Livros de regras carregados da pasta '{PASTA_LIVROS}' com sucesso!")

    cols = st.columns(3)
    slots = list(todos_saves.items())
    
    for idx, (char_id, dados_save) in enumerate(slots):
        p = dados_save["personagem"]
        with cols[idx % 3]:
            icone_esp = "🐺" if p['natureza'] == "Lobisomem" else ("🔮" if p['natureza'] == "Bruxo" else "🩸")
            avatar_url = p.get("avatar") or f"https://api.dicebear.com/7.x/bottts/svg?seed={p['nome']}"
            
            st.markdown(f"""
                <div class="mmo-card">
                    <img src="{avatar_url}" class="mmo-avatar"><br>
                    <strong style="font-size: 1.3em; color: #f3e8ff;">{p['nome']}</strong><br>
                    <span style="color: #c084fc; font-weight: bold;">{icone_esp} {p['natureza']}</span> • <small style="color: #94a3b8;">{p['bairro']}</small>
                    <p style="color: #9ca3af; font-size: 0.85em; margin-top: 6px;"><em>{p['conceito']}</em></p>
                </div>
            """, unsafe_allow_html=True)
            
            col_b1, col_b2 = st.columns([3, 1])
            with col_b1:
                if st.button(f"▶️ Jogar", key=f"play_{char_id}"):
                    st.session_state.id_ativo = char_id
                    st.rerun()
            with col_b2:
                if st.button("🗑️", key=f"del_{char_id}", help="Excluir"):
                    del todos_saves[char_id]
                    salvar_todos_saves(todos_saves)
                    st.rerun()

    proximo_slot = len(slots) % 3
    with cols[proximo_slot]:
        st.markdown("""
            <div class="mmo-slot-empty">
                <div class="mmo-plus">➕</div>
                <strong style="color: #e2e8f0; font-size: 1.1em;">Criar Personagem</strong><br>
                <small style="color: #94a3b8;">Bruxo, Lobisomem ou Vampiro</small>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Novo Slot", key="btn_novo_slot"):
            st.session_state.modo_criacao = True
            st.rerun()

# ==============================================================================
# TELA 2: CRIAÇÃO DE PERSONAGEM
# ==============================================================================
elif st.session_state.modo_criacao:
    st.title("Novo Personagem 🌘")
    if st.button("⬅️ Voltar ao Menu de Seleção"):
        st.session_state.modo_criacao = False
        st.rerun()

    natureza = st.radio("O que você vai ser?", ["Bruxo", "Lobisomem", "Vampiro"], horizontal=True)
    
    tab_id, tab_hab, tab_poder, tab_traits = st.tabs(["Identidade & Retrato", "Atributos & Habilidades", f"Poderes de {natureza}", "Moralidade & Vantagens"])
    
    with tab_id:
        c1, c2 = st.columns([2, 1])
        with c1:
            nome_p = st.text_input("Nome do Personagem:", value="Lucas Batista" if natureza=="Lobisomem" else "Victor Dornelles")
            conceito = st.text_input("Conceito / Profissão Mortal:", value="Motoboy e Protetor Noturno" if natureza=="Lobisomem" else "Investigador Ocultista")
            bairro = st.text_input("Bairro / Refúgio em SP:", value="Santana / ZN" if natureza=="Lobisomem" else "Bixiga / Bela Vista")
            if natureza == "Lobisomem":
                origem_lupina = st.selectbox("Raça de Origem:", ["Homídeo", "Metis", "Lupus"])
                auspicio = st.selectbox("Auspício:", ["Ahroun", "Galliard", "Philodox", "Theurge", "Ragabash"])
                tradic_sub = f"{origem_lupina} • {auspicio}"
            elif natureza == "Bruxo":
                tradic_sub = st.selectbox("Tradição Mágica:", ["Raízes Urbanas", "Círculo da Hera Antiga", "Filhos da Noite e do Sangue", "Ordem dos Elementos Livres", "Conclave dos Tecno-Arcanos"])
            else:
                tradic_sub = st.selectbox("Clã Vampírico:", ["Ventrue", "Toreador", "Tremere", "Brujah", "Nosferatu", "Gangrel", "Malkaviano"])
        
        with c2:
            st.markdown("**Retrato Canônico**")
            if st.button("🎨 Gerar com Gemini"):
                with st.spinner("Pintando..."):
                    desc = f"{natureza} chamado {nome_p}, {conceito}, habitante de {bairro} em SP."
                    img_gemini = gerar_imagem_com_gemini(desc)
                    if img_gemini:
                        st.session_state.avatar_gerado_temp = img_gemini
                        st.image(img_gemini)
            avatar_final = f"https://api.dicebear.com/7.x/bottts/svg?seed={nome_p}"
        
        historia = st.text_area("História e Origem:", value="Cresceu em São Paulo e descobriu o sobrenatural nas ruas da metrópole.")

    with tab_hab:
        st.markdown("### Atributos (1 a 5)")
        col_f, col_s, col_m = st.columns(3)
        with col_f:
            forca = st.slider("Força:", 1, 5, 4 if natureza=="Lobisomem" else 2)
            destreza = st.slider("Destreza:", 1, 5, 3)
            vigor = st.slider("Vigor:", 1, 5, 3)
        with col_s:
            carisma = st.slider("Carisma:", 1, 5, 2)
            manipulacao = st.slider("Manipulação:", 1, 5, 1 if natureza=="Lobisomem" else 3)
            autocontrole = st.slider("Autocontrole:", 1, 5, 2)
        with col_m:
            inteligencia = st.slider("Inteligência:", 1, 5, 2 if natureza=="Lobisomem" else 4)
            raciocinio = st.slider("Raciocínio:", 1, 5, 3)
            determinacao = st.slider("Determinação:", 1, 5, 2 if natureza=="Lobisomem" else 3)
        
        st.markdown("### Habilidades Principais")
        hab_dict = {}
        ch1, ch2, ch3 = st.columns(3)
        with ch1:
            for h in HAB_FISICAS:
                hab_dict[h] = st.number_input(f"{h}:", 0, 5, 3 if h in ["Briga", "Atletismo"] and natureza=="Lobisomem" else 0, key=f"cr_{h}")
        with ch2:
            for h in HAB_SOCIAIS:
                hab_dict[h] = st.number_input(f"{h}:", 0, 5, 2 if h == "Intimidação" and natureza=="Lobisomem" else 0, key=f"cr_{h}")
        with ch3:
            for h in HAB_MENTAIS:
                hab_dict[h] = st.number_input(f"{h}:", 0, 5, 2 if h in ["Percepção", "Ocultismo"] and natureza=="Lobisomem" else 0, key=f"cr_{h}")

    with tab_poder:
        especificos = {}
        if natureza == "Lobisomem":
            dons = st.text_area("Dons Iniciais (Alfa 0.9):", "Cura Feral III\nPredador Ágil II")
            especificos = {"furia": 1, "forma": "Humana (10m)", "dons": dons, "bloqueio_prata": False}
        elif natureza == "Bruxo":
            d_vit = st.slider("Vitalidade:", 0, 5, 3)
            d_cam = st.slider("Caminhos:", 0, 5, 2)
            especificos = {"potencia": 1, "folego_max": 26, "folego_atual": 26, "sobrecarga": 0, "dominios": {"Vitalidade": d_vit, "Caminhos": d_cam}}
        else:
            fome = st.slider("Fome:", 0, 5, 1)
            disc = st.text_input("Disciplinas:", "Potência 2, Fortitude 1")
            especificos = {"fome": fome, "disciplinas": disc}

    with tab_traits:
        conv1 = st.text_input("Convicção:", "Proteger aqueles que dependem de mim")
        pilar1 = st.text_input("Pilar Mortal:", "Irmã / Amigo de infância")
        vantagens_txt = st.text_area("Vantagens (7 pts):", "Recursos 2\nRefúgio 1\nAliados 2\nSono Leve 1\nContatos 1")
        defeitos_txt = st.text_area("Defeitos (2 pts):", "Segredo Perigoso 1\nTimidez 1")

    if st.button("💾 Salvar Personagem e Ir para a Campanha"):
        novo_id = f"char_{len(todos_saves) + 1}_{nome_p.lower().replace(' ', '_')}"
        dados_novo = {
            "personagem": {
                "nome": nome_p, "natureza": natureza, "conceito": conceito, "tradic": tradic_sub, "bairro": bairro, "historia": historia,
                "avatar": avatar_final,
                "atributos": {"Força": forca, "Destreza": destreza, "Vigor": vigor, "Carisma": carisma, "Manipulação": manipulacao, "Autocontrole": autocontrole, "Inteligência": inteligencia, "Raciocínio": raciocinio, "Determinação": determinacao},
                "habilidades": hab_dict, "vitalidade_max": vigor + 3, "dano_superficial": 0, "dano_agravado": 0, "vontade_max": autocontrole + determinacao, "vontade_superficial": 0,
                "humanidade": 7, "conviccoes": [(conv1, pilar1)], "vantagens": vantagens_txt, "defeitos": defeitos_txt, "especificos": especificos
            },
            "dialogos": [{
                "tipo": "narrativa", "npc": "Narrador",
                "acao": f"A noite cai úmida sobre {bairro}. Como um {natureza} ({conceito}), seus instintos percebem a cidade pulsar.",
                "fala": f"Bem-vindo à noite paulistana, {nome_p}. Um mistério recente colocou seus aliados em alerta contra violações do Véu.",
                "pergunta": "O que você faz?", "item_descoberto": None
            }],
            "inventario": [{"nome": "Pertence Pessoal", "tipo": "Item Inicial", "detalhe": "Um foco ou amuleto pessoal.", "icone": "💼"}],
            "npcs": {
                "Helena Viana": {"titulo": "Bibliotecária do Círculo da Hera", "afeto": 15, "personalidade": "Pragmática e reservada.", "segredos": ["Contatos com a corte da Bela Vista."]},
                "Lucas Batista": {"titulo": "Beta dos Trilhos", "afeto": 10, "personalidade": "Protetor territorial.", "segredos": ["Investiga caçadores de prata."]}
            }
        }
        todos_saves[novo_id] = dados_novo
        salvar_todos_saves(todos_saves)
        st.session_state.modo_criacao = False
        st.session_state.id_ativo = novo_id
        st.rerun()

# ==============================================================================
# TELA 3: EM JOGO (TELA DA CAMPANHA)
# ==============================================================================
else:
    char_id = st.session_state.id_ativo
    dados_jogo = todos_saves[char_id]
    p = dados_jogo["personagem"]
    esp = p["especificos"]

    # BARRA LATERAL
    with st.sidebar:
        st.subheader(f"🌘 {p['nome']}")
        st.caption(f"{p['natureza']} • {p['tradic']} • {p['bairro']}")
        
        if st.button("🚪 Menu de Personagens"):
            salvar_todos_saves(todos_saves)
            st.session_state.id_ativo = None
            st.rerun()

        st.markdown("---")
        feridos = p['dano_superficial'] + p['dano_agravado']
        st.write(f"**Vitalidade:** {p['vitalidade_max'] - feridos}/{p['vitalidade_max']}")
        st.progress(max(0.0, min(1.0, (p['vitalidade_max'] - feridos) / p['vitalidade_max'])))
        st.write(f"**Vontade:** {p['vontade_max'] - p['vontade_superficial']}/{p['vontade_max']}")

        if p["natureza"] == "Lobisomem":
            st.markdown("##### 🐺 Fúria")
            esp["forma"] = st.selectbox("Forma:", ["Humana (10m)", "Lupina (15m)", "Híbrida (10m, Garras +2)"], index=0)
            st.write(f"**Fúria:** {esp['furia']}/5")
            st.progress(esp['furia'] / 5.0)
            if st.button("⚡ Checar Fúria"):
                df = random.randint(1, 10)
                if df <= 5 and esp['furia'] < 5:
                    esp['furia'] += 1
                    st.warning(f"Dado {df}: Fúria aumentou para {esp['furia']}!")
                else:
                    st.success(f"Dado {df}: Fúria estável.")
                salvar_todos_saves(todos_saves)
        elif p["natureza"] == "Bruxo":
            st.markdown("##### ⚡ Fôlego")
            st.write(f"**Fôlego:** {esp['folego_atual']}/{esp['folego_max']}")
            st.progress(max(0.0, min(1.0, esp['folego_atual'] / esp['folego_max'])))

    # ÁREA DA CAMPANHA
    aba_av, aba_inv, aba_cod, aba_fic = st.tabs(["📜 Aventura", "🎒 Inventário", "👥 Códex", "📋 Ficha"])

    with aba_av:
        # CALCULADORA DE DADOS
        with st.expander("🎲 Rolar Ação da Ficha (Calculadora de d10)", expanded=False):
            cr1, cr2 = st.columns(2)
            with cr1:
                atr_e = st.selectbox("Atributo:", TODOS_ATRIBUTOS, index=0)
            with cr2:
                hab_e = st.selectbox("Habilidade:", TODAS_HABILIDADES, index=3)
            
            total_parada = max(1, p["atributos"][atr_e] + p["habilidades"].get(hab_e, 0))
            if st.button(f"🎲 Rolar {atr_e} + {hab_e} ({total_parada} dados)"):
                dados = [random.randint(1, 10) for _ in range(total_parada)]
                dez = dados.count(10)
                pares = dez // 2
                sucessos = sum(1 for d in dados if 6 <= d <= 9) + (pares * 4) + (dez % 2)
                
                dados_jogo["dialogos"].append({
                    "tipo": "rolagem",
                    "teste": f"{atr_e} + {hab_e}",
                    "dados": dados,
                    "sucessos": sucessos,
                    "critico": pares > 0
                })
                salvar_todos_saves(todos_saves)
                st.rerun()

        # NARRATIVA VISUAL NOVEL & OFF-GAME OOC
        for d in dados_jogo["dialogos"]:
            if d.get("tipo") == "rolagem":
                crit_txt = "✨ **CRÍTICO!**" if d["critico"] else ""
                st.markdown(f"""
                    <div class="roll-card">
                        🎲 <strong>{d['teste']}:</strong> {d['sucessos']} Sucesso(s) {crit_txt}<br>
                        <small style="color: #94a3b8;">Faces: {d['dados']}</small>
                    </div>
                """, unsafe_allow_html=True)
            elif d.get("tipo") == "ooc":
                # Card de Mensagem Off-Game (OOC)
                st.markdown(f"""
                    <div class="ooc-box">
                        <strong style="color: #c084fc;">💬 [OFF-GAME / OOC] Mestre responde:</strong><br>
                        <span style="color: #e2e8f0; font-size: 0.98em;">{d['fala']}</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="vn-box">
                        <div class="vn-name">🎭 {d['npc']}</div>
                        <div class="vn-action">"{d['acao']}"</div>
                        <div class="vn-dialogue">"{d['fala']}"</div>
                        <div class="vn-prompt">👉 {d['pergunta']}</div>
                    </div>
                """, unsafe_allow_html=True)

        comando = st.chat_input("O que você faz ou diz agora? (Dica: use 'ooc:' para falar em off com o Mestre)...")
        if comando:
            with st.spinner("O Mestre está consultando as regras e respondendo..."):
                resposta = narrar_acao_venice(comando, p, dados_jogo["dialogos"][-3:])
                dados_jogo["dialogos"].append(resposta)
                salvar_todos_saves(todos_saves)
                st.rerun()

    with aba_inv:
        st.subheader("🎒 Inventário")
        for it in dados_jogo["inventario"]:
            st.markdown(f"**{it['icone']} {it['nome']}** — *{it['tipo']}*\n\n{it['detalhe']}")

    with aba_cod:
        st.subheader("👥 Códex de NPCs")
        for nome, dados_npc in dados_jogo["npcs"].items():
            val = dados_npc['afeto']
            st.markdown(f"**{nome}** ({dados_npc['titulo']}) — Afeição: **{val}/100**")
            st.progress((val + 100) / 200.0)

    with aba_fic:
        st.subheader(f"Ficha de {p['nome']}")
        st.write(p["historia"])
        st.write(f"**Convicções:** {p['conviccoes']}")