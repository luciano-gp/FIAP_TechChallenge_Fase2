import streamlit as st
import requests

st.set_page_config(page_title="Dashboard Logístico Hospitalar", layout="wide")
st.title("🚑 Painel de Roteamento Assistido por IA")

with st.sidebar:
    st.header("Cenário e Parâmetros")
    # Cenários mapeados e registrados nas configurações de benchmark
    cenarios = ["base", "alta_prioridade", "alta_demanda", "baixa_autonomia", "frota_reduzida", "maior", "capacidade_insuficiente", "autonomia_insuficiente"]
    cenario_escolhido = st.selectbox("Selecione o Cenário", cenarios)
    
    gen = st.number_input("Gerações", value=200, step=50)
    pop = st.number_input("Tamanho da População", value=100, step=10)
    mut = st.slider("Taxa de Mutação", 0.0, 1.0, 0.25)
    
    iniciar = st.button("Executar Algoritmo Genético e IA")

if iniciar:
    with st.spinner("Evoluindo rotas e consultando o Gemini..."):
        payload = {
            "scenario": cenario_escolhido,
            "generations": gen,
            "population_size": pop,
            "mutation_probability": mut
        }
        
        response = requests.post("http://backend:8000/otimizar", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            dados_brutos = data["dados_brutos"]
            
            st.subheader("📊 Métricas de Eficiência (Algoritmo Genético)")
            col1, col2, col3, col4 = st.columns(4)
            # Acessando o campo objective do JSON estruturado[cite: 10]
            col1.metric("Distância Total", f"{dados_brutos['objective']['total_distance']:.2f} km")
            col2.metric("Penalizações", f"{dados_brutos['objective']['penalty']:.2f}")
            col3.metric("Solução Válida", "Sim" if dados_brutos['objective']['valid'] else "Não")
            col4.metric("Fitness", f"{dados_brutos['objective']['fitness']:.2f}")
            
            st.divider()
            
            st.subheader("🧠 Relatório Logístico (Gemini 1.5 Flash)")
            st.write(data["relatorio_ia"])
            
            with st.expander("Ver JSON Completo gerado pelo vrp_reporting.py"):
                st.json(dados_brutos)
            
            st.divider()
            st.subheader("💬 Tire dúvidas sobre as rotas")
            
            # Inicializa o histórico do chat
            if "mensagens" not in st.session_state:
                st.session_state.mensagens = []

            for msg in st.session_state.mensagens:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

            if pergunta := st.chat_input("Ex: Qual veículo percorre a maior distância?"):
                st.session_state.mensagens.append({"role": "user", "content": pergunta})
                with st.chat_message("user"):
                    st.write(pergunta)

                with st.chat_message("assistant"):
                    with st.spinner("Analisando rotas..."):
                        res_chat = requests.post(
                            "http://backend:8000/chat", 
                            json={"pergunta": pergunta, "contexto_json": dados_brutos}
                        )
                        if res_chat.status_code == 200:
                            resposta = res_chat.json()["resposta"]
                            st.write(resposta)
                            st.session_state.mensagens.append({"role": "assistant", "content": resposta})
                        else:
                            st.error("Erro ao consultar o assistente.")
        else:
            st.error(f"Erro na API de Otimização. Status code: {response.status_code}, Detalhes: {response.text}")
        