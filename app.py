import streamlit as st
from datetime import datetime, date, timedelta
from fpdf import FPDF

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Rescisão 2026", layout="wide", page_icon="⚖️")

# --- FUNÇÕES DE CÁLCULO ---
def calcular_avos_ferias(adm, dem_com_projecao):
    if not adm or not dem_com_projecao: return 0
    dias_totais = (dem_com_projecao - adm).days
    meses = dias_totais // 30
    dias_restantes = dias_totais % 30
    if dias_restantes >= 15: meses += 1
    return meses % 12 if meses % 12 != 0 or meses == 0 else 12

def calcular_irrf(base_calculo):
    base_liquida = max(0, base_calculo - 564.80) 
    if base_liquida <= 2259.20: return 0.0
    elif base_liquida <= 2826.65: return (base_liquida * 0.075) - 169.44
    elif base_liquida <= 3751.05: return (base_liquida * 0.15) - 381.44
    elif base_liquida <= 4664.68: return (base_liquida * 0.225) - 662.77
    else: return (base_liquida * 0.275) - 896.00

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
        
    pdf.ln(3)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(140, 8, " DESCONTOS (DEBITOS)", 1, 0, "L", True)
    pdf.cell(50, 8, "VALOR", 1, 1, "C", True)
    pdf.set_font("Arial", "", 9)
    for k, v in dados['debitos'].items():
        pdf.cell(140, 7, k, 1)
        pdf.cell(50, 7, f"R$ {v}", 1, 1, "R")

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(140, 10, "TOTAL LIQUIDO", 1, 0)
    pdf.cell(50, 10, f"R$ {dados['liquido']:,.2f}", 1, 1, "R")
    
    pdf.ln(25)
    pdf.cell(90, 0.2, "", "T", 0)
    pdf.cell(10, 0.2, "", 0, 0)
    pdf.cell(90, 0.2, "", "T", 1)
    pdf.cell(90, 5, "EMPRESA", 0, 0, "C")
    pdf.cell(90, 5, "COLABORADOR", 0, 1, "R")
    return pdf.output(dest="S").encode("latin-1")

# --- INTERFACE ---
st.title("⚖️ ERP de Rescisão Profissional")

