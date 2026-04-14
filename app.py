import streamlit as st
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="RH System 2026", page_icon="🏢", layout="wide")

def aplicar_piso(valor, piso):
    """Garante o mínimo de 50% do salário mínimo por verba proporcional."""
    return max(valor, piso)

def gerar_pdf(dados):
    """Gera um recibo profissional em PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Demonstrativo de Rescisao de Contrato", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 11)
    for chave, valor in dados.items():
        pdf.cell(100, 8, f"{chave}:", border=0)
        pdf.cell(90, 8, f"{valor}", border=0, ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(200, 10, f"Documento gerado para fins de conferencia em {datetime.now().strftime('%d/%m/%Y')}", ln=True, align="C")
    return pdf.output(dest="S").encode("latin-1")

def main():
    st.title("🏢 Gestao de Desligamento - Modulo 2026")
    st.markdown("---")

    # --- SEÇÃO 1: IDENTIFICAÇÃO (CORPO DO APP) ---
    col_id1, col_id2, col_id3 = st.columns([2, 1, 1])
    with col_id1:
        nome_func = st.text_input("Nome do Colaborador", placeholder="Ex: Joao Silva")
    with col_id2:
        cpf_func = st.text_input("CPF", placeholder="000.000.000-00")
    with col_id3:
        data_rescisao = st.date_input("Data do Desligamento")

    st.sidebar.header("⚙️ Parametros Salariais")
    
    # Tratamento de Alteração Salarial
    ultimo_salario = st.sidebar.number_input("Ultimo Salario Fixo (Atual)", min_value=1630.0, value=3000.0)
    media_salarial_ano = st.sidebar.number_input("Media Salarial (Ultimos 12 meses)", 
                                                 min_value=1630.0, value=2800.0, 
                                                 help="Use a media ponderada se houve aumentos ou comissoes no periodo.")
    
    adicionais = st.sidebar.number_input("Adicionais Fixos (Insalubridade/Peric.)", min_value=0.0, value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo FGTS (p/ Multa)", min_value=0.0, value=5000.0)
    
    st.sidebar.divider()
    
    motivo = st.sidebar.selectbox("Motivo da Saida", ["Sem Justa Causa", "Pedido de Demissao", "Acordo Comum"])
    meses_prop = st.sidebar.slider("Meses Proporcionais (13º/Ferias)", 1, 12, 6)
    dias_trabalhados = st.sidebar.slider("Dias no ultimo mes", 1, 30, 15)

    # --- LOGICA DE CALCULOS EMPRESARIAIS ---
    SALARIO_MINIMO = 1630.00
    PISO_VERBA = SALARIO_MINIMO / 2 # R$ 815,00
    
    # 1. Base para Saldo e Aviso (Ultimo Salario)
    base_imediata = ultimo_salario + adicionais
    res_saldo = (base_imediata / 30) * dias_trabalhados
    
    # 2. Base para 13º e Ferias (Media Salarial)
    # A lei diz que o 13º é pelo salario atual, mas ferias e comissoes seguem a media. 
    # Para ser conservador e evitar processos, usamos a media se for maior, ou o atual.
    base_proporcional = max(media_salarial_ano, ultimo_salario) + adicionais
    
    res_13 = aplicar_piso((base_proporcional / 12) * meses_prop, PISO_VERBA)
    res_ferias = aplicar_piso(((base_proporcional / 12) * meses_prop) * 1.3333, PISO_VERBA)
    
    # 3. Multas e Aviso
    multa_fgts = 0
    aviso_previo = 0
    if motivo == "Sem Justa Causa":
        multa_fgts = saldo_fgts * 0.40
        aviso_previo = base_imediata
    elif motivo == "Acordo Comum":
        multa_fgts = saldo_fgts * 0.20
        aviso_previo = base_imediata * 0.50

    # 4. Descontos (INSS 2026 Progressivo)
    base_inss = res_saldo + res_13
    if base_inss <= 1630: inss = base_inss * 0.075
    elif base_inss <= 2866: inss = (base_inss * 0.09) - 24.45
    else: inss = (base_inss * 0.12) - 110.00

    total_bruto = res_saldo + res_13 + res_ferias + aviso_previo + multa_fgts
    total_liquido = total_bruto - inss

    # --- EXIBIÇÃO DASHBOARD ---
    st.subheader("📊 Demonstrativo Financeiro")
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
        st.metric("Total Bruto", f"R$ {total_bruto:,.2f}")
    with col_res2:
        st.metric("Total Descontos (INSS)", f"R$ {inss:,.2f}")
    with col_res3:
        st.metric("LIQUIDO A PAGAR", f"R$ {total_liquido:,.2f}", delta="Saldo Final")

    # Tabela Profissional
    st.markdown("### 🗂️ Rubricas da Rescisao")
    detalhes = {
        "Codigo": ["101", "102", "103", "104", "105"],
        "Descricao": ["Saldo de Salario", "13º Salario Proporcional", "Ferias Proporcionais + 1/3", "Aviso Previo Indenizado", "Multa Rescisoria FGTS"],
        "Base Utilizada": ["Salario Atual", "Media/Atual", "Media/Atual", "Salario Atual", "Saldo de Fins Rescisorios"],
        "Valor Bruto": [f"R$ {res_saldo:,.2f}", f"R$ {res_13:,.2f}", f"R$ {res_ferias:,.2f}", f"R$ {aviso_previo:,.2f}", f"R$ {multa_fgts:,.2f}"]
    }
    st.table(detalhes)

    # --- EXPORTAÇÃO ---
    st.divider()
    if st.button("🖨️ Gerar Recibo de Quitação em PDF"):
        dados_doc = {
            "Funcionario": nome_func,
            "CPF": cpf_func,
            "Data Rescisao": data_rescisao.strftime('%d/%m/%Y'),
            "Motivo": motivo,
            "Salario Atual": f"R$ {ultimo_salario:,.2f}",
            "Media Salarial": f"R$ {media_salarial_ano:,.2f}",
            "Saldo de Salario": f"R$ {res_saldo:,.2f}",
            "13 Salario": f"R$ {res_13:,.2f}",
            "Ferias + 1/3": f"R$ {res_ferias:,.2f}",
            "Multa FGTS": f"R$ {multa_fgts:,.2f}",
            "TOTAL LIQUIDO": f"R$ {total_liquido:,.2f}"
        }
        try:
            pdf_bytes = gerar_pdf(dados_doc)
            st.download_button(label="📥 Baixar Documento PDF", data=pdf_bytes, file_name=f"Rescisao_{nome_func}.pdf", mime="application/pdf")
        except:
            st.error("Erro ao gerar PDF. Certifique-se de não usar caracteres especiais no nome.")

if __name__ == "__main__":
    main()
