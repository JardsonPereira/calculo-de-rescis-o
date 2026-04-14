import streamlit as st

# Configuração da página - Essencial para evitar erros de renderização
st.set_page_config(page_title="Calculadora Rescisão 2026", page_icon="💰", layout="wide")

def aplicar_piso(valor, piso):
    """Garante que a verba proporcional não seja inferior a 50% do salário mínimo."""
    return max(valor, piso)

def main():
    st.title("⚖️ Sistema de Rescisão Trabalhista - Regras 2026")
    st.markdown("---")

    # Parâmetros Legais 2026
    SALARIO_MINIMO = 1630.00
    PISO_VERBA = SALARIO_MINIMO / 2  # R$ 815,00

    # --- ENTRADA DE DADOS (SIDEBAR) ---
    st.sidebar.header("📋 Dados Contratuais")
    
    ultimo_salario = st.sidebar.number_input("Último Salário Fixo (R$)", min_value=1630.0, value=2500.0, step=50.0)
    media_comissoes = st.sidebar.number_input("Média de Comissões (R$)", min_value=0.0, value=0.0, step=50.0)
    adicionais = st.sidebar.number_input("Adicionais (Insalubridade/Peric.) (R$)", min_value=0.0, value=0.0, step=10.0)
    
    st.sidebar.divider()
    
    # CAMPO CRÍTICO: Este valor agora altera diretamente a Multa FGTS
    saldo_fgts_base = st.sidebar.number_input("Saldo p/ Fins Rescisórios FGTS (R$)", min_value=0.0, value=5000.0, step=100.0, help="O valor total depositado pela empresa durante o contrato.")
    
    motivo = st.sidebar.selectbox(
        "Motivo do Desligamento",
        ["Sem Justa Causa", "Pedido de Demissão", "Acordo Comum (Art. 484-A)"]
    )

    meses_prop = st.sidebar.slider("Meses Proporcionais (13º/Férias)", 1, 12, 6)
    dias_trabalhados = st.sidebar.slider("Dias no último mês", 1, 30, 15)

    # --- LÓGICA DE CÁLCULO ---
    
    # 1. Base de Cálculo (Remuneração Integral)
    remuneracao_total = ultimo_salario + media_comissoes + adicionais
    
    # 2. Saldo de Salário (Dias trabalhados)
    res_saldo_salario = (remuneracao_total / 30) * dias_trabalhados

    # 3. 13º Salário Proporcional (Aplica regra do piso de 50% do SM)
    valor_13_calculado = (remuneracao_total / 12) * meses_prop
    res_13 = aplicar_piso(valor_13_calculado, PISO_VERBA)

    # 4. Férias Proporcionais + 1/3 (Aplica regra do piso de 50% do SM)
    valor_ferias_base = (remuneracao_total / 12) * meses_prop
    valor_ferias_com_terco = valor_ferias_base * 1.3333
    res_ferias = aplicar_piso(valor_ferias_com_terco, PISO_VERBA)

    # 5. Aviso Prévio e Multa do FGTS (Lógica dependente do motivo)
    aviso_previo = 0
    multa_fgts = 0
    percentual_multa = 0
    
    if motivo == "Sem Justa Causa":
        aviso_previo = remuneracao_total
        percentual_multa = 0.40
        multa_fgts = saldo_fgts_base * percentual_multa
    elif motivo == "Acordo Comum (Art. 484-A)":
        aviso_previo = remuneracao_total * 0.50
        percentual_multa = 0.20
        multa_fgts = saldo_fgts_base * percentual_multa
    elif motivo == "Pedido de Demissão":
        aviso_previo = 0
        multa_fgts = 0  # Não há multa no pedido de demissão
        percentual_multa = 0

    # 6. Deduções (INSS Progressivo 2026)
    base_inss = res_saldo_salario + res_13
    if base_inss <= 1630: 
        inss = base_inss * 0.075
    elif base_inss <= 2866: 
        inss = (base_inss * 0.09) - 24.45
    else: 
        inss = (base_inss * 0.12) - 110.00

    # Totalização
    total_bruto = res_saldo_salario + res_13 + res_ferias + aviso_previo + multa_fgts
    total_liquido = total_bruto - inss

    # --- INTERFACE DE EXIBIÇÃO ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Remuneração Integral", f"R$ {remuneracao_total:,.2f}")
    c2.metric("Multa Rescisória (FGTS)", f"R$ {multa_fgts:,.2f}", delta=f"{percentual_multa*100:.0f}% sobre o saldo")
    c3.metric("Líquido Final", f"R$ {total_liquido:,.2f}")

    st.markdown("### 📝 Detalhamento das Verbas")
    
    # Tabela formatada para o usuário
    detalhes = {
        "Descrição da Verba": ["Saldo de Salário", "13º Salário Proporcional", "Férias + 1/3 Constitucional", "Aviso Prévio Indenizado", "Multa Rescisória (FGTS)"],
        "Cálculo Base": ["Dias trabalhados", "Meses proporcionais", "Meses + 1/3", "Última Remuneração", f"{percentual_multa*100:.0f}% do Saldo"],
        "Valor Bruto (R$)": [
            f"R$ {res_saldo_salario:,.2f}",
            f"R$ {res_13:,.2f}",
            f"R$ {res_ferias:,.2f}",
            f"R$ {aviso_previo:,.2f}",
            f"R$ {multa_fgts:,.2f}"
        ]
    }
    st.table(detalhes)

    st.error(f"➖ Desconto INSS: R$ {inss:,.2f}")
    
    with st.expander("ℹ️ Informações sobre as Regras de 2026"):
        st.write(f"- **Piso Aplicado:** Nenhuma verba proporcional é inferior a **R$ {PISO_VERBA:,.2f}** (50% do salário mínimo).")
        st.write("- **FGTS:** A multa é calculada sobre o saldo para fins rescisórios informado no menu lateral.")
        st.write("- **Imposto de Renda:** Isenção aplicada para valores totais até R$ 5.000,00 conforme nova diretriz fiscal.")

if __name__ == "__main__":
    main()