with st.container():
    col1, col2, col3 = st.columns(3)
    nome_emp = col1.text_input("Nome do Colaborador", value="")
    dt_adm = col2.date_input("Data de Admissão", value=None, format="DD/MM/YYYY")
    dt_dem = col3.date_input("Data de Demissão", value=None, format="DD/MM/YYYY")
    motivo_saida = col1.selectbox("Motivo", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum", "Justa Causa"])
    tipo_aviso = col2.radio("Aviso Prévio", ["Indenizado", "Trabalhado", "Descontado"])

st.sidebar.header("💰 Proventos")
sal_base = st.sidebar.number_input("Salário Base", value=0.0)
outras_medias = st.sidebar.number_input("Médias", value=0.0)
fgts_total = st.sidebar.number_input("Saldo FGTS", value=0.0)

st.sidebar.divider()
st.sidebar.header("🛑 Descontos Manuais")
faltas_dias = st.sidebar.number_input("Faltas (Dias)", min_value=0, value=0)
outros_descontos = st.sidebar.number_input("Outros Descontos", value=0.0)

st.sidebar.divider()
st.sidebar.header("⚖️ Opções Legais")
vencidas_check = st.sidebar.checkbox("Possui Férias Vencidas?")
aplicar_multa_477 = st.sidebar.checkbox("Aplicar Multa Art. 477 (Atraso)")

if dt_adm and dt_dem:
    anos_casa = (dt_dem - dt_adm).days // 365
    dias_adicionais = min(anos_casa, 20) * 3
    dias_totais_aviso = 30 + dias_adicionais
    
    dt_projecao = dt_dem
    if tipo_aviso == "Indenizado" and motivo_saida == "Sem Justa Causa":
        dt_projecao = dt_dem + timedelta(days=dias_totais_aviso)

    base = sal_base + outras_medias
    valor_dia = base / 30
    
    # Créditos
    s_salario = valor_dia * dt_dem.day
    avos_13 = (dt_projecao.month if dt_projecao.day >= 15 else dt_projecao.month - 1)
    if dt_adm.year == dt_dem.year: avos_13 = avos_13 - dt_adm.month + 1
    v_13 = (base / 12) * max(0, avos_13)
    
    avos_ferias = calcular_avos_ferias(dt_adm, dt_projecao)
    v_ferias_p = (base / 12) * avos_ferias
    
    # --- LÓGICA DE FÉRIAS VENCIDAS + MULTA (DOBRA) ---
    v_ferias_v = 0.0
    v_dobra_ferias = 0.0
    if vencidas_check:
        v_ferias_v = base  # Valor das férias vencidas simples
        v_dobra_ferias = base  # Multa (Dobra) conforme Art. 137 CLT
    
    # Terço incide sobre as proporcionais, as vencidas e a dobra
    v_terco = (v_ferias_p + v_ferias_v + v_dobra_ferias) / 3
    
    v_aviso_val = (valor_dia * dias_totais_aviso) if (tipo_aviso == "Indenizado" and motivo_saida == "Sem Justa Causa") else 0.0
    v_multa477_val = sal_base if aplicar_multa_477 else 0.0
    v_multa_fgts = fgts_total * (0.4 if motivo_saida == "Sem Justa Causa" else 0.2 if motivo_saida == "Acordo Comum" else 0.0)

    creditos = {
        "Saldo de Salário": f"{s_salario:,.2f}",
        f"13º Salário ({avos_13} avos)": f"{v_13:,.2f}",
        f"Férias Prop. ({avos_ferias}/12)": f"{v_ferias_p:,.2f}",
    }
    
    if vencidas_check:
        creditos["Férias Vencidas"] = f"{v_ferias_v:,.2f}"
        creditos["Dobra de Férias (Art. 137 CLT)"] = f"{v_dobra_ferias:,.2f}"
    
    creditos["1/3 Constitucional (Total)"] = f"{v_terco:,.2f}"
    
    if v_aviso_val > 0: creditos[f"Aviso Prévio ({dias_totais_aviso} dias)"] = f"{v_aviso_val:,.2f}"
    if v_multa477_val > 0: creditos["Multa Art. 477 CLT"] = f"{v_multa477_val:,.2f}"
    if v_multa_fgts > 0: creditos["Multa FGTS"] = f"{v_multa_fgts:,.2f}"

    # Débitos
    v_faltas = valor_dia * faltas_dias
    desc_inss = (s_salario + v_13) * 0.09
    base_irrf = s_salario + v_13 - desc_inss
    v_irrf = calcular_irrf(base_irrf)
    desc_aviso_neg = sal_base if tipo_aviso == "Descontado" else 0.0
    
    debitos = {
        "INSS (Previdência)": f"{desc_inss:,.2f}",
        "IRRF (Imposto de Renda)": f"{v_irrf:,.2f}",
        "Faltas/DSR": f"{v_faltas:,.2f}",
        "Outros Descontos": f"{outros_descontos:,.2f}"
    }
    if desc_aviso_neg > 0: debitos["Aviso Prévio (Desconto)"] = f"{desc_aviso_neg:,.2f}"

    total_bruto = sum(float(x.replace(",", "")) for x in creditos.values())
    total_debitos = sum(float(x.replace(",", "")) for x in debitos.values())
    total_liq = total_bruto - total_debitos

    # EXIBIÇÃO
    st.success(f"### 📜 Lei 12.506/11: {dias_totais_aviso} dias de Aviso Prévio.")
    st.divider()
    c_a, c_b = st.columns(2)
    with c_a:
        st.write("### 🟢 Créditos")
        st.table(creditos)
    with c_b:
        st.write("### 🔴 Descontos")
        st.table(debitos)
        st.metric("LÍQUIDO FINAL", f"R$ {total_liq:,.2f}")

    pdf_b = gerar_pdf_bytes({"nome": nome_emp, "adm": dt_adm.strftime("%d/%m/%Y"), "dem": dt_dem.strftime("%d/%m/%Y"), "creditos": creditos, "debitos": debitos, "liquido": total_liq})
    st.download_button("📥 Baixar PDF Detalhado", data=pdf_b, file_name=f"Rescisao_{nome_emp}.pdf", mime="application/pdf")
else:
    st.warning("Preencha as datas para iniciar o cálculo.")
