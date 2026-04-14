import math

def calcular_rescisao(salario_base, meses_trabalhados, dias_trabalhados_mes, motivo, saldo_fgts):
    """
    Calcula as verbas rescisórias básicas para 2026.
    motivo: 'sem_justa_causa', 'pedido_demissao', 'acordo'
    """
    
    # Parâmetros 2026
    SALARIO_MINIMO = 1630.00
    
    # 1. Saldo de Salário
    saldo_salario = (salario_base / 30) * dias_trabalhados_mes
    
    # 2. 13º Salário Proporcional (Meses trabalhados no ano atual)
    # Consideramos 'meses_trabalhados' como o acumulado do ano para fins de simplificação
    decimo_terceiro = (salario_base / 12) * meses_trabalhados
    
    # 3. Férias Proporcionais + 1/3 Constitucional
    ferias_prop = (salario_base / 12) * meses_trabalhados
    terco_ferias = ferias_prop / 3
    total_ferias = ferias_prop + terco_ferias
    
    # 4. Aviso Prévio (Simplificado: 30 dias)
    aviso_previo = 0
    multa_fgts = 0
    saque_fgts_permitido = 0
    
    if motivo == 'sem_justa_causa':
        aviso_previo = salario_base
        multa_fgts = saldo_fgts * 0.40
        saque_fgts_permitido = saldo_fgts + multa_fgts
        
    elif motivo == 'acordo':
        # Regras de Acordo (Art. 484-A CLT)
        aviso_previo = salario_base * 0.50 # 50% se indenizado
        multa_fgts = saldo_fgts * 0.20
        saque_fgts_permitido = saldo_fgts * 0.80
        
    elif motivo == 'pedido_demissao':
        aviso_previo = 0 # Empregado paga ou trabalha (não recebe)
        multa_fgts = 0
        saque_fgts_permitido = 0

    # 5. Deduções Simplicadas (INSS 2026)
    # Nota: Em 2026, a isenção de IRRF foi ampliada para quem ganha até R$ 5.000,00
    inss = calcular_inss_2026(saldo_salario + decimo_terceiro)
    
    total_bruto = saldo_salario + decimo_terceiro + total_ferias + aviso_previo
    total_liquido = total_bruto - inss

    return {
        "Saldo Salário": round(saldo_salario, 2),
        "13º Proporcional": round(decimo_terceiro, 2),
        "Férias + 1/3": round(total_ferias, 2),
        "Aviso Prévio": round(aviso_previo, 2),
        "Multa FGTS (40%/20%)": round(multa_fgts, 2),
        "Total Bruto": round(total_bruto, 2),
        "Total Líquido": round(total_liquido, 2),
        "FGTS Saque Estimado": round(saque_fgts_permitido, 2)
    }

def calcular_inss_2026(base):
    # Tabela Progressiva Estimada 2026
    if base <= 1630.00: return base * 0.075
    elif base <= 2866.70: return (base * 0.09) - 24.45
    elif base <= 4300.00: return (base * 0.12) - 110.45
    else: return (base * 0.14) - 196.45

# Exemplo de Uso:
resumo = calcular_rescisao(3000.00, 6, 15, 'sem_justa_causa', 5000.00)
for verba, valor in resumo.items():
    print(f"{verba}: R$ {valor}")