import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shiny import App, render, ui, reactive
import base64
import matplotlib.font_manager as fm
import os
import gc

# ======================================================================================
# 1. PREPARAÇÃO DOS DADOS - VERSÃO DEMO
# Esta versão cria dados de exemplo para demonstração
# ======================================================================================

def create_demo_data():
    """Cria dados de demonstração para o dashboard"""
    np.random.seed(42)
    
    # Criar dados de usuários RUP
    n_users = 1000
    df_users = pd.DataFrame({
        'unique_id': [f'user_{i:04d}' for i in range(n_users)],
        'sessions_days': np.random.randint(1, 30, n_users),
        'weeks_active': np.random.randint(1, 12, n_users),
        'events_total': np.random.randint(10, 500, n_users),
        'days_active': np.random.randint(1, 20, n_users),
        'features_distinct': np.random.randint(1, 8, n_users),
        'first_seen': pd.date_range('2024-01-01', periods=n_users, freq='D'),
        'state': np.random.choice(['SP', 'RJ', 'MG', 'RS', 'PR'], n_users),
        'device_type': np.random.choice(['desktop', 'mobile', 'tablet'], n_users)
    })
    
    # Criar dados de interações
    n_interactions = 5000
    df_interactions = pd.DataFrame({
        'unique_id': np.random.choice(df_users['unique_id'], n_interactions),
        'numero_interacao': range(1, n_interactions + 1),
        'user_agent_device_type': np.random.choice(['desktop', 'mobile', 'tablet', 'smarttv'], n_interactions),
        'event_classification': np.random.choice([
            'Visualização e Acesso', 'Criação e Edição', 'Exportação e Download',
            'Engajamento Social', 'Mari IA', 'Não Especificado'
        ], n_interactions)
    })
    
    return df_users, df_interactions

# Carregar dados de demonstração
df_users, df_interactions = create_demo_data()
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
    # Cores para tipos de dispositivo
    'device_desktop': '#1f77b4',     # Azul
    'device_mobile': '#ff7f0e',      # Laranja
    'device_tablet': '#2ca02c',      # Verde
    'device_smarttv': '#d62728',     # Vermelho
    'device_console': '#9467bd',     # Roxo
    
    # Cores para classificações de evento
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
        
        # Criar distribuição igual de datas
        date_range = pd.date_range(min_val, max_val, periods=num_groups+1)
        thresholds = [d.date() for d in date_range[1:-1]]  # Excluir primeiro e último
        
        inputs = []
        for i, threshold in enumerate(thresholds):
            threshold_days = threshold.toordinal()
            threshold_value = pd.Timestamp.fromordinal(threshold_days).date()
            inputs.append(
                ui.input_date(
                    f"threshold_{i}_{var_name}",
                    f"Limite {i+1}:",
                    value=threshold_value,
                    min=min_val,
                    max=max_val
                )
            )
        return inputs
    else:
        # Para variáveis numéricas
        min_val = df_users[var_name].min()
        max_val = df_users[var_name].max()
        
        # Criar distribuição igual
        thresholds = np.linspace(min_val, max_val, num_groups + 1)[1:-1]
        
        inputs = []
        for i, threshold in enumerate(thresholds):
            inputs.append(
                ui.input_numeric(
                    f"threshold_{i}_{var_name}",
                    f"Limite {i+1}:",
                    value=float(threshold),
                    min=min_val,
                    max=max_val
                )
            )
        return inputs

# Função para configurar fonte Montserrat
def setup_montserrat_font():
    """Configura a fonte Montserrat para matplotlib com fallback robusto"""
    try:
        # Tentar configurar Montserrat
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'sans-serif']
        
        # Configurar tamanho de fonte padrão
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['axes.labelsize'] = 10
        plt.rcParams['xtick.labelsize'] = 9
        plt.rcParams['ytick.labelsize'] = 9
        plt.rcParams['legend.fontsize'] = 9
        
        # Suprimir warnings de fonte
        import warnings
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.font_manager')
        
    except Exception as e:
        print(f"Erro ao configurar fonte: {e}")
        # Fallback para fonte padrão
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'sans-serif']

# Configurar fonte
setup_montserrat_font()

# ======================================================================================
# 2. INTERFACE DO USUÁRIO
# ======================================================================================

