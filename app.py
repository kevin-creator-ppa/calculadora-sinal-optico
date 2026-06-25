import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import json
import os
import base64
import html
import math

st.set_page_config(
    page_title="Calculadora de Sinal Óptico",
    page_icon="(antenna)",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown('''
    <style>
    /* Tema neutro: NÃO dependemos de variáveis do Streamlit (esta versão não as
       expõe ao CSS injetado). Os cards usam fundo translúcido e o TEXTO HERDA a
       cor do tema ativo do Streamlit — assim funciona em claro e escuro. As cores
       de marca/acento (azul, laranja, verde, vermelho) funcionam nos dois temas. */
    :root {
        --primary: #2a8fd4;
        --secondary: #ff7f0e;
        --success: #2ecc71;
        --error: #e74c3c;
        --bg-card: rgba(130,130,130,0.10);
        --border-color: rgba(130,130,130,0.28);
        --header-gradient: linear-gradient(135deg, #1e6fb3 0%, #ff7f0e 100%);
        --shadow: 0 6px 20px rgba(0,0,0,0.18);
        --focus-ring: rgba(42,143,212,0.30);
        --base-font: 14px;
    }

    /* Apenas fonte/tamanho; a COR do texto fica por conta do tema do Streamlit. */
    html, body, #root, .block-container {
        font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
        font-size: var(--base-font);
    }

    /* Header */
    .main-header{ background:var(--header-gradient); padding:24px; border-radius:10px; margin-bottom:18px; box-shadow:var(--shadow); }
    .header-content{ display:flex; align-items:center; gap:16px; }
    .header-text h1{ color:#fff; font-size:28px; margin:0; font-weight:700; }

    /* Cards and inputs */
    .input-card, .result-card, .metric-box{ background:var(--bg-card); border-radius:10px; padding:18px; box-shadow:var(--shadow); border:1px solid var(--border-color); }

    /* Linhas dos cards de Resultados: rótulo em azul, valor herdando o tema.
       Rótulo com largura fixa para os valores alinharem em coluna. */
    .result-row{ margin-bottom:6px; }
    .result-label{ color:var(--primary); font-weight:800; display:inline-block; min-width:72px; vertical-align:top; }
    .input-card{ transition:transform .18s ease, box-shadow .18s ease; }
    .input-card:focus-within{ transform:translateY(-3px); box-shadow:0 12px 30px rgba(16,24,40,0.08); }

    /* Floating label helper for markdown-wrapped inputs */
    .floating-label{ position:relative; }
    .floating-label label{ position:absolute; left:12px; top:10px; font-size:12px; opacity:0.7; transition:all .18s ease; pointer-events:none; }
    .floating-label input:focus + label, .floating-label input:not(:placeholder-shown) + label{ transform:translateY(-18px) scale(.92); opacity:0.95; }

    /* Buttons */
    [data-testid="stButton"] button{ border-radius:10px; padding:12px 18px; font-weight:700; min-height:44px; }
    [data-testid="stButton"] button:focus{ box-shadow:0 6px 20px var(--focus-ring); }

    /* Metrics */
    .metric-label{ font-size:11px; opacity:0.65; text-transform:uppercase; }
    .metric-value{ font-size:20px; color:var(--primary); font-weight:800; }

    .validation-grid{ display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:16px; margin-bottom: 18px; }
    .validation-card{ background:var(--bg-card); border-radius:14px; padding:18px; box-shadow:var(--shadow); border:1px solid var(--border-color); }
    .validation-title{ font-weight:700; margin-bottom:12px; }
    .validation-item{ margin-bottom:10px; padding:12px 14px; border-radius:10px; background:rgba(130,130,130,0.10); }
    .validation-item.validation-ok{ border-left:4px solid var(--success); }
    .validation-item.validation-error{ border-left:4px solid var(--error); background:rgba(231,76,60,0.08); }
    .status-container{ margin-top:10px; padding:16px 18px; border-radius:14px; background:rgba(30,111,179,0.07); border:1px solid rgba(30,111,179,0.18); }
    .status-ok{ color:var(--success); font-weight:700; }
    .status-error{ color:var(--error); font-weight:700; }

    /* Responsive columns: stack on small screens */
    @media (max-width:720px){
        .result-content{ grid-template-columns: 1fr !important; }
        .header-text h1{ font-size:22px; }
        .validation-grid{ grid-template-columns: 1fr; }
    }

    /* Accessibility focus visibility */
    :focus{ outline: none; }
    :focus-visible{ outline:3px solid var(--focus-ring); outline-offset:2px; }

    /* Hide deploy */
    button[title="Deploy"], a[title="Deploy"]{ display:none !important; }

    /* Ocultar barra lateral (Configurações + Navegação) e seu botão de abrir */
    [data-testid="stSidebar"]{ display:none !important; }
    [data-testid="stSidebarCollapsedControl"]{ display:none !important; }
    [data-testid="collapsedControl"]{ display:none !important; }
    </style>
    ''', unsafe_allow_html=True)
    

@st.cache_data
def load_gbics_data():
    try:
        df = pd.read_csv("gbics.csv")

        required = ['fabricante', 'modelo', 'tx_min', 'tx_max', 'rx_min', 'rx_max', 'budget']
        missing = [c for c in required if c not in df.columns]
        if missing:
            st.error(f"❌ Colunas ausentes em gbics.csv: {', '.join(missing)}")
            return pd.DataFrame()

        numeric_cols = ['tx_min', 'tx_max', 'rx_min', 'rx_max', 'budget']
        for col in numeric_cols:
            df[col] = (
                df[col].astype(str)
                .str.strip()
                .str.replace(',', '.', regex=False)
                .astype(float)
            )

        # Limpar nomes (espaços nas pontas e espaços duplicados internos)
        for col in ['fabricante', 'modelo']:
            df[col] = df[col].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)

        # Defesa contra faixas invertidas na planilha (min/max trocados):
        # garante sempre tx_min <= tx_max e rx_min <= rx_max.
        for lo, hi in [('tx_min', 'tx_max'), ('rx_min', 'rx_max')]:
            low = df[[lo, hi]].min(axis=1)
            high = df[[lo, hi]].max(axis=1)
            df[lo], df[hi] = low, high

        # Descartar linhas sem dados numéricos essenciais
        df = df.dropna(subset=numeric_cols).reset_index(drop=True)

        if df.empty:
            st.warning("⚠️ Nenhuma linha válida encontrada em gbics.csv.")

        return df
    except FileNotFoundError:
        st.error("❌ Arquivo gbics.csv não encontrado!")
        return pd.DataFrame()

