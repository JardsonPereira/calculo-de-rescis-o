import streamlit as st
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO DO SISTEMA ---
st.set_page_config(page_title="ERP Rescisão Profissional 2026", layout="wide", page_icon="🏢")

def aplicar_piso(valor, piso):
    """Garante o mínimo de 50% do salário mínimo (R$ 815,00) conforme solicitado."""
    return max(valor, piso)

def calcular_aviso_proporcional(data_adm, data_dem):
    """Lei 12.506/2011: 30 dias base + 3 dias por ano completo (limite 90 dias)."""
    anos = (data_dem - data_adm).days // 365
    dias_totais = 30 + (min(anos, 20) * 3)
    return dias_totais, anos

def gerar_pdf(dados, detalhes_tabela):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "DEMONSTRATIVO DE RESCISAO TRABALHISTA", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 10)
    for chave, valor in dados.items():
        pdf.cell(90, 8, f"{chave}:", border=1)
        pdf.cell(100, 8, f"{valor}", border=1, ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "MEMORIA DE CALCULO", ln=True)
    pdf.set_font("Arial", "", 10)
    
    for i in range(len(detalhes_tabela["Rubrica"])):
        pdf.cell(140, 8, detalhes_tabela["Rubrica"][i], border=1)
        pdf.cell(50, 8, detalhes_tabela["Valor (R$)"][i], border=1, ln=True)
        
    return pdf.output(dest="S").encode("latin-1")