# Título principal
app_title = ui.div(
    ui.h1("📊 AprendiZAP Dashboard - Análise de Uso Real (RUP)", 
          style="text-align: center; color: #2c3e50; margin-bottom: 20px;"),
    ui.p("Análise detalhada da população de uso real da plataforma AprendiZAP",
         style="text-align: center; color: #7f8c8d; font-size: 16px; margin-bottom: 30px;")
)

# Sidebar com controles
sidebar = ui.sidebar(
    ui.h3("🎛️ Controles de Segmentação", style="color: #2c3e50; margin-bottom: 20px;"),
    
    # Seleção de variável para segmentação
    ui.input_select(
        "segmentation_variable",
        "📈 Variável para Segmentação:",
        choices=SEGMENTATION_VARIABLES,
        selected="sessions_days"
    ),
    
    # Número de grupos
    ui.input_numeric(
        "num_groups",
        "🔢 Número de Grupos:",
        value=3,
        min=2,
        max=10
    ),
    
    # Controles dinâmicos de faixas
    ui.div(
        ui.h4("📏 Limites dos Grupos:", style="color: #34495e; margin-bottom: 15px;"),
        id="threshold_controls"
    ),
    
    # Botão para aplicar segmentação
    ui.input_action_button(
        "apply_segmentation",
        "🚀 Aplicar Segmentação",
        class_="btn-primary",
        style="width: 100%; margin-top: 20px;"
    ),
    
    # Informações sobre a população
    ui.div(
        ui.h4("📊 Informações da População:", style="color: #34495e; margin-top: 30px; margin-bottom: 15px;"),
        ui.p(f"👥 Total de usuários: {TOTAL_USERS:,}", style="font-size: 14px; color: #2c3e50;"),
        ui.p("📅 Dados de demonstração", style="font-size: 12px; color: #7f8c8d;"),
        style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin-top: 20px;"
    ),
    
    width=350
)

# Painel principal
main_panel = ui.navset_tab(
    ui.nav("📊", "Visão Geral", 
           ui.div(
               ui.h2("📈 Visão Geral da Segmentação", style="color: #2c3e50; margin-bottom: 20px;"),
               ui.output_plot("overview_plot", height="500px"),
               ui.output_text("overview_text")
           )),
    
    ui.nav("📱", "Dispositivos",
           ui.div(
               ui.h2("📱 Análise por Tipo de Dispositivo", style="color: #2c3e50; margin-bottom: 20px;"),
               ui.output_plot("device_plot", height="500px"),
               ui.output_text("device_text")
           )),
    
    ui.nav("🎯", "Eventos",
           ui.div(
               ui.h2("🎯 Análise por Classificação de Eventos", style="color: #2c3e50; margin-bottom: 20px;"),
               ui.output_plot("event_plot", height="500px"),
               ui.output_text("event_text")
           )),
    
    ui.nav("📈", "Tendências",
           ui.div(
               ui.h2("📈 Análise de Tendências Temporais", style="color: #2c3e50; margin-bottom: 20px;"),
               ui.output_plot("trend_plot", height="500px"),
               ui.output_text("trend_text")
           )),
    
    ui.nav("📋", "Tabelas",
           ui.div(
               ui.h2("📋 Dados Detalhados", style="color: #2c3e50; margin-bottom: 20px;"),
               ui.output_data_frame("summary_table")
           ))
)

# Layout principal
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style("""
            .btn-primary {
                background-color: #3498db;
                border-color: #3498db;
            }
            .btn-primary:hover {
                background-color: #2980b9;
                border-color: #2980b9;
            }
            .card {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 15px;
                background-color: #ffffff;
            }
        """)
    ),
    app_title,
    ui.layout_sidebar(sidebar, main_panel)
)

# ======================================================================================
# 3. LÓGICA DO SERVIDOR
# ======================================================================================

