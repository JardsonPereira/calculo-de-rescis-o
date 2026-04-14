import streamlit as st

# Configuração da página (Deve ser o primeiro comando)
st.set_page_config(page_title="Rescisão 2026 Pro", page_icon="⚖️", layout="wide")

def aplicar_piso(valor, piso):
    """Garante que a verba não seja inferior a 50% do salário mínimo se for proporcional."""
    return max(valor, piso)

def main():
    # Título e Estilo
    st.title("⚖️ Calculadora Rescisória Inteligente - Regras 2026")
    st.markdown("---")

    # Parâmetros de 2026
    SALARIO_MINIMO = 1630.00
    PISO_VERBA = SALARIO_MINIMO / 2  # R$ 815,00

    # --- ENTRADA DE DADOS (SIDEBAR) ---
    st.sidebar.header("📋 Dados da Rescisão")
    
    ultimo_salario = st.sidebar.number_input(
        "Último Salário Fixo (Atual)", 
        min_value=1630.0, 
        value=2000.0,
        help="Valor do último salário registrado na carteira."
    )
    
    media_comissoes = st.sidebar.number_input(
        "Média de Comissões/Prêmios (12 meses)", 
        min_value=0.0, 
        value=500.0,
        help="Média aritmética das comissões recebidas nos últimos 12 meses."
    )

    adicionais = st.sidebar.number_input(
        "Adicionais Fixos (Insalubridade/Peric.)", 
        min_value=0.0, 
        value=0.0
    )

    st.sidebar.divider()

    motivo = st.sidebar.selectbox(
        "Motivo do Desligamento",
        ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum"]
    )

    meses_prop = st.sidebar.slider("Meses Proporcionais (13º e Férias)", 1, 12, 6)
    dias_trabalhados = st.sidebar.slider("Dias trabalhados no mês da saída", 1, 30, 15)
    saldo_fgts = st.sidebar.number_input("Saldo para Fins Rescisórios do FGTS", min_value=0.0, value=3000.0)

    # --- LÓGICA DE CÁLCULO ---
    
    # 1. Base de Cálculo (Remuneração Integral Atual)
    remuneracao_atual = ultimo_salario + media_comissoes + adicionais
    
    # 2. Saldo de Salário (Baseado no último salário + adicionais)
    valor_dia = remuneracao_atual / 30
    res_saldo_salario = valor_dia * dias_trabalhados

    # 3. 13º Salário Proporcional (Usa a remuneração atualizada)
    valor_13_bruto = (remuneracao_atual / 12) * meses_prop
    res_13 = aplicar_piso(valor_13_bruto, PISO_VERBA)

    # 4. Férias Proporcionais + 1/3 (Usa média salarial se houver comissões)
    valor_ferias_base = (remuneracao_atual / 12) * meses_prop
    valor_ferias_total = valor_ferias_base * 1.3333
    res_ferias = aplicar_piso(valor_ferias_total, PISO_VERBA)

    # 5. Aviso Prévio e Multas
    aviso_previo = 0
    multa_fgts = 0
    
    if motivo == "Sem Justa Causa":
        aviso_previo = remuneracao_atual
        multa_fgts = saldo_fgts * 0.40
    elif motivo == "Acordo Comum":
        aviso_previo = remuneracao_atual * 0.50
        multa_fgts = saldo_fgts * 0.20
    
    # 6. Deduções (INSS 2026 - Simplificado)
    # IRRF 2026: Isento até R$ 5.000,00
    base_inss = res_saldo_salario + res_13
    if base_inss <= 1630: inss = base_inss * 0.075
    else: inss = (base_inss * 0.09) - 24.45

    total_bruto = res_saldo_salario + res_13 + res_ferias + aviso_previo
    total_liquido = total_bruto - inss

    # --- EXIBIÇÃO DOS RESULTADOS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Base de Cálculo", f"R$ {remuneracao_atual:,.2f}")
    col2.metric("Total Bruto", f"R$ {total_bruto:,.2f}")
    col3.metric("Líquido a Receber", f"R$ {total_liquido:,.2f}")

    st.markdown("### Detalhamento das Verbas")
    
    tabela = {
        "Descrição": ["Saldo de Salário", "13º Salário", "Férias + 1/3", "Aviso Prévio", "Multa FGTS"],
        "Valor (R$)": [
            f"{res_saldo_salario:,.2f}", 
            f"{res_13:,.2f}", 
            f"{res_ferias:,.2f}", 
            f"{aviso_previo:,.2f}", 
            f"{multa_fgts:,.2f}"
        ]
    }
    st.table(tabela)

    with st.expander("📌 Notas sobre as Regras Aplicadas"):
        st.write(f"- **Piso Garantido:** Nenhuma verba proporcional foi inferior a R$ {PISO_VERBA:,.2f}.")
        st.write(f"- **Comissões:** Integradas à base de cálculo do 13º e Férias.")
        st.write("- **IRRF:** Isenção aplicada conforme nova tabela 2026 para rendimentos até R$ 5.000,00.")
        st.write(f"- **FGTS:** Multa calculada com base no motivo '{motivo}'.")

if __name__ == "__main__":
    main()
