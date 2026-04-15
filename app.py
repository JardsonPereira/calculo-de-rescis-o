import streamlit as st
from datetime import datetime, date, timedelta
from fpdf import FPDF

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Rescisão 2026", layout="wide", page_icon="⚖️")

# --- FUNÇÕES SUPORTE ---
def calcular_avos(inicio, fim):
    if not inicio or not fim: return 0
    m = (fim.year - inicio.year) * 12 + fim.month - inicio.month
    if fim.day >= 15: m += 1
    return max(0, m)

def gerar_pdf_bytes(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 15, "RECIBO DE RESCISAO DE CONTRATO", 0, 1, "C")
    
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(190, 8, " IDENTIFICACAO", 0, 1, "L", True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 7, f"Colaborador: {dados['nome']}", 1, 1)
    pdf.cell(95, 7, f"Admissao: {dados['adm']}", 1, 0)
    pdf.cell(95, 7, f"Demissao: {dados['dem']}", 1, 1)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(140, 8, " VERBAS (CREDITOS)", 1, 0, "L", True)
    pdf.cell(50, 8, "VALOR", 1, 1, "C", True)
    pdf.set_font("Arial", "", 9)
    
    for k, v in dados['creditos'].items():
        pdf.cell(140, 7, k, 1)
        pdf.cell(50, 7, f"R$ {v}", 1, 1, "R")
        
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(140, 10, "TOTAL LIQUIDO", 1, 0)
    pdf.cell(50, 10, f"R$ {dados['liquido']:,.2f}", 1, 1, "R")
    
    # Campo de Assinatura
    pdf.ln(30)
    pdf.cell(90, 0.2, "", "T", 0)
    pdf.cell(10, 0.2, "", 0, 0)
    pdf.cell(90, 0.2, "", "T", 1)
    pdf.cell(90, 5, "EMPRESA", 0, 0, "C")
    pdf.cell(90, 5, "COLABORADOR", 0, 1, "R")
    
    return pdf.output(dest="S").encode("latin-1")

# --- INTERFACE PRINCIPAL ---
st.title("⚖️ ERP de Rescisão Profissional")

# Inputs Iniciais Zerados
with st.container():
    col1, col2, col3 = st.columns(3)
    nome_emp = col1.text_input("Nome do Colaborador", value="")
    dt_adm = col2.date_input("Data de Admissão", value=None, format="DD/MM/YYYY")
    dt_dem = col3.date_input("Data de Demissão", value=None, format="DD/MM/YYYY")
    
    motivo_saida = col1.selectbox("Motivo", ["Sem Justa Causa", "Pedido de Demissão", "Justa Causa"])
    tipo_aviso = col2.radio("Aviso Prévio", ["Indenizado", "Trabalhado", "Descontado"])

# Sidebar Zerada
st.sidebar.header("💰 Financeiro")
sal_base = st.sidebar.number_input("Salário Base", value=0.0)
outras_medias = st.sidebar.number_input("Médias", value=0.0)
fgts_total = st.sidebar.number_input("Saldo FGTS", value=0.0)

st.sidebar.divider()
st.sidebar.header("⚖️ Opções Legais")
vencidas_check = st.sidebar.checkbox("Férias Vencidas?")
multa477_check = st.sidebar.checkbox("Aplicar Multa 477 (Atraso)")

# --- LÓGICA DE PROCESSAMENTO ---
if dt_adm and dt_dem:
    # Cálculo Lei 12.506/11 (Aviso Prévio Proporcional)
    anos_casa = (dt_dem - dt_adm).days // 365
    dias_adicionais = min(anos_casa, 20) * 3
    dias_totais_aviso = 30 + dias_adicionais
    
    # Detalhe Visual da Lei
    st.success(f"### 📜 Detalhamento da Lei 12.506/11\n"
               f"Tempo de serviço: **{anos_casa} anos**.\n"
               f"Pela lei, o aviso prévio será de **{dias_totais_aviso} dias** "
               f"(30 dias base + {dias_adicionais} dias por tempo de casa).")

    # Cálculos Financeiros
    base = sal_base + outras_medias
    valor_dia = base / 30
    
    s_salario = valor_dia * dt_dem.day
    v_13 = (base / 12) * calcular_avos(date(dt_dem.year, 1, 1), dt_dem)
    v_ferias_p = (base / 12) * (calcular_avos(dt_adm, dt_dem) % 12)
    v_ferias_v = base if vencidas_check else 0.0
    v_terco = (v_ferias_p + v_ferias_v) / 3
    
    v_aviso_val = (valor_dia * dias_totais_aviso) if (tipo_aviso == "Indenizado" and motivo_saida == "Sem Justa Causa") else 0.0
    v_multa477_val = sal_base if multa477_check else 0.0
    v_multa_fgts = fgts_total * 0.4 if motivo_saida == "Sem Justa Causa" else 0.0

    # Estrutura de Dados (Créditos)
    creditos = {
        "Saldo de Salário": f"{s_salario:,.2f}",
        "13º Salário": f"{v_13:,.2f}",
        "Férias Proporcionais": f"{v_ferias_p:,.2f}",
        "1/3 Constitucional": f"{v_terco:,.2f}"
    }
    if v_ferias_v > 0: creditos["Férias Vencidas"] = f"{v_ferias_v:,.2f}"
    if v_aviso_val > 0: creditos[f"Aviso Prévio ({dias_totais_aviso} dias)"] = f"{v_aviso_val:,.2f}"
    if v_multa477_val > 0: creditos["Multa Art. 477 CLT"] = f"{v_multa477_val:,.2f}"
    if v_multa_fgts > 0: creditos["Multa FGTS (40%)"] = f"{v_multa_fgts:,.2f}"

    # Totais
    total_bruto = sum(float(x.replace(",", "")) for x in creditos.values())
    desc_inss = (s_salario + v_13) * 0.09
    total_liq = total_bruto - desc_inss

    # EXIBIÇÃO NA TELA
    st.divider()
    c_a, c_b = st.columns(2)
    with c_a:
        st.write("### 🟢 Resumo de Créditos")
        st.table(creditos)
    with c_b:
        st.write("### 💰 Totais")
        st.metric("Total Líquido", f"R$ {total_liq:,.2f}")
        st.write(f"Desconto INSS Est.: R$ {desc_inss:,.2f}")

    # Botão de PDF
    dados_p = {
        "nome": nome_emp, "adm": dt_adm.strftime("%d/%m/%Y"), "dem": dt_dem.strftime("%d/%m/%Y"),
        "creditos": creditos, "liquido": total_liq, "motivo": motivo_saida
    }
    
    pdf_b = gerar_pdf_bytes(dados_p)
    st.download_button("📥 Gerar PDF para Assinatura", data=pdf_b, file_name="Rescisao.pdf", mime="application/pdf")

else:
    st.warning("⚠️ Selecione as datas de Admissão e Demissão para começar.")
