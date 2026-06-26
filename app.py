import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import json
import os
import base64
import html
import math
import re

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
        --warning: #e6a700;
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
    .result-label{ color:var(--primary); font-weight:800; display:inline-block; min-width:64px; vertical-align:top; }
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
    /* Indicador de faixa TX/RX */
    .faixa-track{ position:relative; height:7px; border-radius:6px; background:rgba(130,130,130,0.22); margin:8px 4px 2px; }
    .faixa-marker{ position:absolute; top:-4px; width:15px; height:15px; border-radius:50%; transform:translateX(-50%); border:2px solid #fff; box-shadow:0 1px 3px rgba(0,0,0,0.35); }
    .validation-item.validation-ok{ border-left:4px solid var(--success); }
    .validation-item.validation-warn{ border-left:4px solid var(--warning); background:rgba(230,167,0,0.10); }
    .validation-item.validation-error{ border-left:4px solid var(--error); background:rgba(231,76,60,0.08); }
    .status-container{ margin-top:10px; padding:16px 18px; border-radius:14px; background:rgba(30,111,179,0.07); border:1px solid rgba(30,111,179,0.18); }
    .status-ok{ color:var(--success); font-weight:700; }
    .status-warn{ color:var(--warning); font-weight:700; }
    .status-error{ color:var(--error); font-weight:700; }
    /* Cores de semáforo para valores (métrica de margem) */
    .metric-value.sem-ok{ color:var(--success); }
    .metric-value.sem-warn{ color:var(--warning); }
    .metric-value.sem-error{ color:var(--error); }

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

def formatar_opcao_modelo(row):
    """Monta 'Modelo (40 Km)' (sem o fabricante, já escolhido antes)."""
    base = f"{row['modelo']}".strip()
    alc = alcance_texto(row.get("quilometragem") if hasattr(row, "get") else None)
    if alc:
        base += f" ({alc})"
    return base

def onda_texto(valor):
    """Formata o comprimento de onda: número -> '1310 nm'; 'BiDi' -> 'BiDi'.
       Vazio -> ''."""
    if valor is None:
        return ""
    s = str(valor).strip()
    if s.lower() in ("", "nan", "none"):
        return ""
    if s.lower() == "bidi":
        return "BiDi"
    try:
        num = float(s.replace(",", "."))
    except ValueError:
        return s
    txt = str(int(num)) if num == int(num) else ("%g" % num)
    return f"{txt} nm"

def estado_margem(margem, margem_min):
    """Semáforo da margem: 'error' se estourou (<0), 'warn' se no limite
       (0 a margem_min), 'ok' se há folga (>= margem_min)."""
    if margem < 0:
        return "error"
    if margem < margem_min:
        return "warn"
    return "ok"

def barra_faixa(valor, vmin, vmax, ok):
    """Mini-barra mostrando onde a leitura cai dentro de [vmin, vmax].
       Marcador verde se dentro, vermelho se fora (posição limitada às bordas)."""
    try:
        if float(vmax) == float(vmin):
            pos = 50.0
        else:
            pos = (float(valor) - float(vmin)) / (float(vmax) - float(vmin)) * 100.0
    except (TypeError, ValueError, ZeroDivisionError):
        pos = 50.0
    pos = max(0.0, min(100.0, pos))
    cor = "var(--success)" if ok else "var(--error)"
    return (
        f'<div class="faixa-track">'
        f'<div class="faixa-marker" style="left:{pos:.1f}%; background:{cor};"></div>'
        f'</div>'
    )

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

def generate_pdf(pop_a, pop_b, loss_ab, loss_ba, status_texto, status_estado,
                 margem_min, app_title, section_title, pop_a_name, pop_b_name, info=None):
    buffer = io.BytesIO()
    larg_pag, alt_pag = letter
    info = info or {}

    CIANO = colors.HexColor('#1ca9e0')      # cabeçalho das tabelas (estilo RFC)
    TITULO = colors.HexColor('#16527f')
    CINZA = colors.HexColor('#5b6b7a')
    TEXTO = colors.HexColor('#2b3440')
    BORDA = colors.HexColor('#c7d3de')
    ZEBRA = colors.HexColor('#eaf1f7')
    # banner de status (faixa sólida estilo "PASS")
    BANNER = {
        'ok':    (colors.HexColor('#a8d9a0'), colors.HexColor('#1e5b2a')),
        'warn':  (colors.HexColor('#f3da8e'), colors.HexColor('#7a5b00')),
        'error': (colors.HexColor('#e6a6a6'), colors.HexColor('#8a1f1f')),
    }
    COR_ESTADO = {
        'ok': colors.HexColor('#27ae60'),
        'warn': colors.HexColor('#c98a00'),
        'error': colors.HexColor('#d23b3b'),
    }
    banner_bg, banner_fg = BANNER.get(status_estado, (CIANO, colors.white))
    rodape_titulo = app_title or "Calculadora de Sinal Óptico - Telium"

    logo_path = "assets/telium-logo.png"

    def _decor(canvas, doc):
        canvas.saveState()
        # Cabeçalho: logo TELIUM (ou texto de fallback) + página, com régua preta
        if os.path.exists(logo_path):
            canvas.drawImage(logo_path, 0.6 * inch, alt_pag - 0.6 * inch,
                             width=1.15 * inch, height=0.28 * inch,
                             preserveAspectRatio=True, anchor='sw', mask='auto')
        else:
            canvas.setFillColor(TEXTO)
            canvas.setFont('Helvetica-Oblique', 9)
            canvas.drawString(0.6 * inch, alt_pag - 0.55 * inch, "Telium Networks")
        canvas.setFillColor(TEXTO)
        canvas.setFont('Helvetica-Oblique', 9)
        canvas.drawRightString(larg_pag - 0.6 * inch, alt_pag - 0.55 * inch, f"Página {doc.page}")
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(2)
        canvas.line(0.6 * inch, alt_pag - 0.63 * inch, larg_pag - 0.6 * inch, alt_pag - 0.63 * inch)
        # Acento ciano fino logo abaixo da régua (toque de marca, liga ao tema das tabelas)
        canvas.setStrokeColor(CIANO)
        canvas.setLineWidth(1.5)
        canvas.line(0.6 * inch, alt_pag - 0.655 * inch, larg_pag - 0.6 * inch, alt_pag - 0.655 * inch)

        # Rodapé: régua preta + logo à esquerda, título ao centro e data à direita
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(2)
        canvas.line(0.6 * inch, 0.63 * inch, larg_pag - 0.6 * inch, 0.63 * inch)
        if os.path.exists(logo_path):
            canvas.drawImage(logo_path, 0.6 * inch, 0.37 * inch,
                             width=0.85 * inch, height=0.18 * inch,
                             preserveAspectRatio=True, anchor='sw', mask='auto')
        canvas.setFillColor(CINZA)
        canvas.setFont('Helvetica', 8)
        canvas.drawCentredString(larg_pag / 2, 0.45 * inch, rodape_titulo)
        canvas.drawRightString(larg_pag - 0.6 * inch, 0.45 * inch,
                               datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=0.95 * inch, bottomMargin=0.9 * inch,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    story = []
    LARG = 7.3 * inch

    sec_style = ParagraphStyle('Sec', parent=styles['Normal'], fontName='Helvetica-Bold',
                               fontSize=12, textColor=TITULO, spaceAfter=2)

    # --- Título em painel (barra de acento ciano + fundo claro) ---
    titulo_style = ParagraphStyle('T', parent=styles['Normal'], fontName='Helvetica-Bold',
                                  fontSize=17, textColor=TITULO, leading=21)
    subt_style = ParagraphStyle('Tsub', parent=styles['Normal'], fontSize=9.5,
                                textColor=CINZA, leading=13, spaceBefore=3)
    titulo_conteudo = [
        Paragraph("Resultados da Validação de Enlace Óptico", titulo_style),
        Paragraph("Relatório técnico de potência óptica em enlace de fibra", subt_style),
    ]
    titulo_tbl = Table([['', titulo_conteudo]], colWidths=[0.16 * inch, LARG - 0.16 * inch])
    titulo_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), CIANO),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#eef4f9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (1, 0), (1, 0), 14),
        ('RIGHTPADDING', (1, 0), (1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 11),
        ('LINEAFTER', (0, 0), (0, 0), 0, CIANO),
    ]))
    story.append(titulo_tbl)
    story.append(Spacer(1, 0.18 * inch))

    # --- Informações do Relatório (estilo "Job Information") ---
    campos = [
        ("Cliente", str(info.get("cliente", "")).strip()),
        ("Operador", str(info.get("operador", "")).strip()),
        ("Circuit ID", str(info.get("circuito", "")).strip()),
        ("Comentário", str(info.get("comentario", "")).strip()),
    ]
    if any(v for _, v in campos):
        story.append(Paragraph("Informações do Relatório", sec_style))
        story.append(HRFlowable(width="100%", thickness=0.8, color=BORDA, spaceBefore=2, spaceAfter=6))
        info_rows = [["Data", datetime.now().strftime("%d/%m/%Y %H:%M:%S")]]
        info_rows += [[lbl, val or "—"] for lbl, val in campos]
        info_tbl = Table(info_rows, colWidths=[1.7 * inch, LARG - 1.7 * inch])
        info_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f2f6fa')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), TITULO),
            ('TEXTCOLOR', (1, 0), (1, -1), TEXTO),
            ('FONTSIZE', (0, 0), (-1, -1), 9.5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDA),
        ]))
        story.append(info_tbl)
        story.append(Spacer(1, 0.2 * inch))

    # --- Banner de status (callout com borda + descrição) ---
    DESC = {
        'ok': "Todas as medições dentro da especificação, com folga adequada.",
        'warn': "Dentro da especificação, porém com folga abaixo do limite de referência.",
        'error': "Uma ou mais medições fora da especificação.",
    }
    forte = COR_ESTADO.get(status_estado, CIANO)
    banner_titulo = ParagraphStyle('B', parent=styles['Normal'], fontName='Helvetica-Bold',
                                   fontSize=15, textColor=banner_fg, alignment=1, leading=18)
    banner_desc = ParagraphStyle('Bd', parent=styles['Normal'], fontSize=9.5,
                                 textColor=banner_fg, alignment=1, leading=13)
    banner_cell = [
        Paragraph(status_texto, banner_titulo),
        Spacer(1, 3),
        Paragraph(DESC.get(status_estado, ""), banner_desc),
    ]
    banner = Table([[banner_cell]], colWidths=[LARG])
    banner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), banner_bg),
        ('BOX', (0, 0), (-1, -1), 1.3, forte),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(banner)
    story.append(Spacer(1, 0.22 * inch))

    # --- Tabela comparativa (cabeçalho ciano, zebra) ---
    linhas = [
        ["Parâmetro", pop_a_name or 'POP A', pop_b_name or 'POP B'],
        ["Interface", pop_a["interface"], pop_b["interface"]],
        ["TX (dBm)", pop_a["tx"], pop_b["tx"]],
        ["RX (dBm)", pop_a["rx"], pop_b["rx"]],
        ["GBIC / SFP", pop_a["gbic"], pop_b["gbic"]],
        ["Alcance nominal", pop_a["alcance"], pop_b["alcance"]],
        ["Budget (dB)", pop_a["budget"], pop_b["budget"]],
        ["Perda (dB)", pop_a["perda"], pop_b["perda"]],
        ["Margem (dB)", pop_a["margem"], pop_b["margem"]],
    ]
    linhas = [[str(c) for c in row] for row in linhas]
    margem_row = len(linhas) - 1
    table = Table(linhas, colWidths=[2.4 * inch, 2.45 * inch, 2.45 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), CIANO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 1), (0, -1), TEXTO),
        ('TEXTCOLOR', (1, 1), (-1, -1), TEXTO),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDA),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ZEBRA]),
        ('TEXTCOLOR', (1, margem_row), (1, margem_row), COR_ESTADO.get(pop_a["estado"], TEXTO)),
        ('TEXTCOLOR', (2, margem_row), (2, margem_row), COR_ESTADO.get(pop_b["estado"], TEXTO)),
        ('FONTNAME', (1, margem_row), (2, margem_row), 'Helvetica-Bold'),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.24 * inch))

    # --- Memória de cálculo ---
    sec_style = ParagraphStyle('Sec', parent=styles['Normal'], fontName='Helvetica-Bold',
                               fontSize=12, textColor=TITULO, spaceAfter=2)
    story.append(Paragraph("Memória de cálculo", sec_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=BORDA, spaceBefore=2, spaceAfter=8))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9.5,
                                textColor=TEXTO, leading=15)
    calc = (
        f"Perda A -&gt; B = TX(A) - RX(B) = ({pop_a['tx']}) - ({pop_b['rx']}) = <b>{loss_ab} dB</b><br/>"
        f"Perda B -&gt; A = TX(B) - RX(A) = ({pop_b['tx']}) - ({pop_a['rx']}) = <b>{loss_ba} dB</b><br/>"
        f"Margem = Budget - Perda &nbsp;&nbsp;(referência de folga mínima: <b>{margem_min} dB</b>)"
    )
    story.append(Paragraph(calc, body_style))

    doc.build(story, onFirstPage=_decor, onLaterPages=_decor)
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

        with st.expander("📋 Dados do relatório (opcional — aparecem no PDF)", expanded=False):
            jc1, jc2 = st.columns(2)
            with jc1:
                st.text_input("Cliente", key="rel_cliente", placeholder="Ex: Empresa X")
                st.text_input("Circuit ID", key="rel_circuito", placeholder="Ex: CKT-00123")
            with jc2:
                st.text_input("Operador", key="rel_operador", placeholder="Ex: João Silva")
                st.text_input("Comentário", key="rel_comentario", placeholder="Observações")

        col1, col2 = st.columns(2)

        with col1:
            pop_a_inline = st.text_input("", value=st.session_state.pop_a_name, key="pop_a_inline", label_visibility="collapsed")
            if pop_a_inline != st.session_state.pop_a_name:
                st.session_state.pop_a_name = pop_a_inline
            interface_a = st.text_input("Interface", value="TenGigabitEthernet 1/1/1", key="interface_a", label_visibility="collapsed")
            tx_a = st.number_input("TX (dBm)", value=-2.81, step=0.01, key="tx_a", label_visibility="collapsed")
            rx_a = st.number_input("RX (dBm)", value=-13.62, step=0.01, key="rx_a", label_visibility="collapsed")

            fabricantes = list(dict.fromkeys(gbics_df["fabricante"].tolist()))
            fab_a = st.selectbox("Fabricante", options=fabricantes, key="fab_a")
            df_fab_a = gbics_df[gbics_df["fabricante"] == fab_a].reset_index(drop=True)
            opts_a = df_fab_a.apply(formatar_opcao_modelo, axis=1).tolist()
            gbic_a_selected = st.selectbox("SFP", options=opts_a, key=f"gbic_a_{fab_a}")
            gbic_a = df_fab_a.iloc[opts_a.index(gbic_a_selected)]

        with col2:
            pop_b_inline = st.text_input("", value=st.session_state.pop_b_name, key="pop_b_inline", label_visibility="collapsed")
            if pop_b_inline != st.session_state.pop_b_name:
                st.session_state.pop_b_name = pop_b_inline
            interface_b = st.text_input("Interface", value="TenGigabitEthernet 1/1/2", key="interface_b", label_visibility="collapsed")
            tx_b = st.number_input("TX (dBm)", value=-3.19, step=0.01, key="tx_b", label_visibility="collapsed")
            rx_b = st.number_input("RX (dBm)", value=-14.53, step=0.01, key="rx_b", label_visibility="collapsed")

            fab_b = st.selectbox("Fabricante", options=fabricantes, key="fab_b")
            df_fab_b = gbics_df[gbics_df["fabricante"] == fab_b].reset_index(drop=True)
            opts_b = df_fab_b.apply(formatar_opcao_modelo, axis=1).tolist()
            gbic_b_selected = st.selectbox("SFP", options=opts_b, key=f"gbic_b_{fab_b}")
            gbic_b = df_fab_b.iloc[opts_b.index(gbic_b_selected)]

        # Limite de folga abaixo do qual o enlace é marcado como "no limite" (amarelo).
        margem_min = 3.0

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

            # Margem de segurança (folga em relação ao budget) e semáforo
            margem_a = round(budget_a - loss_ab, 2)
            margem_b = round(budget_b - loss_ba, 2)
            estado_a = estado_margem(margem_a, margem_min)
            estado_b = estado_margem(margem_b, margem_min)
            margem_pior = min(margem_a, margem_b)
            estado_pior = estado_margem(margem_pior, margem_min)
            dot = {"ok": "🟢", "warn": "🟡", "error": "🔴"}

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

            col1, col2, col3, col4, col5 = st.columns(5)

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

            with col5:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">Margem (folga)</div>
                    <div class="metric-value sem-{estado_pior}">{dot[estado_pior]} {margem_pior} dB</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown("### Validação")

            st.markdown(f"""
            <div class="validation-grid">
                <div class="validation-card">
                    <div class="validation-title">{st.session_state.pop_a_name} - Validação</div>
                    <div class="validation-item {'validation-ok' if tx_ok_a else 'validation-error'}">TX {tx_a} {'dentro' if tx_ok_a else '❌ fora'} de [{gbic_a['tx_min']}, {gbic_a['tx_max']}]{barra_faixa(tx_a, gbic_a['tx_min'], gbic_a['tx_max'], tx_ok_a)}</div>
                    <div class="validation-item {'validation-ok' if rx_ok_a else 'validation-error'}">RX {rx_a} {'dentro' if rx_ok_a else '❌ fora'} de [{gbic_a['rx_min']}, {gbic_a['rx_max']}]{barra_faixa(rx_a, gbic_a['rx_min'], gbic_a['rx_max'], rx_ok_a)}</div>
                    <div class="validation-item {'validation-ok' if loss_ok_a else 'validation-error'}">Perda {loss_ab} dB {'<=' if loss_ok_a else '>'} {budget_a} dB</div>
                    <div class="validation-item validation-{estado_a}">{dot[estado_a]} Margem {margem_a} dB {'(estourou)' if estado_a == 'error' else '(no limite)' if estado_a == 'warn' else '(folga ok)'}</div>
                </div>
                <div class="validation-card">
                    <div class="validation-title">{st.session_state.pop_b_name} - Validação</div>
                    <div class="validation-item {'validation-ok' if tx_ok_b else 'validation-error'}">TX {tx_b} {'dentro' if tx_ok_b else '❌ fora'} de [{gbic_b['tx_min']}, {gbic_b['tx_max']}]{barra_faixa(tx_b, gbic_b['tx_min'], gbic_b['tx_max'], tx_ok_b)}</div>
                    <div class="validation-item {'validation-ok' if rx_ok_b else 'validation-error'}">RX {rx_b} {'dentro' if rx_ok_b else '❌ fora'} de [{gbic_b['rx_min']}, {gbic_b['rx_max']}]{barra_faixa(rx_b, gbic_b['rx_min'], gbic_b['rx_max'], rx_ok_b)}</div>
                    <div class="validation-item {'validation-ok' if loss_ok_b else 'validation-error'}">Perda {loss_ba} dB {'<=' if loss_ok_b else '>'} {budget_b} dB</div>
                    <div class="validation-item validation-{estado_b}">{dot[estado_b]} Margem {margem_b} dB {'(estourou)' if estado_b == 'error' else '(no limite)' if estado_b == 'warn' else '(folga ok)'}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            all_ok = tx_ok_a and rx_ok_a and loss_ok_a and tx_ok_b and rx_ok_b and loss_ok_b
            no_limite = all_ok and estado_pior == "warn"

            if not all_ok:
                estado_geral = "error"
                status_classe, status_texto = "status-error", "🔴 ENLACE FORA DE ESPECIFICAÇÃO ❌"
                status_pdf = "ENLACE FORA DE ESPECIFICAÇÃO"
            elif no_limite:
                estado_geral = "warn"
                status_classe, status_texto = "status-warn", "🟡 ENLACE NO LIMITE ⚠️"
                status_pdf = "ENLACE NO LIMITE"
            else:
                estado_geral = "ok"
                status_classe, status_texto = "status-ok", "🟢 ENLACE DENTRO DA ESPECIFICAÇÃO ✅"
                status_pdf = "ENLACE DENTRO DA ESPECIFICAÇÃO"

            st.markdown(f"""
            <div class="status-container">
                <div class="{status_classe}">{status_texto}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown("### Ações")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Limpar", use_container_width=True):
                    st.session_state.calcular = False

            with col2:
                pop_a_data = {
                    "interface": interface_a,
                    "tx": tx_a,
                    "rx": rx_a,
                    "gbic": gbic_a["modelo"],
                    "alcance": alcance_a or "—",
                    "budget": budget_a,
                    "perda": loss_ab,
                    "margem": margem_a,
                    "estado": estado_a,
                }

                pop_b_data = {
                    "interface": interface_b,
                    "tx": tx_b,
                    "rx": rx_b,
                    "gbic": gbic_b["modelo"],
                    "alcance": alcance_b or "—",
                    "budget": budget_b,
                    "perda": loss_ba,
                    "margem": margem_b,
                    "estado": estado_b,
                }

                info_relatorio = {
                    "cliente": st.session_state.get("rel_cliente", ""),
                    "operador": st.session_state.get("rel_operador", ""),
                    "circuito": st.session_state.get("rel_circuito", ""),
                    "comentario": st.session_state.get("rel_comentario", ""),
                }

                pdf_buffer = generate_pdf(
                    pop_a_data,
                    pop_b_data,
                    loss_ab,
                    loss_ba,
                    status_pdf,
                    estado_geral,
                    margem_min,
                    st.session_state.get("app_title", "Calculadora de Sinal Óptico - Telium"),
                    st.session_state.get("section_title", ""),
                    st.session_state.get("pop_a_name", "POP A"),
                    st.session_state.get("pop_b_name", "POP B"),
                    info_relatorio,
                )

                def _slug(texto):
                    s = re.sub(r"[^A-Za-z0-9._-]+", "-", str(texto).strip())
                    return s.strip("-")[:40]

                partes = ["relatorio"]
                if info_relatorio.get("circuito", "").strip():
                    partes.append(_slug(info_relatorio["circuito"]))
                if info_relatorio.get("cliente", "").strip():
                    partes.append(_slug(info_relatorio["cliente"]))
                partes.append(datetime.now().strftime("%Y%m%d_%H%M%S"))
                nome_pdf = "_".join(p for p in partes if p) + ".pdf"

                st.download_button(
                    label="Exportar PDF",
                    data=pdf_buffer,
                    file_name=nome_pdf,
                    mime="application/pdf",
                    use_container_width=True
                )

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