def server(input, output, session):
    
    # Reativo para controles de faixas
    @reactive.effect
    def update_threshold_controls():
        var_name = input.segmentation_variable()
        num_groups = input.num_groups()
        
        # Gerar controles dinâmicos
        controls = generate_threshold_inputs(num_groups, var_name)
        
        # Atualizar UI
        ui.remove_ui(selector="#threshold_controls")
        ui.insert_ui(
            selector=".sidebar",
            ui=ui.div(
                ui.h4("📏 Limites dos Grupos:", style="color: #34495e; margin-bottom: 15px;"),
                *controls,
                id="threshold_controls"
            ),
            where="afterEnd"
        )
    
    # Função para criar segmentação
    def create_segmentation():
        var_name = input.segmentation_variable()
        num_groups = input.num_groups()
        
        if var_name not in df_users.columns:
            return df_users.assign(segmento='Grupo 1')
        
        # Obter limites dos inputs
        thresholds = []
        for i in range(num_groups - 1):
            threshold_value = getattr(input, f"threshold_{i}_{var_name}")()
            thresholds.append(threshold_value)
        
        # Criar segmentação
        if var_name == 'first_seen':
            # Para datas, converter para ordinal
            dates = pd.to_datetime(df_users[var_name]).dt.tz_localize(None)
            threshold_days = [pd.Timestamp.fromordinal(t.toordinal()) for t in thresholds]
            df_users['segmento'] = pd.cut(dates, 
                                        bins=[dates.min()] + threshold_days + [dates.max()],
                                        labels=[f'Grupo {i+1}' for i in range(num_groups)],
                                        include_lowest=True)
        else:
            # Para variáveis numéricas
            df_users['segmento'] = pd.cut(df_users[var_name], 
                                        bins=[df_users[var_name].min()] + thresholds + [df_users[var_name].max()],
                                        labels=[f'Grupo {i+1}' for i in range(num_groups)],
                                        include_lowest=True)
        
        return df_users
    
    # Plot de visão geral
    @output
    @render.plot
    def overview_plot():
        df_segmented = create_segmentation()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Gráfico de barras - distribuição por grupo
        segment_counts = df_segmented['segmento'].value_counts().sort_index()
        colors = plt.cm.Set3(np.linspace(0, 1, len(segment_counts)))
        
        bars = ax1.bar(segment_counts.index, segment_counts.values, color=colors)
        ax1.set_title('Distribuição de Usuários por Grupo', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Grupo')
        ax1.set_ylabel('Número de Usuários')
        
        # Adicionar valores nas barras
        for bar, count in zip(bars, segment_counts.values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        # Gráfico de pizza - percentual
        ax2.pie(segment_counts.values, labels=segment_counts.index, autopct='%1.1f%%', 
                colors=colors, startangle=90)
        ax2.set_title('Distribuição Percentual por Grupo', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    # Texto de visão geral
    @output
    @render.text
    def overview_text():
        df_segmented = create_segmentation()
        segment_counts = df_segmented['segmento'].value_counts().sort_index()
        
        text = f"📊 Resumo da Segmentação:\n\n"
        for group, count in segment_counts.items():
            percentage = (count / len(df_segmented)) * 100
            text += f"• {group}: {count:,} usuários ({percentage:.1f}%)\n"
        
        return text
    
    # Plot de dispositivos
    @output
    @render.plot
    def device_plot():
        df_segmented = create_segmentation()
        
        # Merge com dados de interações
        df_merged = df_segmented.merge(df_interactions, on='unique_id', how='left')
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Gráfico de barras - dispositivos por grupo
        device_by_group = df_merged.groupby(['segmento', 'user_agent_device_type']).size().unstack(fill_value=0)
        device_by_group.plot(kind='bar', ax=ax1, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        ax1.set_title('Distribuição de Dispositivos por Grupo', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Grupo')
        ax1.set_ylabel('Número de Interações')
        ax1.legend(title='Tipo de Dispositivo', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.tick_params(axis='x', rotation=45)
        
        # Gráfico de pizza - dispositivos totais
        device_totals = df_merged['user_agent_device_type'].value_counts()
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        ax2.pie(device_totals.values, labels=device_totals.index, autopct='%1.1f%%', 
                colors=colors[:len(device_totals)], startangle=90)
        ax2.set_title('Distribuição Total de Dispositivos', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    # Texto de dispositivos
    @output
    @render.text
    def device_text():
        df_segmented = create_segmentation()
        df_merged = df_segmented.merge(df_interactions, on='unique_id', how='left')
        
        device_totals = df_merged['user_agent_device_type'].value_counts()
        
        text = f"📱 Análise de Dispositivos:\n\n"
        for device, count in device_totals.items():
            percentage = (count / len(df_merged)) * 100
            text += f"• {device}: {count:,} interações ({percentage:.1f}%)\n"
        
        return text
    
    # Plot de eventos
    @output
    @render.plot
    def event_plot():
        df_segmented = create_segmentation()
        
        # Merge com dados de interações
        df_merged = df_segmented.merge(df_interactions, on='unique_id', how='left')
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Gráfico de barras - eventos por grupo
        event_by_group = df_merged.groupby(['segmento', 'event_classification']).size().unstack(fill_value=0)
        event_by_group.plot(kind='bar', ax=ax1, color=['#ffa500', '#e377c2', '#8c564b', '#17becf', '#bcbd22', '#7f7f7f'])
        ax1.set_title('Distribuição de Eventos por Grupo', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Grupo')
        ax1.set_ylabel('Número de Interações')
        ax1.legend(title='Classificação de Evento', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.tick_params(axis='x', rotation=45)
        
        # Gráfico de pizza - eventos totais
        event_totals = df_merged['event_classification'].value_counts()
        colors = ['#ffa500', '#e377c2', '#8c564b', '#17becf', '#bcbd22', '#7f7f7f']
        ax2.pie(event_totals.values, labels=event_totals.index, autopct='%1.1f%%', 
                colors=colors[:len(event_totals)], startangle=90)
        ax2.set_title('Distribuição Total de Eventos', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    # Texto de eventos
    @output
    @render.text
    def event_text():
        df_segmented = create_segmentation()
        df_merged = df_segmented.merge(df_interactions, on='unique_id', how='left')
        
        event_totals = df_merged['event_classification'].value_counts()
        
        text = f"🎯 Análise de Eventos:\n\n"
        for event, count in event_totals.items():
            percentage = (count / len(df_merged)) * 100
            text += f"• {event}: {count:,} interações ({percentage:.1f}%)\n"
        
        return text
    
    # Plot de tendências
    @output
    @render.plot
    def trend_plot():
        df_segmented = create_segmentation()
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # Gráfico de linha - evolução temporal por grupo
        df_segmented['month'] = pd.to_datetime(df_segmented['first_seen']).dt.to_period('M')
        monthly_by_group = df_segmented.groupby(['month', 'segmento']).size().unstack(fill_value=0)
        
        for group in monthly_by_group.columns:
            ax1.plot(monthly_by_group.index.astype(str), monthly_by_group[group], 
                    marker='o', label=group, linewidth=2)
        
        ax1.set_title('Evolução Temporal por Grupo', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Mês')
        ax1.set_ylabel('Número de Usuários')
        ax1.legend(title='Grupo')
        ax1.tick_params(axis='x', rotation=45)
        
        # Gráfico de barras - distribuição por estado
        state_counts = df_segmented['state'].value_counts()
        colors = plt.cm.Set3(np.linspace(0, 1, len(state_counts)))
        
        bars = ax2.bar(state_counts.index, state_counts.values, color=colors)
        ax2.set_title('Distribuição por Estado', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Estado')
        ax2.set_ylabel('Número de Usuários')
        
        # Adicionar valores nas barras
        for bar, count in zip(bars, state_counts.values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    # Texto de tendências
    @output
    @render.text
    def trend_text():
        df_segmented = create_segmentation()
        
        state_counts = df_segmented['state'].value_counts()
        
        text = f"📈 Análise de Tendências:\n\n"
        text += f"📅 Período: {df_segmented['first_seen'].min().strftime('%Y-%m-%d')} a {df_segmented['first_seen'].max().strftime('%Y-%m-%d')}\n\n"
        text += f"🗺️ Distribuição por Estado:\n"
        for state, count in state_counts.items():
            percentage = (count / len(df_segmented)) * 100
            text += f"• {state}: {count:,} usuários ({percentage:.1f}%)\n"
        
        return text
    
    # Tabela resumo
    @output
    @render.data_frame
    def summary_table():
        df_segmented = create_segmentation()
        
        # Calcular estatísticas por grupo
        summary = df_segmented.groupby('segmento').agg({
            'sessions_days': ['count', 'mean', 'std'],
            'weeks_active': ['mean', 'std'],
            'events_total': ['mean', 'std'],
            'days_active': ['mean', 'std'],
            'features_distinct': ['mean', 'std']
        }).round(2)
        
        # Flatten column names
        summary.columns = ['_'.join(col).strip() for col in summary.columns]
        summary = summary.reset_index()
        
        return summary

# ======================================================================================
# 4. APLICAÇÃO
# ======================================================================================

app = App(app_ui, server)
