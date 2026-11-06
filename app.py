import streamlit as st
import random

# Configuração da Página
st.set_page_config(
    page_title="Crônicas do Oculto: Sombras de SP",
    page_icon="🌘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS: Visual Novel Dark Urbana
st.markdown("""
    <style>
        .main { background-color: #0b0d11; color: #e6e6e6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .creation-card {
            background: linear-gradient(135deg, #131722 0%, #1c152b 100%);
            border: 1px solid #4a286c;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.7);
        }
        .vn-box {
            background: linear-gradient(135deg, #131722 0%, #1a1528 100%);
            border: 1px solid #4a286c;
            border-left: 5px solid #9d50e6;
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.6);
        }
        .vn-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
        .vn-name { font-size: 1.25em; font-weight: bold; color: #d8b4fe; }
        .vn-affinity { font-size: 0.85em; padding: 3px 8px; border-radius: 12px; font-weight: bold; }
        .affinity-pos { background-color: #2e1065; color: #c084fc; border: 1px solid #a855f7; }
        .affinity-neg { background-color: #450a0a; color: #f87171; border: 1px solid #ef4444; }
        .affinity-neu { background-color: #1f2937; color: #9ca3af; border: 1px solid #4b5563; }
        .vn-action { font-style: italic; color: #a1a1aa; margin-bottom: 8px; }
        .vn-dialogue { font-size: 1.1em; color: #ffffff; line-height: 1.5; padding: 6px 0; }
        .vn-prompt { color: #facc15; font-weight: bold; margin-top: 10px; text-transform: uppercase; font-size: 0.9em; letter-spacing: 1px; }
        .stButton>button { width: 100%; border-radius: 6px; background-color: #3b1d5a; color: white; border: 1px solid #8b5cf6; font-weight: bold; height: 3em; }
        .stButton>button:hover { background-color: #581c87; border-color: #c084fc; }
    </style>
""", unsafe_allow_html=True)

# 1. ESTADO GLOBAL
if "personagem_pronto" not in st.session_state:
    st.session_state.personagem_pronto = False

if "inventario" not in st.session_state:
    st.session_state.inventario = [
        {"nome": "Foco / Pertence Pessoal", "tipo": "Item Inicial", "detalhe": "Um objeto de valor pessoal que ancora sua humanidade ou poder.", "icone": "守"}
    ]

if "npcs" not in st.session_state:
    st.session_state.npcs = {
        "Helena Viana": {
            "titulo": "Bibliotecária & Bruxa do Círculo da Hera",
            "afeto": 15,
            "personalidade": "Pragmática, metódica e desconfiada de novatos.",
            "segredos": ["Guarda relíquias do século XVIII em um cofre no Bixiga."]
        },
        "Lucas Batista": {
            "titulo": "Lobisomem Beta da Matilha dos Trilhos",
            "afeto": 10,
            "personalidade": "Protetor feroz, leal à família e motoboy na Zona Norte.",
            "segredos": ["Está investigando caçadores com armas de prata perto da Cantareira."]
        }
    }

if "dialogos" not in st.session_state:
    st.session_state.dialogos = []

# LISTA OFICIAL DAS 27 HABILIDADES
HABILIDADES_FISICAS = ["Armas Brancas", "Armas de Fogo", "Atletismo", "Briga", "Condução", "Furtividade", "Ladronagem", "Ofícios", "Sobrevivência"]
HABILIDADES_SOCIAIS = ["Empatia com Animais", "Empatia", "Etiqueta", "Intimidação", "Liderança", "Manha", "Performance", "Persuasão", "Subterfúgio"]
HABILIDADES_MENTAIS = ["Ciência", "Erudição", "Finanças", "Investigação", "Medicina", "Ocultismo", "Percepção", "Política", "Tecnologia"]

# ==============================================================================
# TELA DE CRIAÇÃO COMPLETA DE PERSONAGEM
# ==============================================================================
if not st.session_state.personagem_pronto:
    st.title("Crônicas do Oculto: Sombras de São Paulo 🌘")
    st.subheader("Criação de Personagem • Registro de Ficha")
    
    with st.container():
        st.markdown('<div class="creation-card">', unsafe_allow_html=True)
        
        # 1. ESCOLHA DA ESPÉCIE
        natureza = st.radio(
            "O que você vai ser no submundo de São Paulo?",
            ["Bruxo", "Lobisomem", "Vampiro"],
            horizontal=True
        )
        
        tab_id, tab_hab, tab_poder, tab_traits = st.tabs([
            "1. Identidade & História",
            "2. Atributos & Habilidades (27)",
            f"3. Poderes de {natureza}",
            "4. Vantagens, Defeitos & Moralidade"
        ])
        
        # TAB 1: IDENTIDADE & HISTÓRIA
        with tab_id:
            c1, c2 = st.columns(2)
            with c1:
                nome_p = st.text_input("Nome do Personagem:", value="Lucas Batista" if natureza=="Lobisomem" else "Victor Dornelles")
                conceito = st.text_input("Conceito / Profissão Mortal:", value="Motoboy e Protetor Noturno" if natureza=="Lobisomem" else "Investigador Ocultista")
                bairro = st.text_input("Bairro / Refúgio em SP:", value="Santana / Zona Norte" if natureza=="Lobisomem" else "Bixiga / Bela Vista")
            with c2:
                if natureza == "Lobisomem":
                    matilha = st.text_input("Matilha / Posição:", "Matilha dos Trilhos • Posição: Beta")
                    origem_lupina = st.selectbox("Raça de Origem:", ["Homídeo (Nascido Humano)", "Metis (Nascido Híbrido)", "Lupus (Nascido Lobo)"])
                    auspicio = st.selectbox("Auspício Lunar:", ["Ahroun (Guerreiro / Lua Cheia)", "Galliard (Bardo / Lua Gibosa)", "Philodox (Juiz / Meia-Lua)", "Theurge (Xamã / Lua Crescente)", "Ragabash (Trapaceiro / Lua Nova)"])
                    tradic_sub = f"{origem_lupina} • {auspicio}"
                elif natureza == "Bruxo":
                    tradic_sub = st.selectbox("Tradição Mágica:", ["Raízes Urbanas", "Círculo da Hera Antiga", "Filhos da Noite e do Sangue", "Ordem dos Elementos Livres", "Conclave dos Tecno-Arcanos"])
                else:
                    tradic_sub = st.selectbox("Clã Vampírico:", ["Ventrue", "Toreador", "Tremere", "Brujah", "Nosferatu", "Gangrel", "Malkaviano"])
            
            st.markdown("---")
            st.markdown("**História, Origem e Primeira Transformação / Despertar:**")
            historia = st.text_area(
                "Descreva a trajetória da sua personagem, sua família, laços mortais e como ingressou na noite paulistana:",
                value="Nascido na periferia da Zona Norte de São Paulo, descobriu sua natureza após um confronto violento. Hoje equilibra entregas noturnas com a proteção dos seus e o respeito ao segredo do Véu."
            )

        # TAB 2: ATRIBUTOS & 27 HABILIDADES
        with tab_hab:
            st.markdown("### 📊 Atributos Principais (1 a 5)")
            col_f, col_s, col_m = st.columns(3)
            with col_f:
                st.markdown("**Físicos**")
                forca = st.slider("Força:", 1, 5, 4 if natureza=="Lobisomem" else 2)
                destreza = st.slider("Destreza:", 1, 5, 3)
                vigor = st.slider("Vigor:", 1, 5, 3)
            with col_s:
                st.markdown("**Sociais**")
                carisma = st.slider("Carisma:", 1, 5, 2)
                manipulacao = st.slider("Manipulação:", 1, 5, 1 if natureza=="Lobisomem" else 3)
                autocontrole = st.slider("Autocontrole:", 1, 5, 2)
            with col_m:
                st.markdown("**Mentais**")
                inteligencia = st.slider("Inteligência:", 1, 5, 2 if natureza=="Lobisomem" else 4)
                raciocinio = st.slider("Raciocínio:", 1, 5, 3)
                determinacao = st.slider("Determinação:", 1, 5, 2 if natureza=="Lobisomem" else 3)

            st.markdown("---")
            st.markdown("### 🎯 As 27 Habilidades Padronizadas (0 a 5)")
            habilidades_dict = {}
            col_hf, col_hs, col_hm = st.columns(3)
            
            with col_hf:
                st.markdown("**Físicas**")
                for h in HABILIDADES_FISICAS:
                    default_val = 3 if h in ["Briga", "Atletismo", "Sobrevivência"] and natureza=="Lobisomem" else 0
                    habilidades_dict[h] = st.number_input(f"{h}:", min_value=0, max_value=5, value=default_val, key=f"hab_{h}")
            with col_hs:
                st.markdown("**Sociais**")
                for h in HABILIDADES_SOCIAIS:
                    default_val = 2 if h == "Intimidação" and natureza=="Lobisomem" else 0
                    habilidades_dict[h] = st.number_input(f"{h}:", min_value=0, max_value=5, value=default_val, key=f"hab_{h}")
            with col_hm:
                st.markdown("**Mentais**")
                for h in HABILIDADES_MENTAIS:
                    default_val = 2 if h in ["Percepção", "Ocultismo"] and natureza=="Lobisomem" else 0
                    habilidades_dict[h] = st.number_input(f"{h}:", min_value=0, max_value=5, value=default_val, key=f"hab_{h}")

        # TAB 3: PODERES ESPECÍFICOS DA ESPÉCIE
        with tab_poder:
            especificos = {}
            if natureza == "Lobisomem":
                st.markdown("#### 🐺 Regras dos Lobisomens (Alfa 0.9)")
                st.markdown("Dons Livres (5 pontos iniciais distribuidos por Grau I=1, II=2, III=3, IV=4, V=5):")
                dons_iniciais = st.text_area(
                    "Dons e Rituais Aprendidos (Ex: Cura Feral III, Predador Ágil II):",
                    value="Cura Feral (Regeneração e Vigor - Grau III, 1 ou 2 checagens)\nPredador Ágil (Velocidade Feral - Grau II, passivo +5m / reação 1 checagem)"
                )
                c_ren1, c_ren2 = st.columns(2)
                with c_ren1:
                    renome_pilares = st.selectbox("Pilar de Renome Inicial (Começa com 1):", ["Glória", "Honra", "Sabedoria", "Astúcia", "Pureza"])
                    forma_padrao = st.selectbox("Forma de Início:", ["Humana (10m)", "Lupina (15m, +1 Faro)", "Híbrida (10m, Garras +2 e Força +1)"])
                with c_ren2:
                    bloqueio_prata = st.checkbox("Bloqueio por Prata Ativo?", value=False)
                
                especificos = {
                    "furia": 1,
                    "forma": forma_padrao,
                    "dons": dons_iniciais,
                    "renome": {renome_pilares: 1},
                    "bloqueio_prata": bloqueio_prata
                }
            elif natureza == "Bruxo":
                st.markdown("#### 🔮 Sistema de Magia Livre e Grimório (Alfa 0.25)")
                c1, c2, c3 = st.columns(3)
                with c1:
                    d_vitalidade = st.slider("Vitalidade:", 0, 5, 3)
                    d_caminhos = st.slider("Caminhos:", 0, 5, 2)
                    d_elementos = st.slider("Elementos:", 0, 5, 0)
                with c2:
                    d_psique = st.slider("Psique:", 0, 5, 0)
                    d_essencia = st.slider("Essência:", 0, 5, 0)
                    d_alquimia = st.slider("Alquimia:", 0, 5, 0)
                with c3:
                    d_alem = st.slider("Além:", 0, 5, 0)
                    d_destino = st.slider("Destino:", 0, 5, 0)
                    d_eras = st.slider("Eras:", 0, 5, 0)
                
                especificos = {
                    "potencia": 1,
                    "folego_max": 26,
                    "folego_atual": 26,
                    "sobrecarga": 0,
                    "dominios": {
                        "Vitalidade": d_vitalidade, "Caminhos": d_caminhos, "Elementos": d_elementos,
                        "Psique": d_psique, "Essência": d_essencia, "Alquimia": d_alquimia,
                        "Além": d_alem, "Destino": d_destino, "Eras": d_eras
                    }
                }
            else: # Vampiro
                st.markdown("#### 🩸 Condição Vampírica")
                fome = st.slider("Fome Inicial:", 0, 5, 1)
                pot_sangue = st.slider("Potência do Sangue:", 1, 5, 1)
                disc = st.text_area("Disciplinas:", value="Potência 2, Fortitude 1")
                especificos = {
                    "fome": fome,
                    "potencia_sangue": pot_sangue,
                    "disciplinas": disc
                }

        # TAB 4: VANTAGENS, DEFEITOS & MORALIDADE
        with tab_traits:
            st.markdown("### ⚖️ Moralidade, Convicções e Pilares Humanos")
            c_conv1, c_conv2 = st.columns(2)
            with c_conv1:
                conv1 = st.text_input("Convicção 1:", "Não abandonar quem depende de mim")
                conv2 = st.text_input("Convicção 2:", "Reparar o dano causado aos inocentes")
            with c_conv2:
                pilar1 = st.text_input("Pilar 1 (Pessoa Mortal):", "Minha irmã mais nova")
                pilar2 = st.text_input("Pilar 2 (Pessoa Mortal):", "Amigo de infância")

            st.markdown("---")
            st.markdown("### 🎁 Vantagens (7 pontos) e ⚠️ Defeitos (2 pontos)")
            c_v, c_d = st.columns(2)
            with c_v:
                vantagens_txt = st.text_area("Vantagens & Antecedentes (7 pts):", value="Recursos 2 (Moto e vida estável)\nRefúgio 1 (Quarto seguro na ZN)\nAliados 2 (Mecânico parceiro)\nSono Leve 1\nContatos 1")
            with c_d:
                defeitos_txt = st.text_area("Defeitos (Mínimo 2 pts):", value="Segredo Perigoso 1 (Identidade lupina sob suspeita)\nTimidez 1")

        # BOTÃO SALVAR PERSONAGEM
        st.markdown("---")
        if st.button("💾 Salvar Ficha Completa e Iniciar Campanha"):
            st.session_state.personagem = {
                "nome": nome_p,
                "natureza": natureza,
                "conceito": conceito,
                "tradic": tradic_sub,
                "bairro": bairro,
                "historia": historia,
                "atributos": {
                    "Força": forca, "Destreza": destreza, "Vigor": vigor,
                    "Carisma": carisma, "Manipulação": manipulacao, "Autocontrole": autocontrole,
                    "Inteligência": inteligencia, "Raciocínio": raciocinio, "Determinação": determinacao
                },
                "habilidades": habilidades_dict,
                "vitalidade_max": vigor + 3,
                "dano_superficial": 0,
                "dano_agravado": 0,
                "vontade_max": autocontrole + determinacao,
                "vontade_superficial": 0,
                "humanidade": 7,
                "conviccoes": [(conv1, pilar1), (conv2, pilar2)],
                "vantagens": vantagens_txt,
                "defeitos": defeitos_txt,
                "especificos": especificos
            }
            
            # PRIMEIRA CENA TEMÁTICA
            st.session_state.dialogos = [{
                "npc": "Narrador",
                "afeto": 0,
                "acao": f"A chuva escorre pelas telhas de {bairro}. Como um {natureza} em São Paulo, seus sentidos percebem a cidade despertar para mais uma noite violenta.",
                "fala": f"Suas garras e instintos estão em alerta, {nome_p}. Um odor estranho de sangue e pólvora foi farejado próximo ao galpão onde sua matilha ou aliados se reúnem.",
                "pergunta": "O que você faz?",
                "item_descoberto": None
            }]
            st.session_state.personagem_pronto = True
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# TELA DO JOGO (VISUAL NOVEL + ABAS DE JOGO)
# ==============================================================================
else:
    p = st.session_state.personagem
    
    # BARRA LATERAL DINÂMICA
    with st.sidebar:
        st.title("👤 Ficha Ativa")
        st.subheader(p["nome"])
        st.caption(f"{p['natureza']} • {p['tradic']} • {p['bairro']}")
        
        if st.button("🔄 Editar Ficha / Criar Outro"):
            st.session_state.personagem_pronto = False
            st.rerun()

        st.markdown("---")
        st.markdown("### 🩸 Trilha de Vitalidade")
        feridos = p['dano_superficial'] + p['dano_agravado']
        st.write(f"Dano: {p['dano_superficial']} Superficial | {p['dano_agravado']} Agravado")
        st.progress(max(0.0, min(1.0, (p['vitalidade_max'] - feridos) / p['vitalidade_max'])))
        st.write(f"**Força de Vontade:** {p['vontade_max'] - p['vontade_superficial']} / {p['vontade_max']}")

        # RECURSOS EXCLUSIVOS DE CADA ESPÉCIE
        st.markdown("---")
        esp = p["especificos"]
        if p["natureza"] == "Lobisomem":
            st.markdown("### 🐺 Condição Lupina (Alfa 0.9)")
            
            # Formas Naturais
            forma_sel = st.selectbox("Forma Atual:", ["Humana (10m)", "Lupina (15m, +1 Faro)", "Híbrida (10m, Garras +2)"], index=0)
            esp["forma"] = forma_sel
            
            # Fúria Feral
            st.write(f"**Fúria Atual:** {esp['furia']} / 5")
            st.progress(esp['furia'] / 5.0)
            
            # Checagem de Fúria (Regra 16.1)
            if st.button("⚡ Checagem de Fúria (1d10)"):
                d_furia = random.randint(1, 10)
                if d_furia <= 5:
                    if esp['furia'] < 5:
                        esp['furia'] += 1
                        st.warning(f"Dado {d_furia}: A Fúria subiu para {esp['furia']}!")
                    else:
                        st.error(f"Dado {d_furia}: Fúria já em 5! Teste Autocontrole + Determinação contra Frenesi!")
                else:
                    st.success(f"Dado {d_furia}: A fera permaneceu sob controle.")
            
            # Prata
            esp["bloqueio_prata"] = st.checkbox("⚠️ Bloqueio por Prata Ativo?", value=esp.get("bloqueio_prata", False))

        elif p["natureza"] == "Bruxo":
            st.markdown("### ⚡ Fôlego & Sobrecarga (Alfa 0.25)")
            st.write(f"**Fôlego Mágico:** {esp['folego_atual']} / {esp['folego_max']}")
            st.progress(max(0.0, min(1.0, esp['folego_atual'] / esp['folego_max'])))
            st.write(f"**Sobrecarga:** {esp['sobrecarga']}")
            excesso = max(0, esp['sobrecarga'] - esp['potencia'])
            if excesso > 0:
                st.error(f"⚠️ Sobrecarga Ativa: {excesso}")
        else: # Vampiro
            st.markdown("### 🩸 Condição Vampírica")
            st.write(f"**Fome:** {esp['fome']} / 5")
            st.progress(esp['fome'] / 5.0)

        # ROLADOR DE DADOS D10
        st.markdown("---")
        st.markdown("### 🎲 Rolador de Dados (d10)")
        qtd_dados = st.number_input("Qtd de dados da parada:", min_value=1, max_value=15, value=5)
        
        # Se for Lobisomem, calcula quantos dados são de Fúria
        qtd_furia = min(esp["furia"], qtd_dados) if p["natureza"] == "Lobisomem" else 0
        
        if st.button("🎲 Rolar Dados"):
            dados = [random.randint(1, 10) for _ in range(qtd_dados)]
            dez = dados.count(10)
            pares_10 = dez // 2
            dez_avulsos = dez % 2
            sucessos = sum(1 for d in dados if 6 <= d <= 9) + (pares_10 * 4) + dez_avulsos
            
            st.write(f"**Resultados:** {dados}")
            if qtd_furia > 0:
                st.caption(f"*(Inclui {qtd_furia} Dado(s) de Fúria)*")
            if pares_10 > 0:
                st.success(f"✨ **CRÍTICO!** Sucessos Totais: {sucessos} (com {pares_10} par(es) de 10)")
            else:
                st.info(f"**Sucessos Totais:** {sucessos}")

    # ABAS PRINCIPAIS DO JOGO
    st.title("Crônicas do Oculto 🌘")
    st.caption(f"{p['nome']} • {p['natureza']} • Sombras de São Paulo")

    aba_vn, aba_ficha_comp, aba_inv, aba_npcs, aba_diario = st.tabs([
        "📜 Aventura (Visual Novel)",
        "📋 Ficha Completa",
        "🎒 Inventário & Pistas", 
        "👥 Códex de NPCs", 
        "📖 Diário de Quests"
    ])

    # 1. ABA VISUAL NOVEL
    with aba_vn:
        for d in st.session_state.dialogos:
            afeto = d["afeto"]
            badge_class = "affinity-pos" if afeto > 20 else ("affinity-neg" if afeto < -20 else "affinity-neu")
            status_txt = f"Afeição: +{afeto}" if afeto > 0 else (f"Afeição: {afeto}" if afeto < 0 else "Neutro")

            st.markdown(f"""
                <div class="vn-box">
                    <div class="vn-header">
                        <span class="vn-name">🎭 {d['npc']}</span>
                        <span class="vn-affinity {badge_class}">{status_txt}</span>
                    </div>
                    <div class="vn-action">"{d['acao']}"</div>
                    <div class="vn-dialogue">"{d['fala']}"</div>
                    <div class="vn-prompt">👉 {d['pergunta']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if d.get("item_descoberto"):
                it = d["item_descoberto"]
                st.info(f"🔍 **Nova Pista Encontrada:** {it['nome']} ({it['tipo']}) - Adicionado ao seu Inventário!")

        comando = st.chat_input("O que você faz ou diz agora?...")
        if comando:
            novo_item = None
            if any(w in comando.lower() for w in ["investigar", "farejar", "rastrear", "procurar", "olhar"]):
                novo_item = {
                    "nome": "Cápsula de Prata Vazia",
                    "tipo": "Evidência / Balística",
                    "detalhe": "Um cartucho deflagrado de pistola com revestimento de prata legítima gravada com runas.",
                    "icone": "🪙"
                }
                st.session_state.inventario.append(novo_item)

            st.session_state.dialogos.append({
                "npc": "Lucas Batista" if p["natureza"] != "Lobisomem" else "Helena Viana",
                "afeto": 15,
                "acao": f"Observa atentamente sua reação diante da cena ('{comando}').",
                "fala": f"Você tem instintos afiados, {p['nome']}. Mas o sangue derramado aqui ainda está quente... Fique em guarda.",
                "pergunta": "O que você faz agora?",
                "item_descoberto": novo_item
            })
            st.rerun()

    # 2. ABA FICHA COMPLETA
    with aba_ficha_comp:
        st.subheader("📋 Registro Completo do Personagem")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown(f"**Conceito:** {p['conceito']}")
            st.markdown(f"**História & Origem:** {p['historia']}")
            st.markdown(f"**Vantagens:**\n{p['vantagens']}")
            st.markdown(f"**Defeitos:**\n{p['defeitos']}")
        with col_c2:
            st.markdown("**Convicções e Pilares Humanos:**")
            for c, pil in p['conviccoes']:
                st.markdown(f"- *{c}* (Pilar: **{pil}**)")
            
            st.markdown("---")
            if p["natureza"] == "Lobisomem":
                st.markdown(f"**Dons & Rituais:**\n{p['especificos']['dons']}")
            elif p["natureza"] == "Bruxo":
                st.markdown(f"**Domínios Conhecidos:** {p['especificos']['dominios']}")
            else:
                st.markdown(f"**Disciplinas:** {p['especificos']['disciplinas']}")

    # 3. ABA INVENTÁRIO
    with aba_inv:
        st.subheader("🎒 Inventário & Pistas Encontradas")
        cols = st.columns(3)
        for i, it in enumerate(st.session_state.inventario):
            with cols[i % 3]:
                st.markdown(f"""
                    <div style="background-color: #161a22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 12px;">
                        <div style="font-size: 1.8em;">{it['icone']}</div>
                        <strong style="color: #c084fc; font-size: 1.1em;">{it['nome']}</strong><br>
                        <small style="color: #eab308;">[{it['tipo']}]</small>
                        <p style="color: #9ca3af; font-size: 0.85em; margin-top: 8px;">{it['detalhe']}</p>
                    </div>
                """, unsafe_allow_html=True)

    # 4. ABA CÓDEX
    with aba_npcs:
        st.subheader("👥 Códex de NPCs & Relações (-100 a +100)")
        for nome, dados in st.session_state.npcs.items():
            val = dados['afeto']
            cor_barra = "#a855f7" if val >= 0 else "#ef4444"
            st.markdown(f"""
                <div style="background-color: #131722; border: 1px solid #2d3748; border-radius: 10px; padding: 15px; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: #f3e8ff;">{nome} <span style="font-size: 0.7em; color: #9ca3af;">({dados['titulo']})</span></h4>
                    <p style="font-size: 0.9em; color: #cbd5e1; margin: 5px 0;"><strong>Personalidade:</strong> {dados['personalidade']}</p>
                    <span style="font-size: 0.85em; font-weight: bold;">Relação: {val} / 100</span>
                    <div style="background-color: #1f2937; height: 10px; border-radius: 5px; width: 100%; margin: 6px 0;">
                        <div style="background-color: {cor_barra}; height: 100%; border-radius: 5px; width: {abs(val)}%;"></div>
                    </div>
                    <p style="font-size: 0.85em; color: #eab308; margin-top: 5px;"><strong>Segredos:</strong> {dados['segredos'][0]}</p>
                </div>
            """, unsafe_allow_html=True)

    # 5. ABA DIÁRIO DE QUESTS
    with aba_diario:
        st.subheader("📖 Quests & Pistas em Andamento")
        st.markdown(f"""
        * 🔴 **[Principal] A Sombra sob {p['bairro']}**
          * *Objetivo:* Investigar a movimentação de caçadores com armas de prata e rituais profanos na região.
        """)