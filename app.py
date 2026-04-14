import streamlit as st

# Configuração da página
st.set_page_config(page_title="Rescisão 2026", page_icon="⚖️")

def calcular_verba_com_piso(valor_calculado, piso):
    """Garante que a verba não seja inferior a 50% do salário mínimo"""
    return max(valor_calculado, piso)

def main():
    st.title("⚖️ Calculadora Rescisória - Regras 2026")
    st.info("Nota: Cálculos ajustados para o piso mínimo de 50% do salário mínimo (R$ 815,00) por verba.")

    # Parâmetros 2026
    SALARIO_MINIMO = 1630.00
    PISO_RESCISAO = SALARIO_MINIMO / 2 # R$ 815,00

    # Entradas de dados
    with st.sidebar:
        st.header("Dados do Contrato")
        salario_base = st.number_input("Salário Mensal (R$)", min_value=1630.0, value=2500.0)
        meses_trab = st.number_input("Meses Proporcionais (1 a 12)", min_value=1, max_value=12, value=6)
        dias_trab = st.slider("Dias no último mês", 1, 30, 15)
        saldo_fgts = st.number_input("Saldo FGTS para multa", min_value=0.0, value=3000.0)
        motivo = st.selectbox("Motivo da Saída", ["Sem Justa Causa", "Pedido de Demissão", "Acordo"])

    # Lógica de Cálculos
    # 1. Saldo de Salário
    valor_dia = salario_base / 30
    res_saldo_salario = calcular_verba_com_piso(valor_dia * dias_trab, PISO_RESCISAO)

    # 2. 13º Salário
    res_13 = calcular_verba_com_piso((salario_base / 12) * meses_trab, PISO_RESCISAO)

    # 3. Férias + 1/3
    valor_ferias = (salario_base / 12) * meses_trab
    res_ferias_total = calcular_verba_com_piso(valor_ferias * 1.3333, PISO_RESCISAO)

    # 4. Multas e Aviso
    multa_fgts = 0
    aviso_previo = 0
    if motivo == "Sem Justa Causa":
        multa_fgts = saldo_fgts * 0.40
        aviso_previo = salario_base
    elif motivo == "Acordo":
        multa_fgts = saldo_fgts * 0.20
        aviso_previo = salario_base * 0.50

    total_bruto = res_saldo_salario + res_13 + res_ferias_total + aviso_previo

    # Interface de Resultados
    st.subheader("Detalhamento de Verbas")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Saldo de Salário", f"R$ {res_saldo_salario:,.2f}")
        st.metric("13º Proporcional", f"R$ {res_13:,.2f}")
        st.metric("Férias + 1/3", f"R$ {res_ferias_total:,.2f}")
    
    with col2:
        st.metric("Aviso Prévio", f"R$ {aviso_previo:,.2f}")
        st.metric("Multa FGTS", f"R$ {multa_fgts:,.2f}")
        st.markdown(f"### **Total Líquido Estimado:**")
        st.title(f"R$ {total_bruto:,.2f}")

    if total_bruto > 5000:
        st.caption("Obs: Incidência de IRRF simplificada acima de R$ 5.000,00 conforme nova regra de 2026.")

if __name__ == "__main__":
    main()
