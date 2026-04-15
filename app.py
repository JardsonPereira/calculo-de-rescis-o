import streamlit as st
from datetime import datetime, date, timedelta
from fpdf import FPDF
import base64

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Rescisão Profissional 2026", layout="wide", page_icon="⚖️")

def calcular_avos_clt(data_inicio, data_fim):
    if not data_inicio or not data_fim: return 0
    meses = (data_fim.year - data_inicio.year) * 12 + data_fim.month - data_inicio.month
    if data_fim.day >= 15:
        meses += 1
    return max(0, meses)

def detalhar_lei_12506(data_adm, data_dem, base):
    if not data_adm or not data_dem: return 0, 0, 0, 0, []
    anos_completos = (data_dem - data_adm).days // 365
    anos_para_calculo = min(anos_completos, 20)
    dias_extras = anos_para_calculo * 3
    total_dias = 30 + dias_extras
    valor_dia = base / 30 if base > 0 else 0
    especificacao = [
        {"Descrição": "Aviso Prévio Base", "Dias": 30, "Valor": valor_dia * 30}
    ]
    if anos_para_calculo > 0:
        especificacao.append({
            "Descrição": f"Adicional Lei 12.506 ({anos_para_calculo} anos)",
            "Dias": dias_extras,
            "Valor": valor_dia * dias_extras
        })
    return total_dias, anos_completos, valor_dia * 30, valor_dia * dias_extras, especificacao

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Cabeçalho
    pdf.cell(190, 10, "TRCT - Termo de Rescisão do Contrato de Trabalho", 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, "R")
    pdf.ln(5)

    # Dados do Colaborador
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 8, " DADOS DO CONTRATO", 0, 1, "L", True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(95, 8, f"Colaborador: {dados['nome']}", 0, 0)
    pdf.cell(95, 8, f"Motivo: {dados['motivo']}", 0, 1)
    pdf.cell(95, 8, f"Admissão: {dados['data_adm'].strftime('%d/%m/%Y')}", 0, 0)
    pdf.cell(95, 8, f"Demissão: {dados['data_dem'].strftime('%d/%m/%Y')}", 0, 1)
    pdf.ln(5)

    # Verbas Rescisórias
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 8, " DISCRIMINAÇÃO DAS VERBAS", 0, 1, "L", True)
    pdf.set_font("Arial", "", 10)
    
    for rubrica, valor in dados['creditos'].items():
        pdf.cell(140, 7, rubrica, 1)
        pdf.cell(50, 7, f"R$ {valor}", 1, 1, "R")
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(140, 8, "TOTAL BRUTO", 1)
    pdf.cell(50, 8, f"R$ {dados['total_prov']:,.2f}", 1, 1, "R")
    pdf.ln(5)

    # Descontos
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 8, " DESCONTOS", 0, 1, "L", True)
    pdf.set_font("Arial", "", 10)
    for rubrica, valor in dados['debitos'].items():
        pdf.cell(140, 7, rubrica, 1)
        pdf.cell(50, 7, f"R$ {valor}", 1, 1, "R")
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(140, 10, "LÍQUIDO A RECEBER", 1)
    pdf.cell(50, 10, f"R$ {dados['total_liq']:,.2f}", 1, 1, "R")
    
    # Assinaturas
    pdf.ln(20)
    pdf.cell(90, 10, "________________________________", 0, 0, "C")
    pdf.cell(10, 10, "", 0, 0)
    pdf.cell(90, 10, "________________________________", 0, 1, "C")
    pdf.cell(90, 5, "EMPRESA", 0, 0, "C")
    pdf.cell(10, 5, "", 0, 0)
    pdf.cell(90, 5, "COLABORADOR", 0, 1, "C")
    
    return pdf.output(dest="S").encode("latin-1")

