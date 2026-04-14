import streamlit as st
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO DO SISTEMA ---
st.set_page_config(page_title="Gestão de Rescisões 2026", layout="wide")

def aplicar_piso(valor, piso):
    """Garante o mínimo de 50% do salário mínimo para verbas proporcionais."""
    return max(valor, piso)

def calcular_aviso_proporcional(data_adm, data_dem):
    """Lei 12.506/2011: 30 dias + 3 dias por cada ano completo (máximo 90 dias)."""
    anos = (data_dem - data_adm).days // 365
    dias_totais = 30 + (anos * 3)
    return min(dias_totais, 90), anos

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "TERMO DE RESCISAO DO CONTRATO DE TRABALHO", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    for chave, valor in dados.items():
        pdf.cell(90, 8, f"{chave}:", border=1)
        pdf.cell(100, 8, f"{valor}", border=1, ln=True)
    return pdf.output(dest="S").encode("latin-1")

def main():
    st.title("🏢 Sistema Corporativo de Rescisão - 2026")
    st.markdown("---")

    # --- SEÇÃO 1: DADOS DO CONTRATO ---
    st.subheader("📋 Dados do Colaborador e Vigência")
    c1, c2, c3 = st.columns(3)
    with c1:
        nome_func = st.text_input("Nome Completo")
        cpf_func = st.text_input("CPF")
    with c2:
        data_adm = st.date_input("Data de Admissão", value=datetime(2020, 1, 1))
        data_dem = st.date_input("Data de Demissão")
    with c3:
        motivo = st.selectbox("Motivo da Saída", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])

    # --- SEÇÃO 2: FINANCEIRO (SIDEBAR) ---
    st.sidebar.header("💰 Remuneração e Médias")
    salario_fixo = st.sidebar.number_input("Salário Base Atual", min_value=1630.0, value=3000.0)
    
    st.sidebar.subheader("Médias Variáveis (12 meses)")
    media_comissoes = st.sidebar.number_input("Média de Comissões", min_value=0.0, value=0.0)
    media_horas_extras = st.sidebar.number_input("Média de Horas Extras", min_value=0.0, value=0.0)
    adicionais = st.sidebar.number_input("Adicionais (Insalubridade/Peric.)", min_value=0.0, value=0.0)
    
    saldo_fgts = st.sidebar.number_input("Saldo Fins Rescisórios FGTS", min_value=0.0, value=5000.0)

    # --- LÓGICA DE CÁLCULO ---
    SALARIO_MINIMO_2026 = 1630.00
    PISO_VERBA = SALARIO_MINIMO_2026 / 2 # R$ 815,00

    # 1. Base de Cálculo (Remuneração Integral)
    remun_total = salario_fixo + media_comissoes + media_horas_extras + adicionais
    
    # 2. Tempo de Casa e Aviso Prévio
    dias_aviso, anos_completos = calcular_aviso_proporcional(data_adm, data_dem)
    
    # 3. Verbas Proporcionais
    meses_ano = data_dem.month if data_dem.day >= 15 else data_dem.month - 1
    
    res_saldo = (remun_total / 30) * data_dem.day
    res_13 = aplicar_piso((remun_total / 12) * meses_ano, PISO_VERBA)
    # Férias (considerando um ciclo simples para fins de exemplo)
    res_ferias = aplicar_piso(((remun_total / 12) * meses_ano) * 1.3333, PISO_VERBA)
    
    # 4. Aviso Prévio e FGTS por Motivo
    valor_aviso = 0
    multa_fgts = 0
    if motivo == "Sem Justa Causa":
        valor_aviso = (remun_total / 30) * dias_aviso
        multa_fgts = saldo_fgts * 0.40
    elif motivo == "Acordo Comum":
        valor_aviso = ((remun_total / 30) * dias_aviso) * 0.50
        multa_fgts = saldo_fgts * 0.20

    # 5. Totais
    total_bruto = res_saldo + res_13 + res_ferias + valor_aviso + multa_fgts
    inss = (res_saldo + res_13) * 0.09 # Estimativa INSS 2026
    total_liquido = total_bruto - inss

    # --- EXIBIÇÃO ---
    st.subheader("📊 Demonstrativo de Resultados")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Aviso Prévio", f"{dias_aviso} dias")
    m2.metric("Tempo de Casa", f"{anos_completos} anos")
    m3.metric("Total Bruto", f"R$ {total_bruto:,.2f}")
    m4.metric("LÍQUIDO", f"R$ {total_liquido:,.2f}")

    st.markdown("### 🗂️ Memória de Cálculo Individualizada")
    detalhamento = {
        "Rubrica": ["Salário Base", "Comissões (Média)", "Horas Extras (Média)", "Saldo de Salário", "13º Salário", "Férias + 1/3", "Aviso Prévio", "Multa FGTS"],
        "Valor (R$)": [
            f"{salario_fixo:,.2f}", f"{media_comissoes:,.2f}", f"{media_horas_extras:,.2f}",
            f"{res_saldo:,.2f}", f"{res_13:,.2f}", f"{res_ferias:,.2f}", f"{valor_aviso:,.2f}", f"{multa_fgts:,.2f}"
        ]
    }
    st.table(detalhamento)

    # --- PDF ---
    if st.button("🖨️ Gerar Documento de Quitação"):
        dados_pdf = {
            "Funcionario": nome_func,
            "CPF": cpf_func,
            "Admissao": data_adm.strftime('%d/%m/%Y'),
            "Demissao": data_dem.strftime('%d/%m/%Y'),
            "Anos de Casa": anos_completos,
            "Dias de Aviso": dias_aviso,
            "Total Liquido": f"R$ {total_liquido:,.2f}"
        }
        pdf_bytes = gerar_pdf(dados_pdf)
        st.download_button("📥 Baixar Recibo PDF", pdf_bytes, f"Rescisao_{nome_func}.pdf", "application/pdf")

if __name__ == "__main__":
    main()