def alcance_texto(valor):
    """Formata o alcance com unidade para exibição.
       Aceita número puro (km) ou sufixos m/km. Ex.: '40' -> '40 Km';
       '300m' -> '300 m'; '80km' -> '80 Km'. Vazio/invalido -> '' (ou o texto cru)."""
    if valor is None:
        return ""
    s = str(valor).strip()
    if s.lower() in ("", "nan", "none"):
        return ""
    low = s.lower().replace(" ", "")
    if low.endswith("km"):
        corpo, unidade = low[:-2], "Km"
    elif low.endswith("m"):           # metros
        corpo, unidade = low[:-1], "m"
    elif low.endswith("k"):
        corpo, unidade = low[:-1], "Km"
    else:                             # número puro = km
        corpo, unidade = low, "Km"
    try:
        num = float(corpo.replace(",", "."))
    except ValueError:
        return s
    txt = str(int(num)) if num == int(num) else ("%g" % num).replace(".", ",")
    return f"{txt} {unidade}"

def formatar_opcao_gbic(row):
    """Monta 'Fabricante - Modelo (40 Km)'; o sufixo só aparece se houver alcance."""
    base = f"{row['fabricante']} - {row['modelo']}"
    alc = alcance_texto(row.get("quilometragem") if hasattr(row, "get") else None)
    if alc:
        base += f" ({alc})"
    return base