def main():
    st.title("⚖️ Sistema de Gestão de Rescisões - Versão 2026")

    # --- ENTRADA DE DADOS ---
    with st.container():
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome do Colaborador", value="Colaborador Exemplo")
        data_adm = c2.date_input("Data de Admissão", value=date(2020, 1, 1), format="DD/MM/YYYY")
        data_dem = c3.date_input("Data de Demissão", value=date(2026, 4, 15), format="DD/MM/YYYY")
        motivo = c1.selectbox("Motivo", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum", "Justa Causa"])
        aviso_status = c2.radio("Tipo de Aviso", ["Indenizado", "Trabalhado", "Não Cumprido (Descontar)"])

    # --- SIDEBAR ---
    salario = st.sidebar.number_input("Salário Base", value=3000.0)
    medias = st.sidebar.number_input("Médias Variáveis", value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo FGTS", value=10000.0)
    tem_ferias_vencidas = st.sidebar.checkbox("Possui Férias Vencidas?")
    aplicar_multa_477 = st.sidebar.checkbox("Aplicar Multa Art. 477 (Atraso)")
    faltas_dias = st.sidebar.number_input("Faltas (Dias)", min_value=0)

    if data_adm and data_dem:
        base_calc = salario + medias
        total_dias_aviso, anos_casa, v_base_aviso, v_extras_aviso, tabela_lei = detalhar_lei_12506(data_adm, data_dem, base_calc)
        
        # Cálculos de Verbas
        res_saldo = (salario / 30) * data_dem.day
        avos_13 = calcular_avos_clt(date(data_dem.year, 1, 1), data_dem)
        avos_ferias = calcular_avos_clt(data_adm, data_dem) % 12
        
        res_13 = (base_calc / 12) * avos_13
        res_ferias_prop = (base_calc / 12) * avos_ferias
        res_ferias_vencidas = base_calc if tem_ferias_vencidas else 0.0
        terco_total = (res_ferias_prop + res_ferias_vencidas) / 3
        multa_477 = salario if aplicar_multa_477 else 0.0
        
        v_aviso = (v_base_aviso + v_extras_aviso) if (aviso_status == "Indenizado" and motivo == "Sem Justa Causa") else 0.0
        multa_fgts = saldo_fgts * 0.40 if motivo == "Sem Justa Causa" else 0.0

        # Totais
        total_prov = res_saldo + res_13 + res_ferias_prop + res_ferias_vencidas + terco_total + v_aviso + multa_477 + multa_fgts
        desc_inss = (res_saldo + res_13) * 0.09
        desc_faltas = (salario / 30) * faltas_dias
        total_desc = desc_inss + desc_faltas
        total_liq = total_prov - total_desc

        # --- DICIONÁRIOS PARA O PDF ---
        creditos_dict = {
            "Saldo Salário": f"{res_saldo:,.2f}",
            "13º Proporcional": f"{res_13:,.2f}",
            "Férias Proporcionais": f"{res_ferias_prop:,.2f}",
            "1/3 Constitucional": f"{terco_total:,.2f}",
            "Aviso Prévio Indenizado": f"{v_aviso:,.2f}",
            "Multa FGTS (40%)": f"{multa_fgts:,.2f}"
        }
        if tem_ferias_vencidas: creditos_dict["Férias Vencidas"] = f"{res_ferias_vencidas:,.2f}"
        if aplicar_multa_477: creditos_dict["Multa Art. 477 CLT"] = f"{multa_477:,.2f}"

        debitos_dict = {
            "INSS": f"{desc_inss:,.2f}",
            "Faltas/DSR": f"{desc_faltas:,.2f}"
        }

        # --- INTERFACE ---
        st.divider()
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Proventos", f"R$ {total_prov:,.2f}")
        c_m2.metric("Descontos", f"R$ {total_desc:,.2f}")
        c_m3.metric("Líquido", f"R$ {total_liq:,.2f}")

        # Botão de Download
        dados_rescisao = {
            "nome": nome, "data_adm": data_adm, "data_dem": data_dem, "motivo": motivo,
            "creditos": creditos_dict, "debitos": debitos_dict,
            "total_prov": total_prov, "total_liq": total_liq
        }
        
        pdf_bytes = gerar_pdf(dados_rescisao)
        st.download_button(
            label="📄 Baixar Rescisão Detalhada (PDF)",
            data=pdf_bytes,
            file_name=f"Rescisao_{nome.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        
        st.write("### Detalhamento das Verbas")
        st.table(creditos_dict)

if __name__ == "__main__":
    main()
