import streamlit as st
from fpdf import FPDF
from datetime import datetime, date

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Rescisão Profissional 2026", layout="wide", page_icon="⚖️")

def aplicar_piso(valor, piso):
    """Garante o mínimo de 50% do salário mínimo (R$ 815,00)."""
    return max(valor, piso)

def calcular_aviso_proporcional(data_adm, data_dem):
    """Lei 12.506/2011: 30 dias base + 3 dias por ano completo."""
    anos_completos = (data_dem - data_adm).days // 365
    dias_totais = 30 + (anos_completos * 3)
    return min(dias_totais, 90), anos_completos

def gerar_pdf(dados, rubricas):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "TERMO DE RESCISAO DO CONTRATO DE TRABALHO - 2026", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    for k, v in dados.items():
        pdf.cell(90, 8, f"{k}:", border=1)
        pdf.cell(100, 8, f"{v}", border=1, ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(200, 10, "MEMORIA DE CALCULO", ln=True)
    pdf.set_font("Arial", "", 9)
    for i in range(len(rubricas["Descritivo"])):
        pdf.cell(140, 7, rubricas["Descritivo"][i], border=1)
        pdf.cell(50, 7, rubricas["Valor"][i], border=1, ln=True)
    return pdf.output(dest="S").encode("latin-1")

def main():
    st.title("⚖️ Sistema de Rescisão e Cálculos Trabalhistas - 2026")
    st.markdown("---")

    # --- SEÇÃO 1: DADOS DO CONTRATO ---
    st.subheader("📋 1. Identificação e Cronologia")
    c1, c2, c3 = st.columns(3)
    nome = c1.text_input("Nome do Colaborador")
    cpf = c1.text_input("CPF")
    
    data_adm = c2.date_input("Data de Admissão", value=date(2021, 1, 1))
    data_dem = c2.date_input("Data de Demissão (Último dia trabalhado)", value=date(2026, 4, 10))
    
    motivo = c3.selectbox("Motivo do Desligamento", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])
    aviso_tipo = c3.radio("Aviso Prévio", ["Indenizado", "Trabalhado"])

    # --- SEÇÃO 2: HISTÓRICO E VARIÁVEIS (SIDEBAR) ---
    st.sidebar.header("💰 Remuneração e Histórico")
    ultimo_salario_bruto = st.sidebar.number_input("Último Salário Bruto Atual", min_value=1630.0, value=3000.0)
    
    st.sidebar.subheader("Médias (Últimos 12 meses)")
    media_variaveis = st.sidebar.number_input("Média de Comissões/HE", min_value=0.0, value=0.0)
    
    st.sidebar.divider()
    st.sidebar.subheader("🏦 Fundo de Garantia")
    saldo_fgts_total = st.sidebar.number_input("Saldo Total Depositado (5 anos + correções)", min_value=0.0, value=12000.0)
    tem_ferias_vencidas = st.sidebar.checkbox("Possui Férias Vencidas?")

    # --- LOGICA DE CÁLCULO ESPECÍFICA ---
    SALARIO_MIN_2026 = 1630.00
    PISO_VERBA = SALARIO_MIN_2026 / 2 # R$ 815,00

    # Base: Último salário bruto + Médias (Conforme solicitado)
    base_calculo = ultimo_salario_bruto + media_variaveis
    
    # Aviso Proporcional
    dias_aviso, anos_casa = calcular_aviso_proporcional(data_adm, data_dem)
    
    # Proporcionalidades (1/12 avos)
    # 13º: Meses trabalhados no ano atual (Ex: Jan a Abr = 4 meses)
    meses_13 = data_dem.month if data_dem.day >= 15 else data_dem.month - 1
    
    # Férias Prop: Meses do período aquisitivo atual
    # Para o exemplo (01/01 a 10/04), são 3 meses completos + fração de 10 dias (não conta se < 15)
    meses_ferias_prop = data_dem.month - 1 if data_dem.day < 15 else data_dem.month

    # --- CÁLCULO DAS VERBAS ---
    # 1. Saldo de Salário
    res_saldo_salario = (ultimo_salario_bruto / 30) * data_dem.day

    # 2. Aviso Prévio Indenizado
    res_aviso = 0
    if motivo == "Sem Justa Causa" and aviso_tipo == "Indenizado":
        res_aviso = (base_calculo / 30) * dias_aviso
    elif motivo == "Acordo Comum" and aviso_tipo == "Indenizado":
        res_aviso = ((base_calculo / 30) * dias_aviso) * 0.5

    # 3. 13º Proporcional
    res_13 = aplicar_piso((base_calculo / 12) * meses_13, PISO_VERBA)

    # 4. Férias
    res_ferias_vencidas = (base_calculo * 1.3333) if tem_ferias_vencidas else 0
    res_ferias_prop = aplicar_piso(((base_calculo / 12) * meses_ferias_prop) * 1.3333, PISO_VERBA)

    # 5. Multa FGTS (40% sobre saldo total)
    multa_fgts = 0
    if motivo == "Sem Justa Causa":
        multa_fgts = saldo_fgts_total * 0.40
    elif motivo == "Acordo Comum":
        multa_fgts = saldo_fgts_total * 0.20

    # Totais
    total_bruto = res_saldo_salario + res_aviso + res_13 + res_ferias_vencidas + res_ferias_prop + multa_fgts
    inss = (res_saldo_salario + res_13) * 0.09 # Estimado 2026
    total_liquido = total_bruto - inss

    # --- DASHBOARD DE EXIBIÇÃO ---
    st.subheader("📊 2. Demonstrativo Financeiro")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Aviso Prévio", f"{dias_aviso} dias")
    col2.metric("Tempo de Casa", f"{anos_casa} anos")
    col3.metric("Multa FGTS (40%)", f"R$ {multa_fgts:,.2f}")
    col4.metric("LÍQUIDO FINAL", f"R$ {total_liquido:,.2f}")

    # Tabela de Rubricas
    st.markdown("### 🗂️ Memória de Cálculo")
    rubricas_tabela = {
        "Descritivo": [
            f"Saldo de Salário ({data_dem.day} dias)", 
            f"Aviso Prévio Indenizado ({dias_aviso} dias)", 
            f"13º Proporcional ({meses_13}/12)", 
            "Férias Vencidas + 1/3",
            f"Férias Proporcionais ({meses_ferias_prop}/12) + 1/3", 
            "Multa Rescisória FGTS (sobre saldo total)"
        ],
        "Valor": [
            f"R$ {res_saldo_salario:,.2f}", f"R$ {res_aviso:,.2f}", 
            f"R$ {res_13:,.2f}", f"R$ {res_ferias_vencidas:,.2f}", 
            f"R$ {res_ferias_prop:,.2f}", f"R$ {multa_fgts:,.2f}"
        ]
    }
    st.table(rubricas_tabela)

    # --- SEÇÃO 4: PRAZOS E DOCUMENTOS ---
    st.subheader("📅 3. Prazos e Obrigações (Regras 2026)")
    prazo_pagto = (data_dem.replace(day=data_dem.day + 10) if data_dem.day <= 20 else data_dem) # Simplificação de lógica de calendário
    
    st.warning(f"**Data limite para pagamento:** Até 10 dias corridos (Aprox. {prazo_pagto.strftime('%d/%m/%Y')})")
    
    st.markdown("""
    **Documentação Necessária para Homologação:**
    * **TRCT:** Termo de Rescisão assinado.
    * **Chave FGTS:** Emitida via FGTS Digital.
    * **Guia Seguro-Desemprego:** Se houver direito.
    * **PPP:** Perfil Profissiográfico Previdenciário atualizado.
    * **Exame Demissional:** Realizado dentro do prazo legal.
    """)

    # --- PDF ---
    if st.button("🖨️ Exportar Termo de Quitação em PDF"):
        if not nome: st.error("Informe o nome.")
        else:
            dados_pdf = {
                "Colaborador": nome, "CPF": cpf,
                "Admissao": data_adm.strftime('%d/%m/%Y'),
                "Demissao": data_dem.strftime('%d/%m/%Y'),
                "Tempo de Casa": f"{anos_casa} anos",
                "Aviso Previo": f"{dias_aviso} dias",
                "Total Bruto": f"R$ {total_bruto:,.2f}",
                "Desconto INSS": f"R$ {inss:,.2f}",
                "VALOR LIQUIDO": f"R$ {total_liquido:,.2f}"
            }
            pdf_b = gerar_pdf(dados_pdf, rubricas_tabela)
            st.download_button("📥 Baixar PDF", pdf_b, f"Rescisao_{nome}.pdf", "application/pdf")

if __name__ == "__main__":
    main()