def load_history():
    if os.path.exists("history.json"):
        with open("history.json", "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open("history.json", "w") as f:
        json.dump(history, f, indent=2)

def calculate_loss(tx, rx):
    return round(tx - rx, 2)

def validate_gbic_specs(tx, rx, gbic_row):
    tx_min = gbic_row["tx_min"]
    tx_max = gbic_row["tx_max"]
    rx_min = gbic_row["rx_min"]
    rx_max = gbic_row["rx_max"]
    budget = gbic_row["budget"]

    tx_ok = (tx_min <= tx <= tx_max)
    rx_ok = (rx_min <= rx <= rx_max)

    return tx_ok, rx_ok, budget

def generate_pdf(pop_a_data, pop_b_data, loss_ab, loss_ba, gbic_model, gbic_budget, status, app_title, section_title, pop_a_name, pop_b_name):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=12,
        alignment=1
    )

    story = []
    story.append(Paragraph(app_title or "Calculadora de Sinal Óptico - Telium", title_style))
    if section_title:
        subtitle_style = ParagraphStyle('SubTitle', parent=styles['Normal'], alignment=1, spaceAfter=8, textColor=colors.HexColor('#333333'))
        story.append(Paragraph(section_title, subtitle_style))
    story.append(Spacer(1, 0.3*inch))

    data_table = [
        ["Parâmetro", pop_a_name or 'POP A', pop_b_name or 'POP B'],
        ["Interface", pop_a_data["interface"], pop_b_data["interface"]],
        ["TX (dBm)", str(pop_a_data["tx"]), str(pop_b_data["tx"])],
        ["RX (dBm)", str(pop_a_data["rx"]), str(pop_b_data["rx"])],
        ["GBIC", pop_a_data["gbic"], pop_b_data["gbic"]],
        ["Perda (dB)", str(pop_a_data["perda"]), str(pop_b_data["perda"])],
    ]

    table = Table(data_table, colWidths=[2*inch, 2*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.2*inch))

    calc_text = f"""
    <b>Cálculos:</b><br/>
    Perda A -> B: ({pop_a_data['tx']}) - ({pop_b_data['rx']}) = {loss_ab} dB<br/>
    Perda B -> A: ({pop_b_data['tx']}) - ({pop_a_data['rx']}) = {loss_ba} dB<br/>
    <br/>
    <b>Budget da GBIC ({gbic_model}):</b> {gbic_budget} dB<br/>
    <br/>
    <b>Status:</b> {status}
    """
    story.append(Paragraph(calc_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    footer = Paragraph(f"<i>Relatório gerado em: {timestamp}</i>", styles['Normal'])
    story.append(footer)

    doc.build(story)
    buffer.seek(0)
    return buffer

def main():
    # Inicializar valores padrão
    if "app_title" not in st.session_state:
        st.session_state.app_title = "Calculadora de Sinal Óptico"
    if "pop_a_name" not in st.session_state:
        st.session_state.pop_a_name = "POP A"
    if "pop_b_name" not in st.session_state:
        st.session_state.pop_b_name = "POP B"
    if "app_subtitle" not in st.session_state:
        st.session_state.app_subtitle = ""
    if "section_title" not in st.session_state:
        st.session_state.section_title = "Insira os dados dos equipamentos"

    # Header dinâmico
    safe_app_title = html.escape(st.session_state.app_title)
    header_html = f"""
    <div class="main-header">
        <div class="header-content">
            <div class="header-text">
                <h1>{safe_app_title}</h1>
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    gbics_df = load_gbics_data()

    if gbics_df.empty:
        st.error("❌ Nenhum dado de GBIC carregado")
        return

    # Sidebar com opções de edição
    with st.sidebar:
        st.markdown("### ⚙️ Configurações")

        # Seção de edição do header
        with st.expander("📝 Editar Header", expanded=False):
            new_title = st.text_input(
                "Título do App",
                value=st.session_state.app_title,
                placeholder="Ex: Calculadora de Sinal Óptico",
                key="input_title"
            )
            if new_title != st.session_state.app_title:
                st.session_state.app_title = new_title

        # Seção de edição dos nomes dos POPs
        with st.expander("🔌 Editar POPs", expanded=False):
            new_section = st.text_input(
                "Título da Seção",
                value=st.session_state.section_title,
                placeholder="Ex: Insira os dados dos equipamentos",
                key="input_section"
            )
            if new_section != st.session_state.section_title:
                st.session_state.section_title = new_section

            new_pop_a = st.text_input(
                "Nome do POP A",
                value=st.session_state.pop_a_name,
                placeholder="Ex: POP A",
                key="input_pop_a"
            )
            if new_pop_a != st.session_state.pop_a_name:
                st.session_state.pop_a_name = new_pop_a

            new_pop_b = st.text_input(
                "Nome do POP B",
                value=st.session_state.pop_b_name,
                placeholder="Ex: POP B",
                key="input_pop_b"
            )
            if new_pop_b != st.session_state.pop_b_name:
                st.session_state.pop_b_name = new_pop_b

        st.divider()

    menu = st.sidebar.radio(
        "📋 NAVEGAÇÃO",
        ["Calcular", "Histórico", "Sobre"],
        label_visibility="collapsed"
    )

    if menu == "Calcular":
        st.markdown(f"### {st.session_state.section_title}")

        col1, col2 = st.columns(2)

        with col1:
            pop_a_inline = st.text_input("", value=st.session_state.pop_a_name, key="pop_a_inline", label_visibility="collapsed")
            if pop_a_inline != st.session_state.pop_a_name:
                st.session_state.pop_a_name = pop_a_inline
            interface_a = st.text_input("Interface", value="TenGigabitEthernet 1/1/1", key="interface_a", label_visibility="collapsed")
            tx_a = st.number_input("TX (dBm)", value=-2.81, step=0.01, key="tx_a", label_visibility="collapsed")
            rx_a = st.number_input("RX (dBm)", value=-13.62, step=0.01, key="rx_a", label_visibility="collapsed")

            gbic_options = gbics_df.apply(formatar_opcao_gbic, axis=1).tolist()
            gbic_a_selected = st.selectbox("GBIC", options=gbic_options, key="gbic_a", label_visibility="collapsed")
            gbic_a_idx = gbic_options.index(gbic_a_selected)
            gbic_a = gbics_df.iloc[gbic_a_idx]

        with col2:
            pop_b_inline = st.text_input("", value=st.session_state.pop_b_name, key="pop_b_inline", label_visibility="collapsed")
            if pop_b_inline != st.session_state.pop_b_name:
                st.session_state.pop_b_name = pop_b_inline
            interface_b = st.text_input("Interface", value="TenGigabitEthernet 1/1/2", key="interface_b", label_visibility="collapsed")
            tx_b = st.number_input("TX (dBm)", value=-3.19, step=0.01, key="tx_b", label_visibility="collapsed")
            rx_b = st.number_input("RX (dBm)", value=-14.53, step=0.01, key="rx_b", label_visibility="collapsed")

            gbic_b_selected = st.selectbox("GBIC", options=gbic_options, key="gbic_b", label_visibility="collapsed")
            gbic_b_idx = gbic_options.index(gbic_b_selected)
            gbic_b = gbics_df.iloc[gbic_b_idx]

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("INICIAR CÁLCULO", use_container_width=True, key="calc_button"):
                st.session_state.calcular = True

        if st.session_state.get("calcular", False):
            loss_ab = calculate_loss(tx_a, rx_b)
            loss_ba = calculate_loss(tx_b, rx_a)

            tx_ok_a, rx_ok_a, budget_a = validate_gbic_specs(tx_a, rx_a, gbic_a)
            tx_ok_b, rx_ok_b, budget_b = validate_gbic_specs(tx_b, rx_b, gbic_b)

            loss_ok_a = (loss_ab <= budget_a)
            loss_ok_b = (loss_ba <= budget_b)

            alcance_a = alcance_texto(gbic_a.get("quilometragem"))
            alcance_b = alcance_texto(gbic_b.get("quilometragem"))

            # Valor de alcance para a métrica: combina A e B
            if alcance_a and alcance_b:
                alcance_metrica = alcance_a if alcance_a == alcance_b else f"{alcance_a} / {alcance_b}"
            elif alcance_a or alcance_b:
                alcance_metrica = alcance_a or alcance_b
            else:
                alcance_metrica = "—"

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown("### Resultados")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                <div class="result-card pop-a">
                    <div style="font-weight: 700; font-size: 16px; margin-bottom: 12px;">{st.session_state.pop_a_name}</div>
                    <div class="result-row"><span class="result-label">Interface:</span> <span class="result-value">{interface_a}</span></div>
                    <div class="result-row"><span class="result-label">TX:</span> <span class="result-value">{tx_a} dBm</span></div>
                    <div class="result-row"><span class="result-label">RX:</span> <span class="result-value">{rx_a} dBm</span></div>
                    <div class="result-row"><span class="result-label">GBIC:</span> <span class="result-value">{gbic_a["modelo"]}</span></div>
                    {f'<div class="result-row"><span class="result-label">Alcance:</span> <span class="result-value">{alcance_a}</span></div>' if alcance_a else ''}<div class="result-row" style="margin-top: 10px;"><span class="result-label">Perda:</span> <span class="result-value">{loss_ab} dB</span></div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="result-card pop-b">
                    <div style="font-weight: 700; font-size: 16px; margin-bottom: 12px;">{st.session_state.pop_b_name}</div>
                    <div class="result-row"><span class="result-label">Interface:</span> <span class="result-value">{interface_b}</span></div>
                    <div class="result-row"><span class="result-label">TX:</span> <span class="result-value">{tx_b} dBm</span></div>
                    <div class="result-row"><span class="result-label">RX:</span> <span class="result-value">{rx_b} dBm</span></div>
                    <div class="result-row"><span class="result-label">GBIC:</span> <span class="result-value">{gbic_b["modelo"]}</span></div>
                    {f'<div class="result-row"><span class="result-label">Alcance:</span> <span class="result-value">{alcance_b}</span></div>' if alcance_b else ''}<div class="result-row" style="margin-top: 10px;"><span class="result-label">Perda:</span> <span class="result-value">{loss_ba} dB</span></div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown("### Métricas")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">Perda A -> B</div>
                    <div class="metric-value">{loss_ab} dB</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">Perda B -> A</div>
                    <div class="metric-value secondary">{loss_ba} dB</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">Budget GBIC</div>
                    <div class="metric-value">{budget_a} dB</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">Alcance GBIC</div>
                    <div class="metric-value">{alcance_metrica}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown("### Validação")

            st.markdown(f"""
            <div class="validation-grid">
                <div class="validation-card">
                    <div class="validation-title">{st.session_state.pop_a_name} - Validação</div>
                    <div class="validation-item {'validation-ok' if tx_ok_a else 'validation-error'}">TX {tx_a} {'dentro' if tx_ok_a else '❌ fora'} de [{gbic_a['tx_min']}, {gbic_a['tx_max']}]</div>
                    <div class="validation-item {'validation-ok' if rx_ok_a else 'validation-error'}">RX {rx_a} {'dentro' if rx_ok_a else '❌ fora'} de [{gbic_a['rx_min']}, {gbic_a['rx_max']}]</div>
                    <div class="validation-item {'validation-ok' if loss_ok_a else 'validation-error'}">Perda {loss_ab} dB {'<=' if loss_ok_a else '>'} {budget_a} dB</div>
                </div>
                <div class="validation-card">
                    <div class="validation-title">{st.session_state.pop_b_name} - Validação</div>
                    <div class="validation-item {'validation-ok' if tx_ok_b else 'validation-error'}">TX {tx_b} {'dentro' if tx_ok_b else '❌ fora'} de [{gbic_b['tx_min']}, {gbic_b['tx_max']}]</div>
                    <div class="validation-item {'validation-ok' if rx_ok_b else 'validation-error'}">RX {rx_b} {'dentro' if rx_ok_b else '❌ fora'} de [{gbic_b['rx_min']}, {gbic_b['rx_max']}]</div>
                    <div class="validation-item {'validation-ok' if loss_ok_b else 'validation-error'}">Perda {loss_ba} dB {'<=' if loss_ok_b else '>'} {budget_b} dB</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            all_ok = tx_ok_a and rx_ok_a and loss_ok_a and tx_ok_b and rx_ok_b and loss_ok_b

            st.markdown(f"""
            <div class="status-container">
                <div class="{'status-ok' if all_ok else 'status-error'}">{ 'ENLACE DENTRO DA ESPECIFICAÇÃO' if all_ok else 'ENLACE FORA DE ESPECIFICAÇÃO ❌'}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown("### Ações")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Limpar", use_container_width=True):
                    st.session_state.calcular = False

            with col2:
                pop_a_data = {
                    "interface": interface_a,
                    "tx": tx_a,
                    "rx": rx_a,
                    "gbic": gbic_a["modelo"],
                    "perda": loss_ab
                }

                pop_b_data = {
                    "interface": interface_b,
                    "tx": tx_b,
                    "rx": rx_b,
                    "gbic": gbic_b["modelo"],
                    "perda": loss_ba
                }

                status = " ENLACE DENTRO DA ESPECIFICAÇÃO" if all_ok else "❌ ENLACE FORA DE ESPECIFICAÇÃO"

                pdf_buffer = generate_pdf(
                    pop_a_data,
                    pop_b_data,
                    loss_ab,
                    loss_ba,
                    gbic_a["modelo"],
                    budget_a,
                    status,
                    st.session_state.get("app_title", "Calculadora de Sinal Óptico - Telium"),
                    st.session_state.get("section_title", ""),
                    st.session_state.get("pop_a_name", "POP A"),
                    st.session_state.get("pop_b_name", "POP B")
                )

                st.download_button(
                    label="Exportar PDF",
                    data=pdf_buffer,
                    file_name=f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            with col3:
                if st.button("Salvar", use_container_width=True):
                    history = load_history()

                    new_entry = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "interface_a": interface_a,
                        "tx_a": tx_a,
                        "rx_a": rx_a,
                        "gbic_a": gbic_a["modelo"],
                        "perda_a": loss_ab,
                        "interface_b": interface_b,
                        "tx_b": tx_b,
                        "rx_b": rx_b,
                        "gbic_b": gbic_b["modelo"],
                        "perda_b": loss_ba,
                        "status": " OK" if all_ok else "❌ ERRO"
                    }

                    history.append(new_entry)
                    save_history(history[-20:])

                    st.success(" Cálculo salvo no histórico!")

    elif menu == "Histórico":
        st.markdown("### Histórico de Cálculos")

        history = load_history()

        if history:
            # Show newest first
            history_df = pd.DataFrame(history[::-1])

            # Pagination controls
            page_size = st.selectbox("Linhas por página", [5, 10, 20], index=1, key='hist_page_size')
            total = len(history_df)
            total_pages = max(1, math.ceil(total / page_size))
            if 'hist_page' not in st.session_state:
                st.session_state.hist_page = 1

            col_prev, col_info, col_next = st.columns([1,2,1])
            with col_prev:
                if st.button("Anterior", key='hist_prev'):
                    st.session_state.hist_page = max(1, st.session_state.hist_page - 1)
            with col_info:
                st.markdown(f"**Página {st.session_state.hist_page} de {total_pages} — {total} registros**")
            with col_next:
                if st.button("Próximo >", key='hist_next'):
                    st.session_state.hist_page = min(total_pages, st.session_state.hist_page + 1)

            start = (st.session_state.hist_page - 1) * page_size
            end = start + page_size
            page_df = history_df.iloc[start:end]
            st.dataframe(page_df, use_container_width=True, hide_index=True)

            csv_data = history_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Exportar histórico CSV",
                data=csv_data,
                file_name="historico_optico.csv",
                mime="text/csv",
                use_container_width=True,
            )

            if st.button("Limpar Histórico"):
                save_history([])
                st.success("Histórico limpo!")
                st.experimental_rerun()
        else:
            st.info("📭 Nenhum histórico disponível")
        st.markdown("""
        #### O que é?

        Aplicação web para cálculo e validação de potência óptica em enlaces de fibra.

        #### Funcionalidades

        - Cálculo automático de perda óptica em ambos os sentidos
        - Validação contra especificações da GBIC
        - Suporte a múltiplos modelos de GBIC
        - Interface interativa e responsiva
        - Exportação de relatórios em PDF
        - Histórico de cálculos com exportação

        #### Como Usar

        1. Preencha os dados de POP A e POP B
        2. Selecione as GBICs em cada dropdown
        3. Clique em "INICIAR CÁLCULO"
        4. Verifique resultados e exporte se necessário

        #### Informações Técnicas

        - Versão: 1.0.0
        - Desenvolvido para: Telium Network Solutions
        - Framework: Streamlit + Python
        """)

if __name__ == "__main__":
    main()
