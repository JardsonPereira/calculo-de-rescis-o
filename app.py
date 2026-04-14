import streamlit as st
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DO SISTEMA ---
st.set_page_config(page_title="ERP Rescisão Profissional 2026", layout="wide", page_icon="⚖️")

def calcular_avos_13(data_adm, data_dem_projetada):
    """
    Calcula 13º Proporcional (Ano Civil: Jan a Dez).
    Regra: 15 dias ou mais no mês = 1/12.
    """
    ano_rescisao = data_dem_projetada.year
    inicio_contagem = max(data_adm, date(ano_rescisao, 1, 1))
    
    # Se a demissão for antes de começar o ano de rescisão (erro de data)
    if data_dem_projetada < inicio_contagem: return 0
    
    meses = data_dem_projetada.month
    # Se trabalhou menos de 15 dias no mês da demissão, subtrai esse mês
    if data_dem_projetada.day < 15:
        meses -= 1
        
    # Se admitido no meio do ano, subtrai os meses anteriores à admissão
    if data_adm.year == ano_rescisao:
        meses = meses - (data_adm.month - 1)
        # Se no mês da admissão trabalhou menos de 15 dias, subtrai
        if data_adm.day > 16: # Admissão dia 17 em diante não fecha 15 dias no mês
            meses -= 1
            
    return max(0, meses)

def calcular_avos_ferias(data_adm, data_dem_projetada):
    """
    Calcula Férias Proporcionais (Ciclo Aquisitivo).
    Regra: Cada 30 dias de contrato = 1/12. Fração >= 15 dias = 1/12.
    """
    diff = data_dem_projetada - data_adm
    meses_completos = diff.days // 30
    dias_restantes = diff.days % 30
    
    total_avos = meses_completos
    if dias_restantes >= 15:
        total_avos += 1
        
    return total_avos % 13 # Limita ao ciclo de 12 meses

def detalhar_aviso_lei_12506(data_adm, data_dem, base_calculo):
    anos_completos = (data_dem - data_adm).days // 365
    dias_prop = min(anos_completos, 20) * 3
    valor_dia = base_calculo / 30
    return 30, dias_prop, valor_dia * 30, valor_dia * dias_prop

