import streamlit as st
from fpdf import FPDF
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DO SISTEMA ---
st.set_page_config(page_title="ERP Rescisão Profissional 2026", layout="wide", page_icon="⚖️")

def calcular_avos(data_inicio, data_fim_projetada):
    """
    Calcula meses proporcionais (1/12). 
    Regra CLT: 15 dias ou mais no mês = 1 mês inteiro (1 avo).
    """
    # Para 13º, contamos de Janeiro (ou admissão) até a data de saída
    meses = data_fim_projetada.month
    if data_fim_projetada.day < 15:
        meses -= 1
    return max(0, meses)

def calcular_aviso_lei_12506(data_adm, data_dem):
    """Lei 12.506/2011: 30 dias base + 3 dias por ano completo (limite 90 dias)."""
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
        aviso_tipo = st.radio("Aviso Prévio", ["Indenizado", "Trabalhado"])

    # --- SEÇÃO 2: FINANCEIRO (SIDEBAR) ---
    st.sidebar.header("💰 Remuneração e Médias")
    salario_atual = st.sidebar.number_input("Último Salário Base (R$)", min_value=0.0, value=0.0, step=100.0)
    
    st.sidebar.subheader("Médias Variáveis (Últimos 12 meses)")
    media_comissoes = st.sidebar.number_input("Média de Comissões", min_value=0.0, value=0.0)
    media_he = st.sidebar.number_input("Média de Horas Extras", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    saldo_fgts = st.sidebar.number_input("Saldo p/ Fins Rescisórios FGTS (R$)", min_value=0.0, value=0.0)
    
    st.sidebar.subheader("Férias")
    tem_ferias_vencidas = st.sidebar.checkbox("Possui férias vencidas?")
    ferias_fora_prazo = st.sidebar.checkbox("Aplicar Dobra (Art. 137 CLT)")

    # --- LÓGICA DE CÁLCULO ---
    # 1. Base de Cálculo (Remuneração Integral conforme CLT)
    remuneracao_integral = salario_atual + media_comissoes + media_he
    
    # 2. Aviso Prévio Lei 12.506/2011
    dias_aviso, anos_casa = calcular_aviso_proporcional = calcular_aviso_lei_12506(data_adm, data_dem)
    
    # 3. Projeção do Contrato (O tempo de aviso conta para 13º e Férias)
    data_projetada = data_dem
    if aviso_tipo == "Indenizado" and motivo != "Pedido de Demissão":
        data_projetada = data_dem + timedelta(days=dias_aviso)

    # 4. Saldo de Salário (Dias reais trabalhados)
    res_saldo = (salario_atual / 30) * data_dem.day

    # 5. 13º Salário Proporcional (Regra 15 dias + Projeção)
    # Se admitido no ano atual, conta da admissão
    inicio_contagem_13 = date(data_dem.year, 1, 1) if data_adm.year < data_dem.year else data_adm
    avos_13 = calcular_avos(inicio_contagem_13, data_projetada)
    res_13 = (remuneracao_integral / 12) * avos_13

    # 6. Férias Proporcionais + 1/3 (Regra 15 dias + Projeção)
    # Simplificado: meses desde o último aniversário de admissão
    meses_ferias = ((data_projetada.year - data_adm.year) * 12 + data_projetada.month - data_adm.month) % 12
    if data_projetada.day >= 15: meses_ferias += 1
    res_ferias_prop = ((remuneracao_integral / 12) * meses_ferias) * 1.3333

    # 7. Férias Vencidas e Dobra
    res_ferias_vencidas = (remuneracao_integral * 1.3333) if tem_ferias_vencidas else 0
    multa_ferias_dobra = res_ferias_vencidas if (tem_ferias_vencidas and ferias_fora_prazo) else 0

    # 8. Aviso Prévio e Multa FGTS
    res_aviso = 0
    multa_fgts = 0
    if motivo == "Sem Justa Causa":
        res_aviso = (remuneracao_integral / 30) * dias_aviso if aviso_tipo == "Indenizado" else 0
        multa_fgts = saldo_fgts * 0.40
    elif motivo == "Acordo Comum":
        res_aviso = ((remuneracao_integral / 30) * dias_aviso) * 0.50 if aviso_tipo == "Indenizado" else 0
        multa_fgts = saldo_fgts * 0.20

    # 9. Totais e INSS (Simplificado)
    total_bruto = res_saldo + res_13 + res_ferias_prop + res_ferias_vencidas + multa_ferias_dobra + res_aviso + multa_fgts
    inss = (res_saldo + res_13) * 0.09 # Estimativa INSS 2026
    total_liquido = max(0, total_bruto - inss)

    # --- EXIBIÇÃO ---
    st.subheader("📊 Demonstrativo de Resultados")
    c_res1, c_res2, c_res3 = st.columns(3)
    c_res1.metric("Aviso Prévio", f"{dias_aviso} dias")
    c_res2.metric("Tempo de Casa", f"{anos_casa} anos")
    c_res3.metric("LÍQUIDO FINAL", f"R$ {total_liquido:,.2f}")

    st.markdown(f"**Data Final Projetada (c/ Aviso):** {data_projetada.strftime('%d/%m/%Y')}")

    st.markdown("### 🗂️ Memória de Cálculo (Rubricas)")
    tabela_dados = {
        "Verba": ["Saldo de Salário", "13º Proporcional", "Férias Proporcionais + 1/3", "Férias Vencidas", "Multa Férias (Dobra)", "Aviso Prévio", "Multa FGTS"],
        "Quantidade": [f"{data_dem.day} dias", f"{avos_13}/12 avos", f"{meses_ferias}/12 avos", "1 integral", "Art. 137", f"{dias_aviso} dias", "40% ou 20%"],
        "Valor Bruto": [f"R$ {res_saldo:,.2f}", f"R$ {res_13:,.2f}", f"R$ {res_ferias_prop:,.2f}", f"R$ {res_ferias_vencidas:,.2f}", f"R$ {multa_ferias_dobra:,.2f}", f"R$ {res_aviso:,.2f}", f"R$ {multa_fgts:,.2f}"]
    }
    st.table(tabela_dados)

if __name__ == "__main__":
    main()
