import streamlit as st
from fpdf import FPDF
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DO SISTEMA ---
st.set_page_config(page_title="ERP Rescisão Profissional 2026", layout="wide", page_icon="⚖️")

def calcular_avos(data_inicio, data_fim_projetada):
    """Regra CLT: 15 dias ou mais no mês = 1 mês inteiro (1 avo)."""
    meses = data_fim_projetada.month
    if data_fim_projetada.day < 15:
        meses -= 1
    return max(0, meses)

def detalhar_aviso_lei_12506(data_adm, data_dem, base_calculo):
    """Lei 12.506/2011: 30 dias base + 3 dias por ano completo."""
    anos_completos = (data_dem - data_adm).days // 365
    anos_limitados = min(anos_completos, 20)
    valor_dia = base_calculo / 30
    
    detalhes = [{"Descrição": "Dias Base (Mínimo)", "Dias": 30, "Acumulado": 30}]
    total_acumulado = 30
    for i in range(1, anos_limitados + 1):
        total_acumulado += 3
        detalhes.append({"Descrição": f"Acréscimo {i}º ano completo", "Dias": 3, "Acumulado": total_acumulado})
    
    dias_totais = 30 + (anos_limitados * 3)
    return dias_totais, anos_completos, valor_dia * dias_totais, detalhes

def main():
    st.title("⚖️ Sistema de Rescisão Trabalhista Completo - 2026")
    st.markdown("---")

    # --- SEÇÃO 1: DADOS DO CONTRATO ---
    st.subheader("📋 1. Identificação e Cronologia")
    col_id1, col_id2, col_id3 = st.columns(3)
    with col_id1:
        nome_func = st.text_input("Nome do Colaborador")
        data_adm = c1_adm = st.date_input("Data de Admissão", value=date(2021, 1, 1))
    with col_id2:
        cpf_func = st.text_input("CPF")
        data_dem = c1_dem = st.date_input("Data de Demissão (Último dia trabalhado)", value=date(2026, 4, 10))
    with col_id3:
        motivo = st.selectbox("Motivo da Saída", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])
        aviso_tipo = st.radio("Aviso Prévio", ["Indenizado", "Trabalhado", "Não Cumprido (Descontar)"])

    # --- SEÇÃO 2: FINANCEIRO E DESCONTOS (SIDEBAR) ---
    st.sidebar.header("💰 Proventos e Médias")
    salario_atual = st.sidebar.number_input("Último Salário Base (R$)", min_value=0.0, value=0.0, step=100.0)
    media_comissoes = st.sidebar.number_input("Média de Comissões (12m)", min_value=0.0, value=0.0)
    media_he = st.sidebar.number_input("Média de Horas Extras (12m)", min_value=0.0, value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo Total FGTS (p/ Multa)", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    st.sidebar.header("🛑 Descontos e Retenções")
    dias_faltas = st.sidebar.number_input("Faltas não justificadas (Dias)", min_value=0, value=0)
    consignado = st.sidebar.number_input("Empréstimo Consignado (R$)", min_value=0.0, value=0.0)
    outros_descontos = st.sidebar.number_input("Outros (VR/VT/Saúde) (R$)", min_value=0.0, value=0.0)
    tem_ferias_vencidas = st.sidebar.checkbox("Possui férias vencidas?")
    ferias_fora_prazo = st.sidebar.checkbox("Aplicar Dobra (Art. 137 CLT)")

    # --- LÓGICA DE CÁLCULO ---
    base_calculo = salario_atual + media_comissoes + media_he
    
    # 1. Aviso Prévio Lei 12.506/2011
    dias_aviso, anos_casa, v_aviso_total, lista_aviso = detalhar_aviso_lei_12506(data_adm, data_dem, base_calculo)
    
    # 2. Projeção do Contrato
    data_projetada = data_dem
    if aviso_tipo == "Indenizado" and motivo != "Pedido de Demissão":
        data_projetada = data_dem + timedelta(days=dias_aviso)

    # 3. Créditos (Proventos)
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
        res_aviso_receber = v_aviso_total * 0.50 if aviso_tipo == "Indenizado" else 0
        multa_fgts = saldo_fgts * 0.20

    # 4. Débitos (Descontos)
    desc_inss = (res_saldo + res_13) * 0.09
    desc_faltas = (salario_atual / 30) * dias_faltas
    desc_aviso_previo = salario_atual if (motivo == "Pedido de Demissão" and aviso_tipo == "Não Cumprido (Descontar)") else 0

    # Totais
    total_proventos = res_saldo + res_13 + res_ferias_prop + res_ferias_vencidas + multa_ferias_dobra + res_aviso_receber + multa_fgts
    total_descontos = desc_inss + desc_faltas + desc_aviso_previo + consignado + outros_descontos
    total_liquido = max(0, total_proventos - total_descontos)

    # --- EXIBIÇÃO ---
    st.subheader("📊 Demonstrativo de Resultados")
    c_res1, c_res2, c_res3, c_res4 = st.columns(4)
    c_res1.metric("Proventos Totais", f"R$ {total_proventos:,.2f}")
    c_res2.metric("Descontos Totais", f"R$ {total_descontos:,.2f}")
    c_res3.metric("Aviso Prévio", f"{dias_aviso} dias")
    c_res4.metric("LÍQUIDO A PAGAR", f"R$ {total_liquido:,.2f}")

    # Detalhamento da Lei 12.506/2011
    with st.expander("📜 Detalhamento de Dias (Lei 12.506/2011)", expanded=False):
        st.write(f"Cálculo para **{anos_casa} anos** completos de serviço:")
        st.table(lista_aviso)

    # Memória de Cálculo
    st.markdown("### 🗂️ Memória de Cálculo Detalhada")
    col_tab_left, col_tab_right = st.columns(2)
    
    with col_tab_left:
        st.write("**Créditos (A Receber)**")
        st.table({
            "Verba": ["Saldo de Salário", "13º Proporcional", "Férias Proporcionais", "Férias Vencidas/Dobra", "Aviso Prévio", "Multa FGTS"],
            "Qtde": [f"{data_dem.day} dias", f"{avos_13}/12 avos", f"{meses_ferias}/12 avos", "1 integral", f"{dias_aviso} dias", "40%/20%"],
            "Valor": [f"R$ {res_saldo:,.2f}", f"R$ {res_13:,.2f}", f"R$ {res_ferias_prop:,.2f}", f"R$ {(res_ferias_vencidas + multa_ferias_dobra):,.2f}", f"R$ {res_aviso_receber:,.2f}", f"R$ {multa_fgts:,.2f}"]
        })

    with col_tab_right:
        st.write("**Débitos (Descontos)**")
        st.table({
            "Verba": ["INSS (Saldo/13º)", "Faltas", "Aviso Não Cumprido", "Consignado", "Outros (VR/VT/Saúde)"],
            "Valor": [f"R$ {desc_inss:,.2f}", f"R$ {desc_faltas:,.2f}", f"R$ {desc_aviso_previo:,.2f}", f"R$ {consignado:,.2f}", f"R$ {outros_descontos:,.2f}"]
        })

if __name__ == "__main__":
    main()
