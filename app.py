import streamlit as st
from fpdf import FPDF
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DO SISTEMA ---
st.set_page_config(page_title="Gestão de Rescisão CLT 2026", layout="wide", page_icon="⚖️")

def calcular_avos(data_inicio, data_fim_projetada):
    """Regra CLT: 15 dias ou mais no mês = 1 mês inteiro (1 avo)."""
    # Para o 13º proporcional dentro do ano civil
    meses = data_fim_projetada.month
    if data_fim_projetada.day < 15:
        meses -= 1
    return max(0, meses)

def detalhar_aviso_lei_12506(data_adm, data_dem, base_calculo):
    """Lei 12.506/2011: 30 dias base + 3 dias por ano completo."""
    anos_completos = (data_dem - data_adm).days // 365
    anos_limitados = min(anos_completos, 20)
    valor_dia = base_calculo / 30
    total_dias = 30 + (anos_limitados * 3)
    return total_dias, anos_completos, valor_dia * total_dias

def main():
    st.title("⚖️ Sistema de Rescisão Trabalhista Profissional")
    st.markdown("---")

    # --- SEÇÃO 1: DADOS DO CONTRATO ---
    with st.container():
        c1, c2, c3 = st.columns(3)
        nome_func = c1.text_input("Nome do Colaborador")
        data_adm = c2.date_input("Data de Admissão", value=date(2021, 1, 1))
        data_dem = c3.date_input("Data de Demissão (Último dia)", value=date(2026, 4, 10))
        
        motivo = c1.selectbox("Motivo da Saída", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])
        # Campo crítico: Se marcado como 'Não Cumprido', deve gerar desconto
        aviso_tipo = c2.radio("Situação do Aviso Prévio", ["Indenizado", "Trabalhado", "Não Cumprido (Descontar)"])

    # --- SEÇÃO 2: FINANCEIRO E DESCONTOS (SIDEBAR) ---
    st.sidebar.header("💰 Proventos e Médias")
    salario_atual = st.sidebar.number_input("Último Salário Base (R$)", min_value=0.0, value=0.0)
    media_variaveis = st.sidebar.number_input("Média Comissões/HE (12m)", min_value=0.0, value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo Total FGTS", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    st.sidebar.header("🛑 Descontos e Férias")
    dias_faltas = st.sidebar.number_input("Faltas não justificadas (Dias)", min_value=0, value=0)
    consignado = st.sidebar.number_input("Empréstimo Consignado", min_value=0.0, value=0.0)
    
    tem_ferias_vencidas = st.sidebar.checkbox("Possui férias vencidas?")
    ferias_fora_prazo = st.sidebar.checkbox("Aplicar Dobra (Art. 137 CLT)")

    # --- LÓGICA DE CÁLCULO ---
    base_calculo = salario_atual + media_variaveis
    dias_aviso, anos_casa, v_aviso_total = detalhar_aviso_lei_12506(data_adm, data_dem, base_calculo)
    
    # Projeção do Contrato (Aviso Indenizado soma tempo para 13º e Férias)
    data_projetada = data_dem
    if aviso_tipo == "Indenizado" and motivo != "Pedido de Demissão":
        data_projetada = data_dem + timedelta(days=dias_aviso)

    # 1. CRÉDITOS
    res_saldo = (salario_atual / 30) * data_dem.day
    
    inicio_13 = date(data_dem.year, 1, 1) if data_adm.year < data_dem.year else data_adm
    avos_13 = calcular_avos(inicio_13, data_projetada)
    res_13 = (base_calculo / 12) * avos_13

    meses_ferias = ((data_projetada.year - data_adm.year) * 12 + data_projetada.month - data_adm.month) % 12
    if data_projetada.day >= 15: meses_ferias += 1
    res_ferias_prop = ((base_calculo / 12) * meses_ferias) * 1.3333
    
    res_ferias_vencidas = (base_calculo * 1.3333) if tem_ferias_vencidas else 0
    multa_ferias_dobra = res_ferias_vencidas if (tem_ferias_vencidas and ferias_fora_prazo) else 0

    res_aviso_receber = 0
    multa_fgts = 0
    if motivo == "Sem Justa Causa":
        res_aviso_receber = v_aviso_total if aviso_tipo == "Indenizado" else 0
        multa_fgts = saldo_fgts * 0.40
    elif motivo == "Acordo Comum":
        res_aviso_receber = (v_aviso_total * 0.50) if aviso_tipo == "Indenizado" else 0
        multa_fgts = saldo_fgts * 0.20

    # 2. DÉBITOS (DESCONTOS)
    desc_inss = (res_saldo + res_13) * 0.09
    desc_faltas = (salario_atual / 30) * dias_faltas
    
    # CORREÇÃO: Lógica de desconto de aviso prévio
    desc_aviso_previo = 0
    if aviso_tipo == "Não Cumprido (Descontar)":
        desc_aviso_previo = salario_atual  # Desconto de 1 salário (valor fixo)

    # Totais
    total_proventos = res_saldo + res_13 + res_ferias_prop + res_ferias_vencidas + multa_ferias_dobra + res_aviso_receber + multa_fgts
    total_descontos = desc_inss + desc_faltas + desc_aviso_previo + consignado
    total_liquido = max(0, total_proventos - total_descontos)

    # --- EXIBIÇÃO ---
    st.divider()
    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("Total Proventos", f"R$ {total_proventos:,.2f}")
    c_m2.metric("Total Descontos", f"R$ {total_descontos:,.2f}", delta=f"Desconto Aviso: R$ {desc_aviso_previo:,.2f}" if desc_aviso_previo > 0 else None, delta_color="inverse")
    c_m3.metric("LÍQUIDO FINAL", f"R$ {total_liquido:,.2f}")

    col_esq, col_dir = st.columns(2)
    with col_esq:
        st.write("**Créditos (Proventos)**")
        st.table({
            "Descrição": ["Saldo Salário", "13º Proporcional", "Férias Proporcionais", "Aviso Prévio (Indenizado)", "Multa FGTS"],
            "Valor": [f"R$ {res_saldo:,.2f}", f"R$ {res_13:,.2f}", f"R$ {res_ferias_prop:,.2f}", f"R$ {res_aviso_receber:,.2f}", f"R$ {multa_fgts:,.2f}"]
        })

    with col_dir:
        st.write("**Débitos (Descontos)**")
        st.table({
            "Descrição": ["INSS", "Faltas", "Aviso Não Cumprido", "Empréstimo Consignado"],
            "Valor": [f"R$ {desc_inss:,.2f}", f"R$ {desc_faltas:,.2f}", f"R$ {desc_aviso_previo:,.2f}", f"R$ {consignado:,.2f}"]
        })

if __name__ == "__main__":
    main()
