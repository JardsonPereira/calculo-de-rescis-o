import streamlit as st
from fpdf import FPDF
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Rescisão Profissional 2026", layout="wide", page_icon="⚖️")

def calcular_avos(data_inicio, data_fim_projetada):
    meses = data_fim_projetada.month
    if data_fim_projetada.day < 15:
        meses -= 1
    return max(0, meses)

def calcular_aviso_lei_12506(data_adm, data_dem):
    anos_completos = (data_dem - data_adm).days // 365
    dias_adicionais = min(anos_completos, 20) * 3
    total_dias = 30 + dias_adicionais
    return total_dias, anos_completos

def main():
    st.title("⚖️ Sistema de Rescisão Trabalhista - Padrão CLT 2026")
    st.markdown("---")

    # --- SEÇÃO 1: DADOS DO CONTRATO ---
    st.subheader("📋 1. Identificação e Datas")
    col_id1, col_id2, col_id3 = st.columns(3)
    with col_id1:
        nome_func = st.text_input("Nome do Colaborador")
        data_adm = st.date_input("Data de Admissão", value=date(2021, 1, 1))
    with col_id2:
        cpf_func = st.text_input("CPF")
        data_dem = st.date_input("Data de Demissão (Último dia trabalhado)")
    with col_id3:
        motivo = st.selectbox("Motivo da Saída", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])
        aviso_tipo = st.radio("Aviso Prévio", ["Indenizado", "Trabalhado", "Não Cumprido (Descontar)"])

    # --- SEÇÃO 2: FINANCEIRO E DESCONTOS (SIDEBAR) ---
    st.sidebar.header("💰 Proventos e Médias")
    salario_atual = st.sidebar.number_input("Último Salário Base (R$)", min_value=0.0, value=0.0, step=100.0)
    media_comissoes = st.sidebar.number_input("Média de Comissões", min_value=0.0, value=0.0)
    media_he = st.sidebar.number_input("Média de Horas Extras", min_value=0.0, value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo p/ Fins Rescisórios FGTS (R$)", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    st.sidebar.header("🛑 Descontos e Retenções")
    dias_faltas = st.sidebar.number_input("Faltas não justificadas (Dias)", min_value=0, value=0)
    consignado = st.sidebar.number_input("Empréstimo Consignado (R$)", min_value=0.0, value=0.0)
    outros_descontos = st.sidebar.number_input("Outros (VR/VT/Saúde) (R$)", min_value=0.0, value=0.0)

    # --- LÓGICA DE CÁLCULO ---
    remuneracao_integral = salario_atual + media_comissoes + media_he
    dias_aviso, anos_casa = calcular_aviso_lei_12506(data_adm, data_dem)
    
    # Projeção do Contrato
    data_projetada = data_dem
    if aviso_tipo == "Indenizado" and motivo != "Pedido de Demissão":
        data_projetada = data_dem + timedelta(days=dias_aviso)

    # Proventos
    res_saldo = (salario_atual / 30) * data_dem.day
    inicio_13 = date(data_dem.year, 1, 1) if data_adm.year < data_dem.year else data_adm
    avos_13 = calcular_avos(inicio_13, data_projetada)
    res_13 = (remuneracao_integral / 12) * avos_13
    
    meses_ferias = ((data_projetada.year - data_adm.year) * 12 + data_projetada.month - data_adm.month) % 12
    if data_projetada.day >= 15: meses_ferias += 1
    res_ferias_prop = ((remuneracao_integral / 12) * meses_ferias) * 1.3333

    # Aviso Prévio e Multas
    res_aviso_receber = 0
    multa_fgts = 0
    if motivo == "Sem Justa Causa":
        res_aviso_receber = (remuneracao_integral / 30) * dias_aviso if aviso_tipo == "Indenizado" else 0
        multa_fgts = saldo_fgts * 0.40
    elif motivo == "Acordo Comum":
        res_aviso_receber = ((remuneracao_integral / 30) * dias_aviso) * 0.50 if aviso_tipo == "Indenizado" else 0
        multa_fgts = saldo_fgts * 0.20

    # --- CÁLCULO DOS DESCONTOS ---
    desc_inss = (res_saldo + res_13) * 0.09 # Estimativa base 2026
    desc_faltas = (salario_atual / 30) * dias_faltas
    
    desc_aviso_previo = 0
    if motivo == "Pedido de Demissão" and aviso_tipo == "Não Cumprido (Descontar)":
        desc_aviso_previo = salario_atual # Desconto de 1 mês de salário (Art. 487 CLT)

    total_proventos = res_saldo + res_13 + res_ferias_prop + res_aviso_receber + multa_fgts
    total_descontos = desc_inss + desc_faltas + desc_aviso_previo + consignado + outros_descontos
    
    # Limite de Desconto (Art. 477 CLT - Não pode exceder 1 mês de salário, exceto consignado)
    # Aqui aplicamos a lógica de que o total líquido não pode ser negativo por causa de descontos comuns
    total_liquido = max(0, total_proventos - total_descontos)

    # --- EXIBIÇÃO ---
    st.subheader("📊 Demonstrativo de Resultados")
    c_res1, c_res2, c_res3, c_res4 = st.columns(4)
    c_res1.metric("Proventos Totais", f"R$ {total_proventos:,.2f}")
    c_res2.metric("Descontos Totais", f"R$ {total_descontos:,.2f}", delta_color="inverse")
    c_res3.metric("Tempo de Casa", f"{anos_casa} anos")
    c_res4.metric("LÍQUIDO A PAGAR", f"R$ {total_liquido:,.2f}")

    st.markdown("### 🗂️ Memória de Cálculo Detalhada")
    
    col_tab_left, col_tab_right = st.columns(2)
    
    with col_tab_left:
        st.write("**Créditos (A Receber)**")
        st.table({
            "Verba": ["Saldo de Salário", "13º Proporcional", "Férias + 1/3", "Aviso Prévio", "Multa FGTS"],
            "Valor": [f"R$ {res_saldo:,.2f}", f"R$ {res_13:,.2f}", f"R$ {res_ferias_prop:,.2f}", f"R$ {res_aviso_receber:,.2f}", f"R$ {multa_fgts:,.2f}"]
        })

    with col_tab_right:
        st.write("**Débitos (Descontos)**")
        st.table({
            "Verba": ["INSS (Saldo/13º)", "Faltas", "Aviso Não Cumprido", "Consignado", "Outros"],
            "Valor": [f"R$ {desc_inss:,.2f}", f"R$ {desc_faltas:,.2f}", f"R$ {desc_aviso_previo:,.2f}", f"R$ {consignado:,.2f}", f"R$ {outros_descontos:,.2f}"]
        })

if __name__ == "__main__":
    main()
