import streamlit as st
from datetime import date, timedelta

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Rescisão 2026", layout="wide")

def aplicar_piso(valor, piso=815.00):
    """Garante o mínimo de 50% do salário mínimo para verbas proporcionais."""
    return max(valor, piso) if valor > 0 else 0

def calcular_meses_13(data_adm, data_dem_projetada):
    """
    Regra: 1/12 avos por mês trabalhado no ano atual.
    Considera-se o mês se houver 15 dias ou mais de trabalho.
    """
    ano_rescisao = data_dem_projetada.year
    inicio_ano = date(ano_rescisao, 1, 1)
    
    # Se admitido no mesmo ano, conta da admissão, senão de 1º de Janeiro
    inicio_contagem = max(data_adm, inicio_ano)
    
    meses = 0
    # Loop pelos meses do ano até o mês da demissão projetada
    for mes in range(inicio_contagem.month, data_dem_projetada.month + 1):
        if mes < data_dem_projetada.month:
            meses += 1 # Meses anteriores completos no ano contam 1 avo
        else:
            # No último mês, verifica se trabalhou 15 dias ou mais
            if data_dem_projetada.day >= 15:
                meses += 1
                
    return max(0, meses)

def main():
    st.title("⚖️ Calculadora Rescisória 2026 - Correção de 13º")
    st.markdown("---")

    # --- SIDEBAR: VALORES ---
    st.sidebar.header("💰 Bases Financeiras")
    salario_atual = st.sidebar.number_input("Salário Base Atual", min_value=0.0, step=100.0)
    media_variaveis = st.sidebar.number_input("Média de Comissões/HE (12 meses)", min_value=0.0)
    saldo_fgts = st.sidebar.number_input("Saldo para Fins Rescisórios FGTS", min_value=0.0)

    # --- CORPO: DATAS E MOTIVO ---
    c1, c2, c3 = st.columns(3)
    data_adm = c1.date_input("Data de Admissão", value=date(2021, 1, 1))
    data_dem = c2.date_input("Data de Demissão (Último dia trabalhado)", value=date(2026, 4, 10))
    motivo = c3.selectbox("Motivo", ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"])
    aviso_tipo = c3.radio("Aviso Prévio", ["Indenizado", "Trabalhado"])

    # --- LÓGICA DE CÁLCULO ---
    # 1. Base de Cálculo Integral (Salário + Médias)
    remuneracao_integral = salario_atual + media_variaveis

    # 2. Aviso Prévio Lei 12.506/2011
    anos_casa = (data_dem - data_adm).days // 365
    dias_aviso = 30 + (min(anos_casa, 20) * 3)
    
    # 3. Projeção do Aviso (Crucial para o 13º)
    # Se o aviso for indenizado, o contrato se "estende" para fins de 13º e Férias
    data_projetada = data_dem
    if aviso_tipo == "Indenizado" and motivo != "Pedido de Demissão":
        data_projetada = data_dem + timedelta(days=dias_aviso)

    # 4. Cálculo de 13º Salário Proporcional
    avos_13 = calcular_meses_13(data_adm, data_projetada)
    # Valor 13º = (Remuneração / 12) * Meses Proporcionais
    valor_13_raw = (remuneracao_integral / 12) * avos_13
    res_13_final = aplicar_piso(valor_13_raw) if salario_atual > 0 else 0

    # 5. Outras Verbas
    res_saldo = (salario_atual / 30) * data_dem.day
    res_aviso = (remuneracao_integral / 30) * dias_aviso if (aviso_tipo == "Indenizado" and motivo == "Sem Justa Causa") else 0
    # Férias Proporcionais seguem a mesma contagem de avos da projeção
    res_ferias_prop = aplicar_piso(((remuneracao_integral / 12) * avos_13) * 1.3333) if salario_atual > 0 else 0
    
    multa_fgts = saldo_fgts * 0.4 if motivo == "Sem Justa Causa" else (saldo_fgts * 0.2 if motivo == "Acordo Comum" else 0)

    # --- EXIBIÇÃO ---
    st.subheader("📋 Demonstrativo de Verbas")
    
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("13º Proporcional", f"{avos_13}/12 avos", f"R$ {res_13_final:,.2f}")
    col_r2.metric("Data Projetada", data_projetada.strftime('%d/%m/%Y'))
    col_r3.metric("Total Líquido Est.", f"R$ {(res_saldo + res_13_final + res_ferias_prop + res_aviso + multa_fgts):,.2f}")

    st.markdown("### 🗂️ Memória de Cálculo do 13º")
    st.write(f"- **Salário Base:** R$ {salario_atual:,.2f}")
    st.write(f"- **Média de Variáveis (Comissões/HE):** R$ {media_variaveis:,.2f}")
    st.write(f"- **Base de Cálculo (Salário + Média):** R$ {remuneracao_integral:,.2f}")
    st.write(f"- **Meses Apurados (Ano {data_dem.year}):** {avos_13} meses (considerando regra de 15 dias e projeção de aviso)")

    st.table({
        "Rubrica": ["Saldo de Salário", "13º Proporcional", "Férias Prop + 1/3", "Aviso Prévio", "Multa FGTS"],
        "Cálculo": [f"{data_dem.day} dias", f"{avos_13}/12 avos", f"{avos_13}/12 avos", f"{dias_aviso} dias", "Sobre Saldo"],
        "Valor (R$)": [f"{res_saldo:,.2f}", f"{res_13_final:,.2f}", f"{res_ferias_prop:,.2f}", f"{res_aviso:,.2f}", f"{multa_fgts:,.2f}"]
    })

if __name__ == "__main__":
    main()
