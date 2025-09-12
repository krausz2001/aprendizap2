import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shiny import App, render, ui, reactive
import base64
import matplotlib.font_manager as fm
import os
import gc

# ======================================================================================
# 1. PREPARAÇÃO DOS DADOS
# Como não temos seus dados, vamos criar um DataFrame de amostra realista.
#
# !!! IMPORTANTE: SUBSTITUA ESTA SEÇÃO PELA LEITURA DO SEU DATAFRAME !!!
# Exemplo: df_users = pd.read_parquet('caminho/para/seus/dados.parquet')
# ======================================================================================

df_users = pd.read_parquet('Dados/usuarios_RUP_reduzido.parquet')
# Carregar apenas as colunas necessárias para otimizar memória
df_interactions = pd.read_parquet('Dados/fct_teachers_contents_interactions_classified_2_reduzido.parquet', 
                                 columns=['unique_id', 'numero_interacao', 'user_agent_device_type', 'event_classification'])
TOTAL_USERS = len(df_users)

# Calcular limites dinâmicos para os sliders baseados nos dados reais
def calculate_slider_limits():
    """Calcula os limites mínimo e máximo para cada variável baseado nos dados reais"""
    limits = {}
    
    # Variáveis RUP e seus limites
    rup_variables = {
        'sessions_days': 'sessions_days',
        'weeks_active': 'weeks_active', 
        'events_total': 'events_total',
        'days_active': 'days_active',
        'features_distinct': 'features_distinct'
    }
    
    for slider_name, column_name in rup_variables.items():
        if column_name in df_users.columns:
            min_val = int(df_users[column_name].min())
            max_val = int(df_users[column_name].max())
            limits[slider_name] = {
                'min': min_val,
                'max': max_val,
                'current_min': min_val,
                'current_max': max_val
            }
        else:
            # Fallback se a coluna não existir
            limits[slider_name] = {
                'min': 1,
                'max': 100,
                'current_min': 1,
                'current_max': 100
            }
    
    return limits

# Calcular os limites
SLIDER_LIMITS = calculate_slider_limits()

# Variáveis disponíveis para segmentação
SEGMENTATION_VARIABLES = {
    'sessions_days': 'Sessões (dias distintos)',
    'weeks_active': 'Semanas ativas',
    'events_total': 'Total de interações',
    'days_active': 'Dias ativos',
    'features_distinct': 'Features distintas',
    'first_seen': 'Data de Primeiro Acesso'
}

# Dicionário global de cores para padronização
GLOBAL_COLORS = {
    # Cores para tipos de dispositivo (valores reais do df_interactions)
    'device_desktop': '#1f77b4',     # Azul
    'device_mobile': '#ff7f0e',      # Laranja
    'device_tablet': '#2ca02c',      # Verde
    'device_smarttv': '#d62728',     # Vermelho
    'device_console': '#9467bd',     # Roxo
    
    # Cores para classificações de evento (valores reais do df_interactions)
    'event_Criação e Edição': '#ffa500',           # Amarelo
    'event_Engajamento Social': '#e377c2',         # Rosa
    'event_Exportação e Download': '#8c564b',      # Marrom
    'event_Mari IA': '#17becf',                    # Azul claro
    'event_Visualização e Acesso': '#bcbd22',      # Verde oliva
    'event_Não Especificado': '#7f7f7f',           # Cinza
}

# Função para gerar controles dinâmicos de faixas
def generate_threshold_inputs(num_groups, var_name):
    """Gera inputs dinâmicos para definir faixas de segmentação com distribuição igual"""
    if var_name not in df_users.columns:
        return []
    
    # Tratar datas de forma especial
    if var_name == 'first_seen':
        # Converter para datetime e obter min/max
        dates = pd.to_datetime(df_users[var_name]).dt.tz_localize(None)
        min_val = dates.min().date()
        max_val = dates.max().date()
        
        inputs = []
        for i in range(num_groups - 1):
            # Calcular limite para distribuição igual entre grupos (em dias)
            days_diff = (max_val - min_val).days
            threshold_days = round(min_val.toordinal() + (i + 1) * days_diff / num_groups)
            threshold_value = pd.Timestamp.fromordinal(threshold_days).date()
            
            inputs.append(
                ui.input_date(
                    f"threshold_{i}",
                    f"Limite Grupo {i+1} → {i+2}",
                    value=threshold_value,
                    min=min_val,
                    max=max_val
                )
            )
        return inputs
    else:
        # Para variáveis numéricas
        min_val = int(df_users[var_name].min())
        max_val = int(df_users[var_name].max())
        
        inputs = []
        for i in range(num_groups - 1):
            # Calcular limite para distribuição igual entre grupos
            # Usar round() para obter o número inteiro mais próximo
            if var_name == 'days_active' and i == 0:
                # Para days_active, primeiro limite começa em 5
                threshold_value = 5
            else:
                threshold_value = round(min_val + (i + 1) * (max_val - min_val) / num_groups)
            
            inputs.append(
                ui.input_numeric(
                    f"threshold_{i}",
                    f"Limite Grupo {i+1} → {i+2}",
                    value=threshold_value,
                    min=min_val,
                    max=max_val
                )
            )
        return inputs

# Função para carregar o logo
def load_logo():
    try:
        with open('media/logo_aprendizap.png', 'rb') as f:
            logo_data = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{logo_data}"
    except FileNotFoundError:
        return None

