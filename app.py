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
        detalhamento.append({"Ano": f"{i}º Ano Completo", "Dias": 3, "Valor": round(valor_dia * 3, 2)})
    
    dias_totais = 30 + (anos_limitados * 3)
    valor_total_aviso = valor_dia * dias_totais
    return dias_totais, anos_completos, valor_total_aviso, detalhamento

def main():
    st.title("⚖️ Sistema de Rescisão e Cálculos Trabalhistas - 2026")

    # --- SEÇÃO 1: DADOS DO CONTRATO ---
    st.subheader("📋 1. Identificação e Cronologia")
    c1, c2, c3 = st.columns(3)
    nome = c1.text_input("Nome do Colaborador")
    data_adm = c2.date_input("Data de Admissão", value=date(2021, 1, 1))
    data_dem = c3.date_input("Data de Demissão", value=date(2026, 4, 10))
    motivo = c1.selectbox("Motivo", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])
    aviso_tipo = c2.radio("Aviso Prévio", ["Indenizado", "Trabalhado"])

    # --- SEÇÃO 2: FINANCEIRO (SIDEBAR) ---
    st.sidebar.header("💰 Remuneração e FGTS")
    ultimo_salario = st.sidebar.number_input("Último Salário Bruto", min_value=0.0, value=0.0)
    media_variaveis = st.sidebar.number_input("Média Comissões/HE (12m)", min_value=0.0, value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo Total FGTS", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    st.sidebar.subheader("📅 Férias Vencidas")
    tem_ferias_vencidas = st.sidebar.checkbox("Funcionário tem férias vencidas?")
    
    # Lógica da Multa/Dobra
    multa_ferias_dobra = 0
    valor_ferias_vencidas_simples = 0
    
    if tem_ferias_vencidas:
        fora_do_prazo = st.sidebar.checkbox("⚠️ Estão fora do prazo? (Aplicar Dobra/Multa)")
        base_ferias = ultimo_salario + media_variaveis
        valor_ferias_vencidas_simples = base_ferias * 1.3333
        
        if fora_do_prazo:
            multa_ferias_dobra = valor_ferias_vencidas_simples  # A multa é o valor das férias novamente

    # --- CÁLCULOS ---
    SALARIO_MIN = 1630.00
    PISO = 815.00
    base_total = ultimo_salario + media_variaveis
    
    dias_aviso, anos_casa, v_aviso_total, lista_aviso = detalhar_aviso_lei_12506(data_adm, data_dem, base_total)
    
    # Saldo de Salário
    res_saldo = (ultimo_salario / 30) * data_dem.day
    
    # 13º e Férias Proporcionais
    meses_prop = data_dem.month if data_dem.day >= 15 else data_dem.month - 1
    res_13 = aplicar_piso((base_total / 12) * meses_prop, PISO) if base_total > 0 else 0
    res_ferias_prop = aplicar_piso(((base_total / 12) * meses_prop) * 1.3333, PISO) if base_total > 0 else 0
    
    # Aviso Prévio por Motivo
    res_aviso = 0
    if aviso_tipo == "Indenizado":
        if motivo == "Sem Justa Causa": res_aviso = v_aviso_total
        elif motivo == "Acordo Comum": res_aviso = v_aviso_total * 0.5
        
    # Multa FGTS
    res_multa_fgts = 0
    if motivo == "Sem Justa Causa": res_multa_fgts = saldo_fgts * 0.40
    elif motivo == "Acordo Comum": res_multa_fgts = saldo_fgts * 0.20

    # Totalização
    total_bruto = res_saldo + res_aviso + res_13 + valor_ferias_vencidas_simples + multa_ferias_dobra + res_ferias_prop + res_multa_fgts
    inss = (res_saldo + res_13) * 0.09
    total_liquido = max(0, total_bruto - inss)

    # --- RESULTADOS ---
    st.subheader("📊 Demonstrativo Financeiro")
    col1, col2, col3 = st.columns(3)
    col1.metric("Multa FGTS", f"R$ {res_multa_fgts:,.2f}")
    col2.metric("Multa Férias (Dobra)", f"R$ {multa_ferias_dobra:,.2f}")
    col3.metric("LÍQUIDO FINAL", f"R$ {total_liquido:,.2f}")

    if multa_ferias_dobra > 0:
        st.error(f"PAGAMENTO EM DOBRO: Identificada multa de Art. 137 CLT no valor de R$ {multa_ferias_dobra:,.2f}")

    # Tabela Memória de Cálculo
    tabela = {
        "Descrição": [
            "Saldo de Salário", "Aviso Prévio", "13º Proporcional", 
            "Férias Vencidas (Simples)", "MULTA: Dobra de Férias (Art. 137)", 
            "Férias Proporcionais", "Multa FGTS"
        ],
        "Valor (R$)": [
            f"{res_saldo:,.2f}", f"{res_aviso:,.2f}", f"{res_13:,.2f}", 
            f"{valor_ferias_vencidas_simples:,.2f}", f"{multa_ferias_dobra:,.2f}", 
            f"{res_ferias_prop:,.2f}", f"{res_multa_fgts:,.2f}"
        ]
    }
    st.table(tabela)

if __name__ == "__main__":
    main()
