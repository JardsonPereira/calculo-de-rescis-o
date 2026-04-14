import streamlit as st
from fpdf import FPDF
from datetime import datetime, date

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Rescisão Profissional 2026", layout="wide", page_icon="⚖️")

def aplicar_piso(valor, piso):
    return max(valor, piso)

def detalhar_aviso_lei_12506(data_adm, data_dem, base_calculo):
    anos_completos = (data_dem - data_adm).days // 365
    anos_limitados = min(anos_completos, 20)
    valor_dia = base_calculo / 30
    
    detalhamento = []
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
    st.info("Regra de Férias Vencidas: O não pagamento no prazo legal gera a multa de pagamento em dobro (Art. 137 CLT).")

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
    
    st.sidebar.divider()
    st.sidebar.subheader("📅 Situação de Férias")
    tem_ferias_vencidas = st.sidebar.checkbox("Possui Férias Vencidas (Não Gozadas)?")
    pagar_dobra = st.sidebar.checkbox("Férias estão fora do prazo legal? (Gera Multa/Dobra)", help="Marque se o período concessivo já expirou.")

    # --- LOGICA DE CÁLCULO ---
    SALARIO_MIN_2026 = 1630.00
    PISO_VERBA = SALARIO_MIN_2026 / 2 # R$ 815,00

    base_calculo = ultimo_salario_bruto + media_variaveis
    dias_aviso, anos_casa, valor_aviso_total, lista_aviso = detalhar_aviso_lei_12506(data_adm, data_dem, base_calculo)
    
    meses_13 = data_dem.month if data_dem.day >= 15 else data_dem.month - 1
    meses_ferias_prop = data_dem.month - 1 if data_dem.day < 15 else data_dem.month

    # 1. Saldo de Salário
    res_saldo_salario = (ultimo_salario_bruto / 30) * data_dem.day

    # 2. Aviso Prévio
    res_aviso = 0
    if aviso_tipo == "Indenizado":
        res_aviso = valor_aviso_total if motivo == "Sem Justa Causa" else valor_aviso_total * 0.5 if motivo == "Acordo Comum" else 0

    # 3. 13º Proporcional
    res_13 = aplicar_piso((base_calculo / 12) * meses_13, PISO_VERBA) if base_calculo > 0 else 0

    # 4. FÉRIAS VENCIDAS E MULTA (DOBRA)
    valor_ferias_vencidas_simples = (base_calculo * 1.3333) if tem_ferias_vencidas else 0
    multa_ferias_dobra = valor_ferias_vencidas_simples if (tem_ferias_vencidas and pagar_dobra) else 0
    
    # 5. Férias Proporcionais
    res_ferias_prop = aplicar_piso(((base_calculo / 12) * meses_ferias_prop) * 1.3333, PISO_VERBA) if base_calculo > 0 else 0

    # 6. Multa FGTS
    multa_fgts = 0
    if motivo == "Sem Justa Causa":
        multa_fgts = saldo_fgts_total * 0.40
    elif motivo == "Acordo Comum":
        multa_fgts = saldo_fgts_total * 0.20

    # Totais
    total_bruto = res_saldo_salario + res_aviso + res_13 + valor_ferias_vencidas_simples + multa_ferias_dobra + res_ferias_prop + multa_fgts
    inss = (res_saldo_salario + res_13) * 0.09
    total_liquido = max(0, total_bruto - inss)

    # --- DASHBOARD ---
    st.subheader("📊 2. Demonstrativo Financeiro")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Aviso Prévio", f"{dias_aviso} dias")
    col2.metric("Multa FGTS", f"R$ {multa_fgts:,.2f}")
    col3.metric("Multa Férias (Dobra)", f"R$ {multa_ferias_dobra:,.2f}", delta="Art. 137 CLT" if multa_ferias_dobra > 0 else None)
    col4.metric("LÍQUIDO FINAL", f"R$ {total_liquido:,.2f}")

    if multa_ferias_dobra > 0:
        st.warning(f"⚠️ **Atenção:** Foi aplicada a multa de R$ {multa_ferias_dobra:,.2f} referente ao pagamento em dobro das férias vencidas fora do prazo legal.")

    st.markdown("### 🗂️ Memória de Cálculo Geral")
    rubricas_tabela = {
        "Descritivo": [
            f"Saldo de Salário ({data_dem.day} dias)", 
            f"Aviso Prévio Total ({dias_aviso} dias)", 
            f"13º Proporcional ({meses_13}/12)", 
            "Férias Vencidas + 1/3 (Simples)",
            "MULTA: Dobra de Férias Vencidas (Art. 137)",
            f"Férias Proporcionais ({meses_ferias_prop}/12) + 1/3", 
            "Multa Rescisória FGTS"
        ],
        "Valor": [
            f"R$ {res_saldo_salario:,.2f}", f"R$ {res_aviso:,.2f}", 
            f"R$ {res_13:,.2f}", f"R$ {valor_ferias_vencidas_simples:,.2f}", 
            f"R$ {multa_ferias_dobra:,.2f}", f"R$ {res_ferias_prop:,.2f}", 
            f"R$ {multa_fgts:,.2f}"
        ]
    }
    st.table(rubricas_tabela)

    with st.expander("🔍 Detalhamento do Aviso Prévio (Lei 12.506/2011)"):
        st.table(lista_aviso)

if __name__ == "__main__":
    main()
