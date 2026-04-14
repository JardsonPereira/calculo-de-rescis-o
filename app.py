import streamlit as st
from fpdf import FPDF
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Rescisão Profissional 2026", layout="wide", page_icon="⚖️")

def aplicar_piso(valor, piso):
    """Garante o mínimo de 50% do salário mínimo (R$ 815,00)."""
    return max(valor, piso)

def calcular_avos(data_inicio, data_fim):
    """
    Calcula meses proporcionais (1/12). 
    Regra: 15 dias ou mais no mês = 1 mês inteiro.
    """
    meses = data_fim.month
    if data_fim.day < 15:
        meses -= 1
    return max(0, meses)

def detalhar_aviso_lei_12506(data_adm, data_dem, base_calculo):
    """Lei 12.506/2011: 30 dias base + 3 dias por ano completo."""
    anos_completos = (data_dem - data_adm).days // 365
    anos_limitados = min(anos_completos, 20)
    valor_dia = base_calculo / 30
    
    detalhes = [{"Descrição": "Dias Base (Mínimo)", "Dias": 30, "Valor": round(valor_dia * 30, 2)}]
    for i in range(1, anos_limitados + 1):
        detalhes.append({"Descrição": f"Acréscimo {i}º ano completo", "Dias": 3, "Valor": round(valor_dia * 3, 2)})
    
    dias_totais = 30 + (anos_limitados * 3)
    return dias_totais, anos_completos, valor_dia * dias_totais, detalhes

def main():
    st.title("⚖️ Sistema de Rescisão e Cálculos Trabalhistas - 2026")

    # --- SEÇÃO 1: DADOS DO CONTRATO ---
    st.subheader("📋 1. Identificação e Cronologia")
    c1, c2, c3 = st.columns(3)
    nome = c1.text_input("Nome do Colaborador")
    data_adm = c2.date_input("Data de Admissão", value=date(2021, 1, 1))
    data_dem = c3.date_input("Data de Demissão (Último dia trabalhado)", value=date(2026, 4, 10))
    motivo = c1.selectbox("Motivo", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])
    aviso_tipo = c2.radio("Aviso Prévio", ["Indenizado", "Trabalhado"])

    # --- SEÇÃO 2: FINANCEIRO (SIDEBAR) ---
    st.sidebar.header("💰 Remuneração e FGTS")
    ultimo_salario = st.sidebar.number_input("Último Salário Bruto", min_value=0.0, value=0.0)
    media_variaveis = st.sidebar.number_input("Média Comissões/HE (12m)", min_value=0.0, value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo Total FGTS", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    st.sidebar.subheader("📅 Férias Vencidas")
    tem_ferias_vencidas = st.sidebar.checkbox("Possui férias vencidas?")
    multa_ferias_dobra = 0
    valor_ferias_vencidas_simples = 0
    
    if tem_ferias_vencidas:
        fora_do_prazo = st.sidebar.checkbox("⚠️ Aplicar Dobra (Art. 137 CLT)")
        base_f = ultimo_salario + media_variaveis
        valor_ferias_vencidas_simples = base_f * 1.3333
        if fora_do_prazo:
            multa_ferias_dobra = valor_ferias_vencidas_simples

    # --- LÓGICA DE PROJEÇÃO E CÁLCULOS ---
    PISO = 815.00
    base_total = ultimo_salario + media_variaveis
    
    # 1. Aviso Prévio Proporcional
    dias_aviso, anos_casa, v_aviso_total, lista_aviso = detalhar_aviso_lei_12506(data_adm, data_dem, base_total)
    
    # 2. Projeção do Aviso Prévio (Art. 487 CLT)
    # Se indenizado, a data final para fins de 13º e férias avança os dias do aviso
    data_fim_projetada = data_dem
    if aviso_tipo == "Indenizado":
        data_fim_projetada = data_dem + timedelta(days=dias_aviso)
    
    # 3. Saldo de Salário (Dias reais trabalhados)
    res_saldo = (ultimo_salario / 30) * data_dem.day
    
    # 4. 13º e Férias Proporcionais com Projeção e Regra de 15 dias
    meses_13 = calcular_avos(date(data_dem.year, 1, 1), data_fim_projetada)
    # Férias proporcionais (simplificado: meses desde a admissão ou último aniversário)
    meses_ferias = calcular_avos(data_adm, data_fim_projetada) % 12
    if meses_ferias == 0 and (data_fim_projetada - data_adm).days >= 15: meses_ferias = 12

    res_13 = aplicar_piso((base_total / 12) * meses_13, PISO) if base_total > 0 else 0
    res_ferias_prop = aplicar_piso(((base_total / 12) * meses_ferias) * 1.3333, PISO) if base_total > 0 else 0
    
    # 5. Aviso Prévio por Motivo
    res_aviso = 0
    if aviso_tipo == "Indenizado":
        if motivo == "Sem Justa Causa": res_aviso = v_aviso_total
        elif motivo == "Acordo Comum": res_aviso = v_aviso_total * 0.5
        
    # 6. Multa FGTS (40% sobre saldo total)
    res_multa_fgts = 0
    if motivo == "Sem Justa Causa": res_multa_fgts = saldo_fgts * 0.40
    elif motivo == "Acordo Comum": res_multa_fgts = saldo_fgts * 0.20

    # Totalização
    total_bruto = res_saldo + res_aviso + res_13 + valor_ferias_vencidas_simples + multa_ferias_dobra + res_ferias_prop + res_multa_fgts
    inss = (res_saldo + res_13) * 0.09
    total_liquido = max(0, total_bruto - inss)

    # --- INTERFACE ---
    st.subheader("📊 Demonstrativo Financeiro")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aviso Prévio", f"{dias_aviso} dias")
    c2.metric("13º Proporcional", f"{meses_13}/12 avos")
    c3.metric("Férias Prop.", f"{meses_ferias}/12 avos")
    c4.metric("LÍQUIDO FINAL", f"R$ {total_liquido:,.2f}")

    st.markdown(f"**Nota de Projeção:** Com o aviso indenizado, a data projetada para cálculo de avos é **{data_fim_projetada.strftime('%d/%m/%Y')}**.")

    st.markdown("### 📜 Detalhamento do Aviso (Lei 12.506/2011)")
    st.table(lista_aviso)

    st.markdown("### 🗂️ Memória de Cálculo Geral")
    tabela = {
        "Descrição": ["Saldo de Salário", f"Aviso Prévio ({dias_aviso} dias)", f"13º Proporcional ({meses_13} avos)", "Férias Vencidas + Dobra", f"Férias Proporcionais ({meses_ferias} avos) + 1/3", "Multa FGTS"],
        "Valor (R$)": [f"{res_saldo:,.2f}", f"{res_aviso:,.2f}", f"{res_13:,.2f}", f"{(valor_ferias_vencidas_simples + multa_ferias_dobra):,.2f}", f"{res_ferias_prop:,.2f}", f"{res_multa_fgts:,.2f}"]
    }
    st.table(tabela)

if __name__ == "__main__":
    main()
