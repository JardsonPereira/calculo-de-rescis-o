import streamlit as st

# Configuração da página (Deve ser o primeiro comando Streamlit)
st.set_page_config(page_title="Calculadora 2026", layout="centered")

def calcular_rescisao():
    st.title("⚖️ Calculadora Rescisória 2026")
    
    # Entradas
    salario = st.number_input("Salário Base (R$)", min_value=1630.0, step=100.0)
    meses = st.slider("Meses no ano", 1, 12, 6)
    motivo = st.selectbox("Motivo", ["Sem Justa Causa", "Pedido de Demissão"])

    # Cálculos Simples
    decimo_terceiro = (salario / 12) * meses
    ferias = decimo_terceiro * 1.33
    
    total = decimo_terceiro + ferias
    
    if motivo == "Sem Justa Causa":
        st.success(f"Total Estimado: R$ {total:,.2f}")
    else:
        st.info(f"Total Estimado: R$ {total:,.2f}")

# Execução do App
if __name__ == "__main__":
    calcular_rescisao()
