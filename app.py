import streamlit as st
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="SistRH 2026 - Gestão de Longo Prazo", page_icon="🏢", layout="wide")

def aplicar_piso(valor, piso):
    return max(valor, piso)

def calcular_aviso_proporcional(anos_completos):
    """Lei 12.506/2011: 30 dias base + 3 dias por ano trabalhado (limite 90 dias)"""
    dias_adicionais = anos_completos * 3
    total_dias = 30 + dias_adicionais
    return min(total_dias, 90)

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Simulacao de Rescisao de Contrato - 2026", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 11)
    for chave, valor in dados.items():
        pdf.cell(100, 8, f"{chave}:", border=0)
        pdf.cell(90, 8, f"{valor}", border=0, ln=True)
    return pdf.output(dest="S").encode("latin-1")

def main():
    st.title("🏢 Gestão de Desligamentos Estratégicos (Contratos até 20 anos)")
    st.info("Sistema atualizado com a Lei 12.506/2011 (Aviso Prévio Proporcional) e Regras Fiscais 2026.")

    # --- ENTRADA DE DADOS ---
    with st.expander("👤 Identificação do Colaborador", expanded=True):
        c_id1, c_id2 = st.columns(2)
        nome = c_id1.text_input("Nome do Funcionário")
        cpf = c_id2.text_input("CPF")

    st.sidebar.header("⚙️ Parâmetros Financeiros")
    salario_atual = st.sidebar.number_input("Último Salário Fixo", min_value=1630.0, value=3500.0)
    media_salarial = st.sidebar.number_input("Média Salarial (últimos 12 meses)", min_value=1630.0, value=3500.0)
    adicionais = st.sidebar.number_input("Adicionais Fixos (Insalubridade/etc)", min_value=0.0, value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo FGTS para Fins Rescisórios", min_value=0.0, value=15000.0)
    
    st.sidebar.divider()
    
    st.sidebar.header("⏳ Tempo de Serviço")
    anos_servico = st.sidebar.slider("Anos completos de empresa", 0, 20, 5)
    meses_prop = st.sidebar.slider("Meses proporcionais (ano atual)", 1, 12, 6)
    dias_finais = st.sidebar.slider("Dias trabalhados no mês da saída", 1, 30, 15)
    
    motivo = st.sidebar.selectbox("Motivo da Saída", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])

    # --- LÓGICA DE CÁLCULOS (REGRAS 2026) ---
    SALARIO_MINIMO = 1630.00
    PISO_VERBA = SALARIO_MINIMO / 2 # R$ 815,00
    
    remun_atual = salario_atual + adicionais
    remun_media = media_salarial + adicionais
    
    # 1. Aviso Prévio Proporcional
    dias_aviso = calcular_aviso_proporcional(anos_servico)
    valor_aviso = (remun_atual / 30) * dias_aviso
    
    # Ajuste de Aviso por Motivo
    if motivo == "Pedido de Demissão":
        valor_aviso = 0 # Funcionário não recebe aviso indenizado
    elif motivo == "Acordo Comum":
        valor_aviso = valor_aviso * 0.50 # Recebe metade por lei

    # 2. Verbas Rescisórias
    res_saldo = (remun_atual / 30) * dias_finais
    res_13 = aplicar_piso((max(remun_atual, remun_media) / 12) * meses_prop, PISO_VERBA)
    res_ferias = aplicar_piso(((remun_media / 12) * meses_prop) * 1.3333, PISO_VERBA)
    
    # 3. Multa FGTS
    multa_fgts = 0
    if motivo == "Sem Justa Causa":
        multa_fgts = saldo_fgts * 0.40
    elif motivo == "Acordo Comum":
        multa_fgts = saldo_fgts * 0.20

    # 4. Totalização e Impostos (Simplificado 2026)
    base_inss = res_saldo + res_13
    inss = base_inss * 0.09 # Estimativa progressiva
    
    total_bruto = res_saldo + res_13 + res_ferias + valor_aviso + multa_fgts
    total_liquido = total_bruto - inss

    # --- INTERFACE DE RESULTADOS ---
    st.subheader("📊 Demonstrativo Analítico")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Aviso Prévio", f"{dias_aviso} dias", f"R$ {valor_aviso:,.2f}")
    m2.metric("Multa FGTS", f"R$ {multa_fgts:,.2f}")
    m3.metric("Total Bruto", f"R$ {total_bruto:,.2f}")
    m4.metric("LÍQUIDO FINAL", f"R$ {total_liquido:,.2f}", delta_color="normal")

    st.markdown("### 🗂️ Memória de Cálculo (Rubricas)")
    tabela = {
        "Cód": ["100", "110", "120", "130", "140"],
        "Descrição": ["Saldo de Salário", f"Aviso Prévio ({dias_aviso} dias)", "13º Salário Prop.", "Férias Prop. + 1/3", "Multa Rescisória FGTS"],
        "Valor Bruto": [f"R$ {res_saldo:,.2f}", f"R$ {valor_aviso:,.2f}", f"R$ {res_13:,.2f}", f"R$ {res_ferias:,.2f}", f"R$ {multa_fgts:,.2f}"]
    }
    st.table(tabela)

    # --- DOWNLOAD ---
    if st.button("🖨️ Gerar PDF para Assinatura"):
        dados_doc = {
            "Funcionario": nome,
            "CPF": cpf,
            "Tempo de Casa": f"{anos_servico} anos",
            "Dias de Aviso": f"{dias_aviso} dias",
            "Total Liquido": f"R$ {total_liquido:,.2f}"
        }
        pdf_b = gerar_pdf(dados_doc)
        st.download_button("📥 Baixar PDF", pdf_b, f"rescisao_{nome}.pdf", "application/pdf")

if __name__ == "__main__":
    main()
