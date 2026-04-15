import streamlit as st
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Rescisão Profissional 2026", layout="wide", page_icon="⚖️")

def calcular_avos_clt(data_inicio, data_fim):
    """Regra CLT: 15 dias ou mais no mês = 1/12 avos."""
    if not data_inicio or not data_fim: return 0
    meses = (data_fim.year - data_inicio.year) * 12 + data_fim.month - data_inicio.month
    if data_fim.day >= 15:
        meses += 1
    return max(0, meses)

def detalhar_lei_12506(data_adm, data_dem, base):
    """Especificação técnica da Lei 12.506/2011."""
    if not data_adm or not data_dem: return 0, 0, 0, 0, []
    
    anos_completos = (data_dem - data_adm).days // 365
    anos_para_calculo = min(anos_completos, 20)
    dias_extras = anos_para_calculo * 3
    total_dias = 30 + dias_extras
    
    valor_dia = base / 30 if base > 0 else 0
    
    especificacao = [
        {"Descrição": "Aviso Prévio Base (Constitucional)", "Dias": 30, "Valor (R$)": f"{valor_dia * 30:,.2f}"}
    ]
    
    if anos_para_calculo > 0:
        especificacao.append({
            "Descrição": f"Adicional Lei 12.506 ({anos_para_calculo} anos x 3 dias)",
            "Dias": dias_extras,
            "Valor (R$)": f"{valor_dia * dias_extras:,.2f}"
        })
        
    return total_dias, anos_completos, valor_dia * 30, valor_dia * dias_extras, especificacao