def main():
    st.title("⚖️ Sistema de Rescisão Trabalhista Profissional - 2026")
    st.markdown("---")

    # --- SEÇÃO 1: DADOS DO CONTRATO ---
    with st.container():
        c1, c2, c3 = st.columns(3)
        nome_func = c1.text_input("Nome do Colaborador")
        data_adm = c2.date_input("Data de Admissão", value=date(2024, 2, 1))
        data_dem = c3.date_input("Data de Demissão (Último dia)", value=date(2026, 7, 15))
        
        motivo = c1.selectbox("Modalidade de Demissão", 
                             ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum", "Justa Causa"])
        aviso_tipo = c2.radio("Situação do Aviso Prévio", ["Indenizado", "Trabalhado", "Não Cumprido (Descontar)"])

    # --- SEÇÃO 2: FINANCEIRO (SIDEBAR) ---
    st.sidebar.header("💰 Proventos e Médias")
    sal_base = st.sidebar.number_input("Salário Base (R$)", min_value=0.0, value=3000.0)
    media_var = st.sidebar.number_input("Médias (HE, Adicionais, Comissões)", min_value=0.0, value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo Total FGTS", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    st.sidebar.header("🛑 Descontos")
    consignado = st.sidebar.number_input("Empréstimo Consignado", min_value=0.0, value=0.0)
    tem_ferias_vencidas = st.sidebar.checkbox("Possui férias vencidas?")

    # --- LÓGICA DE CÁLCULO ---
    remuneracao_total = sal_base + media_var
    d_base, d_prop, v_base, v_prop = detalhar_aviso_lei_12506(data_adm, data_dem, remuneracao_total)
    
    # Projeção do Contrato (Aviso Indenizado soma tempo para avos)
    data_projetada = data_dem
    if aviso_tipo == "Indenizado" and motivo == "Sem Justa Causa":
        data_projetada = data_dem + timedelta(days=(d_base + d_prop))

    # 1. CRÉDITOS (PROVENTOS)
    res_saldo = (sal_base / 30) * data_dem.day
    
    # Lógica de 13º e Férias baseada no Motivo (Justa Causa perde proporcionais)
    if motivo == "Justa Causa":
        avos_13, avos_ferias = 0, 0
    else:
        avos_13 = calcular_avos_13(data_adm, data_projetada)
        avos_ferias = calcular_avos_ferias(data_adm, data_projetada)

    res_13 = (remuneracao_total / 12) * avos_13
    res_ferias_prop = (remuneracao_total / 12) * avos_ferias
    res_terco_prop = res_ferias_prop / 3

    # Verbas de Aviso e FGTS
    res_v_aviso, multa_fgts = 0.0, 0.0
    if motivo == "Sem Justa Causa":
        res_v_aviso = (v_base + v_prop) if aviso_tipo == "Indenizado" else 0
        multa_fgts = saldo_fgts * 0.40
    elif motivo == "Acordo Comum":
        res_v_aviso = (v_base + v_prop) * 0.5 if aviso_tipo == "Indenizado" else 0
        multa_fgts = saldo_fgts * 0.20

    # 2. DÉBITOS (DESCONTOS)
    # Férias Indenizadas/Proporcionais não sofrem INSS
    desc_inss = (res_saldo + res_13) * 0.09 
    desc_aviso = sal_base if aviso_tipo == "Não Cumprido (Descontar)" else 0.0

    total_proventos = res_saldo + res_13 + res_ferias_prop + res_terco_prop + res_v_aviso + multa_fgts
    total_descontos = desc_inss + desc_aviso + consignado
    total_liquido = max(0, total_proventos - total_descontos)

    # --- EXIBIÇÃO ---
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Proventos Brutos", f"R$ {total_proventos:,.2f}")
    m2.metric("Descontos Totais", f"R$ {total_descontos:,.2f}", delta_color="inverse")
    m3.metric("LÍQUIDO FINAL", f"R$ {total_liquido:,.2f}")

    col_e, col_d = st.columns(2)
    with col_e:
        st.write("### 🟢 Créditos Detalhados")
        creditos_tabela = {
            "Rubrica": ["Saldo Salário", "13º Proporcional", "Férias Proporcionais", "1/3 Constitucional Férias"],
            "Quantidade": [f"{data_dem.day} dias", f"{avos_13}/12 avos", f"{avos_ferias}/12 avos", "33.3% sobre férias"],
            "Valor (R$)": [f"{res_saldo:,.2f}", f"{res_13:,.2f}", f"{res_ferias_prop:,.2f}", f"{res_terco_prop:,.2f}"]
        }
        if res_v_aviso > 0:
            creditos_tabela["Rubrica"].append("Aviso Prévio Indenizado")
            creditos_tabela["Quantidade"].append(f"{d_base + d_prop} dias")
            creditos_tabela["Valor (R$)"].append(f"{res_v_aviso:,.2f}")
        if multa_fgts > 0:
            creditos_tabela["Rubrica"].append("Multa Rescisória FGTS")
            creditos_tabela["Quantidade"].append("40% ou 20%")
            creditos_tabela["Valor (R$)"].append(f"{multa_fgts:,.2f}")
        st.table(creditos_tabela)

    with col_d:
        st.write("### 🔴 Débitos e Prazos")
        st.table({
            "Rubrica": ["INSS (Tributável)", "Aviso Não Cumprido", "Consignado"],
            "Valor (R$)": [f"{desc_inss:,.2f}", f"{desc_aviso:,.2f}", f"{consignado:,.2f}"]
        })
        prazo_pagto = data_dem + timedelta(days=10)
        st.warning(f"📅 **Prazo de Pagamento:** Até {prazo_pagto.strftime('%d/%m/%Y')} (10 dias corridos).")

if __name__ == "__main__":
    main()
