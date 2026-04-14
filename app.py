import streamlit as st
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÕES DO SISTEMA ---
st.set_page_config(page_title="Gestão de Rescisões v2026", layout="wide")

def aplicar_piso(valor, piso):
    return max(valor, piso)

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Termo de Rescisão do Contrato de Trabalho (Simulação)", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    for chave, valor in dados.items():
        pdf.cell(200, 10, f"{chave}: {valor}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(200, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
    return pdf.output(dest="S").encode("latin-1")

def main():
    st.title("🏢 Portal de RH - Módulo de Desligamento 2026")
    st.markdown("---")

    # --- ENTRADA DE DADOS ORGANIZADA ---
    with st.container():
        col_id1, col_id2 = st.columns(2)
        with col_id1:
            nome_func = st.text_input("Nome Completo do Colaborador")
            cpf_func = st.text_input("CPF")
        with col_id2:
            data_adm = st.date_input("Data de Admissão")
            data_dem = st.date_input("Data de Demissão")

    st.sidebar.header("📊 Parâmetros de Cálculo")
    salario_base = st.sidebar.number_input("Salário Fixo Mensal", min_value=1630.0, value=2500.0)
    media_variaveis = st.sidebar.number_input("Média de Comissões/DSR (12 meses)", min_value=0.0, value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo p/ Fins Rescisórios FGTS", min_value=0.0, value=5000.0)
    
    motivo = st.sidebar.selectbox("Tipo de Rescisão", 
        ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])
    
    meses_prop = st.sidebar.slider("Meses Proporcionais (Ano Atual)", 1, 12, 6)
    dias_trabalhados = st.sidebar.slider("Dias Trabalhados no Mês Final", 1, 30, 15)

    # --- PROCESSAMENTO LOGÍSTICO (REGRAS 2026) ---
    SALARIO_MINIMO = 1630.00
    PISO_VERBA = SALARIO_MINIMO / 2 # R$ 815,00
    
    remuneracao_total = salario_base + media_variaveis
    
    # Cálculos
    res_saldo = (remuneracao_total / 30) * dias_trabalhados
    res_13 = aplicar_piso((remuneracao_total / 12) * meses_prop, PISO_VERBA)
    res_ferias = aplicar_piso(((remuneracao_total / 12) * meses_prop) * 1.3333, PISO_VERBA)
    
    multa_fgts = 0
    aviso_previo = 0
    if motivo == "Sem Justa Causa":
        multa_fgts = saldo_fgts * 0.40
        aviso_previo = remuneracao_total
    elif motivo == "Acordo Comum":
        multa_fgts = saldo_fgts * 0.20
        aviso_previo = remuneracao_total * 0.50

    # Deduções
    inss = (res_saldo + res_13) * 0.09 # Simplificado p/ exemplo
    total_bruto = res_saldo + res_13 + res_ferias + aviso_previo + multa_fgts
    total_liquido = total_bruto - inss

    # --- PAINEL DE RESULTADOS ESTILO DASHBOARD ---
    st.subheader("📋 Resumo Financeiro")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Bruto", f"R$ {total_bruto:,.2f}")
    m2.metric("Total Descontos", f"R$ {inss:,.2f}")
    m3.metric("Líquido Final", f"R$ {total_liquido:,.2f}")
    m4.metric("Multa FGTS", f"R$ {multa_fgts:,.2f}")

    st.markdown("### 📄 Detalhamento para o Holerite")
    tabela_rh = {
        "Cód": ["001", "002", "003", "004", "005"],
        "Descrição da Verba": ["Saldo de Salário", "13º Salário Proporcional", "Férias Prop. + 1/3", "Aviso Prévio Indenizado", "Multa Rescisória FGTS"],
        "Valor (R$)": [f"{res_saldo:,.2f}", f"{res_13:,.2f}", f"{res_ferias:,.2f}", f"{aviso_previo:,.2f}", f"{multa_fgts:,.2f}"]
    }
    st.table(tabela_rh)

    # --- EXPORTAÇÃO ---
    st.markdown("---")
    if st.button("🖨️ Gerar Recibo de Quitação em PDF"):
        dados_doc = {
            "Colaborador": nome_func,
            "CPF": cpf_func,
            "Motivo": motivo,
            "Remuneração Base": f"R$ {remuneracao_total:,.2f}",
            "Saldo de Salário": f"R$ {res_saldo:,.2f}",
            "13 Salário": f"R$ {res_13:,.2f}",
            "Férias + 1/3": f"R$ {res_ferias:,.2f}",
            "Multa FGTS": f"R$ {multa_fgts:,.2f}",
            "TOTAL LÍQUIDO": f"R$ {total_liquido:,.2f}"
        }
        pdf_bytes = gerar_pdf(dados_doc)
        st.download_button(label="Baixar PDF", data=pdf_bytes, file_name=f"rescisao_{nome_func}.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()
