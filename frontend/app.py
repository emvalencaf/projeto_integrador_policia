import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime
import folium
from config import BACKEND_URL
from folium.plugins import HeatMapWithTime, HeatMap
from streamlit_folium import st_folium
import requests

# Configuração da página
st.set_page_config(
    page_title="Dashboard Policial",
    page_icon="🚔",
    layout="wide"
)

# Inicializar session state
if 'df_resultado' not in st.session_state:
    st.session_state.df_resultado = None

# Estilo minimalista
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    h1 {
        color: #1f2937;
        font-weight: 600;
    }
    .stAlert {
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Título
st.title("🚔 Dashboard de Previsão Criminal")
st.markdown("---")

# Função para processar JSON de previsões
def process_predictions(dados):
    """Converte JSON de previsões para DataFrame"""
    if isinstance(dados, str):
        dados = json.loads(dados)
    
    if 'forecast' in dados:
        df = pd.DataFrame(dados['forecast'])
        df['ds'] = pd.to_datetime(df['ds'])
        return df
    else:
        return pd.DataFrame(dados)

# Sidebar para seleção
with st.sidebar:
    st.header("Configurações")
    
    # Seleção do modelo
    modelo = st.selectbox(
        "Selecione o modelo:",
        ["Recife", "Chicago"],
        help="Escolha a cidade/modelo para análise"
    )
    
    st.markdown("---")
    
    # Tipo de operação
    operacao = st.radio(
        "Tipo de operação:",
        ["Carregar Previsões", "Fazer Previsão"],
        help="Escolha se deseja visualizar previsões existentes ou gerar novas"
    )

# Conteúdo principal
if operacao == "Carregar Previsões":
    st.header("📊 Visualizar Previsões Existentes")
    st.info("Carregue um arquivo JSON ou CSV contendo as previsões do modelo")
    
    arquivo_previsoes = st.file_uploader(
        "Selecione o arquivo de previsões:",
        type=['json', 'csv'],
        key="previsoes"
    )
    
    if arquivo_previsoes:
        try:
            # Carregar dados
            if arquivo_previsoes.name.endswith('.json'):
                dados = json.load(arquivo_previsoes)
                df = process_predictions(dados)
            else:
                df = pd.read_csv(arquivo_previsoes)
                if 'ds' in df.columns:
                    df['ds'] = pd.to_datetime(df['ds'])
            
            # Armazenar no session state
            st.session_state.df_resultado = df
            
            # Métricas principais
            st.subheader("📈 Resumo Geral")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Previsões", len(df))
            with col2:
                if 'mean_crimes' in df.columns:
                    total_crimes = df['mean_crimes'].sum()
                    st.metric("Crimes Previstos", f"{int(total_crimes)}")
            with col3:
                if 'hotspot_id' in df.columns:
                    st.metric("Hotspots Identificados", df['hotspot_id'].nunique())
            with col4:
                if 'ds' in df.columns:
                    st.metric("Período", f"{df['ds'].dt.date.nunique()} dias")
            
            st.markdown("---")
            
            # Mapa de Calor Temporal
            st.subheader("🗺️ Mapa de Calor de Crimes")
            
            # Verificar se temos as colunas necessárias
            required_cols = ['latitude', 'longitude', 'mean_crimes']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.warning(f"⚠️ Colunas faltando para criar o mapa: {missing_cols}")
                st.info("💡 O arquivo precisa conter as colunas: latitude, longitude e mean_crimes")
            else:
                try:
                    # Tabs para diferentes visualizações
                    tab1, _ = st.tabs(["📊 Mapa Agregado", "⏱️ Animação Temporal"])
                    
                    with tab1:
                        # Agregar crimes por localização (somar ao longo do tempo)
                        df_agg = df.groupby(['latitude', 'longitude']).agg({
                            'mean_crimes': 'sum',
                            'hotspot_id': 'first'
                        }).reset_index()
                        
                        # Remover linhas com valores nulos
                        df_map = df_agg.dropna(subset=['latitude', 'longitude', 'mean_crimes'])
                        
                        if len(df_map) == 0:
                            st.warning("⚠️ Não há dados válidos de localização")
                        else:
                            # Informações do mapa
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total de Hotspots", len(df_map))
                            with col2:
                                st.metric("Total de Crimes", f"{df_map['mean_crimes'].sum():.0f}")
                            with col3:
                                st.metric("Média por Hotspot", f"{df_map['mean_crimes'].mean():.1f}")
                            
                            # Criar mapa base
                            center_lat = df_map['latitude'].mean()
                            center_lon = df_map['longitude'].mean()
                            
                            m = folium.Map(
                                location=[center_lat, center_lon],
                                zoom_start=11,
                                tiles='cartodbpositron'
                            )
                            
                            # Preparar dados para o heatmap (com intensidade agregada)
                            heat_data = df_map[['latitude', 'longitude', 'mean_crimes']].values.tolist()
                            
                            # Adicionar HeatMap
                            HeatMap(
                                heat_data,
                                min_opacity=0.4,
                                max_opacity=0.9,
                                radius=20,
                                blur=25,
                                gradient={
                                    0.0: 'blue',
                                    0.3: 'cyan',
                                    0.5: 'lime',
                                    0.7: 'yellow',
                                    0.9: 'orange',
                                    1.0: 'red'
                                }
                            ).add_to(m)
                            
                            # Adicionar marcadores para os top 15 hotspots mais críticos
                            top_hotspots = df_map.nlargest(15, 'mean_crimes')
                            for idx, row in top_hotspots.iterrows():
                                folium.CircleMarker(
                                    location=[row['latitude'], row['longitude']],
                                    radius=6,
                                    popup=folium.Popup(
                                        f"<b>Hotspot ID:</b> {row['hotspot_id']}<br>"
                                        f"<b>Total Crimes:</b> {row['mean_crimes']:.1f}<br>"
                                        f"<b>Lat:</b> {row['latitude']:.4f}<br>"
                                        f"<b>Lon:</b> {row['longitude']:.4f}",
                                        max_width=200
                                    ),
                                    tooltip=f"Hotspot {row['hotspot_id']}: {row['mean_crimes']:.0f} crimes",
                                    color='darkred',
                                    fill=True,
                                    fillColor='red',
                                    fillOpacity=0.8,
                                    weight=2
                                ).add_to(m)
                            
                            # Exibir mapa
                            st_folium(m, width=1200, height=600, key="heatmap_loaded")
                            
                            # Legenda e informações
                            st.info("🔴 **Vermelho/Laranja:** Alta concentração de crimes | 🟢 **Verde/Ciano:** Média concentração | 🔵 **Azul:** Baixa concentração")
                            st.caption("💡 Os pontos vermelhos marcam os 15 hotspots mais críticos. Passe o mouse ou clique para ver detalhes.")
                            
                
                except Exception as e:
                    st.error(f"Erro ao criar mapa: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
            
            st.markdown("---")
        
            # Tabela de dados
            st.subheader("📋 Dados Detalhados")
            
            # Formatar para exibição
            df_display = df.copy()
            if 'ds' in df_display.columns:
                df_display['ds'] = df_display['ds'].dt.strftime('%Y-%m-%d %H:%M')
            
            # Ordenar por crimes previstos
            if 'mean_crimes' in df_display.columns:
                df_display = df_display.sort_values('mean_crimes', ascending=False)
            
            st.dataframe(df_display, use_container_width=True, height=400)
            
            # Downloads
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="⬇️ Baixar CSV",
                    data=df.to_csv(index=False).encode('utf-8'),
                    file_name=f"previsoes_{modelo.lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            with col2:
                st.download_button(
                    label="⬇️ Baixar JSON",
                    data=json.dumps({'forecast': df.to_dict('records')}, indent=2, default=str),
                    file_name=f"previsoes_{modelo.lower()}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {str(e)}")

else:  # Fazer Previsão
    st.header("🔮 Gerar Novas Previsões")
    st.info("Carregue dados brutos para processar e gerar previsões")
    
    arquivo_bruto = st.file_uploader(
        "Selecione o arquivo de dados brutos:",
        type=['csv', 'json'],
        key="brutos"
    )
    
    if arquivo_bruto:
        try:
            # Carregar dados brutos
            if arquivo_bruto.name.endswith('.json'):
                df_bruto = pd.DataFrame(json.load(arquivo_bruto))
            else:
                df_bruto = pd.read_csv(arquivo_bruto)
            
            st.success(f"✅ Arquivo carregado: {len(df_bruto)} registros")
            
            # Preview dos dados
            st.subheader("👁️ Prévia dos Dados")
            st.dataframe(df_bruto.head(10), use_container_width=True)
            
            # Informações do dataset
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Linhas", len(df_bruto))
            with col2:
                st.metric("Colunas", len(df_bruto.columns))
            
            st.markdown("---")
            
            # Parâmetros de previsão
            st.subheader("⚙️ Parâmetros da Previsão")
            dias = st.number_input(
                "Quantos dias deseja prever?",
                min_value=1,
                max_value=90,
                value=7,
                help="Número de dias para gerar previsões"
            )
            
            # URL da API (pode ser configurável)
            api_url = f"{BACKEND_URL}/forecast"
            print(api_url)
            st.markdown("---")
            
            # Botão para processar
            if st.button("🚀 Processar e Gerar Previsões", type="primary"):
                with st.spinner(f"Processando com modelo {modelo}..."):
                    try:
                        # Preparar dados para envio
                        arquivo_bruto.seek(0)  # Voltar ao início do arquivo
                        
                        # Criar formulário multipart
                        files = {
                            'file': (arquivo_bruto.name, arquivo_bruto.getvalue(), 'text/csv')
                        }
                        data = {
                            'city': modelo.lower(),
                            'days': dias
                        }
                        
                        # Fazer requisição POST
                        response = requests.post(api_url, files=files, data=data, timeout=300)
                        
                        if response.status_code == 200:
                            resultado = response.json()
                            df_resultado = process_predictions(resultado)
                            
                            # Armazenar no session state
                            st.session_state.df_resultado = df_resultado
                            
                            st.success("✅ Previsões geradas com sucesso!")
                        else:
                            st.error(f"Erro na API: {response.status_code} - {response.text}")
                            st.stop()
                    
                    except requests.exceptions.RequestException as e:
                        st.error(f"Erro ao conectar com a API: {str(e)}")
                        st.info("💡 Verifique se a API está rodando e a URL está correta")
                        st.stop()
                    except Exception as e:
                        st.error(f"Erro ao processar resposta: {str(e)}")
                        st.stop()
            
            # Mostrar resultados se existirem no session state
            if st.session_state.df_resultado is not None:
                df_resultado = st.session_state.df_resultado
                
                # Mostrar resultados
                st.subheader("📊 Resultados")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Mínimo de Crimes", f"{df_resultado['min_crimes'].min():.0f}")
                with col2:
                    st.metric("Média de Crimes", f"{df_resultado['mean_crimes'].mean():.2f}")
                with col3:
                    st.metric("Máximo de Crimes", f"{df_resultado['max_crimes'].max():.0f}")
                
                st.markdown("---")
                
                # Mapa de Calor Temporal
                st.subheader("🗺️ Mapa de Calor de Crimes")
                
                # Verificar se temos as colunas necessárias
                required_cols = ['latitude', 'longitude', 'mean_crimes']
                missing_cols = [col for col in required_cols if col not in df_resultado.columns]
                
                if missing_cols:
                    st.warning(f"⚠️ Colunas faltando para criar o mapa: {missing_cols}")
                    st.info("💡 O arquivo precisa conter as colunas: latitude, longitude e mean_crimes")
                else:
                    try:
                        # Tabs para diferentes visualizações
                        tab1, tab2 = st.tabs(["📊 Mapa Agregado", "⏱️ Animação Temporal"])
                        
                        with tab1:
                            # Agregar crimes por localização (somar ao longo do tempo)
                            df_agg = df_resultado.groupby(['latitude', 'longitude']).agg({
                                'mean_crimes': 'sum',
                                'hotspot_id': 'first'
                            }).reset_index()
                            
                            # Remover linhas com valores nulos
                            df_map = df_agg.dropna(subset=['latitude', 'longitude', 'mean_crimes'])
                            
                            if len(df_map) == 0:
                                st.warning("⚠️ Não há dados válidos de localização")
                            else:
                                # Informações do mapa
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total de Hotspots", len(df_map))
                                with col2:
                                    st.metric("Total de Crimes", f"{df_map['mean_crimes'].sum():.0f}")
                                with col3:
                                    st.metric("Média por Hotspot", f"{df_map['mean_crimes'].mean():.1f}")
                                
                                # Criar mapa base
                                center_lat = df_map['latitude'].mean()
                                center_lon = df_map['longitude'].mean()
                                
                                m = folium.Map(
                                    location=[center_lat, center_lon],
                                    zoom_start=11,
                                    tiles='cartodbpositron'
                                )
                                
                                # Preparar dados para o heatmap (com intensidade agregada)
                                heat_data = df_map[['latitude', 'longitude', 'mean_crimes']].values.tolist()
                                
                                # Adicionar HeatMap
                                HeatMap(
                                    heat_data,
                                    min_opacity=0.4,
                                    max_opacity=0.9,
                                    radius=20,
                                    blur=25,
                                    gradient={
                                        0.0: 'blue',
                                        0.3: 'cyan',
                                        0.5: 'lime',
                                        0.7: 'yellow',
                                        0.9: 'orange',
                                        1.0: 'red'
                                    }
                                ).add_to(m)
                                
                                # Adicionar marcadores para os top 15 hotspots mais críticos
                                top_hotspots = df_map.nlargest(15, 'mean_crimes')
                                for idx, row in top_hotspots.iterrows():
                                    folium.CircleMarker(
                                        location=[row['latitude'], row['longitude']],
                                        radius=6,
                                        popup=folium.Popup(
                                            f"<b>Hotspot ID:</b> {row['hotspot_id']}<br>"
                                            f"<b>Total Crimes:</b> {row['mean_crimes']:.1f}<br>"
                                            f"<b>Lat:</b> {row['latitude']:.4f}<br>"
                                            f"<b>Lon:</b> {row['longitude']:.4f}",
                                            max_width=200
                                        ),
                                        tooltip=f"Hotspot {row['hotspot_id']}: {row['mean_crimes']:.0f} crimes",
                                        color='darkred',
                                        fill=True,
                                        fillColor='red',
                                        fillOpacity=0.8,
                                        weight=2
                                    ).add_to(m)
                                
                                # Exibir mapa
                                st_folium(m, width=1200, height=600, key="heatmap_loaded")
                                
                                # Legenda e informações
                                st.info("🔴 **Vermelho/Laranja:** Alta concentração de crimes | 🟢 **Verde/Ciano:** Média concentração | 🔵 **Azul:** Baixa concentração")
                                st.caption("💡 Os pontos vermelhos marcam os 15 hotspots mais críticos. Passe o mouse ou clique para ver detalhes.")
                    
                    except Exception as e:
                        st.error(f"Erro ao criar mapa: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                
                st.markdown("---")
                            
                # Tabela de dados
                st.subheader("📋 Dados Detalhados")
                st.dataframe(df_resultado, use_container_width=True, height=400)
                
                # Downloads
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="⬇️ Baixar CSV",
                        data=df_resultado.to_csv(index=False).encode('utf-8'),
                        file_name=f"previsoes_{modelo.lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                with col2:
                    st.download_button(
                        label="⬇️ Baixar JSON",
                        data=json.dumps({'forecast': df_resultado.to_dict('records')}, indent=2, default=str),
                        file_name=f"previsoes_{modelo.lower()}_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
        
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")

# Footer
st.markdown("---")
st.caption(f"Dashboard Policial - Modelo: {modelo} | Operação: {operacao}")