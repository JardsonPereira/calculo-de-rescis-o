import streamlit as st
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DO SISTEMA ---
st.set_page_config(page_title="ERP Rescisão Profissional 2026", layout="wide", page_icon="⚖️")

def calcular_avos_clt(data_inicio, data_fim):
    """Regra CLT: 15 dias ou mais no mês = 1/12 avos."""
    if not data_inicio or not data_fim: return 0
    meses = (data_fim.year - data_inicio.year) * 12 + data_fim.month - data_inicio.month
    if data_fim.day >= 15:
        meses += 1
    return max(0, meses)

def detalhar_aviso(data_adm, data_dem, base):
    """Lei 12.506/2011: 30 dias + 3 dias por ano completo."""
    if not data_adm or not data_dem: return 0, 0, 0, 0
    anos = (data_dem - data_adm).days // 365
    dias_extras = min(anos, 20) * 3
    total_dias = 30 + dias_extras
    valor_dia = base / 30 if base > 0 else 0
    return total_dias, dias_extras, valor_dia * 30, valor_dia * dias_extras

def main():
    st.title("⚖️ Sistema de Gestão de Rescisões - Versão 2026")
    st.info("Preencha as datas e o salário base para iniciar os cálculos.")

    # --- ENTRADA DE DADOS ---
    with st.container():
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome do Colaborador")
        
        # DATAS INICIANDO EM BRANCO (None)
        data_adm = c2.date_input("Data de Admissão", value=None, format="DD/MM/YYYY")
        data_dem = c3.date_input("Data de Demissão (Último dia)", value=None, format="DD/MM/YYYY")
        
        motivo = c1.selectbox("Motivo da Saída", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])
        aviso_status = c2.radio("Tipo de Aviso", ["Indenizado", "Trabalhado", "Não Cumprido (Descontar)"])

    # --- FINANCEIRO (SIDEBAR) ---
    st.sidebar.header("💰 Proventos e Médias")
    salario = st.sidebar.number_input("Salário Base", min_value=0.0, value=0.0, step=100.0)
    medias = st.sidebar.number_input("Médias Variáveis (HE/Comissões)", min_value=0.0, value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo Total FGTS", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    st.sidebar.header("🛑 Descontos Possíveis")
    faltas_dias = st.sidebar.number_input("Faltas (Dias)", min_value=0)
    adiantamento = st.sidebar.number_input("Adiantamento Salarial", min_value=0.0)
    consignado = st.sidebar.number_input("Empréstimo Consignado", min_value=0.0)
    
    tem_ferias_vencidas = st.sidebar.checkbox("Possui férias vencidas?")
    ferias_fora_prazo = st.sidebar.checkbox("Aplicar Dobra (Art. 137 CLT)")

    # --- BLOQUEIO DE CÁLCULO SE DATAS ESTIVEREM VAZIAS ---
    if data_adm and data_dem:
        if data_dem < data_adm:
            st.error("A data de demissão não pode ser anterior à data de admissão.")
            return

        # LÓGICA DE CÁLCULO
        base_calc = salario + medias
        d_totais, d_exced, v_base_aviso, v_exced_aviso = detalhar_aviso(data_adm, data_dem, base_calc)
        
        data_proj = data_dem
        if aviso_status == "Indenizado" and motivo == "Sem Justa Causa":
            data_proj = data_dem + timedelta(days=d_totais)

        # CRÉDITOS
        res_saldo = (salario / 30) * data_dem.day
        inicio_13 = date(data_dem.year, 1, 1) if data_adm.year < data_dem.year else data_adm
        avos_13 = calcular_avos_clt(inicio_13, data_proj)
        res_13 = (base_calc / 12) * avos_13
        
        avos_ferias = calcular_avos_clt(data_adm, data_proj) % 12
        if avos_ferias == 0 and (data_proj - data_adm).days >= 15: avos_ferias = 12
        res_ferias = (base_calc / 12) * avos_ferias
        res_terco = res_ferias / 3
        
        res_ferias_venc = (base_calc * 1.3333) if tem_ferias_vencidas else 0
        multa_dobra = res_ferias_venc if (tem_ferias_vencidas and ferias_fora_prazo) else 0

        v_aviso_receber, multa_fgts = 0.0, 0.0
        if motivo == "Sem Justa Causa":
            multa_fgts = saldo_fgts * 0.40
            v_aviso_receber = (v_base_aviso + v_exced_aviso) if aviso_status == "Indenizado" else v_exced_aviso
        elif motivo == "Acordo Comum":
            multa_fgts = saldo_fgts * 0.20
            v_aviso_receber = ((v_base_aviso + v_exced_aviso) * 0.5) if aviso_status == "Indenizado" else (v_exced_aviso * 0.5)

        # DÉBITOS
        desc_inss = (res_saldo + res_13) * 0.09
        desc_faltas = (salario / 30) * faltas_dias
        desc_aviso_nao_cump = salario if aviso_status == "Não Cumprido (Descontar)" else 0.0
        
        total_prov = res_saldo + res_13 + res_ferias + res_terco + res_ferias_venc + multa_dobra + v_aviso_receber + multa_fgts
        total_desc = desc_inss + desc_faltas + desc_aviso_nao_cump + adiantamento + consignado
        total_liq = max(0, total_prov - total_desc)

        # EXIBIÇÃO
        st.divider()
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Total Proventos", f"R$ {total_prov:,.2f}")
        c_m2.metric("Total Descontos", f"R$ {total_desc:,.2f}", delta_color="inverse")
        c_m3.metric("LÍQUIDO FINAL", f"R$ {total_liq:,.2f}")

        col_e, col_d = st.columns(2)
        with col_e:
            st.write("### 🟢 Créditos")
            st.table({
                "Rubrica": ["Saldo Salário", "13º Prop.", "Férias Prop.", "1/3 Férias", "Aviso Prévio", "Multa FGTS"],
                "Valor (R$)": [f"{res_saldo:,.2f}", f"{res_13:,.2f}", f"{res_ferias:,.2f}", f"{res_terco:,.2f}", f"{v_aviso_receber:,.2f}", f"{multa_fgts:,.2f}"]
            })
        with col_d:
            st.write("### 🔴 Débitos")
            st.table({
                "Rubrica": ["INSS", "Faltas", "Aviso Desc.", "Consignado"],
                "Valor (R$)": [f"{desc_inss:,.2f}", f"{desc_faltas:,.2f}", f"{desc_aviso_nao_cump:,.2f}", f"{consignado:,.2f}"]
            })
    else:
        st.warning("⚠️ Aguardando preenchimento das datas de admissão e demissão para processar.")

if __name__ == "__main__":
    main()
