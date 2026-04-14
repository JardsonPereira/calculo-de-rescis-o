import streamlit as st
from fpdf import FPDF
from datetime import datetime, date

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Rescisão Profissional 2026", layout="wide", page_icon="⚖️")

def aplicar_piso(valor, piso):
    """Garante o mínimo de 50% do salário mínimo (R$ 815,00)."""
    return max(valor, piso)

def detalhar_aviso_lei_12506(data_adm, data_dem, base_calculo):
    """
    Calcula o aviso prévio proporcional detalhado ano a ano.
    Lei 12.506/2011: 30 dias base + 3 dias por ano completo.
    """
    anos_completos = (data_dem - data_adm).days // 365
    anos_limitados = min(anos_completos, 20) # Limite de 20 anos para somar 60 dias (total 90)
    
    valor_dia = base_calculo / 30
    
    detalhamento = []
    # 30 dias base sempre existem
    detalhamento.append({"Ano": "Base (30 dias)", "Dias": 30, "Valor": round(valor_dia * 30, 2)})
    
    for i in range(1, anos_limitados + 1):
        detalhamento.append({
            "Ano": f"{i}º Ano Completo",
            "Dias": 3,
            "Valor": round(valor_dia * 3, 2)
        })
    
    dias_totais = 30 + (anos_limitados * 3)
    valor_total_aviso = valor_dia * dias_totais
    
    return dias_totais, anos_completos, valor_total_aviso, detalhamento

def main():
    st.title("⚖️ Sistema de Rescisão e Cálculos Trabalhistas - 2026")
    st.markdown("---")

    # --- SEÇÃO 1: DADOS DO CONTRATO ---
    st.subheader("📋 1. Identificação e Cronologia")
    c1, c2, c3 = st.columns(3)
    nome = c1.text_input("Nome do Colaborador")
    cpf = c1.text_input("CPF")
    
    data_adm = c2.date_input("Data de Admissão", value=date(2018, 1, 1))
    data_dem = c2.date_input("Data de Demissão", value=date(2026, 4, 10))
    
    motivo = c3.selectbox("Motivo do Desligamento", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])
    aviso_tipo = c3.radio("Aviso Prévio", ["Indenizado", "Trabalhado"])

    # --- SEÇÃO 2: FINANCEIRO (SIDEBAR) ---
    st.sidebar.header("💰 Remuneração e Histórico")
    
    ultimo_salario_bruto = st.sidebar.number_input("Último Salário Bruto Atual", min_value=0.0, value=0.0, step=100.0)
    media_variaveis = st.sidebar.number_input("Média de Comissões/HE (12 meses)", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    st.sidebar.subheader("🏦 Fundo de Garantia")
    saldo_fgts_total = st.sidebar.number_input("Saldo Total Depositado (FGTS)", min_value=0.0, value=0.0, step=100.0)
    tem_ferias_vencidas = st.sidebar.checkbox("Possui Férias Vencidas?")

    # --- LOGICA DE CÁLCULO ---
    SALARIO_MIN_2026 = 1630.00
    PISO_VERBA = SALARIO_MIN_2026 / 2 # R$ 815,00

    base_calculo = ultimo_salario_bruto + media_variaveis
    
    # Aviso Prévio Proporcional Detalhado
    dias_aviso, anos_casa, valor_aviso_total, lista_aviso = detalhar_aviso_lei_12506(data_adm, data_dem, base_calculo)
    
    meses_13 = data_dem.month if data_dem.day >= 15 else data_dem.month - 1
    meses_ferias_prop = data_dem.month - 1 if data_dem.day < 15 else data_dem.month

    # Cálculos das Verbas
    res_saldo_salario = (ultimo_salario_bruto / 30) * data_dem.day

    # Ajuste do Aviso pelo Motivo
    res_aviso = 0
    if aviso_tipo == "Indenizado":
        if motivo == "Sem Justa Causa":
            res_aviso = valor_aviso_total
        elif motivo == "Acordo Comum":
            res_aviso = valor_aviso_total * 0.5

    res_13 = aplicar_piso((base_calculo / 12) * meses_13, PISO_VERBA) if base_calculo > 0 else 0
    res_ferias_vencidas = (base_calculo * 1.3333) if tem_ferias_vencidas else 0
    res_ferias_prop = aplicar_piso(((base_calculo / 12) * meses_ferias_prop) * 1.3333, PISO_VERBA) if base_calculo > 0 else 0

    multa_fgts = 0
    if motivo == "Sem Justa Causa":
        multa_fgts = saldo_fgts_total * 0.40
    elif motivo == "Acordo Comum":
        multa_fgts = saldo_fgts_total * 0.20

    # Totais
    total_bruto = res_saldo_salario + res_aviso + res_13 + res_ferias_vencidas + res_ferias_prop + multa_fgts
    inss = (res_saldo_salario + res_13) * 0.09
    total_liquido = max(0, total_bruto - inss)

    # --- EXIBIÇÃO DASHBOARD ---
    st.subheader("📊 2. Demonstrativo Financeiro")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Aviso Prévio", f"{dias_aviso} dias")
    col2.metric("Anos de Casa", f"{anos_casa} anos")
    col3.metric("Multa FGTS", f"R$ {multa_fgts:,.2f}")
    col4.metric("LÍQUIDO FINAL", f"R$ {total_liquido:,.2f}")

    # Tabela de Aviso Detalhado (Lei 12.506/2011)
    with st.expander("🔍 Detalhamento do Aviso Prévio (Lei 12.506/2011)", expanded=True):
        st.write(f"Cálculo baseado na remuneração de **R$ {base_calculo:,.2f}**")
        st.table(lista_aviso)
        st.info(f"O colaborador tem direito a 30 dias base + {dias_aviso - 30} dias proporcionais.")

    st.markdown("### 🗂️ Memória de Cálculo Geral")
    rubricas_tabela = {
        "Descritivo": [
            f"Saldo de Salário ({data_dem.day} dias)", 
            f"Aviso Prévio Total ({dias_aviso} dias)", 
            f"13º Proporcional ({meses_13}/12)", 
            "Férias Vencidas + 1/3",
            f"Férias Proporcionais ({meses_ferias_prop}/12) + 1/3", 
            "Multa Rescisória FGTS"
        ],
        "Valor": [
            f"R$ {res_saldo_salario:,.2f}", f"R$ {res_aviso:,.2f}", 
            f"R$ {res_13:,.2f}", f"R$ {res_ferias_vencidas:,.2f}", 
            f"R$ {res_ferias_prop:,.2f}", f"R$ {multa_fgts:,.2f}"
        ]
    }
    st.table(rubricas_tabela)

if __name__ == "__main__":
    main()