def main():
    st.title("🏢 Sistema de Gestão de Desligamentos - Versão 2026")
    st.markdown("---")

    # --- SEÇÃO 1: DADOS DO CONTRATO ---
    with st.container():
        st.subheader("📋 Identificação e Cronologia")
        c1, c2, c3 = st.columns(3)
        with c1:
            nome_func = st.text_input("Nome do Colaborador")
            cpf_func = st.text_input("CPF")
        with c2:
            data_adm = st.date_input("Data de Admissão", value=datetime(2020, 1, 1))
            data_dem = st.date_input("Data de Demissão")
        with c3:
            motivo = st.selectbox("Motivo da Saída", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])

    st.divider()

    # --- SEÇÃO 2: HISTÓRICO SALARIAL (ÚLTIMOS 6 MESES) ---
    st.subheader("📅 Histórico Salarial Mensal")
    st.caption("Insira os valores para cálculo automático da média (base para 13º e Férias).")
    
    h1, h2, h3, h4, h5, h6 = st.columns(6)
    s1 = h1.number_input("Mês 1 (R$)", min_value=1630.0, value=3000.0)
    s2 = h2.number_input("Mês 2 (R$)", min_value=1630.0, value=3000.0)
    s3 = h3.number_input("Mês 3 (R$)", min_value=1630.0, value=3000.0)
    s4 = h4.number_input("Mês 4 (R$)", min_value=1630.0, value=3200.0)
    s5 = h5.number_input("Mês 5 (R$)", min_value=1630.0, value=3200.0)
    s6 = h6.number_input("Mês 6 / Atual (R$)", min_value=1630.0, value=3500.0)
    
    lista_salarios = [s1, s2, s3, s4, s5, s6]
    media_salarial_hist = sum(lista_salarios) / len(lista_salarios)
    salario_atual = s6

    # --- SEÇÃO 3: VARIÁVEIS E FGTS (SIDEBAR) ---
    st.sidebar.header("📊 Variáveis e Encargos")
    media_comissoes = st.sidebar.number_input("Média de Comissões (12m)", min_value=0.0, value=0.0)
    media_horas_extras = st.sidebar.number_input("Média de Horas Extras (12m)", min_value=0.0, value=0.0)
    adicionais_fixos = st.sidebar.number_input("Adicionais (Insalubridade/etc)", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    saldo_fgts_rescisorio = st.sidebar.number_input("Saldo p/ Fins Rescisórios FGTS", min_value=0.0, value=5000.0)
    st.sidebar.info("O saldo deve incluir depósitos e correções até a data da demissão.")

    # --- PROCESSAMENTO DOS CÁLCULOS 2026 ---
    SALARIO_MIN_2026 = 1630.00
    PISO_VERBA = SALARIO_MIN_2026 / 2 # R$ 815,00

    # Bases
    base_atual = salario_atual + media_comissoes + media_horas_extras + adicionais_fixos
    base_media = media_salarial_hist + media_comissoes + media_horas_extras + adicionais_fixos
    
    # Tempo e Aviso
    dias_aviso, anos_casa = calcular_aviso_proporcional(data_adm, data_dem)
    meses_prop = data_dem.month if data_dem.day >= 15 else data_dem.month - 1

    # Verbas
    res_saldo_salario = (base_atual / 30) * data_dem.day
    res_13 = aplicar_piso((base_media / 12) * meses_prop, PISO_VERBA)
    res_ferias = aplicar_piso(((base_media / 12) * meses_prop) * 1.3333, PISO_VERBA)
    
    # Aviso e Multa FGTS
    valor_aviso = 0
    multa_fgts = 0
    if motivo == "Sem Justa Causa":
        valor_aviso = (base_atual / 30) * dias_aviso
        multa_fgts = saldo_fgts_rescisorio * 0.40
    elif motivo == "Acordo Comum":
        valor_aviso = ((base_atual / 30) * dias_aviso) * 0.50
        multa_fgts = saldo_fgts_rescisorio * 0.20

    # Totais e Deduções
    base_inss = res_saldo_salario + res_13
    inss = (base_inss * 0.09) - 24.45 if base_inss > 1630 else base_inss * 0.075
    
    total_bruto = res_saldo_salario + res_13 + res_ferias + valor_aviso + multa_fgts
    total_liquido = total_bruto - inss

    # --- PAINEL DE RESULTADOS ---
    st.subheader("📑 Demonstrativo de Resultados")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Média Apurada", f"R$ {media_salarial_hist:,.2f}")
    m2.metric("Aviso Prévio", f"{dias_aviso} dias")
    m3.metric("Multa FGTS", f"R$ {multa_fgts:,.2f}")
    m4.metric("LÍQUIDO A PAGAR", f"R$ {total_liquido:,.2f}")

    detalhamento_tabela = {
        "Rubrica": [
            "Salário Atual (Base)", "Média Histórica (6 meses)", "Comissões/Horas Extras", 
            "Saldo de Salário", "13º Salário Proporcional", "Férias Proporcionais + 1/3", 
            f"Aviso Prévio ({dias_aviso} dias)", "Multa Rescisória FGTS"
        ],
        "Valor (R$)": [
            f"{salario_atual:,.2f}", f"{media_salarial_hist:,.2f}", 
            f"{(media_comissoes + media_horas_extras):,.2f}",
            f"{res_saldo_salario:,.2f}", f"{res_13:,.2f}", 
            f"{res_ferias:,.2f}", f"{valor_aviso:,.2f}", f"{multa_fgts:,.2f}"
        ]
    }
    st.table(detalhamento_tabela)

    # --- EXPORTAÇÃO PDF ---
    st.divider()
    if st.button("🖨️ Gerar Documento PDF"):
        if not nome_func:
            st.error("Por favor, preencha o nome do colaborador.")
        else:
            dados_pdf = {
                "Funcionario": nome_func,
                "CPF": cpf_func,
                "Admissao": data_adm.strftime('%d/%m/%Y'),
                "Demissao": data_dem.strftime('%d/%m/%Y'),
                "Motivo": motivo,
                "Tempo de Casa": f"{anos_casa} anos",
                "Aviso Previo": f"{dias_aviso} dias",
                "Total Liquido": f"R$ {total_liquido:,.2f}"
            }
            pdf_bytes = gerar_pdf(dados_pdf, detalhamento_tabela)
            st.download_button("📥 Baixar Termo de Rescisão", pdf_bytes, f"Rescisao_{nome_func.replace(' ', '_')}.pdf", "application/pdf")

if __name__ == "__main__":
    main()
