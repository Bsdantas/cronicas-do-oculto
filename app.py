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
# CARREGAMENTO AUTOMÁTICO DOS LIVROS
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
                        texto_total += f"\n--- FONTE: {arquivo} ---\n" + f.read()[:20000]
                elif arquivo.lower().endswith(".pdf") and pypdf:
                    leitor = pypdf.PdfReader(caminho)
                    texto_pdf = ""
                    for pag in leitor.pages[:25]:
                        extraido = pag.extract_text()
                        if extraido:
                            texto_pdf += extraido + "\n"
                    texto_total += f"\n--- FONTE: {arquivo} ---\n" + texto_pdf[:30000]
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

# Estilização CSS Dark Urbana
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

NOVE_DOMINIOS = ["Além", "Alquimia", "Caminhos", "Destino", "Elementos", "Eras", "Essência", "Psique", "Vitalidade"]

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
            prompt=f"Dark fantasy, gothic urban, Sombras de São Paulo, gritty cinematic portrait, 8k: {prompt_descricao}",
            number_of_images=1,
            aspect_ratio="1:1"
        )
        for img in result.images:
            return img._pil_image
    except Exception as e:
        print(f"Erro ao gerar imagem no Gemini: {e}")
        return None

# ==============================================================================
# MOTOR VENICE AI (COM REGRAS DOS LIVROS)
# ==============================================================================
def narrar_acao_venice(comando_jogador, personagem, historico_recente):
    venice_key = st.secrets.get("VENICE_API_KEY", "")
    venice_url = st.secrets.get("VENICE_BASE_URL", "https://api.venice.ai/api/v1")
    
    if not venice_key:
        return {
            "tipo": "narrativa",
            "npc": "Mestre do Oculto",
            "acao": "Observa a garoa paulistana esperando a configuração de API.",
            "fala": "A chave da Venice AI não foi configurada nos Secrets. Configure-a para que a história ganhe vida!",
            "pergunta": "O que você faz?"
        }

    eh_ooc = comando_jogador.strip().lower().startswith("ooc:") or comando_jogador.strip().lower().startswith("[ooc]")

    if eh_ooc:
        prompt_sistema = f"""
Você é o Mestre/Narrador do RPG 'Crônicas do Oculto: Sombras de São Paulo'.
O jogador está falando em OFF-GAME (OOC:) para tirar dúvidas de regras, consultar lore ou pedir conselhos de cena.

CONHECIMENTO DOS LIVROS (LOBISOMENS ALFA 0.9 / BRUXOS ALFA 0.25):
{LORE_DOS_LIVROS[:12000]}

DADOS DO PROTAGONISTA:
- Nome: {personagem['nome']} ({personagem['natureza']})
- Ficha: {personagem['atributos']} | {personagem['habilidades']} | {personagem['especificos']}

INSTRUÇÕES:
Responda em formato JSON com chaves "tipo": "ooc" e "fala": "Explicação clara e amigável das regras, citando mecânicas oficiais da Alfa 0.9 (Lobisomens) ou Alfa 0.25 (Bruxos)."
"""
    else:
        prompt_sistema = f"""
Você é o Mestre do RPG 'Crônicas do Oculto: Sombras de São Paulo'.
Cenário: Fantasia urbana visceral, sombria, madura, dark romance, o segredo do Véu, disputas territoriais e intrigas na metrópole paulistana.

REGRAS OFICIAIS VIGENTES:
- BRUXOS (Alfa 0.25): Magia Livre! Nove Domínios (Círculos I a V). Fôlego Mágico e Sobrecarga física. Canalização segura = 3 + Potência.
- LOBISOMENS (Alfa 0.9): Fúria (0 a 5). Formas (Humana, Lupina, Híbrida). Prata causa Agravado e bloqueia regeneração por 3 rodadas.
- VAMPIROS (V5): Fome (Hunger 0-5), Disciplinas e rivalidade histórica mortal com lobisomens.

PROTAGONISTA ATUAL:
- Nome: {personagem['nome']} ({personagem['natureza']})
- Linhagem/Origem/Clã: {personagem['tradic']}
- Bairro: {personagem['bairro']}
- Conceito & História: {personagem['conceito']} • {personagem['historia']}
- Recursos: {personagem['especificos']}

INSTRUÇÕES:
1. Responda ESTRITAMENTE em formato JSON com 4 chaves:
   "tipo": "narrativa",
   "npc": Nome do personagem falando (ou 'Narrador'),
   "acao": Descrição atmosférica da cena ou ação do NPC (tom cinematográfico, sensorial e imersivo),
   "fala": Diálogo do NPC ou a consequência direta do que aconteceu,
   "pergunta": Sempre termine com "O QUE VOCÊ FAZ?"
2. Jamais tome decisões pelo jogador. Respeite as regras oficiais dos livros.
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
        conteudo["tipo"] = "ooc" if eh_ooc else "narrativa"
        return conteudo
    except Exception as e:
        return {
            "tipo": "narrativa",
            "npc": "Mestre (Aviso)",
            "acao": "As sombras da metrópole tremeluzem.",
            "fala": f"Erro de conexão com a IA: {str(e)}",
            "pergunta": "O que você faz?"
        }

# ==============================================================================
# TELA 1: SELEÇÃO DE PERSONAGENS (ESTILO MMO)
# ==============================================================================
if st.session_state.id_ativo is None and not st.session_state.modo_criacao:
    st.title("Crônicas do Oculto 🌘")
    st.subheader("Seleção de Personagens • Sombras de São Paulo")
    
    if LORE_DOS_LIVROS:
        st.success(f"📚 Livros de regras oficiais carregados da pasta '{PASTA_LIVROS}'!")

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
# TELA 2: CRIAÇÃO COMPLETA DE PERSONAGEM
# ==============================================================================
elif st.session_state.modo_criacao:
    st.title("Criação de Personagem 🌘")
    if st.button("⬅️ Voltar ao Menu de Seleção"):
        st.session_state.modo_criacao = False
        st.rerun()

    natureza = st.radio("O que você vai ser no cenário de São Paulo?", ["Bruxo", "Lobisomem", "Vampiro"], horizontal=True)
    
    tab_id, tab_hab, tab_poder, tab_traits = st.tabs(["1. Identidade & Retrato", "2. Atributos & Habilidades (27)", f"3. Poderes de {natureza}", "4. Moralidade, Vantagens & Defeitos"])
    
    with tab_id:
        c1, c2 = st.columns([2, 1])
        with c1:
            nome_p = st.text_input("Nome do Personagem:", value="Victor Dornelles" if natureza=="Bruxo" else ("Lucas Batista" if natureza=="Lobisomem" else "Klaus Van Der Bilt"))
            conceito = st.text_input("Conceito / Ocupação Mortal:", value="Investigador Ocultista do Centro" if natureza=="Bruxo" else "Motoboy e Protetor Noturno")
            bairro = st.text_input("Bairro / Refúgio em SP:", value="Bixiga / Bela Vista" if natureza=="Bruxo" else "Santana / Zona Norte")
            
            if natureza == "Bruxo":
                tradic_sub = st.selectbox("Tradição Mágica (Alfa 0.25):", ["Raízes Urbanas", "Círculo da Hera Antiga", "Filhos da Noite e do Sangue", "Ordem dos Elementos Livres", "Conclave dos Tecno-Arcanos"])
            elif natureza == "Lobisomem":
                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    origem_lupina = st.selectbox("Raça de Origem:", ["Homídeo", "Metis", "Lupus"])
                    posicao = st.selectbox("Posição na Matilha:", ["Beta", "Ômega"])
                with col_l2:
                    auspicio = st.selectbox("Auspício Lunar:", ["Ahroun", "Galliard", "Philodox", "Theurge", "Ragabash"])
                    matilha = st.text_input("Matilha / Território:", value="Matilha dos Trilhos (Zona Norte)")
                tradic_sub = f"{origem_lupina} • {auspicio} • {posicao}"
            else:
                col_v1, col_v2 = st.columns(2)
                with col_v1:
                    clã = st.selectbox("Clã:", ["Ventrue", "Toreador", "Tremere", "Brujah", "Nosferatu", "Gangrel", "Malkaviano"])
                with col_v2:
                    seita = st.selectbox("Seita / Facção:", ["Camarilla", "Anarquistas", "Autônomo"])
                tradic_sub = f"{clã} • {seita}"
        
        with c2:
            st.markdown("**Retrato Canônico Oficial**")
            if st.button("🎨 Gerar com Gemini"):
                with st.spinner("Pintando..."):
                    desc = f"{natureza} chamado {nome_p}, {conceito}, habitante de {bairro} em São Paulo."
                    img_gemini = gerar_imagem_com_gemini(desc)
                    if img_gemini:
                        st.session_state.avatar_gerado_temp = img_gemini
                        st.image(img_gemini)
            avatar_final = f"https://api.dicebear.com/7.x/bottts/svg?seed={nome_p}"
        
        historia = st.text_area("História, Origem e Vínculos com São Paulo:", value="Cresceu em São Paulo convivendo com as sombras da cidade até seu Despertar.")

    with tab_hab:
        st.markdown("### 📊 Atributos Principais (Escala 1 a 5)")
        col_f, col_s, col_m = st.columns(3)
        with col_f:
            st.caption("Físicos")
            forca = st.slider("Força:", 1, 5, 2 if natureza=="Bruxo" else 4)
            destreza = st.slider("Destreza:", 1, 5, 3)
            vigor = st.slider("Vigor:", 1, 5, 3)
        with col_s:
            st.caption("Sociais")
            carisma = st.slider("Carisma:", 1, 5, 2)
            manipulacao = st.slider("Manipulação:", 1, 5, 3)
            autocontrole = st.slider("Autocontrole:", 1, 5, 2)
        with col_m:
            st.caption("Mentais")
            inteligencia = st.slider("Inteligência:", 1, 5, 4 if natureza=="Bruxo" else 2)
            raciocinio = st.slider("Raciocínio:", 1, 5, 3)
            determinacao = st.slider("Determinação:", 1, 5, 3)
        
        st.markdown("---")
        st.markdown("### 🎯 As 27 Habilidades Padronizadas (0 a 5)")
        hab_dict = {}
        ch1, ch2, ch3 = st.columns(3)
        with ch1:
            st.caption("Físicas")
            for h in HAB_FISICAS:
                hab_dict[h] = st.number_input(f"{h}:", 0, 5, 0, key=f"cr_{h}")
        with ch2:
            st.caption("Sociais")
            for h in HAB_SOCIAIS:
                hab_dict[h] = st.number_input(f"{h}:", 0, 5, 0, key=f"cr_{h}")
        with ch3:
            st.caption("Mentais")
            for h in HAB_MENTAIS:
                def_v = 2 if h in ["Ocultismo", "Investigação"] and natureza=="Bruxo" else 0
                hab_dict[h] = st.number_input(f"{h}:", 0, 5, def_v, key=f"cr_{h}")

    with tab_poder:
        especificos = {}
        
        # BRUXO: MAGIA LIVRE DOS NOVE DOMÍNIOS
        if natureza == "Bruxo":
            st.markdown("#### 🔮 Sistema de Magia Livre — Nove Domínios (Alfa 0.25)")
            st.caption("Distribua **5 pontos iniciais livremente** entre quaisquer Domínios (Círculos I a V):")
            
            dom_escolhidos = {}
            c1, c2, c3 = st.columns(3)
            
            with c1:
                dom_escolhidos["Além"] = st.slider("Além (Espíritos):", 0, 5, 0)
                dom_escolhidos["Alquimia"] = st.slider("Alquimia (Matéria):", 0, 5, 0)
                dom_escolhidos["Caminhos"] = st.slider("Caminhos (Espaço):", 0, 5, 2)
            with c2:
                dom_escolhidos["Destino"] = st.slider("Destino (Probabilidade):", 0, 5, 0)
                dom_escolhidos["Elementos"] = st.slider("Elementos (Forças Físicas):", 0, 5, 0)
                dom_escolhidos["Eras"] = st.slider("Eras (Tempo):", 0, 5, 0)
            with c3:
                dom_escolhidos["Essência"] = st.slider("Essência (Energia/Fixação):", 0, 5, 0)
                dom_escolhidos["Psique"] = st.slider("Psique (Mente/Telecinese):", 0, 5, 0)
                dom_escolhidos["Vitalidade"] = st.slider("Vitalidade (Vida/Sangue):", 0, 5, 3)

            # Cálculo de Pontos Gastos e Bônus de Conhecimento (Regra Seção 10)
            pontos_gastos = sum(dom_escolhidos.values())
            bonus_conhecimento = 0
            for circ in dom_escolhidos.values():
                if circ == 3: bonus_conhecimento += 2
                elif circ == 4: bonus_conhecimento += 4
                elif circ == 5: bonus_conhecimento += 6
            
            folego_inicial = 24 + bonus_conhecimento # Potência 1 base = 24
            
            st.markdown("---")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if pontos_gastos == 5:
                    st.success(f"✅ Pontos de Domínio: **{pontos_gastos} / 5 gastos**")
                elif pontos_gastos < 5:
                    st.info(f"💡 Pontos de Domínio: **{pontos_gastos} / 5 gastos** (Você ainda tem {5 - pontos_gastos} ponto(s) para distribuir!)")
                else:
                    st.error(f"⚠️ Atenção: Você gastou **{pontos_gastos} / 5 pontos**. O limite inicial é 5!")
            
            with col_b2:
                st.info(f"⚡ **Fôlego Mágico Inicial Calculado:** **{folego_inicial}** (Base 24 + Bônus {bonus_conhecimento})")

            grimorio_notas = st.text_area("Grimório / Feitiços e Fórmulas Favoritas de Improvisação:", value="Cura de Emergência (Vitalidade III), Janela Distante (Caminhos III)")

            especificos = {
                "potencia": 1,
                "folego_max": folego_inicial,
                "folego_atual": folego_inicial,
                "sobrecarga": 0,
                "dominios": dom_escolhidos,
                "grimorio": grimorio_notas
            }
            
        elif natureza == "Lobisomem":
            st.markdown("#### 🐺 Regras dos Lobisomens (Alfa 0.9)")
            st.markdown("Distribua **5 pontos iniciais em Dons livres** (Grau I=1, II=2, III=3, IV=4, V=5) entre as 8 Afinidades:")
            
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                dons_texto = st.text_area(
                    "Dons e Rituais Livres Aprendidos:",
                    value="Cura Feral (Regeneração e Vigor — Grau III, 1 ou 2 checagens)\nPredador Ágil (Velocidade Feral — Grau II, passivo +5m / reação 1 checagem)"
                )
            with c_d2:
                renome_pilares = st.selectbox("Pilar de Renome Inicial (Começa com 1 pt):", ["Glória (Glory)", "Honra (Honor)", "Sabedoria (Wisdom)", "Astúcia (Cunning)", "Pureza (Purity)"])
                forma_inicial = st.selectbox("Forma Inicial:", ["Humana (10m deslocamento)", "Lupina (15m deslocamento, +1 Faro)", "Híbrida (10m, Garras +2 e Força +1)"])
            
            especificos = {
                "furia": 1,
                "forma": forma_inicial,
                "dons": dons_texto,
                "renome": {renome_pilares.split(' ')[0]: 1},
                "bloqueio_prata": 0
            }
        else: # Vampiro
            st.markdown("#### 🩸 Condição Vampírica (Padrão V5)")
            c_v1, c_v2 = st.columns(2)
            with c_v1:
                fome = st.slider("Fome Inicial (Hunger):", 0, 5, 1)
                pot_sangue = st.slider("Potência do Sangue:", 1, 5, 1)
            with c_v2:
                disc_texto = st.text_area("Disciplinas Iniciais:", "Potência 2, Fortitude 1")
            especificos = {"fome": fome, "potencia_sangue": pot_sangue, "disciplinas": disc_texto}

    with tab_traits:
        st.markdown("### ⚖️ Convicções, Pilares, Vantagens & Defeitos")
        c_cv1, c_cv2 = st.columns(2)
        with c_cv1:
            conv1 = st.text_input("Convicção 1:", "Não abandonar quem depende de mim")
            conv2 = st.text_input("Convicção 2:", "Reparar o dano causado aos inocentes")
        with c_cv2:
            pilar1 = st.text_input("Pilar Mortal 1:", "Pessoa próxima da família")
            pilar2 = st.text_input("Pilar Mortal 2:", "Amigo de infância")
        
        st.markdown("---")
        c_vt, c_df = st.columns(2)
        with c_vt:
            vantagens_txt = st.text_area("Vantagens (7 Pontos):", "Recursos 2\nRefúgio 1\nAliados 2\nSono Leve 1\nContatos 1")
        with c_df:
            defeitos_txt = st.text_area("Defeitos (2 Pontos):", "Segredo Perigoso 1\nTimidez 1")

    st.markdown("---")
    if st.button("💾 Salvar Ficha e Iniciar Campanha"):
        novo_id = f"char_{len(todos_saves) + 1}_{nome_p.lower().replace(' ', '_')}"
        dados_novo = {
            "personagem": {
                "nome": nome_p, "natureza": natureza, "conceito": conceito, "tradic": tradic_sub, "bairro": bairro, "historia": historia,
                "avatar": avatar_final,
                "atributos": {"Força": forca, "Destreza": destreza, "Vigor": vigor, "Carisma": carisma, "Manipulação": manipulacao, "Autocontrole": autocontrole, "Inteligência": inteligencia, "Raciocínio": raciocinio, "Determinação": determinacao},
                "habilidades": hab_dict, "vitalidade_max": vigor + 3, "dano_superficial": 0, "dano_agravado": 0, "vontade_max": autocontrole + determinacao, "vontade_superficial": 0,
                "humanidade": 7, "conviccoes": [(conv1, pilar1), (conv2, pilar2)], "vantagens": vantagens_txt, "defeitos": defeitos_txt, "especificos": especificos
            },
            "dialogos": [{
                "tipo": "narrativa", "npc": "Narrador",
                "acao": f"A noite cai úmida sobre {bairro}. Como um {natureza} ({conceito}), seus sentidos percebem o perigo pulsar sob a garoa paulistana.",
                "fala": f"Bem-vindo à noite de São Paulo, {nome_p}. Um mistério recente colocou seus aliados em alerta contra violações do segredo do Véu.",
                "pergunta": "O que você faz?", "item_descoberto": None
            }],
            "inventario": [{"nome": "Pertence Pessoal", "tipo": "Item Inicial", "detalhe": "Um foco, amuleto ou chave do seu refúgio.", "icone": "💼"}],
            "npcs": {
                "Helena Viana": {"titulo": "Bibliotecária do Círculo da Hera", "afeto": 15, "personalidade": "Pragmática, culta e reservada.", "segredos": ["Contatos com a corte da Bela Vista."]},
                "Lucas Batista": {"titulo": "Beta da Matilha dos Trilhos", "afeto": 10, "personalidade": "Protetor territorial e motoboy.", "segredos": ["Investiga caçadores armados com prata."]}
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

    # --- BARRA LATERAL DINÂMICA ---
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

        # RECURSOS EXCLUSIVOS POR ESPÉCIE
        if p["natureza"] == "Lobisomem":
            st.markdown("##### 🐺 Fúria e Formas (Alfa 0.9)")
            forma_escolhida = st.selectbox("Forma Atual:", ["Humana (10m)", "Lupina (15m, +1 Faro)", "Híbrida (10m, Garras +2)"], index=0)
            esp["forma"] = forma_escolhida
            
            st.write(f"**Fúria Atual:** {esp['furia']}/5")
            st.progress(esp['furia'] / 5.0)
            
            if st.button("⚡ Checagem de Fúria (1d10)"):
                df = random.randint(1, 10)
                if df <= 5:
                    if esp['furia'] < 5:
                        esp['furia'] += 1
                        st.warning(f"Dado {df}: Fúria subiu para {esp['furia']}!")
                    else:
                        st.error(f"Dado {df}: Fúria em 5! Teste Autocontrole + Determinação contra Frenesi!")
                else:
                    st.success(f"Dado {df}: A fera permaneceu serena.")
                salvar_todos_saves(todos_saves)
            
            prata_ativa = st.checkbox("Bloqueio por Prata Ativo?", value=esp.get("bloqueio_prata", 0) > 0)
            if prata_ativa:
                st.caption("⚠️ Regeneração bloqueada por prata!")

        elif p["natureza"] == "Bruxo":
            st.markdown("##### ⚡ Fôlego & Sobrecarga (Alfa 0.25)")
            st.write(f"**Fôlego:** {esp['folego_atual']}/{esp['folego_max']}")
            st.progress(max(0.0, min(1.0, esp['folego_atual'] / esp['folego_max'])))
            st.write(f"**Sobrecarga:** {esp['sobrecarga']}")
            excesso = max(0, esp['sobrecarga'] - esp['potencia'])
            if excesso > 0:
                st.error(f"⚠️ Sobrecarga Ativa: {excesso}")
        else: # Vampiro
            st.markdown("##### 🩸 Fome (Hunger)")
            st.write(f"**Fome:** {esp['fome']}/5")
            st.progress(esp['fome'] / 5.0)

    # --- ÁREA PRINCIPAL DA CAMPANHA ---
    aba_av, aba_inv, aba_cod, aba_fic = st.tabs(["📜 Aventura", "🎒 Inventário", "👥 Códex", "📋 Ficha"])

    with aba_av:
        # CALCULADORA DE DADOS COM SUPORTE A DADOS DE FÚRIA
        with st.expander("🎲 Rolar Ação da Ficha (Calculadora de d10)", expanded=False):
            cr1, cr2 = st.columns(2)
            with cr1:
                atr_e = st.selectbox("Atributo:", TODOS_ATRIBUTOS, index=0)
            with cr2:
                hab_e = st.selectbox("Habilidade:", TODAS_HABILIDADES, index=3)
            
            total_parada = max(1, p["atributos"][atr_e] + p["habilidades"].get(hab_e, 0))
            qtd_furia = min(esp.get("furia", 0), total_parada) if p["natureza"] == "Lobisomem" else 0
            
            if st.button(f"🎲 Rolar {atr_e} + {hab_e} ({total_parada} dados)"):
                dados = [random.randint(1, 10) for _ in range(total_parada)]
                dez = dados.count(10)
                pares = dez // 2
                sucessos = sum(1 for d in dados if 6 <= d <= 9) + (pares * 4) + (dez % 2)
                
                critico_feral = False
                falha_feral = False
                if qtd_furia > 0:
                    dados_furia = dados[:qtd_furia]
                    if pares > 0 and 10 in dados_furia:
                        critico_feral = True
                    if sucessos == 0 and 1 in dados_furia:
                        falha_feral = True

                dados_jogo["dialogos"].append({
                    "tipo": "rolagem",
                    "teste": f"{atr_e} + {hab_e}",
                    "dados": dados,
                    "sucessos": sucessos,
                    "critico": pares > 0,
                    "critico_feral": critico_feral,
                    "falha_feral": falha_feral
                })
                salvar_todos_saves(todos_saves)
                st.rerun()

        # HISTÓRICO DE NARRATIVA
        for d in dados_jogo["dialogos"]:
            if d.get("tipo") == "rolagem":
                crit_txt = "✨ **CRÍTICO!**" if d["critico"] else ""
                if d.get("critico_feral"):
                    crit_txt = "🐺💥 **CRÍTICO FERAL! (A Fera assumiu o golpe!)**"
                if d.get("falha_feral"):
                    crit_txt = "⚠️ **FALHA FERAL! (-1 dado na próxima ação física)**"

                st.markdown(f"""
                    <div class="roll-card">
                        🎲 <strong>{d['teste']}:</strong> {d['sucessos']} Sucesso(s) {crit_txt}<br>
                        <small style="color: #94a3b8;">Faces dos dados: {d['dados']}</small>
                    </div>
                """, unsafe_allow_html=True)
            elif d.get("tipo") == "ooc":
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
            with st.spinner("Venice AI consultando os livros de regras de São Paulo..."):
                resposta = narrar_acao_venice(comando, p, dados_jogo["dialogos"][-3:])
                dados_jogo["dialogos"].append(resposta)
                salvar_todos_saves(todos_saves)
                st.rerun()

    with aba_inv:
        st.subheader("🎒 Inventário & Pistas")
        for it in dados_jogo["inventario"]:
            st.markdown(f"**{it['icone']} {it['nome']}** — *{it['tipo']}*\n\n{it['detalhe']}")

    with aba_cod:
        st.subheader("👥 Códex de NPCs & Relações (-100 a +100)")
        for nome, dados_npc in dados_jogo["npcs"].items():
            val = dados_npc['afeto']
            st.markdown(f"**{nome}** ({dados_npc['titulo']}) — Afeição: **{val}/100**")
            st.progress((val + 100) / 200.0)

    with aba_fic:
        st.subheader(f"Ficha de {p['nome']} ({p['natureza']})")
        st.markdown(f"**Conceito:** {p['conceito']} | **Linhagem:** {p['tradic']}")
        st.markdown(f"**História:** {p['historia']}")
        st.markdown("---")
        if p["natureza"] == "Bruxo":
            st.markdown(f"**Domínios Conhecidos:** {p['especificos']['dominios']}")
            st.markdown(f"**Grimório & Fórmulas:**\n{p['especificos'].get('grimorio', 'Nenhum feitiço anotado.')}")
        elif p["natureza"] == "Lobisomem":
            st.markdown(f"**Dons & Rituais:**\n{p['especificos']['dons']}")