def main():
    st.title("⚖️ Sistema de Gestão de Rescisões - Versão 2026")
    st.info("Preencha as datas em branco e o salário base para iniciar.")

    # --- ENTRADA DE DADOS ---
    with st.container():
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome do Colaborador")
        data_adm = c2.date_input("Data de Admissão", value=None, format="DD/MM/YYYY")
        data_dem = c3.date_input("Data de Demissão (Último dia)", value=None, format="DD/MM/YYYY")
        
        motivo = c1.selectbox("Motivo da Saída", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum", "Justa Causa"])
        aviso_status = c2.radio("Tipo de Aviso", ["Indenizado", "Trabalhado", "Não Cumprido (Descontar)"])

    # --- FINANCEIRO (SIDEBAR) ---
    st.sidebar.header("💰 Proventos e Médias")
    salario = st.sidebar.number_input("Salário Base", min_value=0.0, value=0.0, step=100.0)
    medias = st.sidebar.number_input("Médias Variáveis", min_value=0.0, value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo FGTS", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    st.sidebar.header("⚖️ Verbas Legais Extras")
    tem_ferias_vencidas = st.sidebar.checkbox("Possui Férias Vencidas?")
    aplicar_multa_477 = st.sidebar.checkbox("Aplicar Multa Art. 477 (Atraso)")
    
    st.sidebar.divider()
    st.sidebar.header("🛑 Descontos")
    faltas_dias = st.sidebar.number_input("Faltas (Dias)", min_value=0)
    consignado = st.sidebar.number_input("Empréstimo Consignado", min_value=0.0)

    if data_adm and data_dem:
        # LÓGICA DE CÁLCULO
        base_calc = salario + medias
        total_dias_aviso, anos_casa, v_base_aviso, v_extras_aviso, tabela_lei = detalhar_lei_12506(data_adm, data_dem, base_calc)
        
        # Projeção
        data_proj = data_dem
        if aviso_status == "Indenizado" and motivo == "Sem Justa Causa":
            data_proj = data_dem + timedelta(days=total_dias_aviso)

        # 1. Saldo de Salário
        res_saldo = (salario / 30) * data_dem.day

        # 2. 13º Salário
        inicio_13 = date(data_dem.year, 1, 1) if data_adm.year < data_dem.year else data_adm
        
        # 3. Férias Proporcionais
        if motivo == "Justa Causa":
            avos_13, avos_ferias = 0, 0
        else:
            avos_13 = calcular_avos_clt(inicio_13, data_proj)
            avos_ferias = calcular_avos_clt(data_adm, data_proj) % 12
            if avos_ferias == 0 and (data_proj - data_adm).days >= 15: avos_ferias = 12

        res_13 = (base_calc / 12) * avos_13
        res_ferias_prop = (base_calc / 12) * avos_ferias
        
        # --- LÓGICA DE FÉRIAS VENCIDAS ---
        res_ferias_vencidas = base_calc if tem_ferias_vencidas else 0.0
        terco_constitucional = (res_ferias_prop + res_ferias_vencidas) / 3
        
        # --- MULTA ART. 477 ---
        valor_multa_477 = salario if aplicar_multa_477 else 0.0
        
        # Aviso e Multas FGTS
        v_aviso_total = 0.0
        multa_fgts = 0.0
        if motivo == "Sem Justa Causa":
            v_aviso_total = (v_base_aviso + v_extras_aviso) if aviso_status == "Indenizado" else v_extras_aviso
            multa_fgts = saldo_fgts * 0.40
        elif motivo == "Acordo Comum":
            v_aviso_total = (v_base_aviso + v_extras_aviso) * 0.5 if aviso_status == "Indenizado" else (v_extras_aviso * 0.5)
            multa_fgts = saldo_fgts * 0.20

        # Descontos
        desc_inss = (res_saldo + res_13) * 0.09 # Simplificado para exemplo
        desc_aviso = salario if aviso_status == "Não Cumprido (Descontar)" else 0.0
        
        total_prov = res_saldo + res_13 + res_ferias_prop + res_ferias_vencidas + terco_constitucional + v_aviso_total + multa_fgts + valor_multa_477
        total_desc = desc_inss + desc_aviso + consignado + ((salario / 30) * faltas_dias)
        total_liq = max(0, total_prov - total_desc)

        # EXIBIÇÃO
        st.divider()
        st.subheader("📜 Detalhamento Legal")
        
        col_info1, col_info2 = st.columns(2)
        col_info1.write(f"**Tempo de Casa:** {anos_casa} anos")
        col_info2.write(f"**Projeção do Aviso:** {data_proj.strftime('%d/%m/%Y')}")

        # Tabelas de Memória
        col_e, col_d = st.columns(2)
        with col_e:
            st.write("### 🟢 Créditos")
            dados_creditos = {
                "Rubrica": ["Saldo Salário", f"13º Prop. ({avos_13}/12)", f"Férias Prop. ({avos_ferias}/12)", "1/3 Constitucional", "Multa FGTS"],
                "Valor": [f"{res_saldo:,.2f}", f"{res_13:,.2f}", f"{res_ferias_prop:,.2f}", f"{terco_constitucional:,.2f}", f"{multa_fgts:,.2f}"]
            }
            
            if tem_ferias_vencidas:
                dados_creditos["Rubrica"].append("Férias Vencidas")
                dados_creditos["Valor"].append(f"{res_ferias_vencidas:,.2f}")
            
            if valor_multa_477 > 0:
                dados_creditos["Rubrica"].append("Multa Art. 477 CLT")
                dados_creditos["Valor"].append(f"{valor_multa_477:,.2f}")
                
            st.table(dados_creditos)

        with col_d:
            st.write("### 🔴 Débitos")
            st.table({"Rubrica": ["INSS (S. Salário + 13º)", "Aviso Prévio Indenizado (Desc.)", "Consignado / Faltas"], 
                      "Valor": [f"{desc_inss:,.2f}", f"{desc_aviso:,.2f}", f"{consignado + ((salario/30)*faltas_dias):,.2f}"]})

        st.divider()
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Total Proventos", f"R$ {total_prov:,.2f}")
        c_m2.metric("Total Descontos", f"R$ {total_desc:,.2f}", delta_color="inverse")
        c_m3.metric("LÍQUIDO A RECEBER", f"R$ {total_liq:,.2f}")
        
    else:
        st.warning("⚠️ Insira as datas para visualizar o detalhamento da Lei 12.506/2011.")

if __name__ == "__main__":
    main()
