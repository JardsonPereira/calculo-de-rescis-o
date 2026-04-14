import streamlit as st
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gestão de Rescisão CLT 2026", layout="wide", page_icon="⚖️")

def calcular_avos(data_inicio, data_fim_projetada):
    """Regra CLT: 15 dias ou mais no mês = 1 mês inteiro (1 avo)."""
    meses = data_fim_projetada.month
    if data_fim_projetada.day < 15:
        meses -= 1
    return max(0, meses)

def detalhar_aviso_lei_12506(data_adm, data_dem, base_calculo):
    """Calcula os dias base e proporcionais separadamente."""
    anos_completos = (data_dem - data_adm).days // 365
    anos_limitados = min(anos_completos, 20)
    dias_prop = anos_limitados * 3
    
    valor_dia = base_calculo / 30
    val_base = valor_dia * 30
    val_prop = valor_dia * dias_prop
    
    return 30, dias_prop, val_base, val_prop, anos_completos

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
        aviso_tipo = c2.radio("Situação do Aviso Prévio", ["Indenizado", "Trabalhado", "Não Cumprido (Descontar)"])

    # --- SEÇÃO 2: FINANCEIRO (SIDEBAR) ---
    st.sidebar.header("💰 Proventos e Médias")
    sal_base = st.sidebar.number_input("Último Salário Base (R$)", min_value=0.0, value=0.0)
    media_var = st.sidebar.number_input("Média Comissões/HE (12m)", min_value=0.0, value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo Total FGTS", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    st.sidebar.header("🛑 Descontos")
    dias_faltas = st.sidebar.number_input("Faltas não justificadas (Dias)", min_value=0, value=0)
    consignado = st.sidebar.number_input("Empréstimo Consignado", min_value=0.0, value=0.0)

    # --- LÓGICA DE CÁLCULO ---
    remuneracao_total = sal_base + media_var
    d_base, d_prop, v_base, v_prop, anos = detalhar_aviso_lei_12506(data_adm, data_dem, remuneracao_total)
    
    # Projeção do Contrato
    data_projetada = data_dem
    if aviso_tipo == "Indenizado" and motivo != "Pedido de Demissão":
        data_projetada = data_dem + timedelta(days=(d_base + d_prop))

    # CRÉDITOS
    res_saldo = (sal_base / 30) * data_dem.day
    
    inicio_13 = date(data_dem.year, 1, 1) if data_adm.year < data_dem.year else data_adm
    avos_13 = calcular_avos(inicio_13, data_projetada)
    res_13 = (remuneracao_total / 12) * avos_13

    meses_ferias = ((data_projetada.year - data_adm.year) * 12 + data_projetada.month - data_adm.month) % 12
    if data_projetada.day >= 15: meses_ferias += 1
    res_ferias_prop = ((remuneracao_total / 12) * meses_ferias) * 1.3333

    # Ajuste do Aviso Recebido por Motivo
    res_v_base, res_v_prop = 0.0, 0.0
    multa_fgts = 0.0
    
    if aviso_tipo == "Indenizado":
        if motivo == "Sem Justa Causa":
            res_v_base, res_v_prop = v_base, v_prop
            multa_fgts = saldo_fgts * 0.40
        elif motivo == "Acordo Comum":
            res_v_base, res_v_prop = v_base * 0.5, v_prop * 0.5
            multa_fgts = saldo_fgts * 0.20

    # DÉBITOS
    desc_inss = (res_saldo + res_13) * 0.09
    desc_faltas = (sal_base / 30) * dias_faltas
    desc_aviso = sal_base if aviso_tipo == "Não Cumprido (Descontar)" else 0.0

    total_proventos = res_saldo + res_13 + res_ferias_prop + res_v_base + res_v_prop + multa_fgts
    total_descontos = desc_inss + desc_faltas + desc_aviso + consignado
    total_liquido = max(0, total_proventos - total_descontos)

    # --- EXIBIÇÃO ---
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Proventos Brutos", f"R$ {total_proventos:,.2f}")
    m2.metric("Descontos Totais", f"R$ {total_descontos:,.2f}", delta_color="inverse")
    m3.metric("LÍQUIDO A RECEBER", f"R$ {total_liquido:,.2f}")

    col_e, col_d = st.columns(2)
    with col_e:
        st.write("### 🟢 Créditos (Detalhados)")
        # Tabela dinâmica que detalha o aviso se for indenizado
        creditos_lista = {
            "Rubrica": ["Saldo Salário", "13º Proporcional", "Férias Prop + 1/3"],
            "Quantidade": [f"{data_dem.day} dias", f"{avos_13}/12 avos", f"{meses_ferias}/12 avos"],
            "Valor (R$)": [f"{res_saldo:,.2f}", f"{res_13:,.2f}", f"{res_ferias_prop:,.2f}"]
        }
        
        if aviso_tipo == "Indenizado" and res_v_base > 0:
            creditos_lista["Rubrica"].extend(["Aviso Prévio (Base 30 dias)", f"Aviso Prévio (Lei 12.506 - {d_prop} dias)"])
            creditos_lista["Quantidade"].extend(["30 dias", f"{d_prop} dias"])
            creditos_lista["Valor (R$)"].extend([f"{res_v_base:,.2f}", f"{res_v_prop:,.2f}"])
            
        if multa_fgts > 0:
            creditos_lista["Rubrica"].append("Multa Rescisória FGTS")
            creditos_lista["Quantidade"].append("40% ou 20%")
            creditos_lista["Valor (R$)"].append(f"{multa_fgts:,.2f}")
            
        st.table(creditos_lista)

    with col_d:
        st.write("### 🔴 Débitos (Descontos)")
        st.table({
            "Rubrica": ["INSS", "Faltas", "Aviso Não Cumprido", "Empréstimo Consignado"],
            "Valor (R$)": [f"{desc_inss:,.2f}", f"{desc_faltas:,.2f}", f"{desc_aviso:,.2f}", f"{consignado:,.2f}"]
        })

if __name__ == "__main__":
    main()
