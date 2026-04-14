import streamlit as st
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO DO AMBIENTE ---
st.set_page_config(page_title="ERP Rescisão 2026", page_icon="🏢", layout="wide")

def aplicar_piso(valor, piso):
    """Garante que verbas proporcionais não fiquem abaixo de 50% do SM (R$ 815,00)."""
    return max(valor, piso)

def calcular_aviso_proporcional(data_adm, data_dem):
    """Calcula anos de serviço e dias de aviso (Lei 12.506/2011)."""
    anos = (data_dem - data_adm).days // 365
    # 30 dias base + 3 dias por ano completo (limitado a 90 dias / 20 anos)
    dias_totais = 30 + (min(anos, 20) * 3)
    return dias_totais, anos

def gerar_pdf(dados):
    """Gera o documento oficial para assinatura."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "DEMONSTRATIVO DE QUITACAO TRABALHISTA - 2026", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    for chave, valor in dados.items():
        pdf.cell(80, 8, f"{chave}:", border=1)
        pdf.cell(110, 8, f"{str(valor)}", border=1, ln=True)
    return pdf.output(dest="S").encode("latin-1")

def main():
    st.title("🏢 Gestão de Rescisões Corporativas")
    st.info("Regras 2026: Piso de R$ 815,00 por verba | Isenção IRRF até R$ 5.000,00 | Aviso Proporcional até 90 dias.")

    # --- INPUT DE DADOS: COLABORADOR ---
    with st.container():
        st.subheader("📋 Identificação e Vigência")
        c1, c2, c3 = st.columns(3)
        nome_func = c1.text_input("Nome do Colaborador")
        cpf_func = c1.text_input("CPF")
        
        data_adm = c2.date_input("Data de Admissão", value=datetime(2020, 1, 1))
        data_dem = c2.date_input("Data de Demissão")
        
        motivo = c3.selectbox("Motivo do Desligamento", 
                             ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])

    # --- INPUT DE DADOS: FINANCEIRO (SIDEBAR) ---
    st.sidebar.header("💰 Composição Salarial")
    salario_fixo = st.sidebar.number_input("Salário Base Atual (R$)", min_value=1630.0, value=3000.0)
    
    st.sidebar.subheader("Médias de Variáveis")
    media_comissoes = st.sidebar.number_input("Média Comissões (12 meses)", min_value=0.0, value=0.0)
    media_horas_extras = st.sidebar.number_input("Média Horas Extras (12 meses)", min_value=0.0, value=0.0)
    adicionais = st.sidebar.number_input("Adicionais (Insalubridade/Peric.)", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    saldo_fgts = st.sidebar.number_input("Saldo p/ Fins Rescisórios FGTS", min_value=0.0, value=5000.0)

    # --- PROCESSAMENTO DOS CÁLCULOS ---
    SALARIO_MIN_2026 = 1630.00
    PISO_VERBA = SALARIO_MIN_2026 / 2 # R$ 815,00

    # 1. Base de Cálculo (Remuneração Integral)
    remun_total = salario_fixo + media_comissoes + media_horas_extras + adicionais
    
    # 2. Tempo de Casa e Aviso Prévio (Lei 12.506)
    dias_aviso, anos_casa = calcular_aviso_proporcional(data_adm, data_dem)
    
    # 3. Meses Proporcionais (Regra 15 dias = 1 mês)
    # Cálculo simplificado baseado no mês da demissão
    meses_prop = data_dem.month if data_dem.day >= 15 else data_dem.month - 1
    
    # 4. Verbas Rescisórias
    res_saldo = (remun_total / 30) * data_dem.day
    res_13 = aplicar_piso((remun_total / 12) * meses_prop, PISO_VERBA)
    res_ferias = aplicar_piso(((remun_total / 12) * meses_prop) * 1.3333, PISO_VERBA)
    
    # 5. Aviso Prévio Indenizado e Multa FGTS
    valor_aviso = 0
    multa_fgts = 0
    if motivo == "Sem Justa Causa":
        valor_aviso = (remun_total / 30) * dias_aviso
        multa_fgts = saldo_fgts * 0.40
    elif motivo == "Acordo Comum":
        valor_aviso = ((remun_total / 30) * dias_aviso) * 0.50
        multa_fgts = saldo_fgts * 0.20
    else: # Pedido de Demissão
        valor_aviso = 0
        multa_fgts = 0

    # 6. Dedução (INSS Progressivo 2026)
    base_inss = res_saldo + res_13
    inss = (base_inss * 0.09) - 24.45 if base_inss > 1630 else base_inss * 0.075

    total_bruto = res_saldo + res_13 + res_ferias + valor_aviso + multa_fgts
    total_liquido = total_bruto - inss

    # --- EXIBIÇÃO DASHBOARD ---
    st.divider()
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Anos de Casa", f"{anos_casa} anos")
    col_m2.metric("Aviso Prévio", f"{dias_aviso} dias")
    col_m3.metric("Total Bruto", f"R$ {total_bruto:,.2f}")
    col_m4.metric("LÍQUIDO", f"R$ {total_liquido:,.2f}", delta="A pagar")

    # Tabela Detalhada
    st.markdown("### 🗂️ Memória de Cálculo Individualizada")
    detalhamento = {
        "Rubrica": [
            "Salário Base Atual", 
            "Comissões (Média 12m)", 
            "Horas Extras (Média 12m)", 
            "Saldo de Salário (Dias)", 
            "13º Salário Proporcional", 
            "Férias Proporcionais + 1/3", 
            "Aviso Prévio Indenizado", 
            "Multa Rescisória FGTS"
        ],
        "Valor (R$)": [
            f"{salario_fixo:,.2f}", 
            f"{media_comissoes:,.2f}", 
            f"{media_horas_extras:,.2f}",
            f"{res_saldo:,.2f}", 
            f"{res_13:,.2f}", 
            f"{res_ferias:,.2f}", 
            f"{valor_aviso:,.2f}", 
            f"{multa_fgts:,.2f}"
        ]
    }
    st.table(detalhamento)

    # --- EXPORTAÇÃO ---
    if st.button("🖨️ Gerar PDF para Assinatura"):
        if not nome_func:
            st.warning("Por favor, informe o nome do colaborador antes de gerar o PDF.")
        else:
            dados_pdf = {
                "Colaborador": nome_func,
                "CPF": cpf_func,
                "Admissao": data_adm.strftime('%d/%m/%Y'),
                "Demissao": data_dem.strftime('%d/%m/%Y'),
                "Motivo": motivo,
                "Tempo de Casa": f"{anos_casa} anos",
                "Dias de Aviso": f"{dias_aviso} dias",
                "Remuneracao Base": f"R$ {remun_total:,.2f}",
                "Total Bruto": f"R$ {total_bruto:,.2f}",
                "Desconto INSS": f"R$ {inss:,.2f}",
                "VALOR LIQUIDO": f"R$ {total_liquido:,.2f}"
            }
            pdf_bytes = gerar_pdf(dados_pdf)
            st.download_button("📥 Baixar Recibo PDF", pdf_bytes, f"Rescisao_{nome_func.replace(' ', '_')}.pdf", "application/pdf")

if __name__ == "__main__":
    main()