# Função para carregar o favicon (versão otimizada)
def load_favicon():
    """Carrega o logo como favicon, com versão SVG otimizada"""
    try:
        # Criar um favicon SVG simples com as cores do AprendiZAP
        favicon_svg = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
            <defs>
                <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#8A2BE2;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#f72585;stop-opacity:1" />
                </linearGradient>
            </defs>
            <rect width="32" height="32" rx="6" fill="url(#grad1)"/>
            <text x="16" y="22" font-family="Arial, sans-serif" font-size="18" font-weight="bold" 
                  text-anchor="middle" fill="white">A</text>
        </svg>
        """
        # Adicionar timestamp para cache-busting
        import time
        timestamp = str(int(time.time()))
        return f"data:image/svg+xml;base64,{base64.b64encode(favicon_svg.encode()).decode()}#{timestamp}"
    except Exception:
        # Fallback para emoji de livro se houver erro
        return "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48dGV4dCB5PSIuOWVtIiBmb250LXNpemU9IjkwIj7wn5SaPC90ZXh0Pjwvc3ZnPg=="

# Função para gerar favicon em diferentes tamanhos
def generate_favicon_sizes():
    """Gera favicons em diferentes tamanhos para melhor compatibilidade"""
    import time
    timestamp = str(int(time.time()))
    
    # Favicon 16x16
    favicon_16 = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">
        <defs>
            <linearGradient id="grad16" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#8A2BE2;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#f72585;stop-opacity:1" />
            </linearGradient>
        </defs>
        <rect width="16" height="16" rx="3" fill="url(#grad16)"/>
        <text x="8" y="11" font-family="Arial, sans-serif" font-size="10" font-weight="bold" 
              text-anchor="middle" fill="white">A</text>
    </svg>
    """
    
    # Favicon 32x32
    favicon_32 = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
        <defs>
            <linearGradient id="grad32" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#8A2BE2;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#f72585;stop-opacity:1" />
            </linearGradient>
        </defs>
        <rect width="32" height="32" rx="6" fill="url(#grad32)"/>
        <text x="16" y="22" font-family="Arial, sans-serif" font-size="18" font-weight="bold" 
              text-anchor="middle" fill="white">A</text>
    </svg>
    """
    
    return {
        '16x16': f"data:image/svg+xml;base64,{base64.b64encode(favicon_16.encode()).decode()}#{timestamp}",
        '32x32': f"data:image/svg+xml;base64,{base64.b64encode(favicon_32.encode()).decode()}#{timestamp}"
    }

# Função para configurar a fonte Montserrat
def setup_montserrat_font():
    """Configura a fonte Montserrat para matplotlib com fallback robusto"""
    try:
        # Usar apenas fontes que estão garantidamente disponíveis no Windows
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'sans-serif']
        
        # Remover avisos de fonte
        import warnings
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.font_manager')
        warnings.filterwarnings('ignore', message='findfont: Font family.*not found')
        
        return False  # Sempre retorna False pois não usamos Montserrat
    except Exception as e:
        print(f"Erro ao configurar fonte: {e}")
        # Fallback para fonte padrão
        plt.rcParams['font.family'] = 'sans-serif'
        return False

# Função para carregar o CSS externo
def load_css():
    """Carrega o arquivo CSS externo"""
    try:
        with open('styles.css', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("Arquivo styles.css não encontrado. Usando estilos padrão.")
        return ""


# ======================================================================================
# 2. A INTERFACE DO USUÁRIO (UI)
# Define a aparência e os controles interativos do dashboard.
# ======================================================================================
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style(load_css()),
        ui.tags.title("AprendiZAP - Simulador RUP"),
        # Múltiplos tamanhos de favicon para melhor compatibilidade
        ui.tags.link(rel="icon", type="image/svg+xml", sizes="any", href=load_favicon()),
        ui.tags.link(rel="icon", type="image/svg+xml", sizes="16x16", href=generate_favicon_sizes()['16x16']),
        ui.tags.link(rel="icon", type="image/svg+xml", sizes="32x32", href=generate_favicon_sizes()['32x32']),
        ui.tags.link(rel="apple-touch-icon", sizes="180x180", href=generate_favicon_sizes()['32x32']),
        ui.tags.link(rel="shortcut icon", href=load_favicon()),
        ui.tags.meta(name="description", content="Simulador de Segmentação de Usuários RUP - AprendiZAP"),
        ui.tags.meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        ui.tags.meta(name="theme-color", content="#8A2BE2"),
        ui.tags.meta(name="author", content="AprendiZAP"),
        ui.tags.meta(name="keywords", content="AprendiZAP, RUP, segmentação, usuários, dashboard, analytics"),
        # Meta tags para forçar atualização do cache
        ui.tags.meta(http_equiv="Cache-Control", content="no-cache, no-store, must-revalidate"),
        ui.tags.meta(http_equiv="Pragma", content="no-cache"),
        ui.tags.meta(http_equiv="Expires", content="0"),
        # Open Graph para redes sociais
        ui.tags.meta(property="og:title", content="AprendiZAP - Simulador RUP"),
        ui.tags.meta(property="og:description", content="Simulador de Segmentação de Usuários RUP - AprendiZAP"),
        ui.tags.meta(property="og:image", content=load_favicon()),
        ui.tags.meta(property="og:type", content="website"),
        # Twitter Card
        ui.tags.meta(name="twitter:card", content="summary"),
        ui.tags.meta(name="twitter:title", content="AprendiZAP - Simulador RUP"),
        ui.tags.meta(name="twitter:description", content="Simulador de Segmentação de Usuários RUP - AprendiZAP"),
        ui.tags.meta(name="twitter:image", content=load_favicon())
    ),
    ui.div(
        ui.div(
            ui.tags.img(src=load_logo(), alt="AprendiZAP Logo", style="max-width: 200px; height: auto;") if load_logo() else ui.h1("AprendiZAP", style="color: #8A2BE2; font-family: 'Montserrat', sans-serif; font-weight: 700;"),
            class_="logo-container"
        ),
        ui.h1("Simulador de Segmentação de Usuários (RUP)", 
              style="text-align: center; color: #8A2BE2; font-family: 'Montserrat', sans-serif; font-weight: 600; margin-bottom: 30px;"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Ajuste os Critérios da RUP"),
                ui.input_slider(
                    "min_sessoes", 
                    "Mínimo de Sessões (dias distintos)", 
                    min=1, 
                    max=SLIDER_LIMITS['sessions_days']['max'], 
                    value=2
                ),
                ui.input_slider(
                    "min_semanas", 
                    "Mínimo de Semanas Ativas", 
                    min=SLIDER_LIMITS['weeks_active']['min'], 
                    max=SLIDER_LIMITS['weeks_active']['max'], 
                    value=2
                ),
                ui.input_slider(
                    "min_interacoes", 
                    "Mínimo de Interações (eventos)", 
                    min=SLIDER_LIMITS['events_total']['min'], 
                    max=SLIDER_LIMITS['events_total']['max'], 
                    value=10
                ),
                ui.input_slider(
                    "min_dias", 
                    "Mínimo de Dias Ativos", 
                    min=SLIDER_LIMITS['days_active']['min'], 
                    max=SLIDER_LIMITS['days_active']['max'], 
                    value=2
                ),
                ui.input_slider(
                    "min_features", 
                    "Mínimo de Features Distintas", 
                    min=SLIDER_LIMITS['features_distinct']['min'], 
                    max=SLIDER_LIMITS['features_distinct']['max'], 
                    value=1
                ),
                ui.hr(style="border-color: rgba(255,255,255,0.3); margin: 20px 0;"),
                ui.h4("Opções de Visualização"),
                ui.input_checkbox("show_rup_only", "Mostrar apenas usuários RUP", value=False),
                ui.input_checkbox("show_post_mari", "Mostrar apenas dados após Mari IA (ago/2024)", value=False),
                ui.input_date_range("date_range", "Filtrar por período", 
                                  start=pd.to_datetime(df_users['first_seen']).min().date() if 'first_seen' in df_users.columns else None,
                                  end=pd.to_datetime(df_users['first_seen']).max().date() if 'first_seen' in df_users.columns else None),
                ui.hr(style="border-color: rgba(255,255,255,0.3); margin: 20px 0;"),
                ui.h4("Filtros Cruzados"),
                ui.input_checkbox("enable_cross_filters", "Habilitar filtros cruzados", value=True),
                ui.output_ui("cross_filter_controls"),
                
                ui.hr(style="border-color: rgba(255,255,255,0.3); margin: 20px 0;"),
                ui.h4("Segmentação Dinâmica"),
                ui.input_select("segmentation_variable", "Variável para segmentar", choices=SEGMENTATION_VARIABLES, selected="days_active"),
                ui.input_slider("num_groups", "Número de grupos", min=2, max=5, value=3, step=1),
                ui.tags.div(
                    ui.tags.h5("Definir Faixas dos Grupos", style="color: #ffffff; margin-top: 15px; margin-bottom: 10px;"),
                    ui.output_ui("segmentation_thresholds"),
                    id="segmentation_thresholds_container"
                ),
                ui.hr(style="border-color: rgba(255,255,255,0.3); margin: 20px 0;"),
                
                # Escala dos Gráficos - movida para depois das faixas dos grupos
                ui.h4("Escala dos Gráficos", style="margin-top: 20px;"),
                ui.input_radio_buttons("chart_scale", "Escala dos Gráficos", 
                                     choices={"absolute": "Números Absolutos", "proportional": "Proporcionais"}, 
                                     selected="proportional"),
                ui.input_numeric("y_axis_max", "Valor Máximo do Eixo Y (apenas para escala absoluta)", 
                               value=100, min=1, max=10000, step=10),
                ui.hr(style="border-color: rgba(255,255,255,0.3); margin: 20px 0;"),
                
                # Filtro de primeiras interações
                ui.h4("Filtro de Interações", style="margin-top: 20px;"),
                ui.input_slider("first_interactions", "Analisar X primeiras interações", 
                               min=1, max=100, value=10, step=1,
                               ticks=False),
                
                # Opções de visualização
                ui.h4("Opções de Visualização", style="margin-top: 20px;"),
                ui.input_radio_buttons("segmentation_view", "Visualização da Segmentação", 
                                     choices={"grouped": "Agrupada", "temporal": "Temporal"}, 
                                     selected="temporal"),
                
                # Botão para calcular gráficos - movido para o final
                ui.tags.div(
                    ui.input_action_button("calculate_btn", "Calcular Gráficos", class_="btn-primary", style="width: 100%; margin-top: 20px;"),
                    style="margin: 20px 0;"
                ),
            ),
            ui.div(
        ui.output_ui("kpi_panel"), # Painel dinâmico para os KPIs
                ui.hr(style="border-color: #8A2BE2; margin: 30px 0;"), # Linha horizontal para separar
                ui.div(
                    ui.div(
                        ui.h4("Distribuição de Usuários", style="text-align: center; color: #8A2BE2; margin-bottom: 15px;"),
        ui.output_plot("rup_distribution_plot"), # Gráfico de distribuição
                        style="flex: 1; margin-right: 10px;"
                    ),
                    ui.div(
                        ui.h4("Evolução Temporal RUP vs Não-RUP", style="text-align: center; color: #8A2BE2; margin-bottom: 15px;"),
                        ui.output_plot("temporal_plot"), # Gráfico temporal
                        style="flex: 1; margin-left: 10px;"
                    ),
                    style="display: flex; gap: 20px; margin-top: 20px;"
                ),
                ui.hr(style="border-color: #8A2BE2; margin: 40px 0 20px 0;"),
                ui.h3("Segmentação dos Usuários Reais", style="text-align: center; color: #8A2BE2; margin-bottom: 20px; font-family: 'Montserrat', sans-serif;"),
                ui.div(
                    ui.h4("Distribuição da Variável de Segmentação", style="text-align: center; color: #8A2BE2; margin-bottom: 15px;"),
                    ui.output_plot("segmentation_histogram"),
                    style="margin-bottom: 30px;"
                ),
                ui.div(
                    ui.div(
                        ui.h4("Distribuição por Grupos", style="text-align: center; color: #8A2BE2; margin-bottom: 15px;"),
                        ui.output_plot("segmentation_bar_plot"),
                        style="flex: 1; margin-right: 10px;"
                    ),
                    ui.div(
                        ui.h4("Evolução Temporal dos Grupos", style="text-align: center; color: #8A2BE2; margin-bottom: 15px;"),
                        ui.output_plot("segmentation_line_plot"),
                        style="flex: 1; margin-left: 10px;"
                    ),
                    style="display: flex; gap: 20px; margin-top: 20px;"
                ),
                ui.hr(style="border-color: #8A2BE2; margin: 40px 0 20px 0;"),
                ui.h3("Análise da Segmentação", style="text-align: center; color: #8A2BE2; margin-bottom: 20px; font-family: 'Montserrat', sans-serif;"),
                ui.output_ui("segmentation_analysis_ui"),
        ui.hr(style="border-color: #8A2BE2; margin: 40px 0 20px 0;"),
        ui.h3("Trajetória Individual", style="text-align: center; color: #8A2BE2; margin-bottom: 20px; font-family: 'Montserrat', sans-serif;"),
                ui.div(
                    ui.h4("Usuários Extremos Selecionados", style="text-align: center; color: #8A2BE2; margin-bottom: 15px;"),
                    ui.output_ui("extreme_users_info"),
                    style="margin-bottom: 20px;"
                ),
                ui.div(
                    ui.h4("Trajetórias Individuais", style="text-align: center; color: #8A2BE2; margin-bottom: 15px; font-size: 16px; font-weight: bold;"),
                    ui.div(
                        ui.h5("Trajetórias Individuais - Melhor vs Pior Usuário", style="text-align: center; color: #8A2BE2; margin-bottom: 10px; font-size: 14px; font-weight: bold;"),
                        ui.output_plot("trajectory_best_plot"),
                        style="margin-bottom: 30px;"
                    ),
                    style="margin-top: 20px;"
                ),
                class_="main-content"
            ),
        ),
    ),
)


# ======================================================================================
# 3. A LÓGICA DO SERVIDOR (SERVER)
# Define como as entradas (sliders) afetam as saídas (KPIs e gráfico).
# ======================================================================================

def server(input, output, session):
    
    @output
    @render.ui
    def segmentation_analysis_ui():
        """Gera UI dinâmica para análise de segmentação baseada no modo de visualização"""
        if input.segmentation_view() == "temporal":
            # Modo evolução temporal: 4 gráficos separados
            return ui.div(
                ui.div(
                    ui.h4("Classificação de Evento - Evolução Temporal", style="text-align: center; color: #8A2BE2; margin-bottom: 15px;"),
                    ui.output_plot("seg_event_temporal_plot"),
                    style="margin-bottom: 20px;"
                ),
                ui.div(
                    ui.h4("Tipo de Dispositivo - Evolução Temporal", style="text-align: center; color: #8A2BE2; margin-bottom: 15px;"),
                    ui.output_plot("seg_device_temporal_plot"),
                    style="margin-bottom: 20px;"
                ),
                style="margin-top: 20px;"
            )
        else:
            # Modo normal: 2 gráficos empilhados
            return ui.div(
                ui.div(
                    ui.h4("Interações por Classificação de Evento", style="text-align: center; color: #8A2BE2; margin-bottom: 15px;"),
                    ui.output_plot("event_classification_plot"),
                    style="flex: 1; margin-right: 10px;"
                ),
                ui.div(
                    ui.h4("Interações por Tipo de Dispositivo", style="text-align: center; color: #8A2BE2; margin-bottom: 15px;"),
                    ui.output_plot("device_interactions_plot"),
                    style="flex: 1; margin-left: 10px;"
                ),
                style="display: flex; gap: 20px; margin-top: 20px;"
            )
    
    # Evento para limpar filtros cruzados
    @reactive.Effect
    @reactive.event(input.clear_cross_filters)
    def clear_cross_filters():
        # Limpar seleções dos filtros cruzados
        # Como não podemos modificar diretamente os inputs, vamos usar uma abordagem diferente
        pass

    # Função para criar grupos baseados em faixas personalizadas
    def create_custom_groups(df, var_name, num_groups):
        """Cria grupos baseados nas faixas personalizadas definidas pelo usuário"""
        try:
            if num_groups == 1:
                return pd.Series(['Grupo 1'] * len(df), index=df.index)
            
            # Obter os limites definidos pelo usuário
            thresholds = []
            for i in range(num_groups - 1):
                try:
                    threshold = getattr(input, f'threshold_{i}')()
                    thresholds.append(threshold)
                except Exception:
                    # Fallback para distribuição igual se não conseguir obter o valor
                    if var_name == 'first_seen':
                        # Para datas, converter para datetime
                        dates = pd.to_datetime(df[var_name]).dt.tz_localize(None)
                        min_val = dates.min()
                        max_val = dates.max()
                        days_diff = (max_val - min_val).days
                        threshold_days = round(min_val.toordinal() + (i + 1) * days_diff / num_groups)
                        threshold = pd.Timestamp.fromordinal(threshold_days).date()
                    else:
                        # Para variáveis numéricas
                        min_val = df[var_name].min()
                        max_val = df[var_name].max()
                        threshold = round(min_val + (i + 1) * (max_val - min_val) / num_groups)
                    thresholds.append(threshold)
            
            # Ordenar os limites
            thresholds = sorted(thresholds)
            
            # Criar os grupos usando pd.cut com os limites personalizados
            if var_name == 'first_seen':
                # Para datas, converter para datetime e criar bins
                dates = pd.to_datetime(df[var_name]).dt.tz_localize(None)
                min_val = dates.min()
                max_val = dates.max()
                bins = [min_val] + [pd.to_datetime(t) for t in thresholds] + [max_val]
                bins[0] = pd.Timestamp.min  # Para incluir o valor mínimo
                bins[-1] = pd.Timestamp.max  # Para incluir o valor máximo
            else:
                # Para variáveis numéricas
                bins = [df[var_name].min()] + thresholds + [df[var_name].max()]
                bins[0] = float('-inf')  # Para incluir o valor mínimo
                bins[-1] = float('inf')  # Para incluir o valor máximo
            
            # Criar grupos com labels invertidos: Grupo 1 = melhor (maior valor), Grupo N = pior (menor valor)
            labels = [f'Grupo {i+1}' for i in range(num_groups)]
            groups = pd.cut(df[var_name], bins=bins, labels=labels)
            
            # Inverter a ordem dos grupos para que Grupo 1 seja o melhor (maior valor)
            group_mapping = {f'Grupo {i+1}': f'Grupo {num_groups-i}' for i in range(num_groups)}
            groups = groups.map(group_mapping)
            
            return groups
        except Exception as e:
            print(f"Erro na criação de grupos: {e}")
            # Fallback para distribuição igual
            try:
                if var_name == 'first_seen':
                    # Para datas, converter para datetime
                    dates = pd.to_datetime(df[var_name]).dt.tz_localize(None)
                    min_val = dates.min()
                    max_val = dates.max()
                    days_diff = (max_val - min_val).days
                    bins = [pd.Timestamp.fromordinal(round(min_val.toordinal() + i * days_diff / num_groups)) for i in range(num_groups + 1)]
                    bins[0] = pd.Timestamp.min
                    bins[-1] = pd.Timestamp.max
                else:
                    # Para variáveis numéricas
                    min_val = df[var_name].min()
                    max_val = df[var_name].max()
                    # Calcular bins com distribuição igual usando números inteiros
                    bins = [round(min_val + i * (max_val - min_val) / num_groups) for i in range(num_groups + 1)]
                    bins[0] = float('-inf')
                    bins[-1] = float('inf')
                
                groups = pd.cut(df[var_name], bins=bins, labels=[f'Grupo {i+1}' for i in range(num_groups)])
                
                # Inverter a ordem dos grupos para que Grupo 1 seja o melhor (maior valor)
                group_mapping = {f'Grupo {i+1}': f'Grupo {num_groups-i}' for i in range(num_groups)}
                groups = groups.map(group_mapping)
                return groups
            except:
                return pd.Series(['Grupo 1'] * len(df), index=df.index)

    # @reactive.Calc: O coração da reatividade.
    # Esta função recalcula o DataFrame sempre que um slider muda.
    @reactive.Calc
    def calculate_rup():
        # Pega os valores atuais dos sliders
        rup_min_sessoes = input.min_sessoes()
        rup_min_semanas = input.min_semanas()
        rup_min_interacoes = input.min_interacoes()
        rup_min_dias = input.min_dias()
        rup_min_features = input.min_features()

        # Cria uma cópia para não alterar o DataFrame original
        df = df_users.copy()
        
        # Renomear coluna uid para unique_id se existir, senão criar usando o índice
        if 'uid' in df.columns:
            df = df.rename(columns={'uid': 'unique_id'})
        elif 'unique_id' not in df.columns:
            df['unique_id'] = df.index.astype(str)
        
        # Aplica a lógica de RUP com os valores dinâmicos dos sliders
        df["in_RUP"] = (
            (df["sessions_days"] >= rup_min_sessoes) &
            (df["weeks_active"] >= rup_min_semanas) &
            (df["events_total"] >= rup_min_interacoes) &
            (df["days_active"] >= rup_min_dias) &
            (df["features_distinct"] >= rup_min_features)
        )
        return df

    # Renderiza os controles dinâmicos de faixas
    @output
    @render.ui
    def segmentation_thresholds():
        """Renderiza os controles dinâmicos para definir faixas de segmentação"""
        try:
            var_name = input.segmentation_variable()
            num_groups = input.num_groups()
            
            if var_name not in df_users.columns:
                return ui.p("Variável não encontrada nos dados", style="color: red;")
            
            # Criar inputs dinâmicos para cada limite
            inputs = []
            
            if var_name == 'first_seen':
                # Tratar datas de forma especial
                dates = pd.to_datetime(df_users[var_name]).dt.tz_localize(None)
                min_val = dates.min().date()
                max_val = dates.max().date()
                
                # Adicionar informações sobre os limites
                info_text = f"Limites da variável: {min_val} a {max_val}"
                explanation_text = "Grupo 1 (verde) = usuários mais recentes, Grupo N (vermelho) = usuários mais antigos"
                inputs.append(ui.p(info_text, style="font-size: 12px; color: white; margin-bottom: 5px;"))
                inputs.append(ui.p(explanation_text, style="font-size: 11px; color: white; margin-bottom: 10px; font-weight: bold;"))
            else:
                # Para variáveis numéricas
                min_val = int(df_users[var_name].min())
                max_val = int(df_users[var_name].max())
                
                # Adicionar informações sobre os limites
                info_text = f"Limites da variável: {min_val} a {max_val}"
                explanation_text = "Grupo 1 (verde) = melhor performance, Grupo N (vermelho) = pior performance"
                inputs.append(ui.p(info_text, style="font-size: 12px; color: white; margin-bottom: 5px;"))
                inputs.append(ui.p(explanation_text, style="font-size: 11px; color: white; margin-bottom: 10px; font-weight: bold;"))
            
            # Criar inputs para cada limite (num_groups - 1)
            if var_name == 'first_seen':
                for i in range(num_groups - 1):
                    # Calcular valor padrão baseado na distribuição igual (em dias)
                    days_diff = (max_val - min_val).days
                    threshold_days = round(min_val.toordinal() + (i + 1) * days_diff / num_groups)
                    default_value = pd.Timestamp.fromordinal(threshold_days).date()
                    
                    inputs.append(
                        ui.input_date(
                            f"threshold_{i}",
                            f"Limite: Grupo {num_groups-i} (≤) → Grupo {num_groups-i-1} (>)",
                            value=default_value,
                            min=min_val,
                            max=max_val
                        )
                    )
            else:
                # Para variáveis numéricas
                for i in range(num_groups - 1):
                    # Calcular valor padrão baseado na distribuição igual
                    # Usar round() para obter o número inteiro mais próximo
                    default_value = round(min_val + (i + 1) * (max_val - min_val) / num_groups)
                    
                    inputs.append(
                        ui.input_numeric(
                            f"threshold_{i}",
                            f"Limite: Grupo {num_groups-i} (≤) → Grupo {num_groups-i-1} (>)",
                            value=default_value,
                            min=min_val,
                            max=max_val,
                            step=1
                        )
                    )
            
            return ui.div(*inputs)
            
        except Exception as e:
            return ui.p(f"Erro ao carregar controles: {str(e)}", style="color: red;")

    # Renderiza controles de filtro cruzado
    @output
    @render.ui
    def cross_filter_controls():
        """Renderiza controles para filtros cruzados de device type e event classification"""
        if not input.enable_cross_filters():
            return ui.div()
        
        try:
            # Obter dados de interações para descobrir tipos disponíveis
            if df_interactions.empty:
                return ui.p("Dados de interações não disponíveis para filtros", style="color: red;")
            
            # Obter tipos de dispositivo únicos
            device_types = sorted(df_interactions['user_agent_device_type'].dropna().unique()) if 'user_agent_device_type' in df_interactions.columns else []
            
            # Obter classificações de evento únicas
            event_classes = sorted(df_interactions['event_classification'].dropna().unique()) if 'event_classification' in df_interactions.columns else []
            
            controls = []
            
            if device_types:
                controls.append(
                    ui.input_selectize(
                        "filter_device_types",
                        "Filtrar por Tipo de Dispositivo",
                        choices={dt: dt for dt in device_types},
                        selected=[],
                        multiple=True
                    )
                )
            
            if event_classes:
                controls.append(
                    ui.input_selectize(
                        "filter_event_classes",
                        "Filtrar por Classificação de Evento",
                        choices={ec: ec for ec in event_classes},
                        selected=[],
                        multiple=True
                    )
                )
            
            if controls:
                controls.append(
                    ui.input_action_button("clear_cross_filters", "Limpar Filtros Cruzados", 
                                         style="background-color: #f72585; color: white; border: none; padding: 5px 10px; border-radius: 3px; font-size: 12px; margin-top: 10px;")
                )
            
            return ui.div(*controls, style="margin: 10px 0; padding: 10px; background-color: rgba(138, 43, 226, 0.1); border-radius: 5px; border-left: 3px solid #8A2BE2;")
            
        except Exception as e:
            return ui.p(f"Erro ao carregar filtros cruzados: {str(e)}", style="color: red;")


    # Função para identificar usuários extremos
    def get_extreme_users():
        """Identifica o melhor e pior usuário baseado na variável de segmentação selecionada"""
        try:
            df_rup = calculate_rup()
            df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if df_rup.empty:
                return None, None, None
            
            var_name = input.segmentation_variable()
            
            if var_name not in df_rup.columns:
                return None, None, None
            
            # Aplicar filtros temporais
            if input.show_rup_only():
                df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if input.show_post_mari():
                df_rup = df_rup[df_rup['first_seen'] >= '2024-08-01'].copy()
            
            # Aplicar filtro de data
            date_range = input.date_range()
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
                df_rup = df_rup[(df_rup['first_seen'].dt.date >= start_date) & (df_rup['first_seen'].dt.date <= end_date)].copy()
            
            if df_rup.empty:
                return None, None, None
            
            # Identificar melhor e pior usuário
            data = df_rup[var_name].dropna()
            if data.empty:
                return None, None, None
            
            best_idx = data.idxmax()
            worst_idx = data.idxmin()
            
            best_user = df_rup.loc[best_idx]
            worst_user = df_rup.loc[worst_idx]
            
            return best_user, worst_user, var_name
            
        except Exception as e:
            print(f"Erro ao identificar usuários extremos: {e}")
            return None, None, None

    # Renderiza informações dos usuários extremos
    @output
    @render.ui
    def extreme_users_info():
        """Exibe informações dos usuários extremos selecionados"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                return ui.p("Clique em 'Calcular Gráficos' para visualizar os dados", style="text-align: center; color: #666;")
            
            best_user, worst_user, var_name = get_extreme_users()
            
            if best_user is None or worst_user is None:
                return ui.p("Nenhum usuário encontrado com os filtros selecionados", style="text-align: center; color: #666;")
            
            # Obter nome da variável para exibição
            var_display_name = SEGMENTATION_VARIABLES.get(var_name, var_name)
            
            # Criar informações dos usuários
            best_value = best_user[var_name]
            worst_value = worst_user[var_name]
            best_id = best_user.get('unique_id', best_user.get('uid', 'N/A'))
            worst_id = worst_user.get('unique_id', worst_user.get('uid', 'N/A'))
            
            return ui.div(
                ui.div(
                    ui.h5("Melhor Usuário", style="color: #2ca02c; font-weight: bold; margin-bottom: 5px;"),
                    ui.p(f"ID: {best_id}", style="margin: 2px 0; font-size: 14px;"),
                    ui.p(f"{var_display_name}: {best_value:,.0f}".replace(",", "."), style="margin: 2px 0; font-size: 14px; font-weight: bold;"),
                    style="flex: 1; text-align: center; padding: 15px; background-color: rgba(44, 160, 44, 0.1); border-radius: 8px; margin-right: 10px;"
                ),
                ui.div(
                    ui.h5("Pior Usuário", style="color: #d62728; font-weight: bold; margin-bottom: 5px;"),
                    ui.p(f"ID: {worst_id}", style="margin: 2px 0; font-size: 14px;"),
                    ui.p(f"{var_display_name}: {worst_value:,.0f}".replace(",", "."), style="margin: 2px 0; font-size: 14px; font-weight: bold;"),
                    style="flex: 1; text-align: center; padding: 15px; background-color: rgba(214, 39, 40, 0.1); border-radius: 8px; margin-left: 10px;"
                ),
                style="display: flex; gap: 20px; margin: 10px 0;"
            )
            
        except Exception as e:
            return ui.p(f"Erro ao carregar informações dos usuários: {str(e)}", style="color: red; text-align: center;")

    # Renderiza o painel de KPIs
    @output
    @render.ui
    def kpi_panel():
        df_rup = calculate_rup()
        rup_count = df_rup["in_RUP"].sum()
        rup_percentage = (rup_count / TOTAL_USERS) * 100

        return ui.div(
            ui.h3("Resultados da Simulação"),
            ui.p(f"Número de usuários na RUP: {rup_count:,.0f}".replace(",", ".")),
            ui.p(f"Percentual do Total: {rup_percentage:.2f}%"),
            class_="kpi-panel"
        )

    # Renderiza o gráfico de barras
    @output
    @render.plot
    def rup_distribution_plot():
        # Verificar se o botão foi clicado
        if not input.calculate_btn():
            fig, ax = plt.subplots(figsize=(3, 4))
            ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Distribuição de Usuários RUP', fontsize=14, fontweight='bold')
            return fig
        
        df_rup = calculate_rup()
        
        # Aplicar filtros temporais
        if input.show_rup_only():
            df_rup = df_rup[df_rup["in_RUP"] == True].copy()
        
        if input.show_post_mari():
            # Filtrar dados após agosto de 2024
            df_rup = df_rup[df_rup["first_seen"] >= "2024-08-01"].copy()
        
        # Aplicar filtro de data
        date_range = input.date_range()
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            # Converter first_seen para datetime se necessário e remover timezone
            df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
            df_rup = df_rup[(df_rup['first_seen'].dt.date >= start_date) & (df_rup['first_seen'].dt.date <= end_date)].copy()
        
        counts = df_rup["in_RUP"].value_counts().sort_index()
        
        # Criar um novo Series com a ordem correta: RUP=True primeiro, RUP=False segundo
        if len(counts) == 2:
            # Se temos ambos os valores, ordenar corretamente
            ordered_counts = pd.Series([
                counts.get(True, 0),  # RUP=True primeiro
                counts.get(False, 0)  # RUP=False segundo
            ], index=['RUP', 'Não RUP'])
        elif len(counts) == 1:
            # Se temos apenas um valor, criar o outro como 0
            if True in counts.index:
                ordered_counts = pd.Series([counts[True], 0], index=['RUP', 'Não RUP'])
            else:
                ordered_counts = pd.Series([0, counts[False]], index=['RUP', 'Não RUP'])
        else:
            # Fallback se não houver dados
            ordered_counts = pd.Series([0, 0], index=['RUP', 'Não RUP'])
        
        # Configurar o estilo do matplotlib
        plt.style.use('default')
        setup_montserrat_font()
        
        fig, ax = plt.subplots(figsize=(3, 4))
        
        # Cores personalizadas: RUP=True (#8A2BE2), RUP=False (cinza)
        colors = ["#8A2BE2", "#808080"]  # Roxo para RUP=True, Cinza para RUP=False
        bars = ax.bar(ordered_counts.index, ordered_counts.values, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
        
        # Estilizar o gráfico
        ax.set_title("Distribuição de Usuários Dentro e Fora da RUP", 
                    fontsize=16, fontweight='600', color='#8A2BE2', pad=20)
        ax.set_ylabel("Quantidade de Usuários", fontsize=12, fontweight='500', color='#333')
        ax.set_xlabel("Categoria de Usuário", fontsize=12, fontweight='500', color='#333')
        
        # Personalizar as barras
        for i, (bar, count) in enumerate(zip(bars, ordered_counts.values)):
            # Adicionar rótulos de contagem em cima das barras
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (ordered_counts.max() * 0.01), 
                   f'{count:,.0f}'.replace(",", "."), 
                   ha='center', va='bottom', fontweight='600', fontsize=11)
            
            # Adicionar percentual
            if ordered_counts.sum() > 0:
                percentage = (count / ordered_counts.sum()) * 100
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, 
                       f'{percentage:.1f}%', 
                       ha='center', va='center', fontweight='600', fontsize=11, color='white')
        
        # Personalizar o eixo Y
        ax.set_ylim(0, ordered_counts.max() * 1.15)
        ax.grid(True, alpha=0.3, axis='y')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#ccc')
        ax.spines['bottom'].set_color('#ccc')
        
        # Ajustar layout
        plt.tight_layout()
        
        return fig

    # Renderiza o gráfico temporal
    @output
    @render.plot
    def temporal_plot():
        # Verificar se o botão foi clicado
        if not input.calculate_btn():
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Evolução Temporal RUP vs Não RUP', fontsize=14, fontweight='bold')
            return fig
        
        df_rup = calculate_rup().copy()  # Criar uma cópia para evitar warnings
        
        # Aplicar filtros de visualização
        if input.show_rup_only():
            df_rup = df_rup[df_rup["in_RUP"] == True].copy()
        
        if input.show_post_mari():
            # Filtrar dados após agosto de 2024
            df_rup = df_rup[df_rup["first_seen"] >= "2024-08-01"].copy()
        
        # Aplicar filtro de data
        date_range = input.date_range()
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            # Converter first_seen para datetime se necessário e remover timezone
            df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
            df_rup = df_rup[(df_rup['first_seen'].dt.date >= start_date) & (df_rup['first_seen'].dt.date <= end_date)].copy()
        else:
            # Converter first_seen para datetime se necessário, removendo timezone se existir
            df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
        
        # Verificar se temos dados suficientes
        if len(df_rup) == 0:
            # Criar um gráfico vazio se não houver dados
            fig, ax = plt.subplots(figsize=(3, 4))
            ax.text(0.5, 0.5, 'Nenhum dado disponível\ncom os filtros selecionados', 
                   ha='center', va='center', transform=ax.transAxes, 
                   fontsize=12, color='#666')
            ax.set_title("Evolução Temporal", fontsize=14, fontweight='600', color='#8A2BE2', pad=15)
            return fig
        
        # Sempre agrupar por mês para evolução temporal RUP vs não RUP
        df_rup['period'] = df_rup['first_seen'].dt.to_period('M')
        period_counts = df_rup.groupby(['period', 'in_RUP'], observed=True).size().unstack(fill_value=0)
        period_label = "Mês"
        
        # Renomear colunas para melhor visualização
        if True in period_counts.columns:
            period_counts['RUP'] = period_counts[True]
        if False in period_counts.columns:
            period_counts['Não RUP'] = period_counts[False]
        
        # Remover colunas booleanas originais
        period_counts = period_counts.drop(columns=[col for col in period_counts.columns if col in [True, False]], errors='ignore')
        
        # Configurar o estilo do matplotlib
        plt.style.use('default')
        setup_montserrat_font()
        
        fig, ax = plt.subplots(figsize=(3, 4))
        
        # Plotar linhas
        if 'RUP' in period_counts.columns:
            ax.plot(period_counts.index.astype(str), period_counts['RUP'], 
                   color='#8A2BE2', linewidth=2.5, marker='o', markersize=4, label='RUP')
        
        if 'Não RUP' in period_counts.columns:
            ax.plot(period_counts.index.astype(str), period_counts['Não RUP'], 
                   color='#808080', linewidth=2.5, marker='s', markersize=4, label='Não RUP')
        
        # Adicionar linha vertical em agosto de 2024 (apenas se estiver no range dos dados)
        if not period_counts.empty:
            # Verificar se agosto de 2024 está no range dos dados
            aug_2024 = pd.Period('2024-08', freq='M')
            if aug_2024 in period_counts.index or (period_counts.index >= aug_2024).any():
                ax.axvline(x='2024-08', color='#f72585', linestyle='--', linewidth=2, alpha=0.8)
                ax.text('2024-08', ax.get_ylim()[1] * 0.9, 'Mari IA', 
                       rotation=90, verticalalignment='top', color='#f72585', 
                       fontweight='bold', fontsize=10)
        
        
        # Estilizar o gráfico
        ax.set_title("Evolução Temporal", fontsize=14, fontweight='600', color='#8A2BE2', pad=15)
        ax.set_ylabel("Novos Usuários", fontsize=11, fontweight='500', color='#333')
        ax.set_xlabel(period_label, fontsize=11, fontweight='500', color='#333')
        
        # Rotacionar labels do eixo x para melhor legibilidade
        ax.tick_params(axis='x', rotation=0)
        
        # Adicionar legenda
        ax.legend(loc='upper right', fontsize=10)
        
        # Personalizar o eixo Y
        ax.grid(True, alpha=0.3, axis='y')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#ccc')
        ax.spines['bottom'].set_color('#ccc')
        
        # Ajustar layout
        plt.tight_layout()
        
        # Adicionar pontos nas linhas para melhor visualização
        if 'RUP' in period_counts.columns:
            ax.scatter(period_counts.index.astype(str), period_counts['RUP'], 
                      color='#8A2BE2', s=30, alpha=0.8, zorder=5)
        
        if 'Não RUP' in period_counts.columns:
            ax.scatter(period_counts.index.astype(str), period_counts['Não RUP'], 
                      color='#808080', s=30, alpha=0.8, zorder=5)

        return fig

    # Renderiza o histograma da variável de segmentação
    @output
    @render.plot
    def segmentation_histogram():
        """Histograma da variável selecionada para segmentação"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Distribuição da Variável de Segmentação', fontsize=14, fontweight='bold')
                return fig
            
            df_rup = calculate_rup()
            df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, 'Nenhum usuário RUP encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Distribuição da Variável de Segmentação', fontsize=14, fontweight='bold')
                return fig
            
            # Aplicar filtros temporais
            if input.show_rup_only():
                df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if input.show_post_mari():
                df_rup = df_rup[df_rup['first_seen'] >= '2024-08-01'].copy()
            
            # Aplicar filtro de data
            date_range = input.date_range()
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
                df_rup = df_rup[(df_rup['first_seen'].dt.date >= start_date) & (df_rup['first_seen'].dt.date <= end_date)].copy()
            
            
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, 'Nenhum dado disponível para os filtros selecionados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Distribuição da Variável de Segmentação', fontsize=14, fontweight='bold')
                return fig
            
            # Obter parâmetros de segmentação
            var_name = input.segmentation_variable()
            num_groups = input.num_groups()
            
            if var_name not in df_rup.columns:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, f'Variável {var_name} não encontrada nos dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Distribuição da Variável de Segmentação', fontsize=14, fontweight='bold')
                return fig
            
            # Obter dados da variável
            data = df_rup[var_name].dropna()
            
            if data.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, 'Nenhum dado válido para a variável selecionada', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Distribuição da Variável de Segmentação', fontsize=14, fontweight='bold')
                return fig
            
            # Tratar datas de forma especial
            if var_name == 'first_seen':
                # Para datas, converter para datetime e usar data filtrada
                data = pd.to_datetime(data).dt.tz_localize(None)
                data_filtered = data  # Para datas, não filtrar outliers por IQR
            else:
                # Detectar e excluir outliers severos usando IQR para variáveis numéricas
                Q1 = data.quantile(0.25)
                Q3 = data.quantile(0.75)
                IQR = Q3 - Q1
                
                # Definir limites para outliers severos (1.5 * IQR é moderado, 3 * IQR é severo)
                lower_bound = Q1 - 3 * IQR
                upper_bound = Q3 + 3 * IQR
                
                # Filtrar outliers severos
                data_filtered = data[(data >= lower_bound) & (data <= upper_bound)]
                
                # Se muitos dados foram removidos, usar método menos restritivo
                if len(data_filtered) < len(data) * 0.5:  # Se mais de 50% foram removidos
                    # Usar método menos restritivo (2 * IQR)
                    lower_bound = Q1 - 2 * IQR
                    upper_bound = Q3 + 2 * IQR
                    data_filtered = data[(data >= lower_bound) & (data <= upper_bound)]
                
                # Se ainda muitos dados foram removidos, usar percentis
                if len(data_filtered) < len(data) * 0.7:  # Se mais de 30% foram removidos
                    # Usar percentis 5% e 95%
                    lower_bound = data.quantile(0.05)
                    upper_bound = data.quantile(0.95)
                    data_filtered = data[(data >= lower_bound) & (data <= upper_bound)]
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if var_name == 'first_seen':
                # Para datas, criar histograma temporal
                n, bins, patches = ax.hist(data_filtered, bins=30, alpha=0.7, color='#8A2BE2', edgecolor='white', linewidth=1)
                
                # Adicionar linhas verticais para os limites dos grupos (usando dados filtrados)
                min_val = data_filtered.min()
                max_val = data_filtered.max()
                
                # Calcular limites dos grupos (em dias)
                days_diff = (max_val - min_val).days
                group_limits = []
                for i in range(num_groups - 1):
                    limit_days = round(min_val.toordinal() + (i + 1) * days_diff / num_groups)
                    limit = pd.Timestamp.fromordinal(limit_days)
                    group_limits.append(limit)
                    ax.axvline(x=limit, color='#f72585', linestyle='--', linewidth=2, alpha=0.8)
            else:
                # Para variáveis numéricas
                n, bins, patches = ax.hist(data_filtered, bins=30, alpha=0.7, color='#8A2BE2', edgecolor='white', linewidth=1)
                
                # Adicionar linhas verticais para os limites dos grupos (usando dados filtrados)
                min_val = data_filtered.min()
                max_val = data_filtered.max()
                
                # Calcular limites dos grupos
                group_limits = []
                for i in range(num_groups - 1):
                    limit = round(min_val + (i + 1) * (max_val - min_val) / num_groups)
                    group_limits.append(limit)
                    ax.axvline(x=limit, color='#f72585', linestyle='--', linewidth=2, alpha=0.8)
            
            # Adicionar linhas para min e max
            ax.axvline(x=min_val, color='#2ca02c', linestyle='-', linewidth=2, alpha=0.8, label='Mínimo')
            ax.axvline(x=max_val, color='#d62728', linestyle='-', linewidth=2, alpha=0.8, label='Máximo')
            
            # Estilizar o gráfico
            ax.set_title(f"Distribuição de {SEGMENTATION_VARIABLES[var_name]}", 
                        fontsize=16, fontweight='600', color='#8A2BE2', pad=20)
            ax.set_ylabel("Frequência", fontsize=12, fontweight='500', color='#333')
            ax.set_xlabel(SEGMENTATION_VARIABLES[var_name], fontsize=12, fontweight='500', color='#333')
            
            # Adicionar estatísticas (usando dados filtrados)
            mean_val = data_filtered.mean()
            median_val = data_filtered.median()
            ax.axvline(x=mean_val, color='#ff7f0e', linestyle=':', linewidth=2, alpha=0.8, label=f'Média: {mean_val:.1f}')
            ax.axvline(x=median_val, color='#17becf', linestyle=':', linewidth=2, alpha=0.8, label=f'Mediana: {median_val:.1f}')
            
            # Adicionar legenda
            ax.legend(loc='upper right', fontsize=10)
            
            # Personalizar o eixo Y
            ax.grid(True, alpha=0.3, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#ccc')
            ax.spines['bottom'].set_color('#ccc')
            
            # Adicionar informações sobre os grupos e outliers
            outliers_removed = len(data) - len(data_filtered)
            outlier_percentage = (outliers_removed / len(data)) * 100 if len(data) > 0 else 0
            
            group_info = f"Limites dos grupos: {min_val:.0f} | " + " | ".join([f"{limit:.0f}" for limit in group_limits]) + f" | {max_val:.0f}"
            outlier_info = f"Outliers removidos: {outliers_removed} ({outlier_percentage:.1f}%)"
            
            ax.text(0.02, 0.98, group_info, transform=ax.transAxes, fontsize=10, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            ax.text(0.02, 0.90, outlier_info, transform=ax.transAxes, fontsize=9, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no histograma de segmentação: {e}")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f'Erro ao carregar histograma: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Erro no Histograma', fontsize=14, fontweight='bold')
            return fig

    # Renderiza o gráfico de colunas da segmentação
    @output
    @render.plot
    def segmentation_bar_plot():
        """Gráfico de colunas da segmentação dos usuários RUP=True"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Segmentação dos Usuários Reais', fontsize=14, fontweight='bold')
                return fig
            
            df_rup = calculate_rup()
            df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum usuário RUP encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Segmentação dos Usuários RUP', fontsize=14, fontweight='bold')
                return fig
            
            # Aplicar filtros temporais
            if input.show_rup_only():
                df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if input.show_post_mari():
                df_rup = df_rup[df_rup['first_seen'] >= '2024-08-01'].copy()
            
            # Aplicar filtro de data
            date_range = input.date_range()
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                # Converter first_seen para datetime se necessário e remover timezone
                df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
                df_rup = df_rup[(df_rup['first_seen'].dt.date >= start_date) & (df_rup['first_seen'].dt.date <= end_date)].copy()
            
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum dado disponível para os filtros selecionados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Segmentação dos Usuários RUP', fontsize=14, fontweight='bold')
                return fig
            
            # Obter parâmetros de segmentação
            var_name = input.segmentation_variable()
            num_groups = input.num_groups()
            
            # Criar grupos baseados nas faixas personalizadas
            df_rup['group'] = create_custom_groups(df_rup, var_name, num_groups)
            
            # Contar usuários por grupo e ordenar corretamente (Grupo 1 primeiro)
            group_counts = df_rup['group'].value_counts()
            
            # Ordenar os grupos: Grupo 1, Grupo 2, etc.
            group_order = sorted(group_counts.index, key=lambda x: int(x.split()[-1]) if isinstance(x, str) and ' ' in x else int(x))
            group_counts = group_counts.reindex(group_order)
            
            # Criar cores da escala verde-vermelho (Grupo 1 = verde, Grupo N = vermelho)
            colors = plt.cm.RdYlGn_r(np.linspace(0, 1, len(group_counts)))
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            fig, ax = plt.subplots(figsize=(3, 4))
            bars = ax.bar(range(len(group_counts)), group_counts.values, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
            
            # Adicionar valores nas barras
            for i, (bar, count) in enumerate(zip(bars, group_counts.values)):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + (group_counts.max() * 0.01),
                       f'{count:,.0f}'.replace(",", "."), 
                       ha='center', va='bottom', fontweight='600', fontsize=11)
            
            # Configurar eixos
            ax.set_xticks(range(len(group_counts)))
            ax.set_xticklabels(group_counts.index)
            
            # Estilizar o gráfico
            ax.set_title("Distribuição por Grupos de Segmentação", 
                        fontsize=16, fontweight='600', color='#8A2BE2', pad=20)
            ax.set_ylabel("Quantidade de Usuários", fontsize=12, fontweight='500', color='#333')
            ax.set_xlabel("Grupos", fontsize=12, fontweight='500', color='#333')
            
            # Personalizar o eixo Y
            ax.set_ylim(0, group_counts.max() * 1.15)
            ax.grid(True, alpha=0.3, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#ccc')
            ax.spines['bottom'].set_color('#ccc')
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico de barras: {e}")
            fig, ax = plt.subplots(figsize=(3, 4))
            ax.text(0.5, 0.5, f'Erro ao carregar gráfico: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Erro na Segmentação', fontsize=14, fontweight='bold')
            return fig

    # Renderiza o gráfico de linhas da segmentação
    @output
    @render.plot
    def segmentation_line_plot():
        """Gráfico de linhas da evolução temporal dos grupos de segmentação"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Evolução Temporal dos Grupos', fontsize=14, fontweight='bold')
                return fig
            
            df_rup = calculate_rup()
            df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum usuário RUP encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Evolução Temporal dos Grupos', fontsize=14, fontweight='bold')
                return fig
            
            # Aplicar filtros temporais
            if input.show_rup_only():
                df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if input.show_post_mari():
                df_rup = df_rup[df_rup['first_seen'] >= '2024-08-01'].copy()
            
            # Aplicar filtro de data
            date_range = input.date_range()
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                # Converter first_seen para datetime se necessário e remover timezone
                df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
                df_rup = df_rup[(df_rup['first_seen'].dt.date >= start_date) & (df_rup['first_seen'].dt.date <= end_date)].copy()
            
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum dado disponível para os filtros selecionados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Evolução Temporal dos Grupos', fontsize=14, fontweight='bold')
                return fig
            
            # Obter parâmetros de segmentação
            var_name = input.segmentation_variable()
            num_groups = input.num_groups()
            
            # Criar grupos baseados nas faixas personalizadas
            df_rup['group'] = create_custom_groups(df_rup, var_name, num_groups)
            
            # Converter first_seen para datetime e remover timezone
            df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
            df_rup['month'] = df_rup['first_seen'].dt.to_period('M')
            
            # Agrupar por mês e grupo
            monthly_counts = df_rup.groupby(['month', 'group'], observed=True).size().unstack(fill_value=0)
            
            # Ordenar as colunas (Grupo 1 primeiro)
            group_order = sorted(monthly_counts.columns, key=lambda x: int(x.split()[-1]) if isinstance(x, str) and ' ' in x else int(x))
            monthly_counts = monthly_counts[group_order]
            
            # Criar cores da escala verde-vermelho (Grupo 1 = verde, Grupo N = vermelho)
            colors = plt.cm.RdYlGn_r(np.linspace(0, 1, len(monthly_counts.columns)))
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            fig, ax = plt.subplots(figsize=(3, 4))
            
            for i, group in enumerate(monthly_counts.columns):
                ax.plot(monthly_counts.index.astype(str), monthly_counts[group], 
                       marker='o', linewidth=2.5, markersize=4, color=colors[i], label=group)
            
            # Adicionar linha vertical para Mari IA
            ax.axvline(x='2024-08', color='#f72585', linestyle='--', linewidth=2, alpha=0.8)
            ax.text('2024-08', ax.get_ylim()[1] * 0.9, 'Mari IA', rotation=90, 
                   ha='right', va='top', fontsize=10, color='#f72585', fontweight='bold')
            
            # Estilizar o gráfico
            ax.set_title("Evolução Temporal dos Grupos de Segmentação", 
                        fontsize=14, fontweight='600', color='#8A2BE2', pad=15)
            ax.set_ylabel("Novos Usuários", fontsize=11, fontweight='500', color='#333')
            ax.set_xlabel("Mês", fontsize=11, fontweight='500', color='#333')
            
            # Rotacionar labels do eixo x para melhor legibilidade
            ax.tick_params(axis='x', rotation=0)
            
            # Adicionar legenda
            ax.legend(loc='upper right', fontsize=10)
            
            # Personalizar o eixo Y
            ax.grid(True, alpha=0.3, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#ccc')
            ax.spines['bottom'].set_color('#ccc')
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico de linhas: {e}")
            fig, ax = plt.subplots(figsize=(3, 4))
            ax.text(0.5, 0.5, f'Erro ao carregar gráfico: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Erro na Segmentação', fontsize=14, fontweight='bold')
        return fig

    # Renderiza o gráfico de interações por dispositivo
    @output
    @render.plot
    def device_interactions_plot():
        """Gráfico de barras empilhadas mostrando interações por tipo de dispositivo e grupo"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Interações por Tipo de Dispositivo', fontsize=14, fontweight='bold')
                return fig
            
            # Obter dados de segmentação
            df_rup = calculate_rup()
            df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, 'Nenhum usuário RUP encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Interações por Tipo de Dispositivo', fontsize=14, fontweight='bold')
                return fig
            
            # Aplicar filtros temporais
            if input.show_rup_only():
                df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if input.show_post_mari():
                df_rup = df_rup[df_rup['first_seen'] >= '2024-08-01'].copy()
            
            # Aplicar filtro de data
            date_range = input.date_range()
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
                df_rup = df_rup[(df_rup['first_seen'].dt.date >= start_date) & (df_rup['first_seen'].dt.date <= end_date)].copy()
            
            # Obter parâmetros de segmentação
            var_name = input.segmentation_variable()
            num_groups = input.num_groups()
            
            # Criar grupos baseados nas faixas personalizadas
            df_rup['group'] = create_custom_groups(df_rup, var_name, num_groups)
            
            # Verificar se temos dados de interações
            if df_interactions.empty or 'unique_id' not in df_interactions.columns or 'user_agent_device_type' not in df_interactions.columns:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, 'Dados de interações não disponíveis', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Interações por Tipo de Dispositivo', fontsize=14, fontweight='bold')
                return fig
            
            # Verificar se temos a coluna unique_id
            if 'unique_id' not in df_rup.columns:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, 'Coluna unique_id não encontrada nos dados de usuários', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Interações por Tipo de Dispositivo', fontsize=14, fontweight='bold')
                return fig
            
            # Filtrar interações apenas para usuários RUP (otimização de memória)
            unique_users_rup = set(df_rup['unique_id'].unique())
            
            # Aplicar filtros de forma mais eficiente
            mask = df_interactions['unique_id'].isin(unique_users_rup)
            
            # Aplicar filtros cruzados se habilitados
            if input.enable_cross_filters():
                selected_device_types = input.filter_device_types()
                if selected_device_types:
                    mask &= df_interactions['user_agent_device_type'].isin(selected_device_types)
                
                selected_event_classes = input.filter_event_classes()
                if selected_event_classes:
                    mask &= df_interactions['event_classification'].isin(selected_event_classes)
            
            # Aplicar máscara de uma vez
            df_interactions_filtered = df_interactions[mask].copy()
            
            # Aplicar filtro de X primeiras interações
            first_interactions_count = input.first_interactions()
            if first_interactions_count:
                # Aplicar filtro por usuário (X primeiras interações de cada usuário)
                df_interactions_filtered = df_interactions_filtered.groupby('unique_id').head(first_interactions_count)
            
            # Agrupar interações por usuário e tipo de dispositivo
            if input.segmentation_view() == "temporal":
                # Para evolução temporal, agrupar também por numero_interacao
                if 'numero_interacao' in df_interactions_filtered.columns:
                    df_interactions_grouped = df_interactions_filtered.groupby(['unique_id', 'user_agent_device_type', 'numero_interacao']).size().reset_index(name='interaction_count')
                else:
                    df_interactions_grouped = df_interactions_filtered.groupby(['unique_id', 'user_agent_device_type']).size().reset_index(name='interaction_count')
            else:
                # Agrupamento normal (total de interações)
                df_interactions_grouped = df_interactions_filtered.groupby(['unique_id', 'user_agent_device_type']).size().reset_index(name='interaction_count')
            
            # Limpar memória
            del df_interactions_filtered
            gc.collect()
            
            df_merged = df_rup.merge(df_interactions_grouped, on='unique_id', how='inner')
            
            if df_merged.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, 'Nenhuma interação encontrada para os filtros selecionados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Interações por Tipo de Dispositivo', fontsize=14, fontweight='bold')
                return fig
            
            # Somar interações por dispositivo e grupo
            if input.segmentation_view() == "temporal" and 'numero_interacao' in df_merged.columns:
                # Para evolução temporal, agrupar por dispositivo, grupo e numero_interacao
                device_group_counts = df_merged.groupby(['user_agent_device_type', 'group', 'numero_interacao'])['interaction_count'].sum().unstack(fill_value=0)
            else:
                # Agrupamento normal (total de interações)
                device_group_counts = df_merged.groupby(['user_agent_device_type', 'group'])['interaction_count'].sum().unstack(fill_value=0)
            
            # Limpar memória
            del df_merged
            del df_interactions_grouped
            gc.collect()
            
            # Ordenar as colunas (Grupo 1 primeiro)
            group_order = sorted(device_group_counts.columns, key=lambda x: int(x.split()[-1]) if isinstance(x, str) and ' ' in x else int(x))
            device_group_counts = device_group_counts[group_order]
            
            # Aplicar escala proporcional se selecionada
            chart_scale = input.chart_scale()
            if chart_scale == "proportional":
                # Normalizar para proporções (0-1) por coluna (grupo)
                device_group_counts = device_group_counts.div(device_group_counts.sum(axis=0), axis=1)
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            fig, ax = plt.subplots(figsize=(8, 5))
            
            # Usar cores padronizadas para dispositivos (valores reais)
            device_colors = {
                'desktop': GLOBAL_COLORS['device_desktop'],
                'mobile': GLOBAL_COLORS['device_mobile'],
                'tablet': GLOBAL_COLORS['device_tablet'],
                'smarttv': GLOBAL_COLORS['device_smarttv'],
                'console': GLOBAL_COLORS['device_console']
            }
            
            # Verificar se deve mostrar evolução temporal
            if input.segmentation_view() == "temporal" and 'numero_interacao' in device_group_counts.columns:
                # Gráfico de evolução temporal (linhas)
                for group in group_order:
                    if group in device_group_counts.columns:
                        group_data = device_group_counts[group]
                        for device_type in group_data.index:
                            if device_type in device_colors:
                                values = group_data.loc[device_type].values
                                days = group_data.columns
                                ax.plot(days, values, marker='o', linewidth=2, markersize=4,
                                       label=f"{device_type} - {group}", color=device_colors[device_type], alpha=0.8)
                
                ax.set_xlabel('Dia de Interação', fontsize=10)
                ax.set_ylabel('Número de Interações', fontsize=10)
                ax.set_title('Evolução Temporal - Tipo de Dispositivo', fontsize=14, fontweight='bold')
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                ax.grid(True, alpha=0.3)
                
            else:
                # Gráfico de barras empilhadas (modo normal)
                bottom = np.zeros(len(device_group_counts.columns))
                bars = []
                
                for device_type in device_group_counts.index:
                    device_data = device_group_counts.loc[device_type]
                    color = device_colors.get(device_type, '#17becf')  # Azul claro como fallback
                    
                    # Usar índices numéricos para evitar problemas de alinhamento
                    x_positions = range(len(device_group_counts.columns))
                    bars.append(ax.bar(x_positions, device_data, 
                                      bottom=bottom, color=color, alpha=0.8, 
                                      edgecolor='white', linewidth=1, label=device_type))
                    bottom += device_data
                
                # Estilizar o gráfico
                scale_label = "Proporção" if chart_scale == "proportional" else "Total de Interações"
                
                # Adicionar informações de filtros no título
                title = "Interações por Grupo de Usuário e Tipo de Dispositivo"
                if input.enable_cross_filters():
                    selected_device_types = input.filter_device_types()
                    selected_event_classes = input.filter_event_classes()
                    filters = []
                if selected_device_types:
                    filters.append(f"Dispositivos: {', '.join(selected_device_types)}")
                if selected_event_classes:
                    filters.append(f"Eventos: {', '.join(selected_event_classes)}")
                if filters:
                    title += f"\n(Filtrado: {' | '.join(filters)})"
            
            ax.set_title(title, fontsize=16, fontweight='600', color='#8A2BE2', pad=20)
            ax.set_ylabel(scale_label, fontsize=12, fontweight='500', color='#333')
            ax.set_xlabel("Grupo de Usuário", fontsize=12, fontweight='500', color='#333')
            
            # Configurar eixo X com labels corretos
            ax.set_xticks(range(len(device_group_counts.columns)))
            ax.set_xticklabels(device_group_counts.columns)
            ax.tick_params(axis='x', rotation=0)
            
            # Adicionar legenda
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
            
            # Personalizar o eixo Y
            if chart_scale == "proportional":
                ax.set_ylim(0, 1)
            else:
                ax.set_ylim(0, None)
            
            ax.grid(True, alpha=0.3, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico de interações por dispositivo: {e}")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f'Erro ao carregar gráfico: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Erro na Análise de Dispositivos', fontsize=14, fontweight='bold')
        return fig

    # Renderiza o gráfico de interações por classificação de evento (modo agrupado)
    @output
    @render.plot
    def event_classification_plot():
        """Gráfico de barras empilhadas mostrando interações por classificação de evento e grupo"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Interações por Classificação de Evento', fontsize=14, fontweight='bold')
                return fig
            
            # Obter dados de segmentação
            df_rup = calculate_rup()
            df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, 'Nenhum usuário RUP encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Interações por Classificação de Evento', fontsize=14, fontweight='bold')
                return fig
            
            # Aplicar filtros temporais
            if input.show_rup_only():
                df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if input.show_post_mari():
                df_rup = df_rup[df_rup['first_seen'] >= '2024-08-01'].copy()
            
            # Aplicar filtro de data
            date_range = input.date_range()
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
                df_rup = df_rup[(df_rup['first_seen'].dt.date >= start_date) & (df_rup['first_seen'].dt.date <= end_date)].copy()
            
            # Obter parâmetros de segmentação
            var_name = input.segmentation_variable()
            num_groups = input.num_groups()
            
            # Criar grupos baseados nas faixas personalizadas
            df_rup['group'] = create_custom_groups(df_rup, var_name, num_groups)
            
            # Filtrar interações apenas para usuários RUP
            unique_users_rup = set(df_rup['unique_id'].unique())
            mask = df_interactions['unique_id'].isin(unique_users_rup)
            
            # Aplicar filtros cruzados se habilitados
            if input.enable_cross_filters():
                selected_device_types = input.filter_device_types()
                if selected_device_types:
                    mask &= df_interactions['user_agent_device_type'].isin(selected_device_types)
                
                selected_event_classes = input.filter_event_classes()
                if selected_event_classes:
                    mask &= df_interactions['event_classification'].isin(selected_event_classes)
            
            # Aplicar filtro de X primeiras interações
            first_interactions_count = input.first_interactions()
            if first_interactions_count:
                df_interactions_filtered = df_interactions[mask].copy()
                df_interactions_filtered = df_interactions_filtered.groupby('unique_id').head(first_interactions_count)
            else:
                df_interactions_filtered = df_interactions[mask].copy()
            
            # Agrupar interações por usuário e classificação de evento
            df_interactions_grouped = df_interactions_filtered.groupby(['unique_id', 'event_classification']).size().reset_index(name='interaction_count')
            
            # Fazer merge com dados de usuários
            df_merged = df_rup.merge(df_interactions_grouped, on='unique_id', how='inner')
            
            if df_merged.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, 'Nenhuma interação encontrada para os filtros selecionados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Interações por Classificação de Evento', fontsize=14, fontweight='bold')
                return fig
            
            # Somar interações por classificação de evento e grupo
            event_group_counts = df_merged.groupby(['event_classification', 'group'])['interaction_count'].sum().unstack(fill_value=0)
            
            # Ordenar as colunas (Grupo 1 primeiro)
            group_order = sorted(event_group_counts.columns, key=lambda x: int(x.split()[-1]) if isinstance(x, str) and ' ' in x else int(x))
            event_group_counts = event_group_counts[group_order]
            
            # Aplicar escala proporcional se selecionada
            chart_scale = input.chart_scale()
            if chart_scale == "proportional":
                event_group_counts = event_group_counts.div(event_group_counts.sum(axis=0), axis=1)
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            fig, ax = plt.subplots(figsize=(8, 5))
            
            # Usar cores padronizadas para eventos
            event_colors = {
                'Criação e Edição': GLOBAL_COLORS['event_Criação e Edição'],
                'Engajamento Social': GLOBAL_COLORS['event_Engajamento Social'],
                'Exportação e Download': GLOBAL_COLORS['event_Exportação e Download'],
                'Mari IA': GLOBAL_COLORS['event_Mari IA'],
                'Visualização e Acesso': GLOBAL_COLORS['event_Visualização e Acesso'],
                'Não Especificado': GLOBAL_COLORS['event_Não Especificado']
            }
            
            # Gráfico de barras empilhadas
            bottom = np.zeros(len(event_group_counts.columns))
            bars = []
            
            for event_class in event_group_counts.index:
                event_data = event_group_counts.loc[event_class]
                color = event_colors.get(event_class, '#17becf')
                
                if event_data.sum() > 0:
                    # Usar índices numéricos para evitar problemas de alinhamento
                    x_positions = range(len(event_group_counts.columns))
                    bars.append(ax.bar(x_positions, event_data, 
                                      bottom=bottom, color=color, alpha=0.8, 
                                      edgecolor='white', linewidth=1, label=event_class))
                    bottom += event_data
            
            # Estilizar o gráfico
            scale_label = "Proporção" if chart_scale == "proportional" else "Total de Interações"
            ax.set_ylabel(scale_label, fontsize=10, fontweight='500', color='#333')
            ax.set_title('Interações por Classificação de Evento', fontsize=14, fontweight='bold', color='#8A2BE2')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
            ax.grid(True, alpha=0.3, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico de classificação de eventos: {e}")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f'Erro ao carregar gráfico: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Erro na Classificação de Eventos', fontsize=14, fontweight='bold')
            return fig
            
            # Limpar memória
            del df_interactions_filtered
            gc.collect()
            
            df_merged = df_rup.merge(df_interactions_grouped, on='unique_id', how='inner')
            
            if df_merged.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, 'Nenhuma interação encontrada para os filtros selecionados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Interações por Classificação de Evento', fontsize=14, fontweight='bold')
                return fig
            
            # Somar interações por classificação de evento e grupo
            if input.segmentation_view() == "temporal" and 'numero_interacao' in df_merged.columns:
                # Para evolução temporal, agrupar por classificação, grupo e numero_interacao
                event_group_counts = df_merged.groupby(['event_classification', 'group', 'numero_interacao'])['interaction_count'].sum().unstack(fill_value=0)
            else:
                # Agrupamento normal (total de interações)
                event_group_counts = df_merged.groupby(['event_classification', 'group'])['interaction_count'].sum().unstack(fill_value=0)
            
            # Limpar memória
            del df_merged
            del df_interactions_grouped
            gc.collect()
            
            # Ordenar as colunas (Grupo 1 primeiro)
            if input.segmentation_view() == "temporal" and 'numero_interacao' in event_group_counts.columns:
                # Para evolução temporal, as colunas são números de interação
                group_order = sorted(event_group_counts.columns)
            else:
                # Para modo normal, as colunas são grupos
                group_order = sorted(event_group_counts.columns, key=lambda x: int(x.split()[-1]) if isinstance(x, str) and ' ' in x else int(x))
            event_group_counts = event_group_counts[group_order]
            
            # Aplicar escala proporcional se selecionada
            chart_scale = input.chart_scale()
            if chart_scale == "proportional":
                # Normalizar para proporções (0-1) por coluna (grupo)
                event_group_counts = event_group_counts.div(event_group_counts.sum(axis=0), axis=1)
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            fig, ax = plt.subplots(figsize=(8, 5))
            
            # Usar cores padronizadas para eventos (valores reais)
            event_colors = {
                'Criação e Edição': GLOBAL_COLORS['event_Criação e Edição'],
                'Engajamento Social': GLOBAL_COLORS['event_Engajamento Social'],
                'Exportação e Download': GLOBAL_COLORS['event_Exportação e Download'],
                'Mari IA': GLOBAL_COLORS['event_Mari IA'],
                'Visualização e Acesso': GLOBAL_COLORS['event_Visualização e Acesso'],
                'Não Especificado': GLOBAL_COLORS['event_Não Especificado']
            }
            
            # Verificar se deve mostrar evolução temporal
            if input.segmentation_view() == "temporal" and 'numero_interacao' in event_group_counts.columns:
                # Gráfico de evolução temporal (linhas)
                for group in group_order:
                    if group in event_group_counts.columns:
                        group_data = event_group_counts[group]
                        for event_class in group_data.index:
                            if event_class in event_colors:
                                values = group_data.loc[event_class].values
                                days = group_data.columns
                                ax.plot(days, values, marker='o', linewidth=2, markersize=4,
                                       label=f"{event_class} - {group}", color=event_colors[event_class], alpha=0.8)
                
                ax.set_xlabel('Dia de Interação', fontsize=10)
                ax.set_ylabel('Número de Interações', fontsize=10)
                ax.set_title('Evolução Temporal - Classificação de Evento', fontsize=14, fontweight='bold')
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                ax.grid(True, alpha=0.3)
                
            else:
                # Gráfico de barras empilhadas (modo normal)
                bottom = np.zeros(len(event_group_counts.columns))
                bars = []
                
                # Garantir que temos dados para plotar
                if not event_group_counts.empty:
                    for i, event_class in enumerate(event_group_counts.index):
                        event_data = event_group_counts.loc[event_class]
                        color = event_colors.get(event_class, f'C{i}')  # Usar cor do matplotlib se não encontrar
                        
                        # Verificar se há dados para este evento
                        if event_data.sum() > 0:
                            # Usar índices numéricos para evitar problemas de alinhamento
                            x_positions = range(len(event_group_counts.columns))
                            bars.append(ax.bar(x_positions, event_data, 
                                              bottom=bottom, color=color, alpha=0.8, 
                                              edgecolor='white', linewidth=1, label=event_class))
                            bottom += event_data
                
                # Estilizar o gráfico
                scale_label = "Proporção" if chart_scale == "proportional" else "Total de Interações"
            
            # Adicionar informações de filtros no título
            title = "Interações por Grupo de Usuário e Classificação de Evento"
            if input.enable_cross_filters():
                selected_device_types = input.filter_device_types()
                selected_event_classes = input.filter_event_classes()
                filters = []
                if selected_device_types:
                    filters.append(f"Dispositivos: {', '.join(selected_device_types)}")
                if selected_event_classes:
                    filters.append(f"Eventos: {', '.join(selected_event_classes)}")
                if filters:
                    title += f"\n(Filtrado: {' | '.join(filters)})"
            
            ax.set_title(title, fontsize=16, fontweight='600', color='#8A2BE2', pad=20)
            ax.set_ylabel(scale_label, fontsize=12, fontweight='500', color='#333')
            ax.set_xlabel("Grupo de Usuário", fontsize=12, fontweight='500', color='#333')
            
            # Configurar eixo X com labels corretos
            ax.set_xticks(range(len(event_group_counts.columns)))
            ax.set_xticklabels(event_group_counts.columns)
            ax.tick_params(axis='x', rotation=0)
            
            # Adicionar legenda
            ax.legend(loc='upper right', fontsize=10, title='Classificação de Evento')
            
            # Personalizar o eixo Y
            if chart_scale == "proportional":
                ax.set_ylim(0, 1)
            else:
                ax.set_ylim(0, None)
            
            ax.grid(True, alpha=0.3, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#ccc')
            ax.spines['bottom'].set_color('#ccc')
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico de classificação de eventos: {e}")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f'Erro ao carregar gráfico: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Erro na Análise de Classificação de Eventos', fontsize=14, fontweight='bold')
        return fig

    # Função auxiliar para obter dados de trajetória de um usuário específico
    def get_user_trajectory_data(user_id, group_name):
        """Obtém dados de trajetória temporal para um usuário específico"""
        try:
            if df_interactions.empty or 'unique_id' not in df_interactions.columns:
                return None, None
            
            # Filtrar interações do usuário específico de forma mais eficiente
            mask = df_interactions['unique_id'] == user_id
            
            # Aplicar filtros cruzados se habilitados
            if input.enable_cross_filters():
                selected_device_types = input.filter_device_types()
                if selected_device_types:
                    mask &= df_interactions['user_agent_device_type'].isin(selected_device_types)
                
                selected_event_classes = input.filter_event_classes()
                if selected_event_classes:
                    mask &= df_interactions['event_classification'].isin(selected_event_classes)
            
            # Aplicar filtro de X primeiras interações (primeiros X dias)
            first_interactions_count = input.first_interactions()
            if first_interactions_count and 'numero_interacao' in df_interactions.columns:
                mask &= df_interactions['numero_interacao'] <= first_interactions_count
            
            # Aplicar máscara de uma vez
            user_interactions = df_interactions[mask].copy()
            
            if user_interactions.empty:
                return None, None
            
            # Aplicar fallback se numero_interacao não existir
            if first_interactions_count and 'numero_interacao' not in df_interactions.columns and first_interactions_count < len(user_interactions):
                user_interactions = user_interactions.head(first_interactions_count)
            
            # Usar numero_interacao para agrupamento temporal
            if 'numero_interacao' in user_interactions.columns:
                user_interactions['day'] = user_interactions['numero_interacao']
            else:
                # Fallback para data_inicio se numero_interacao não existir
                if 'data_inicio' in user_interactions.columns:
                    user_interactions['day'] = pd.to_datetime(user_interactions['data_inicio']).dt.date
                elif 'timestamp' in user_interactions.columns:
                    user_interactions['day'] = pd.to_datetime(user_interactions['timestamp']).dt.date
                elif 'created_at' in user_interactions.columns:
                    user_interactions['day'] = pd.to_datetime(user_interactions['created_at']).dt.date
                else:
                    # Se não houver coluna de data, usar data padrão
                    user_interactions['day'] = pd.to_datetime('2024-01-01').date()
            
            # Agrupar por dia e tipo de dispositivo
            device_data = user_interactions.groupby(['day', 'user_agent_device_type']).size().unstack(fill_value=0)
            
            # Agrupar por dia e classificação de evento
            event_data = user_interactions.groupby(['day', 'event_classification']).size().unstack(fill_value=0)
            
            return device_data, event_data
            
        except Exception as e:
            print(f"Erro ao obter dados de trajetória para usuário {user_id}: {e}")
            return None, None


    # Gráfico de trajetória - Grupo 1 + Tipo de Dispositivo
    @output
    @render.plot
    def trajectory_g1_device():
        """Gráfico de trajetória temporal do melhor usuário por tipo de dispositivo"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Grupo 1 - Tipo de Dispositivo', fontsize=12, fontweight='bold')
                return fig
            
            best_user, worst_user, var_name = get_extreme_users()
            
            if best_user is None:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum usuário encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Grupo 1 - Tipo de Dispositivo', fontsize=12, fontweight='bold')
                return fig
            
            best_id = best_user.get('unique_id', best_user.get('uid', 'N/A'))
            worst_id = worst_user.get('unique_id', worst_user.get('uid', 'N/A'))
            
            device_data, _ = get_user_trajectory_data(best_id, 'Melhor Usuário')
            
            if device_data is None or device_data.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Grupo 1 - Tipo de Dispositivo', fontsize=12, fontweight='bold')
                return fig
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            fig, ax = plt.subplots(figsize=(3, 4))
            
            # Usar cores padronizadas para dispositivos (valores reais)
            device_colors = {
                'desktop': GLOBAL_COLORS['device_desktop'],
                'mobile': GLOBAL_COLORS['device_mobile'],
                'tablet': GLOBAL_COLORS['device_tablet'],
                'smarttv': GLOBAL_COLORS['device_smarttv'],
                'console': GLOBAL_COLORS['device_console']
            }
            
            # Preparar dados para barras empilhadas
            days = device_data.index
            bottom = np.zeros(len(days))
            
            # Plotar cada tipo de dispositivo como barra empilhada
            for device_type in device_data.columns:
                if device_data[device_type].sum() > 0:  # Só plotar se houver dados
                    color = device_colors.get(device_type, '#17becf')
                    values = device_data[device_type].values
                    ax.bar(days, values, bottom=bottom, 
                          label=device_type, color=color, alpha=0.8)
                    bottom += values
            
            ax.set_title(f"Tipo de Dispositivo", 
                        fontsize=12, fontweight='600', color='#8A2BE2', pad=10)
            ax.set_ylabel("Interações", fontsize=10, fontweight='500', color='#333')
            ax.set_xlabel("Dia", fontsize=10, fontweight='500', color='#333')
            
            # Configurar eixo X para mostrar números inteiros (dias)
            ax.tick_params(axis='x', rotation=0)
            ax.set_xticks(range(1, len(days) + 1))
            ax.set_xticklabels(range(1, len(days) + 1))
            
            # Adicionar legenda
            ax.legend(loc='upper right', fontsize=8)
            
            # Personalizar o eixo - escala fixa de 0 a 5
            ax.set_ylim(0, 5)
            ax.grid(True, alpha=0.3, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico de trajetória G1 device: {e}")
            fig, ax = plt.subplots(figsize=(3, 4))
            ax.text(0.5, 0.5, f'Erro: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Erro - Grupo 1 Device', fontsize=12, fontweight='bold')
            return fig

    # Gráfico de trajetória - Grupo 2 + Tipo de Dispositivo
    @output
    @render.plot
    def trajectory_g2_device():
        """Gráfico de trajetória temporal do pior usuário por tipo de dispositivo"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Grupo 2 - Tipo de Dispositivo', fontsize=12, fontweight='bold')
                return fig
            
            best_user, worst_user, var_name = get_extreme_users()
            
            if worst_user is None:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum usuário encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Grupo 2 - Tipo de Dispositivo', fontsize=12, fontweight='bold')
                return fig
            
            worst_id = worst_user.get('unique_id', worst_user.get('uid', 'N/A'))
            best_id = best_user.get('unique_id', best_user.get('uid', 'N/A'))
            
            device_data, _ = get_user_trajectory_data(worst_id, 'Pior Usuário')
            
            if device_data is None or device_data.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Grupo 2 - Tipo de Dispositivo', fontsize=12, fontweight='bold')
                return fig
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            fig, ax = plt.subplots(figsize=(3, 4))
            
            # Usar cores padronizadas para dispositivos (valores reais)
            device_colors = {
                'desktop': GLOBAL_COLORS['device_desktop'],
                'mobile': GLOBAL_COLORS['device_mobile'],
                'tablet': GLOBAL_COLORS['device_tablet'],
                'smarttv': GLOBAL_COLORS['device_smarttv'],
                'console': GLOBAL_COLORS['device_console']
            }
            
            # Preparar dados para barras empilhadas
            days = device_data.index
            bottom = np.zeros(len(days))
            
            # Plotar cada tipo de dispositivo como barra empilhada
            for device_type in device_data.columns:
                if device_data[device_type].sum() > 0:  # Só plotar se houver dados
                    color = device_colors.get(device_type, '#17becf')
                    values = device_data[device_type].values
                    ax.bar(days, values, bottom=bottom, 
                          label=device_type, color=color, alpha=0.8)
                    bottom += values
            
            ax.set_title(f"Tipo de Dispositivo", 
                        fontsize=12, fontweight='600', color='#8A2BE2', pad=10)
            ax.set_ylabel("Interações", fontsize=10, fontweight='500', color='#333')
            ax.set_xlabel("Dia", fontsize=10, fontweight='500', color='#333')
            
            # Configurar eixo X para mostrar números inteiros (dias)
            ax.tick_params(axis='x', rotation=0)
            ax.set_xticks(range(1, len(days) + 1))
            ax.set_xticklabels(range(1, len(days) + 1))
            
            # Adicionar legenda
            ax.legend(loc='upper right', fontsize=8)
            
            # Personalizar o eixo - escala fixa de 0 a 5
            ax.set_ylim(0, 5)
            ax.grid(True, alpha=0.3, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico de trajetória G2 device: {e}")
            fig, ax = plt.subplots(figsize=(3, 4))
            ax.text(0.5, 0.5, f'Erro: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Erro - Grupo 2 Device', fontsize=12, fontweight='bold')
            return fig

    # Gráfico de trajetória - Grupo 1 + Classificação de Evento
    @output
    @render.plot
    def trajectory_g1_event():
        """Gráfico de trajetória temporal do melhor usuário por classificação de evento"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Grupo 1 - Classificação de Evento', fontsize=12, fontweight='bold')
                return fig
            
            best_user, worst_user, var_name = get_extreme_users()
            
            if best_user is None:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum usuário encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Grupo 1 - Classificação de Evento', fontsize=12, fontweight='bold')
                return fig
            
            best_id = best_user.get('unique_id', best_user.get('uid', 'N/A'))
            worst_id = worst_user.get('unique_id', worst_user.get('uid', 'N/A'))
            
            _, event_data = get_user_trajectory_data(best_id, 'Melhor Usuário')
            
            if event_data is None or event_data.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Grupo 1 - Classificação de Evento', fontsize=12, fontweight='bold')
                return fig
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            fig, ax = plt.subplots(figsize=(3, 4))
            
            # Usar cores padronizadas para eventos (valores reais)
            event_colors = {
                'Criação e Edição': GLOBAL_COLORS['event_Criação e Edição'],
                'Engajamento Social': GLOBAL_COLORS['event_Engajamento Social'],
                'Exportação e Download': GLOBAL_COLORS['event_Exportação e Download'],
                'Mari IA': GLOBAL_COLORS['event_Mari IA'],
                'Visualização e Acesso': GLOBAL_COLORS['event_Visualização e Acesso'],
                'Não Especificado': GLOBAL_COLORS['event_Não Especificado']
            }
            
            # Visualização separada (barras empilhadas)
            days = event_data.index
            bottom = np.zeros(len(days))
            
            # Plotar cada classificação de evento como barra empilhada
            for event_class in event_data.columns:
                if event_data[event_class].sum() > 0:  # Só plotar se houver dados
                    color = event_colors.get(event_class, '#17becf')
                    values = event_data[event_class].values
                    ax.bar(days, values, bottom=bottom, 
                          label=event_class, color=color, alpha=0.8)
                    bottom += values
            ax.set_ylabel("Interações", fontsize=10, fontweight='500', color='#333')
            
            ax.set_title(f"Classificação de Evento", 
                        fontsize=12, fontweight='600', color='#8A2BE2', pad=10)
            ax.set_xlabel("Dia", fontsize=10, fontweight='500', color='#333')
            
            # Configurar eixo X para mostrar números inteiros (dias)
            ax.tick_params(axis='x', rotation=0)
            ax.set_xticks(range(1, len(days) + 1))
            ax.set_xticklabels(range(1, len(days) + 1))
            
            # Adicionar legenda
            ax.legend(loc='upper right', fontsize=8)
            
            # Personalizar o eixo - escala fixa de 0 a 5
            ax.set_ylim(0, 5)
            ax.grid(True, alpha=0.3, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico de trajetória G1 event: {e}")
            fig, ax = plt.subplots(figsize=(3, 4))
            ax.text(0.5, 0.5, f'Erro: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Erro - Grupo 1 Event', fontsize=12, fontweight='bold')
            return fig

    # Gráfico de trajetória - Grupo 2 + Classificação de Evento
    @output
    @render.plot
    def trajectory_g2_event():
        """Gráfico de trajetória temporal do pior usuário por classificação de evento"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Grupo 2 - Classificação de Evento', fontsize=12, fontweight='bold')
                return fig
            
            best_user, worst_user, var_name = get_extreme_users()
            
            if worst_user is None:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum usuário encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Grupo 2 - Classificação de Evento', fontsize=12, fontweight='bold')
                return fig
            
            worst_id = worst_user.get('unique_id', worst_user.get('uid', 'N/A'))
            best_id = best_user.get('unique_id', best_user.get('uid', 'N/A'))
            
            _, event_data = get_user_trajectory_data(worst_id, 'Pior Usuário')
            
            if event_data is None or event_data.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Grupo 2 - Classificação de Evento', fontsize=12, fontweight='bold')
                return fig
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            fig, ax = plt.subplots(figsize=(3, 4))
            
            # Usar cores padronizadas para eventos (valores reais)
            event_colors = {
                'Criação e Edição': GLOBAL_COLORS['event_Criação e Edição'],
                'Engajamento Social': GLOBAL_COLORS['event_Engajamento Social'],
                'Exportação e Download': GLOBAL_COLORS['event_Exportação e Download'],
                'Mari IA': GLOBAL_COLORS['event_Mari IA'],
                'Visualização e Acesso': GLOBAL_COLORS['event_Visualização e Acesso'],
                'Não Especificado': GLOBAL_COLORS['event_Não Especificado']
            }
            
            # Preparar dados para barras empilhadas
            days = event_data.index
            bottom = np.zeros(len(days))
            
            # Plotar cada classificação de evento como barra empilhada
            for event_class in event_data.columns:
                if event_data[event_class].sum() > 0:  # Só plotar se houver dados
                    color = event_colors.get(event_class, '#17becf')
                    values = event_data[event_class].values
                    ax.bar(days, values, bottom=bottom, 
                          label=event_class, color=color, alpha=0.8)
                    bottom += values
            
            ax.set_title(f"Classificação de Evento", 
                        fontsize=12, fontweight='600', color='#8A2BE2', pad=10)
            ax.set_ylabel("Interações", fontsize=10, fontweight='500', color='#333')
            ax.set_xlabel("Dia", fontsize=10, fontweight='500', color='#333')
            
            # Configurar eixo X para mostrar números inteiros (dias)
            ax.tick_params(axis='x', rotation=0)
            ax.set_xticks(range(1, len(days) + 1))
            ax.set_xticklabels(range(1, len(days) + 1))
            
            # Adicionar legenda
            ax.legend(loc='upper right', fontsize=8)
            
            # Personalizar o eixo - escala fixa de 0 a 5
            ax.set_ylim(0, 5)
            ax.grid(True, alpha=0.3, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico de trajetória G2 event: {e}")
            fig, ax = plt.subplots(figsize=(3, 4))
            ax.text(0.5, 0.5, f'Erro: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Erro - Grupo 2 Event', fontsize=12, fontweight='bold')
        return fig

    # ======================================================================================
    # GRÁFICO COMBINADO DE TRAJETÓRIAS INDIVIDUAIS (2x2)
    # ======================================================================================

    @output
    @render.plot
    def trajectory_combined_plot():
        """Gráfico combinado de trajetórias individuais - 2x2 (melhor/pior usuário)"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                fig, ax = plt.subplots(figsize=(12, 8))
                ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Trajetórias Individuais', fontsize=16, fontweight='bold')
                return fig
            
            best_user, worst_user, var_name = get_extreme_users()
            
            if best_user is None or worst_user is None:
                fig, ax = plt.subplots(figsize=(12, 8))
                ax.text(0.5, 0.5, 'Nenhum usuário encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Trajetórias Individuais', fontsize=16, fontweight='bold')
                return fig
            
            best_id = best_user.get('unique_id', best_user.get('uid', 'N/A'))
            worst_id = worst_user.get('unique_id', worst_user.get('uid', 'N/A'))
            
            # Obter dados de trajetória
            best_device_data, best_event_data = get_user_trajectory_data(best_id, 'Melhor Usuário')
            worst_device_data, worst_event_data = get_user_trajectory_data(worst_id, 'Pior Usuário')
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            # Criar 2 figuras separadas: uma para melhor usuário e uma para pior usuário
            # Cada figura terá 2 gráficos: eventos e dispositivos
            fig1, axes1 = plt.subplots(nrows=1, ncols=2, figsize=(12, 5))  # Melhor usuário
            fig2, axes2 = plt.subplots(nrows=1, ncols=2, figsize=(12, 5))  # Pior usuário
            
            # Cores padronizadas
            event_colors = {
                'Criação e Edição': GLOBAL_COLORS['event_Criação e Edição'],
                'Engajamento Social': GLOBAL_COLORS['event_Engajamento Social'],
                'Exportação e Download': GLOBAL_COLORS['event_Exportação e Download'],
                'Mari IA': GLOBAL_COLORS['event_Mari IA'],
                'Visualização e Acesso': GLOBAL_COLORS['event_Visualização e Acesso'],
                'Não Especificado': GLOBAL_COLORS['event_Não Especificado']
            }
            
            device_colors = {
                'desktop': GLOBAL_COLORS['device_desktop'],
                'mobile': GLOBAL_COLORS['device_mobile'],
                'tablet': GLOBAL_COLORS['device_tablet'],
                'smarttv': GLOBAL_COLORS['device_smarttv'],
                'console': GLOBAL_COLORS['device_console']
            }
            
            # Coletar todas as categorias para legendas unificadas
            all_event_classes = set()
            all_device_types = set()
            
            if best_event_data is not None and not best_event_data.empty:
                all_event_classes.update(best_event_data.columns)
            if worst_event_data is not None and not worst_event_data.empty:
                all_event_classes.update(worst_event_data.columns)
            if best_device_data is not None and not best_device_data.empty:
                all_device_types.update(best_device_data.columns)
            if worst_device_data is not None and not worst_device_data.empty:
                all_device_types.update(worst_device_data.columns)
            
            # Calcular escalas máximas para padronização
            max_event_y = 0
            max_device_y = 0
            max_days = 0
            
            for data in [best_event_data, worst_event_data]:
                if data is not None and not data.empty:
                    max_event_y = max(max_event_y, data.sum(axis=1).max())
                    max_days = max(max_days, len(data.index))
            
            for data in [best_device_data, worst_device_data]:
                if data is not None and not data.empty:
                    max_device_y = max(max_device_y, data.sum(axis=1).max())
                    max_days = max(max_days, len(data.index))
            
            # BLOCO 1: MELHOR USUÁRIO
            # Gráfico 1: Melhor Usuário - Classificação de Evento
            ax1 = axes1[0]
            if best_event_data is not None and not best_event_data.empty:
                days = best_event_data.index
                bottom = np.zeros(len(days))
                
                for event_class in all_event_classes:
                    if event_class in best_event_data.columns and best_event_data[event_class].sum() > 0:
                        color = event_colors.get(event_class, '#17becf')
                        values = best_event_data[event_class].values
                        ax1.bar(days, values, bottom=bottom, 
                              label=event_class, color=color, alpha=0.8)
                        bottom += values
                    elif event_class in best_event_data.columns:
                        # Adicionar barra vazia para manter consistência na legenda
                        ax1.bar(days, np.zeros(len(days)), bottom=bottom, 
                              label=event_class, color=event_colors.get(event_class, '#17becf'), alpha=0.3)
                
                ax1.set_title(f"Classificação de Evento", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
                ax1.set_ylabel("Interações", fontsize=10, fontweight='500', color='#333')
                ax1.set_xlabel("Dia", fontsize=10, fontweight='500', color='#333')
                ax1.set_ylim(0, max_event_y * 1.1 if max_event_y > 0 else 5)
                ax1.grid(True, alpha=0.3, axis='y')
                ax1.spines['top'].set_visible(False)
                ax1.spines['right'].set_visible(False)
            else:
                ax1.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title(f"Classificação de Evento", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
            
            # Gráfico 2: Melhor Usuário - Tipo de Dispositivo
            ax2 = axes1[1]
            if best_device_data is not None and not best_device_data.empty:
                days = best_device_data.index
                bottom = np.zeros(len(days))
                
                for device_type in all_device_types:
                    if device_type in best_device_data.columns and best_device_data[device_type].sum() > 0:
                        color = device_colors.get(device_type, '#17becf')
                        values = best_device_data[device_type].values
                        ax2.bar(days, values, bottom=bottom, 
                              label=device_type.title(), color=color, alpha=0.8)
                        bottom += values
                    elif device_type in best_device_data.columns:
                        # Adicionar barra vazia para manter consistência na legenda
                        ax2.bar(days, np.zeros(len(days)), bottom=bottom, 
                              label=device_type.title(), color=device_colors.get(device_type, '#17becf'), alpha=0.3)
                
                ax2.set_title(f"Tipo de Dispositivo", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
                ax2.set_ylabel("Interações", fontsize=10, fontweight='500', color='#333')
                ax2.set_xlabel("Dia", fontsize=10, fontweight='500', color='#333')
                ax2.set_ylim(0, max_device_y * 1.1 if max_device_y > 0 else 5)
                ax2.grid(True, alpha=0.3, axis='y')
                ax2.spines['top'].set_visible(False)
                ax2.spines['right'].set_visible(False)
                # Legenda para dispositivos no segundo gráfico do melhor usuário
                ax2.legend(loc='upper right', fontsize=8, framealpha=0.9)
            else:
                ax2.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title(f"Tipo de Dispositivo", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
            
            # BLOCO 2: PIOR USUÁRIO
            # Gráfico 3: Pior Usuário - Classificação de Evento
            ax3 = axes2[0]
            if worst_event_data is not None and not worst_event_data.empty:
                days = worst_event_data.index
                bottom = np.zeros(len(days))
                
                for event_class in all_event_classes:
                    if event_class in worst_event_data.columns and worst_event_data[event_class].sum() > 0:
                        color = event_colors.get(event_class, '#17becf')
                        values = worst_event_data[event_class].values
                        ax3.bar(days, values, bottom=bottom, 
                              label=event_class, color=color, alpha=0.8)
                        bottom += values
                    elif event_class in worst_event_data.columns:
                        # Adicionar barra vazia para manter consistência na legenda
                        ax3.bar(days, np.zeros(len(days)), bottom=bottom, 
                              label=event_class, color=event_colors.get(event_class, '#17becf'), alpha=0.3)
                
                ax3.set_title(f"Classificação de Evento", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
                ax3.set_ylabel("Interações", fontsize=10, fontweight='500', color='#333')
                ax3.set_xlabel("Dia", fontsize=10, fontweight='500', color='#333')
                ax3.set_ylim(0, max_event_y * 1.1 if max_event_y > 0 else 5)
                ax3.grid(True, alpha=0.3, axis='y')
                ax3.spines['top'].set_visible(False)
                ax3.spines['right'].set_visible(False)
                # Legenda para eventos no primeiro gráfico do pior usuário
                ax3.legend(loc='upper right', fontsize=8, framealpha=0.9)
            else:
                ax3.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax3.transAxes)
                ax3.set_title(f"Classificação de Evento", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
            
            # Gráfico 4: Pior Usuário - Tipo de Dispositivo
            ax4 = axes2[1]
            if worst_device_data is not None and not worst_device_data.empty:
                days = worst_device_data.index
                bottom = np.zeros(len(days))
                
                for device_type in all_device_types:
                    if device_type in worst_device_data.columns and worst_device_data[device_type].sum() > 0:
                        color = device_colors.get(device_type, '#17becf')
                        values = worst_device_data[device_type].values
                        ax4.bar(days, values, bottom=bottom, 
                              label=device_type.title(), color=color, alpha=0.8)
                        bottom += values
                    elif device_type in worst_device_data.columns:
                        # Adicionar barra vazia para manter consistência na legenda
                        ax4.bar(days, np.zeros(len(days)), bottom=bottom, 
                              label=device_type.title(), color=device_colors.get(device_type, '#17becf'), alpha=0.3)
                
                ax4.set_title(f"Tipo de Dispositivo", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
                ax4.set_ylabel("Interações", fontsize=10, fontweight='500', color='#333')
                ax4.set_xlabel("Dia", fontsize=10, fontweight='500', color='#333')
                ax4.set_ylim(0, max_device_y * 1.1 if max_device_y > 0 else 5)
                ax4.grid(True, alpha=0.3, axis='y')
                ax4.spines['top'].set_visible(False)
                ax4.spines['right'].set_visible(False)
                # Legenda para dispositivos no segundo gráfico do pior usuário
                ax4.legend(loc='upper right', fontsize=8, framealpha=0.9)
            else:
                ax4.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax4.transAxes)
                ax4.set_title(f"Tipo de Dispositivo", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
            
            # Configurar eixo X para todos os subplots (valores inteiros)
            for ax in [ax1, ax2, ax3, ax4]:
                ax.tick_params(axis='x', rotation=0)
                # Configurar eixo X para mostrar números inteiros sequenciais
                if hasattr(ax, 'get_xlim'):
                    xlim = ax.get_xlim()
                    if xlim[1] > xlim[0]:
                        max_days = int(xlim[1])
                        ax.set_xticks(range(1, max_days + 1))
                        ax.set_xticklabels(range(1, max_days + 1))
            
            # Ajustar layout das duas figuras
            plt.tight_layout()
            
            # Retornar as duas figuras como uma lista
            return [fig1, fig2]
            
        except Exception as e:
            print(f"Erro no gráfico combinado de trajetórias: {e}")
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.text(0.5, 0.5, f'Erro: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Trajetórias Individuais', fontsize=16, fontweight='bold')
            return [fig, fig]

    @output
    @render.plot
    def trajectory_best_plot():
        """Gráfico de trajetórias do melhor usuário"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                fig, ax = plt.subplots(figsize=(12, 5))
                ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Melhor Usuário - Trajetórias', fontsize=14, fontweight='bold')
                return fig
            
            # Obter usuários extremos
            best_user, worst_user, var_name = get_extreme_users()
            
            if best_user is None or worst_user is None:
                fig, ax = plt.subplots(figsize=(12, 5))
                ax.text(0.5, 0.5, 'Nenhum usuário encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Melhor Usuário - Trajetórias', fontsize=14, fontweight='bold')
                return fig
            
            best_id = best_user.get('unique_id', best_user.get('uid', 'N/A'))
            worst_id = worst_user.get('unique_id', worst_user.get('uid', 'N/A'))
            
            # Obter dados de trajetória para ambos os usuários
            best_event_data, best_device_data = get_user_trajectory_data(best_id, 'Melhor Usuário')
            worst_event_data, worst_device_data = get_user_trajectory_data(worst_id, 'Pior Usuário')
            
            print(f"DEBUG: Melhor usuário - Eventos: {best_event_data.columns.tolist() if best_event_data is not None else 'None'}")
            print(f"DEBUG: Melhor usuário - Dispositivos: {best_device_data.columns.tolist() if best_device_data is not None else 'None'}")
            print(f"DEBUG: Pior usuário - Eventos: {worst_event_data.columns.tolist() if worst_event_data is not None else 'None'}")
            print(f"DEBUG: Pior usuário - Dispositivos: {worst_device_data.columns.tolist() if worst_device_data is not None else 'None'}")
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            # Criar figura com 2x2 subplots (classificação na primeira linha, dispositivos na segunda)
            fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 8))
            
            # Adicionar títulos de coluna centralizados
            fig.text(0.25, 0.95, f"Melhor Usuário (ID: {best_id})", ha='center', va='top', fontsize=14, fontweight='bold', color='#8A2BE2')
            fig.text(0.75, 0.95, f"Pior Usuário (ID: {worst_id})", ha='center', va='top', fontsize=14, fontweight='bold', color='#8A2BE2')
            
            # Usar cores padronizadas globais para consistência
            event_colors = {
                'Criação e Edição': GLOBAL_COLORS['event_Criação e Edição'],
                'Engajamento Social': GLOBAL_COLORS['event_Engajamento Social'],
                'Exportação e Download': GLOBAL_COLORS['event_Exportação e Download'],
                'Mari IA': GLOBAL_COLORS['event_Mari IA'],
                'Visualização e Acesso': GLOBAL_COLORS['event_Visualização e Acesso'],
                'Não Especificado': GLOBAL_COLORS['event_Não Especificado']
            }
            
            device_colors = {
                'desktop': GLOBAL_COLORS['device_desktop'],
                'mobile': GLOBAL_COLORS['device_mobile'],
                'tablet': GLOBAL_COLORS['device_tablet'],
                'smarttv': GLOBAL_COLORS['device_smarttv'],
                'console': GLOBAL_COLORS['device_console']
            }
            
            # Coletar todas as categorias para legendas unificadas (incluindo dados do pior usuário)
            all_event_classes = set()
            all_device_types = set()
            
            for data in [best_event_data, worst_event_data]:
                if data is not None and not data.empty:
                    all_event_classes.update(data.columns)
            
            for data in [best_device_data, worst_device_data]:
                if data is not None and not data.empty:
                    all_device_types.update(data.columns)
            
            print(f"DEBUG: Todas as categorias de evento: {sorted(all_event_classes)}")
            print(f"DEBUG: Todos os tipos de dispositivo: {sorted(all_device_types)}")
            print(f"DEBUG: Chaves do event_colors: {list(event_colors.keys())}")
            print(f"DEBUG: Chaves do device_colors: {list(device_colors.keys())}")
            
            # Calcular escalas máximas considerando ambos os usuários
            max_event_y = 0
            max_device_y = 0
            max_days = 0
            
            for data in [best_event_data, worst_event_data]:
                if data is not None and not data.empty:
                    max_event_y = max(max_event_y, data.sum(axis=1).max())
                    max_days = max(max_days, len(data.index))
            
            for data in [best_device_data, worst_device_data]:
                if data is not None and not data.empty:
                    max_device_y = max(max_device_y, data.sum(axis=1).max())
                    max_days = max(max_days, len(data.index))
            
            # PRIMEIRA LINHA: Classificação de Evento (Melhor vs Pior)
            # Gráfico 1: Melhor Usuário - Classificação de Evento
            ax1 = axes[0, 0]
            if best_event_data is not None and not best_event_data.empty:
                days = best_event_data.index
                bottom = np.zeros(len(days))
                
                for event_class in all_event_classes:
                    if event_class in best_event_data.columns and best_event_data[event_class].sum() > 0:
                        color = event_colors.get(event_class, '#17becf')
                        values = best_event_data[event_class].values
                        print(f"DEBUG: Plotando {event_class} com cor {color} para melhor usuário (encontrada: {event_class in event_colors})")
                        ax1.bar(days, values, bottom=bottom, 
                              label=event_class, color=color, alpha=0.8)
                        bottom += values
                    elif event_class in best_event_data.columns:
                        color = event_colors.get(event_class, '#17becf')
                        print(f"DEBUG: Plotando {event_class} vazio com cor {color} para melhor usuário (encontrada: {event_class in event_colors})")
                        ax1.bar(days, np.zeros(len(days)), bottom=bottom, 
                              label=event_class, color=color, alpha=0.3)
                
                ax1.set_title(f"Classificação de Evento", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
                ax1.set_ylabel("Interações", fontsize=10, fontweight='500', color='#333')
                ax1.set_xlabel("Dia", fontsize=10, fontweight='500', color='#333')
                ax1.set_ylim(0, max_event_y * 1.1 if max_event_y > 0 else 5)
                ax1.grid(True, alpha=0.3, axis='y')
                ax1.spines['top'].set_visible(False)
                ax1.spines['right'].set_visible(False)
            else:
                ax1.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title(f"Classificação de Evento", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
            
            # Gráfico 2: Pior Usuário - Classificação de Evento
            ax2 = axes[0, 1]
            
            if worst_event_data is not None and not worst_event_data.empty:
                days = worst_event_data.index
                bottom = np.zeros(len(days))
                
                for event_class in all_event_classes:
                    if event_class in worst_event_data.columns and worst_event_data[event_class].sum() > 0:
                        color = event_colors.get(event_class, '#17becf')
                        values = worst_event_data[event_class].values
                        print(f"DEBUG: Plotando {event_class} com cor {color} para pior usuário")
                        ax2.bar(days, values, bottom=bottom, 
                              label=event_class, color=color, alpha=0.8)
                        bottom += values
                    elif event_class in worst_event_data.columns:
                        color = event_colors.get(event_class, '#17becf')
                        print(f"DEBUG: Plotando {event_class} vazio com cor {color} para pior usuário")
                        ax2.bar(days, np.zeros(len(days)), bottom=bottom, 
                              label=event_class, color=color, alpha=0.3)
                
                ax2.set_title(f"Classificação de Evento", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
                ax2.set_ylabel("Interações", fontsize=10, fontweight='500', color='#333')
                ax2.set_xlabel("Dia", fontsize=10, fontweight='500', color='#333')
                ax2.set_ylim(0, max_event_y * 1.1 if max_event_y > 0 else 5)
                ax2.grid(True, alpha=0.3, axis='y')
                ax2.spines['top'].set_visible(False)
                ax2.spines['right'].set_visible(False)
                
                # Legenda para eventos (apenas no último gráfico da linha)
                ax2.legend(loc='upper right', fontsize=8, framealpha=0.9)
            else:
                ax2.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title(f"Classificação de Evento", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
            
            # SEGUNDA LINHA: Tipo de Dispositivo (Melhor vs Pior)
            # Gráfico 3: Melhor Usuário - Tipo de Dispositivo
            ax3 = axes[1, 0]
            if best_device_data is not None and not best_device_data.empty:
                days = best_device_data.index
                bottom = np.zeros(len(days))
                
                for device_type in all_device_types:
                    if device_type in best_device_data.columns and best_device_data[device_type].sum() > 0:
                        color = device_colors.get(device_type, '#17becf')
                        values = best_device_data[device_type].values
                        ax3.bar(days, values, bottom=bottom, 
                              label=device_type.title(), color=color, alpha=0.8)
                        bottom += values
                    elif device_type in best_device_data.columns:
                        ax3.bar(days, np.zeros(len(days)), bottom=bottom, 
                              label=device_type.title(), color=device_colors.get(device_type, '#17becf'), alpha=0.3)
                
                ax3.set_title(f"Tipo de Dispositivo", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
                ax3.set_ylabel("Interações", fontsize=10, fontweight='500', color='#333')
                ax3.set_xlabel("Dia", fontsize=10, fontweight='500', color='#333')
                ax3.set_ylim(0, max_device_y * 1.1 if max_device_y > 0 else 5)
                ax3.grid(True, alpha=0.3, axis='y')
                ax3.spines['top'].set_visible(False)
                ax3.spines['right'].set_visible(False)
            else:
                ax3.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax3.transAxes)
                ax3.set_title(f"Tipo de Dispositivo", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
            
            # Gráfico 4: Pior Usuário - Tipo de Dispositivo
            ax4 = axes[1, 1]
            if worst_device_data is not None and not worst_device_data.empty:
                days = worst_device_data.index
                bottom = np.zeros(len(days))
                
                for device_type in all_device_types:
                    if device_type in worst_device_data.columns and worst_device_data[device_type].sum() > 0:
                        color = device_colors.get(device_type, '#17becf')
                        values = worst_device_data[device_type].values
                        ax4.bar(days, values, bottom=bottom, 
                              label=device_type.title(), color=color, alpha=0.8)
                        bottom += values
                    elif device_type in worst_device_data.columns:
                        ax4.bar(days, np.zeros(len(days)), bottom=bottom, 
                              label=device_type.title(), color=device_colors.get(device_type, '#17becf'), alpha=0.3)
                
                ax4.set_title(f"Tipo de Dispositivo", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
                ax4.set_ylabel("Interações", fontsize=10, fontweight='500', color='#333')
                ax4.set_xlabel("Dia", fontsize=10, fontweight='500', color='#333')
                ax4.set_ylim(0, max_device_y * 1.1 if max_device_y > 0 else 5)
                ax4.grid(True, alpha=0.3, axis='y')
                ax4.spines['top'].set_visible(False)
                ax4.spines['right'].set_visible(False)
                
                # Legenda para dispositivos (apenas no último gráfico da linha)
                ax4.legend(loc='upper right', fontsize=8, framealpha=0.9)
            else:
                ax4.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax4.transAxes)
                ax4.set_title(f"Tipo de Dispositivo", 
                            fontsize=12, fontweight='bold', color='#8A2BE2')
            
            # Configurar eixo X padronizado para todos os gráficos
            for ax in [ax1, ax2, ax3, ax4]:
                ax.tick_params(axis='x', rotation=0)
                if max_days > 0:
                    ax.set_xticks(range(1, max_days + 1))
                    ax.set_xticklabels(range(1, max_days + 1))
                    ax.set_xlim(0.5, max_days + 0.5)
            
            plt.tight_layout(rect=[0, 0, 1, 0.85])  # Deixar mais espaço para os títulos de coluna
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico do melhor usuário: {e}")
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.text(0.5, 0.5, f'Erro: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Melhor Usuário - Trajetórias', fontsize=14, fontweight='bold')
            return fig


    # ======================================================================================
    # GRÁFICOS DE EVOLUÇÃO TEMPORAL PARA SEGMENTAÇÃO
    # ======================================================================================

    @output
    @render.plot
    def seg_event_temporal_plot():
        """Gráfico de evolução temporal - Classificação de Evento - Todos os Grupos"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Classificação de Evento - Evolução Temporal', fontsize=14, fontweight='bold')
                return fig
            
            # Obter dados de segmentação
            df_rup = calculate_rup()
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.text(0.5, 0.5, 'Nenhum usuário RUP encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Classificação de Evento - Evolução Temporal', fontsize=14, fontweight='bold')
                return fig
            
            # Aplicar filtros temporais
            if input.show_rup_only():
                df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if input.show_post_mari():
                df_rup = df_rup[df_rup['first_seen'] >= '2024-08-01'].copy()
            
            # Aplicar filtro de data
            date_range = input.date_range()
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
                df_rup = df_rup[(df_rup['first_seen'].dt.date >= start_date) & (df_rup['first_seen'].dt.date <= end_date)].copy()
            
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.text(0.5, 0.5, 'Nenhum dado após filtros temporais', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Classificação de Evento - Evolução Temporal', fontsize=14, fontweight='bold')
                return fig
            
            # Criar grupos baseados nas faixas personalizadas
            var_name = input.segmentation_variable()
            num_groups = input.num_groups()
            df_rup['group'] = create_custom_groups(df_rup, var_name, num_groups)
            
            # Obter grupos únicos
            unique_groups = sorted(df_rup['group'].unique())
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            # Criar subplots com mais largura e menos distanciamento
            fig, axes = plt.subplots(nrows=1, ncols=len(unique_groups), figsize=(4*len(unique_groups), 4))
            if len(unique_groups) == 1:
                axes = [axes]
            
            # Usar cores padronizadas para eventos
            event_colors = {
                'Criação e Edição': GLOBAL_COLORS['event_Criação e Edição'],
                'Engajamento Social': GLOBAL_COLORS['event_Engajamento Social'],
                'Exportação e Download': GLOBAL_COLORS['event_Exportação e Download'],
                'Mari IA': GLOBAL_COLORS['event_Mari IA'],
                'Visualização e Acesso': GLOBAL_COLORS['event_Visualização e Acesso'],
                'Não Especificado': GLOBAL_COLORS['event_Não Especificado']
            }
            
            # Aplicar escala proporcional se selecionada
            chart_scale = input.chart_scale()
            
            # Primeiro, calcular valores máximos para padronizar escalas
            max_y_value = 0
            max_x_value = 0
            all_event_classes = set()
            
            for group in unique_groups:
                df_group = df_rup[df_rup['group'] == group].copy()
                if df_group.empty:
                    continue
                
                # Filtrar interações para usuários do grupo
                unique_users_group = set(df_group['unique_id'].unique())
                mask = df_interactions['unique_id'].isin(unique_users_group)
                
                # Aplicar filtros cruzados se habilitados
                if input.enable_cross_filters():
                    selected_device_types = input.filter_device_types()
                    if selected_device_types:
                        mask &= df_interactions['user_agent_device_type'].isin(selected_device_types)
                    
                    selected_event_classes = input.filter_event_classes()
                    if selected_event_classes:
                        mask &= df_interactions['event_classification'].isin(selected_event_classes)
                
                # Aplicar filtro de X primeiras interações
                first_interactions_count = input.first_interactions()
                if 'numero_interacao' in df_interactions.columns:
                    mask &= df_interactions['numero_interacao'] <= first_interactions_count
                
                df_interactions_filtered = df_interactions[mask].copy()
                
                if not df_interactions_filtered.empty and 'numero_interacao' in df_interactions_filtered.columns:
                    df_grouped = df_interactions_filtered.groupby(['event_classification', 'numero_interacao']).size().reset_index(name='interaction_count')
                    df_pivot = df_grouped.pivot(index='numero_interacao', columns='event_classification', values='interaction_count').fillna(0)
                    
                    # Aplicar escala proporcional se selecionada
                    if chart_scale == "proportional":
                        df_pivot = df_pivot.div(df_pivot.sum(axis=1), axis=0).fillna(0)
                    
                    # Atualizar valores máximos
                    max_y_value = max(max_y_value, df_pivot.sum(axis=1).max() if not df_pivot.empty else 0)
                    max_x_value = max(max_x_value, df_pivot.index.max() if not df_pivot.empty else 0)
                    all_event_classes.update(df_pivot.columns)
            
            # Agora criar os gráficos com escalas padronizadas
            for i, group in enumerate(unique_groups):
                ax = axes[i]
                
                # Filtrar usuários do grupo atual
                df_group = df_rup[df_rup['group'] == group].copy()
                if df_group.empty:
                    ax.text(0.5, 0.5, f'Nenhum usuário do {group}', ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(f'{group}', fontsize=12, fontweight='bold', color='#8A2BE2')
                    continue
                
                # Filtrar interações para usuários do grupo
                unique_users_group = set(df_group['unique_id'].unique())
                mask = df_interactions['unique_id'].isin(unique_users_group)
                
                # Aplicar filtros cruzados se habilitados
                if input.enable_cross_filters():
                    selected_device_types = input.filter_device_types()
                    if selected_device_types:
                        mask &= df_interactions['user_agent_device_type'].isin(selected_device_types)
                    
                    selected_event_classes = input.filter_event_classes()
                    if selected_event_classes:
                        mask &= df_interactions['event_classification'].isin(selected_event_classes)
                
                # Aplicar filtro de X primeiras interações
                first_interactions_count = input.first_interactions()
                if 'numero_interacao' in df_interactions.columns:
                    mask &= df_interactions['numero_interacao'] <= first_interactions_count
                
                df_interactions_filtered = df_interactions[mask].copy()
                
                if df_interactions_filtered.empty:
                    ax.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(f'{group}', fontsize=12, fontweight='bold', color='#8A2BE2')
                    continue
                
                # Agrupar por classificação de evento e numero_interacao
                if 'numero_interacao' in df_interactions_filtered.columns:
                    df_grouped = df_interactions_filtered.groupby(['event_classification', 'numero_interacao']).size().reset_index(name='interaction_count')
                    df_pivot = df_grouped.pivot(index='numero_interacao', columns='event_classification', values='interaction_count').fillna(0)
                    
                    # Aplicar escala proporcional se selecionada
                    if chart_scale == "proportional":
                        df_pivot = df_pivot.div(df_pivot.sum(axis=1), axis=0).fillna(0)
                    
                    # Plotar barras empilhadas para todas as classes de evento (mesmo que vazias)
                    bottom = np.zeros(len(df_pivot.index))
                    
                    for event_class in all_event_classes:
                        if event_class in df_pivot.columns and df_pivot[event_class].sum() > 0:
                            color = event_colors.get(event_class, '#17becf')
                            ax.bar(df_pivot.index, df_pivot[event_class], 
                                  bottom=bottom, color=color, alpha=0.8, 
                                  edgecolor='white', linewidth=1, label=event_class)
                            bottom += df_pivot[event_class]
                        elif event_class in df_pivot.columns:
                            # Adicionar barra vazia para manter consistência na legenda
                            ax.bar(df_pivot.index, np.zeros(len(df_pivot.index)), 
                                  bottom=bottom, color=event_colors.get(event_class, '#17becf'), 
                                  alpha=0.3, edgecolor='white', linewidth=1, label=event_class)
                    
                    # Configurar subplot com escalas padronizadas
                    scale_label = "Proporção" if chart_scale == "proportional" else "Número de Interações"
                    ax.set_xlabel('Dia', fontsize=10, fontweight='500', color='#333')
                    ax.set_ylabel(scale_label, fontsize=10, fontweight='500', color='#333')
                    ax.set_title(f'{group}', fontsize=12, fontweight='bold', color='#8A2BE2')
                    ax.grid(True, alpha=0.3, axis='y')
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    
                    # Configurar escalas padronizadas
                    if chart_scale == "proportional":
                        ax.set_ylim(0, 1)
                    else:
                        y_max = input.y_axis_max() if input.y_axis_max() else max_y_value * 1.1
                        ax.set_ylim(0, y_max)
                    if max_x_value > 0:
                        ax.set_xlim(0, max_x_value + 1)
                    
                    # Adicionar legenda apenas no último subplot (mais à direita) - DENTRO do gráfico
                    if i == len(unique_groups) - 1:
                        ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
                else:
                    ax.text(0.5, 0.5, 'Coluna numero_interacao não encontrada', ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(f'{group}', fontsize=12, fontweight='bold', color='#8A2BE2')
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico de classificação de eventos temporal: {e}")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.text(0.5, 0.5, f'Erro: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Classificação de Evento - Evolução Temporal', fontsize=14, fontweight='bold')
            return fig

    @output
    @render.plot
    def seg_event_g2_plot():
        """Gráfico de evolução temporal - Classificação de Evento - Grupo 2"""
        try:
            # Obter dados de segmentação
            df_rup = calculate_rup()
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum usuário RUP encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Classificação de Evento - Grupo 2', fontsize=12, fontweight='bold')
                return fig
            
            # Aplicar filtros temporais
            if input.show_rup_only():
                df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if input.show_post_mari():
                df_rup = df_rup[df_rup['first_seen'] >= '2024-08-01'].copy()
            
            # Aplicar filtro de data
            date_range = input.date_range()
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
                df_rup = df_rup[(df_rup['first_seen'].dt.date >= start_date) & (df_rup['first_seen'].dt.date <= end_date)].copy()
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum dado após filtros temporais', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Classificação de Evento - Grupo 2', fontsize=12, fontweight='bold')
                return fig
            
            # Criar grupos baseados nas faixas personalizadas
            var_name = input.segmentation_variable()
            num_groups = input.num_groups()
            df_rup['group'] = create_custom_groups(df_rup, var_name, num_groups)
            
            # Verificar se temos a coluna unique_id
            if 'unique_id' not in df_rup.columns:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Coluna unique_id não encontrada', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Classificação de Evento - Grupo 2', fontsize=12, fontweight='bold')
                return fig
            
            # Filtrar apenas usuários do Grupo 2
            df_g2 = df_rup[df_rup['group'] == 'Grupo 2'].copy()
            if df_g2.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum usuário no Grupo 2', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Classificação de Evento - Grupo 2', fontsize=12, fontweight='bold')
                return fig
            
            # Obter dados de interações com filtro de X primeiras interações
            first_interactions_count = input.first_interactions()
            unique_users_g2 = df_g2['unique_id'].unique()
            
            # Aplicar filtros cruzados
            mask = df_interactions['unique_id'].isin(unique_users_g2)
            if input.enable_cross_filters():
                selected_device_types = input.filter_device_types()
                selected_event_classes = input.filter_event_classes()
                if selected_device_types:
                    mask &= df_interactions['user_agent_device_type'].isin(selected_device_types)
                if selected_event_classes:
                    mask &= df_interactions['event_classification'].isin(selected_event_classes)
            
            # Aplicar filtro de X primeiras interações
            if 'numero_interacao' in df_interactions.columns:
                mask &= df_interactions['numero_interacao'] <= first_interactions_count
            else:
                # Fallback: usar head() se numero_interacao não existir
                df_interactions_filtered = df_interactions[mask].copy()
                df_interactions_filtered = df_interactions_filtered.head(first_interactions_count)
                mask = df_interactions.index.isin(df_interactions_filtered.index)
            
            df_interactions_filtered = df_interactions[mask].copy()
            
            if df_interactions_filtered.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Classificação de Evento - Grupo 2', fontsize=12, fontweight='bold')
                return fig
            
            # Agrupar por classificação de evento e numero_interacao
            if 'numero_interacao' in df_interactions_filtered.columns:
                df_grouped = df_interactions_filtered.groupby(['event_classification', 'numero_interacao']).size().reset_index(name='interaction_count')
                df_pivot = df_grouped.pivot(index='numero_interacao', columns='event_classification', values='interaction_count').fillna(0)
            else:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Coluna numero_interacao não encontrada', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Classificação de Evento - Grupo 2', fontsize=12, fontweight='bold')
                return fig
            
            # Limpar memória
            del df_interactions_filtered
            gc.collect()
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            fig, ax = plt.subplots(figsize=(3, 4))
            
            # Usar cores padronizadas para eventos
            event_colors = {
                'Criação e Edição': GLOBAL_COLORS['event_Criação e Edição'],
                'Engajamento Social': GLOBAL_COLORS['event_Engajamento Social'],
                'Exportação e Download': GLOBAL_COLORS['event_Exportação e Download'],
                'Mari IA': GLOBAL_COLORS['event_Mari IA'],
                'Visualização e Acesso': GLOBAL_COLORS['event_Visualização e Acesso'],
                'Não Especificado': GLOBAL_COLORS['event_Não Especificado']
            }
            
            # Plotar barras empilhadas para cada classificação de evento
            bottom = np.zeros(len(df_pivot.index))
            bars = []
            
            for event_class in df_pivot.columns:
                if df_pivot[event_class].sum() > 0:
                    color = event_colors.get(event_class, '#17becf')
                    bars.append(ax.bar(df_pivot.index, df_pivot[event_class], 
                                     bottom=bottom, color=color, alpha=0.8, 
                                     edgecolor='white', linewidth=1, label=event_class))
                    bottom += df_pivot[event_class]
            
            ax.set_xlabel('Dia de Interação', fontsize=10, fontweight='500', color='#333')
            ax.set_ylabel('Número de Interações', fontsize=10, fontweight='500', color='#333')
            ax.set_title('Classificação de Evento - Grupo 2', fontsize=12, fontweight='bold', color='#8A2BE2')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
            ax.grid(True, alpha=0.3, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico de classificação de eventos G2: {e}")
            fig, ax = plt.subplots(figsize=(3, 4))
            ax.text(0.5, 0.5, f'Erro: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Classificação de Evento - Grupo 2', fontsize=12, fontweight='bold')
            return fig

    @output
    @render.plot
    def seg_device_temporal_plot():
        """Gráfico de evolução temporal - Tipo de Dispositivo - Todos os Grupos"""
        try:
            # Verificar se o botão foi clicado
            if not input.calculate_btn():
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.text(0.5, 0.5, 'Clique em "Calcular Gráficos" para visualizar os dados', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Tipo de Dispositivo - Evolução Temporal', fontsize=14, fontweight='bold')
                return fig
            
            # Obter dados de segmentação
            df_rup = calculate_rup()
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.text(0.5, 0.5, 'Nenhum usuário RUP encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Tipo de Dispositivo - Evolução Temporal', fontsize=14, fontweight='bold')
                return fig
            
            # Aplicar filtros temporais
            if input.show_rup_only():
                df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if input.show_post_mari():
                df_rup = df_rup[df_rup['first_seen'] >= '2024-08-01'].copy()
            
            # Aplicar filtro de data
            date_range = input.date_range()
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
                df_rup = df_rup[(df_rup['first_seen'].dt.date >= start_date) & (df_rup['first_seen'].dt.date <= end_date)].copy()
            
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.text(0.5, 0.5, 'Nenhum dado após filtros temporais', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Tipo de Dispositivo - Evolução Temporal', fontsize=14, fontweight='bold')
                return fig
            
            # Criar grupos baseados nas faixas personalizadas
            var_name = input.segmentation_variable()
            num_groups = input.num_groups()
            df_rup['group'] = create_custom_groups(df_rup, var_name, num_groups)
            
            # Obter grupos únicos
            unique_groups = sorted(df_rup['group'].unique())
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            # Criar subplots com mais largura e menos distanciamento
            fig, axes = plt.subplots(nrows=1, ncols=len(unique_groups), figsize=(4*len(unique_groups), 4))
            if len(unique_groups) == 1:
                axes = [axes]
            
            # Usar cores padronizadas para dispositivos
            device_colors = {
                'desktop': GLOBAL_COLORS['device_desktop'],
                'mobile': GLOBAL_COLORS['device_mobile'],
                'tablet': GLOBAL_COLORS['device_tablet'],
                'smarttv': GLOBAL_COLORS['device_smarttv'],
                'console': GLOBAL_COLORS['device_console']
            }
            
            # Aplicar escala proporcional se selecionada
            chart_scale = input.chart_scale()
            
            # Primeiro, calcular valores máximos para padronizar escalas
            max_y_value = 0
            max_x_value = 0
            all_device_types = set()
            
            for group in unique_groups:
                df_group = df_rup[df_rup['group'] == group].copy()
                if df_group.empty:
                    continue
                
                # Filtrar interações para usuários do grupo
                unique_users_group = set(df_group['unique_id'].unique())
                mask = df_interactions['unique_id'].isin(unique_users_group)
                
                # Aplicar filtros cruzados se habilitados
                if input.enable_cross_filters():
                    selected_device_types = input.filter_device_types()
                    if selected_device_types:
                        mask &= df_interactions['user_agent_device_type'].isin(selected_device_types)
                    
                    selected_event_classes = input.filter_event_classes()
                    if selected_event_classes:
                        mask &= df_interactions['event_classification'].isin(selected_event_classes)
                
                # Aplicar filtro de X primeiras interações
                first_interactions_count = input.first_interactions()
                if 'numero_interacao' in df_interactions.columns:
                    mask &= df_interactions['numero_interacao'] <= first_interactions_count
                
                df_interactions_filtered = df_interactions[mask].copy()
                
                if not df_interactions_filtered.empty and 'numero_interacao' in df_interactions_filtered.columns:
                    df_grouped = df_interactions_filtered.groupby(['user_agent_device_type', 'numero_interacao']).size().reset_index(name='interaction_count')
                    df_pivot = df_grouped.pivot(index='numero_interacao', columns='user_agent_device_type', values='interaction_count').fillna(0)
                    
                    # Aplicar escala proporcional se selecionada
                    if chart_scale == "proportional":
                        df_pivot = df_pivot.div(df_pivot.sum(axis=1), axis=0).fillna(0)
                    
                    # Atualizar valores máximos
                    max_y_value = max(max_y_value, df_pivot.sum(axis=1).max() if not df_pivot.empty else 0)
                    max_x_value = max(max_x_value, df_pivot.index.max() if not df_pivot.empty else 0)
                    all_device_types.update(df_pivot.columns)
            
            # Agora criar os gráficos com escalas padronizadas
            for i, group in enumerate(unique_groups):
                ax = axes[i]
                
                # Filtrar usuários do grupo atual
                df_group = df_rup[df_rup['group'] == group].copy()
                if df_group.empty:
                    ax.text(0.5, 0.5, f'Nenhum usuário do {group}', ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(f'{group}', fontsize=12, fontweight='bold', color='#8A2BE2')
                    continue
                
                # Filtrar interações para usuários do grupo
                unique_users_group = set(df_group['unique_id'].unique())
                mask = df_interactions['unique_id'].isin(unique_users_group)
                
                # Aplicar filtros cruzados se habilitados
                if input.enable_cross_filters():
                    selected_device_types = input.filter_device_types()
                    if selected_device_types:
                        mask &= df_interactions['user_agent_device_type'].isin(selected_device_types)
                    
                    selected_event_classes = input.filter_event_classes()
                    if selected_event_classes:
                        mask &= df_interactions['event_classification'].isin(selected_event_classes)
                
                # Aplicar filtro de X primeiras interações
                first_interactions_count = input.first_interactions()
                if 'numero_interacao' in df_interactions.columns:
                    mask &= df_interactions['numero_interacao'] <= first_interactions_count
                
                df_interactions_filtered = df_interactions[mask].copy()
                
                if df_interactions_filtered.empty:
                    ax.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(f'{group}', fontsize=12, fontweight='bold', color='#8A2BE2')
                    continue
                
                # Agrupar por tipo de dispositivo e numero_interacao
                if 'numero_interacao' in df_interactions_filtered.columns:
                    df_grouped = df_interactions_filtered.groupby(['user_agent_device_type', 'numero_interacao']).size().reset_index(name='interaction_count')
                    df_pivot = df_grouped.pivot(index='numero_interacao', columns='user_agent_device_type', values='interaction_count').fillna(0)
                    
                    # Aplicar escala proporcional se selecionada
                    if chart_scale == "proportional":
                        df_pivot = df_pivot.div(df_pivot.sum(axis=1), axis=0).fillna(0)
                    
                    # Plotar barras empilhadas para todos os tipos de dispositivo (mesmo que vazios)
                    bottom = np.zeros(len(df_pivot.index))
                    
                    for device_type in all_device_types:
                        if device_type in df_pivot.columns and df_pivot[device_type].sum() > 0:
                            color = device_colors.get(device_type, '#17becf')
                            ax.bar(df_pivot.index, df_pivot[device_type], 
                                  bottom=bottom, color=color, alpha=0.8, 
                                  edgecolor='white', linewidth=1, label=device_type.title())
                            bottom += df_pivot[device_type]
                        elif device_type in df_pivot.columns:
                            # Adicionar barra vazia para manter consistência na legenda
                            ax.bar(df_pivot.index, np.zeros(len(df_pivot.index)), 
                                  bottom=bottom, color=device_colors.get(device_type, '#17becf'), 
                                  alpha=0.3, edgecolor='white', linewidth=1, label=device_type.title())
                    
                    # Configurar subplot com escalas padronizadas
                    scale_label = "Proporção" if chart_scale == "proportional" else "Número de Interações"
                    ax.set_xlabel('Dia', fontsize=10, fontweight='500', color='#333')
                    ax.set_ylabel(scale_label, fontsize=10, fontweight='500', color='#333')
                    ax.set_title(f'{group}', fontsize=12, fontweight='bold', color='#8A2BE2')
                    ax.grid(True, alpha=0.3, axis='y')
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    
                    # Configurar escalas padronizadas
                    if chart_scale == "proportional":
                        ax.set_ylim(0, 1)
                    else:
                        y_max = input.y_axis_max() if input.y_axis_max() else max_y_value * 1.1
                        ax.set_ylim(0, y_max)
                    if max_x_value > 0:
                        ax.set_xlim(0, max_x_value + 1)
                    
                    # Adicionar legenda apenas no último subplot (mais à direita) - DENTRO do gráfico
                    if i == len(unique_groups) - 1:
                        ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
                else:
                    ax.text(0.5, 0.5, 'Coluna numero_interacao não encontrada', ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(f'{group}', fontsize=12, fontweight='bold', color='#8A2BE2')
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico de tipo de dispositivo temporal: {e}")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.text(0.5, 0.5, f'Erro: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Tipo de Dispositivo - Evolução Temporal', fontsize=14, fontweight='bold')
            return fig

    @output
    @render.plot
    def seg_device_g2_plot():
        """Gráfico de evolução temporal - Tipo de Dispositivo - Grupo 2"""
        try:
            # Obter dados de segmentação
            df_rup = calculate_rup()
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum usuário RUP encontrado', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Tipo de Dispositivo - Grupo 2', fontsize=12, fontweight='bold')
                return fig
            
            # Aplicar filtros temporais
            if input.show_rup_only():
                df_rup = df_rup[df_rup['in_RUP'] == True].copy()
            
            if input.show_post_mari():
                df_rup = df_rup[df_rup['first_seen'] >= '2024-08-01'].copy()
            
            # Aplicar filtro de data
            date_range = input.date_range()
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                df_rup['first_seen'] = pd.to_datetime(df_rup['first_seen']).dt.tz_localize(None)
                df_rup = df_rup[(df_rup['first_seen'].dt.date >= start_date) & (df_rup['first_seen'].dt.date <= end_date)].copy()
            if df_rup.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum dado após filtros temporais', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Tipo de Dispositivo - Grupo 2', fontsize=12, fontweight='bold')
                return fig
            
            # Criar grupos baseados nas faixas personalizadas
            var_name = input.segmentation_variable()
            num_groups = input.num_groups()
            df_rup['group'] = create_custom_groups(df_rup, var_name, num_groups)
            
            # Verificar se temos a coluna unique_id
            if 'unique_id' not in df_rup.columns:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Coluna unique_id não encontrada', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Tipo de Dispositivo - Grupo 2', fontsize=12, fontweight='bold')
                return fig
            
            # Filtrar apenas usuários do Grupo 2
            df_g2 = df_rup[df_rup['group'] == 'Grupo 2'].copy()
            if df_g2.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhum usuário no Grupo 2', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Tipo de Dispositivo - Grupo 2', fontsize=12, fontweight='bold')
                return fig
            
            # Obter dados de interações com filtro de X primeiras interações
            first_interactions_count = input.first_interactions()
            unique_users_g2 = df_g2['unique_id'].unique()
            
            # Aplicar filtros cruzados
            mask = df_interactions['unique_id'].isin(unique_users_g2)
            if input.enable_cross_filters():
                selected_device_types = input.filter_device_types()
                selected_event_classes = input.filter_event_classes()
                if selected_device_types:
                    mask &= df_interactions['user_agent_device_type'].isin(selected_device_types)
                if selected_event_classes:
                    mask &= df_interactions['event_classification'].isin(selected_event_classes)
            
            # Aplicar filtro de X primeiras interações
            if 'numero_interacao' in df_interactions.columns:
                mask &= df_interactions['numero_interacao'] <= first_interactions_count
            else:
                # Fallback: usar head() se numero_interacao não existir
                df_interactions_filtered = df_interactions[mask].copy()
                df_interactions_filtered = df_interactions_filtered.head(first_interactions_count)
                mask = df_interactions.index.isin(df_interactions_filtered.index)
            
            df_interactions_filtered = df_interactions[mask].copy()
            
            if df_interactions_filtered.empty:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Nenhuma interação encontrada', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Tipo de Dispositivo - Grupo 2', fontsize=12, fontweight='bold')
                return fig
            
            # Agrupar por tipo de dispositivo e numero_interacao
            if 'numero_interacao' in df_interactions_filtered.columns:
                df_grouped = df_interactions_filtered.groupby(['user_agent_device_type', 'numero_interacao']).size().reset_index(name='interaction_count')
                df_pivot = df_grouped.pivot(index='numero_interacao', columns='user_agent_device_type', values='interaction_count').fillna(0)
            else:
                fig, ax = plt.subplots(figsize=(3, 4))
                ax.text(0.5, 0.5, 'Coluna numero_interacao não encontrada', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Tipo de Dispositivo - Grupo 2', fontsize=12, fontweight='bold')
                return fig
            
            # Limpar memória
            del df_interactions_filtered
            gc.collect()
            
            # Configurar o estilo do matplotlib
            plt.style.use('default')
            setup_montserrat_font()
            
            fig, ax = plt.subplots(figsize=(3, 4))
            
            # Usar cores padronizadas para dispositivos
            device_colors = {
                'desktop': GLOBAL_COLORS['device_desktop'],
                'mobile': GLOBAL_COLORS['device_mobile'],
                'tablet': GLOBAL_COLORS['device_tablet'],
                'smarttv': GLOBAL_COLORS['device_smarttv'],
                'console': GLOBAL_COLORS['device_console']
            }
            
            # Plotar barras empilhadas para cada tipo de dispositivo
            bottom = np.zeros(len(df_pivot.index))
            bars = []
            
            for device_type in df_pivot.columns:
                if df_pivot[device_type].sum() > 0:
                    color = device_colors.get(device_type, '#17becf')
                    bars.append(ax.bar(df_pivot.index, df_pivot[device_type], 
                                     bottom=bottom, color=color, alpha=0.8, 
                                     edgecolor='white', linewidth=1, label=device_type.title()))
                    bottom += df_pivot[device_type]
            
            ax.set_xlabel('Dia de Interação', fontsize=10, fontweight='500', color='#333')
            ax.set_ylabel('Número de Interações', fontsize=10, fontweight='500', color='#333')
            ax.set_title('Tipo de Dispositivo - Grupo 2', fontsize=12, fontweight='bold', color='#8A2BE2')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
            ax.grid(True, alpha=0.3, axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Erro no gráfico de tipo de dispositivo G2: {e}")
            fig, ax = plt.subplots(figsize=(3, 4))
            ax.text(0.5, 0.5, f'Erro: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Tipo de Dispositivo - Grupo 2', fontsize=12, fontweight='bold')
        return fig

# ======================================================================================
# 4. CRIA A APLICAÇÃO
# ======================================================================================
if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()

app = App(app_ui, server)
