import streamlit as st
from fpdf import FPDF
from datetime import datetime
import pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Rescisão 2026", layout="wide")

def aplicar_piso(valor, piso):
    return max(valor, piso)

def calcular_aviso_proporcional(data_adm, data_dem):
    anos = (data_dem - data_adm).days // 365
    dias_totais = 30 + (min(anos, 20) * 3)
    return dias_totais, anos

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "DEMONSTRATIVO DE RESCISAO E HISTORICO - 2026", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    for chave, valor in dados.items():
        pdf.cell(80, 8, f"{chave}:", border=1)
        pdf.cell(110, 8, f"{str(valor)}", border=1, ln=True)
    return pdf.output(dest="S").encode("latin-1")

def main():
    st.title("🏢 Gestão de Desligamento com Histórico Salarial")
    
    # --- SEÇÃO 1: DADOS BÁSICOS ---
    with st.container():
        c1, c2, c3 = st.columns(3)
        nome_func = c1.text_input("Nome do Colaborador")
        data_adm = c2.date_input("Data de Admissão", value=datetime(2022, 1, 1))
        data_dem = c3.date_input("Data de Demissão")
        motivo = c1.selectbox("Motivo", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])

    st.divider()

    # --- SEÇÃO 2: HISTÓRICO SALARIAL E MÉDIAS ---
    st.subheader("📅 Histórico Salarial (Últimos 6 meses)")
    st.write("Informe os salários recebidos para cálculo automático da média.")
    
    col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns(6)
    s1 = col_h1.number_input("Mês 1 (R$)", min_value=1630.0, value=3000.0)
    s2 = col_h2.number_input("Mês 2 (R$)", min_value=1630.0, value=3000.0)
    s3 = col_h3.number_input("Mês 3 (R$)", min_value=1630.0, value=3000.0)
    s4 = col_h4.number_input("Mês 4 (R$)", min_value=1630.0, value=3200.0)
    s5 = col_h5.number_input("Mês 5 (R$)", min_value=1630.0, value=3200.0)
    s6 = col_h6.number_input("Mês 6 (Atual)", min_value=1630.0, value=3500.0)
    
    lista_salarios = [s1, s2, s3, s4, s5, s6]
    media_salarial = sum(lista_salarios) / len(lista_salarios)
    ultimo_salario = s6 # O último informado é o salário atual

    # --- SEÇÃO 3: VARIÁVEIS E FGTS (SIDEBAR) ---
    st.sidebar.header("📂 Variáveis e Encargos")
    media_comissoes = st.sidebar.number_input("Média de Comissões", min_value=0.0, value=0.0)
    media_he = st.sidebar.number_input("Média de Horas Extras", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    st.sidebar.subheader("💰 Fundo de Garantia")
    saldo_fgts_atual = st.sidebar.number_input("Saldo p/ Fins Rescisórios FGTS", min_value=0.0, value=5000.0, step=100.0)
    st.sidebar.caption("Este saldo deve incluir os depósitos mensais e correções até a data atual.")

    # --- CÁLCULOS 2026 ---
    PISO_2026 = 1630.00 / 2 # R$ 815,00
    
    # Bases de cálculo
    base_atual = ultimo_salario + media_comissoes + media_he
    base_media = media_salarial + media_comissoes + media_he
    
    dias_aviso, anos_casa = calcular_aviso_proporcional(data_adm, data_dem)
    meses_prop = data_dem.month if data_dem.day >= 15 else data_dem.month - 1

    # Verbas
    res_saldo = (base_atual / 30) * data_dem.day
    res_13 = aplicar_piso((base_media / 12) * meses_prop, PISO_2026)
    res_ferias = aplicar_piso(((base_media / 12) * meses_prop) * 1.3333, PISO_2026)
    
    # Aviso e Multas
    valor_aviso = 0
    multa_fgts = 0
    if motivo == "Sem Justa Causa":
        valor_aviso = (base_atual / 30) * dias_aviso
        multa_fgts = saldo_fgts_atual * 0.40
    elif motivo == "Acordo Comum":
        valor_aviso = ((base_atual / 30) * dias_aviso) * 0.50
        multa_fgts = saldo_fgts_atual * 0.20

    total_bruto = res_saldo + res_13 + res_ferias + valor_aviso + multa_fgts
    inss = (res_saldo + res_13) * 0.09
    total_liquido = total_bruto - inss

    # --- DASHBOARD ---
    st.subheader("📊 Demonstrativo Final")
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Média Salarial Apurada", f"R$ {media_salarial:,.2f}")
    col_m2.metric("Multa FGTS", f"R$ {multa_fgts:,.2f}")
    col_m3.metric("LÍQUIDO A RECEBER", f"R$ {total_liquido:,.2f}")

    # Detalhamento
    st.markdown("### 🗂️ Memória de Cálculo Individualizada")
    detalhes = {
        "Descrição": ["Salário Atual", "Média Histórica (6m)", "Saldo Salário", "13º Salário", "Férias + 1/3", f"Aviso Prévio ({dias_aviso} dias)", "Multa FGTS"],
        "Valor": [f"R$ {ultimo_salario:,.2f}", f"R$ {media_salarial:,.2f}", f"R$ {res_saldo:,.2f}", f"R$ {res_13:,.2f}", f"R$ {res_ferias:,.2f}", f"R$ {valor_aviso:,.2f}", f"R$ {multa_fgts:,.2f}"]
    }
    st.table(detalhes)

    # --- PDF ---
    if st.button("🖨️ Exportar Termo de Rescisão"):
        dados_pdf = {
            "Nome": nome_func,
            "Admissao": data_adm.strftime('%d/%m/%Y'),
            "Demissao": data_dem.strftime('%d/%m/%Y'),
            "Motivo": motivo,
            "Media Salarial": f"R$ {media_salarial:,.2f}",
            "Saldo FGTS": f"R$ {saldo_fgts_atual:,.2f}",
            "Multa FGTS": f"R$ {multa_fgts:,.2f}",
            "Total Liquido": f"R$ {total_liquido:,.2f}"
        }
        pdf_b = gerar_pdf(dados_pdf)
        st.download_button("📥 Baixar PDF", pdf_b, f"Rescisao_{nome_func}.pdf", "application/pdf")

if __name__ == "__main__":
    main()
