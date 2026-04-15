import streamlit as st
from datetime import datetime, date, timedelta
from fpdf import FPDF

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ERP Rescisão Profissional 2026", layout="wide", page_icon="⚖️")

# --- FUNÇÕES DE CÁLCULO ---
def calcular_avos_clt(data_inicio, data_fim):
    """Regra CLT: 15 dias ou mais no mês = 1/12 avos."""
    if not data_inicio or not data_fim: return 0
    meses = (data_fim.year - data_inicio.year) * 12 + data_fim.month - data_inicio.month
    if data_fim.day >= 15:
        meses += 1
    return max(0, meses)

def detalhar_lei_12506(data_adm, data_dem, base):
    """Lógica da Lei 12.506/11: 30 dias base + 3 dias por ano completo."""
    if not data_adm or not data_dem: return 0, 0, 0, 0
    anos_completos = (data_dem - data_adm).days // 365
    anos_para_calculo = min(anos_completos, 20)
    dias_extras = anos_para_calculo * 3
    total_dias = 30 + dias_extras
    valor_dia = base / 30 if base > 0 else 0
    return total_dias, anos_completos, valor_dia * 30, valor_dia * dias_extras

def gerar_pdf(dados):
    """Gera o documento PDF com assinaturas."""
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 15, "RECIBO DE QUITACAO DE RESCISAO", 0, 1, "C")
    
    # Identificação
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(190, 8, " 1. IDENTIFICACAO", 0, 1, "L", True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, f"Colaborador: {dados['nome']}", 1)
    pdf.cell(95, 8, f"Motivo: {dados['motivo']}", 1, 1)
    pdf.cell(63, 8, f"Admissao: {dados['data_adm'].strftime('%d/%m/%Y')}", 1)
    pdf.cell(63, 8, f"Demissao: {dados['data_dem'].strftime('%d/%m/%Y')}", 1)
    pdf.cell(64, 8, f"Tempo: {dados['anos_casa']} anos", 1, 1)
    pdf.ln(5)

    # Proventos
    pdf.set_font("Arial", "B", 10)
    pdf.cell(190, 8, " 2. VERBAS RESCISSORIAS (CREDITOS)", 0, 1, "L", True)
    pdf.set_font("Arial", "", 9)
    for rubrica, valor in dados['creditos'].items():
        pdf.cell(140, 7, rubrica, 1)
        pdf.cell(50, 7, valor, 1, 1, "R")
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(140, 8, "TOTAL BRUTO", 1)
    pdf.cell(50, 8, f"R$ {dados['total_prov']:,.2f}", 1, 1, "R")
    pdf.ln(5)

    # Descontos
    pdf.set_font("Arial", "B", 10)
    pdf.cell(190, 8, " 3. DESCONTOS", 0, 1, "L", True)
    pdf.set_font("Arial", "", 9)
    for rubrica, valor in dados['debitos'].items():
        pdf.cell(140, 7, rubrica, 1)
        pdf.cell(50, 7, valor, 1, 1, "R")
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(140, 10, "VALOR LIQUIDO A RECEBER", 1)
    pdf.cell(50, 10, f"R$ {dados['total_liq']:,.2f}", 1, 1, "R")

    # Assinaturas
    pdf.ln(30)
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Data: ____/____/2026", 0, 1, "L")
    pdf.ln(10)
    pdf.cell(90, 0.2, "", "T", 0)
    pdf.cell(10, 0.2, "", 0, 0)
    pdf.cell(90, 0.2, "", "T", 1)
    pdf.cell(90, 5, "EMPRESA", 0, 0, "C")
    pdf.cell(10, 5, "", 0, 0)
    pdf.cell(90, 5, "COLABORADOR", 0, 1, "C")

    return pdf.output(dest="S").encode("latin-1")

def main():
    st.title("⚖️ Sistema de Gestão de Rescisões - Versão 2026")
    st.info("Cálculo integrado: Lei 12.506 (Aviso), Férias Vencidas e Multas CLT.")

    # --- ENTRADA DE DADOS ---
    with st.container():
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome do Colaborador", "Nome Completo")
        data_adm = c2.date_input("Data de Admissão", value=date(2024, 1, 1), format="DD/MM/YYYY")
        data_dem = c3.date_input("Data de Demissão", value=date(2026, 4, 15), format="DD/MM/YYYY")
        motivo = c1.selectbox("Motivo da Saída", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum", "Justa Causa"])
        aviso_status = c2.radio("Aviso Prévio", ["Indenizado", "Trabalhado", "Descontar (Não Cumprido)"])

    # --- SIDEBAR FINANCEIRA ---
    st.sidebar.header("💰 Proventos e Médias")
    salario = st.sidebar.number_input("Salário Base", min_value=0.0, value=3000.0)
    medias = st.sidebar.number_input("Médias Variáveis", min_value=0.0, value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo FGTS", min_value=0.0, value=5000.0)
    
    st.sidebar.divider()
    st.sidebar.header("⚖️ Verbas Legais")
    tem_ferias_vencidas = st.sidebar.checkbox("Possui Férias Vencidas?")
    aplicar_multa_477 = st.sidebar.checkbox("Multa Art. 477 (Atraso)")
    faltas_dias = st.sidebar.number_input("Dias de Falta", min_value=0)

    if data_adm and data_dem:
        # Lógica de Cálculo
        base_calc = salario + medias
        total_dias_aviso, anos_casa, v_base_aviso, v_extras_aviso = detalhar_lei_12506(data_adm, data_dem, base_calc)
        
        # Projeção para 13º e Férias
        data_proj = data_dem
        if aviso_status == "Indenizado" and motivo == "Sem Justa Causa":
            data_proj = data_dem + timedelta(days=total_dias_aviso)

        # Créditos
        res_saldo = (salario / 30) * data_dem.day
        avos_13 = calcular_avos_clt(date(data_dem.year, 1, 1), data_proj)
        avos_ferias = calcular_avos_clt(data_adm, data_proj) % 12
        if avos_ferias == 0 and (data_proj - data_adm).days >= 15: avos_ferias = 12

        v_13 = (base_calc / 12) * avos_13
        v_ferias_prop = (base_calc / 12) * avos_ferias
        v_ferias_venc = base_calc if tem_ferias_vencidas else 0.0
        v_terco = (v_ferias_prop + v_ferias_venc) / 3
        
        v_aviso = (v_base_aviso + v_extras_aviso) if (aviso_status == "Indenizado" and motivo == "Sem Justa Causa") else 0.0
        v_multa_477 = salario if aplicar_multa_477 else 0.0
        v_multa_fgts = saldo_fgts * (0.40 if motivo == "Sem Justa Causa" else 0.20 if motivo == "Acordo Comum" else 0.0)

        # Montagem dos Dicionários de Dados
        creditos = {
            "Saldo de Salário": f"{res_saldo:,.2f}",
            f"13º Salário ({avos_13}/12)": f"{v_13:,.2f}",
            f"Férias Prop. ({avos_ferias}/12)": f"{v_ferias_prop:,.2f}",
            "1/3 Constitucional": f"{v_terco:,.2f}"
        }
        if v_aviso > 0: creditos[f"Aviso Prévio ({total_dias_aviso} dias)"] = f"{v_aviso:,.2f}"
        if tem_ferias_vencidas: creditos["Férias Vencidas"] = f"{v_ferias_venc:,.2f}"
        if v_multa_477 > 0: creditos["Multa Art. 477 CLT"] = f"{v_multa_477:,.2f}"
        if v_multa_fgts > 0: creditos["Multa FGTS"] = f"{v_multa_fgts:,.2f}"

        # Débitos
        desc_inss = (res_saldo + v_13) * 0.09
        desc_faltas = (salario / 30) * faltas_dias
        desc_aviso = salario if aviso_status == "Descontar (Não Cumprido)" else 0.0
        
        debitos = {
            "INSS (Provisório)": f"{desc_inss:,.2f}",
            "Faltas/DSR": f"{desc_faltas:,.2f}"
        }
        if desc_aviso > 0: debitos["Aviso Prévio (Desconto)"] = f"{desc_aviso:,.2f}"

        # Totais
        total_prov = sum(float(v.replace(',', '')) for v in creditos.values())
        total_desc = sum(float(v.replace(',', '')) for v in debitos.values())
        total_liq = max(0, total_prov - total_desc)

        # --- EXIBIÇÃO ---
        st.divider()
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Proventos", f"R$ {total_prov:,.2f}")
        col_m2.metric("Descontos", f"R$ {total_desc:,.2f}", delta_color="inverse")
        col_m3.metric("Líquido Final", f"R$ {total_liq:,.2f}")

        st.divider()
        # Botão de PDF
        dados_pdf = {
            "nome": nome, "data_adm": data_adm, "data_dem": data_dem, "motivo": motivo,
            "anos_casa": anos_casa, "creditos": creditos, "debitos": debitos,
            "total_prov": total_prov, "total_liq": total_liq
        }
        
        st.download_button(
            label="📄 Baixar Rescisão em PDF",
            data=gerar_pdf(dados_pdf),
            file_name=f"Rescisao_{nome.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

        # Tabelas de Detalhamento
        c_tab1, c_tab2 = st.columns(2)
        with c_tab1:
            st.write("### 🟢 Créditos")
            st.table(creditos)
        with c_tab2:
            st.write("### 🔴 Débitos")
            st.table(debitos)

    else:
        st.warning("Insira as datas para calcular.")

if __name__ == "__main__":
    main()
