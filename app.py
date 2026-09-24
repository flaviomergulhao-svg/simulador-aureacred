import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Áurea Cred - Simulador", page_icon="🛡️")
st.title("🛡️ Áurea Cred - Simulador de Eficiência de Capital")
st.caption("Modelagem Financeira Avançada de Alavancagem Concomitante Progressiva")

# 1. PAINEL DE CONTROLE LATERAL (INPUTS)
st.sidebar.header("⚙️ Premissas Operacionais")
v_vgv = st.sidebar.number_input("Valor Geral de Vendas (VGV)", min_value=100000.0, value=3000000.0, step=100000.0, format="%.2f")
v_obra = st.sidebar.number_input("Orçamento Estimado da Obra", min_value=100000.0, value=1500000.0, step=50000.0, format="%.2f")
v_terr = st.sidebar.number_input("Aporte de Terreno Próprio", min_value=0.0, value=500000.0, step=50000.0, format="%.2f")
m_venda = st.sidebar.slider("Prazo Estimado de Venda (Meses)", min_value=6, max_value=36, value=18, step=1)

st.sidebar.subheader("Encargos e Taxas")
tx_juros = st.sidebar.number_input("Taxa Financiamento (% a.m.)", min_value=0.1, max_value=5.0, value=1.40, step=0.05) / 100.0
v_taoc = st.sidebar.number_input("Taxa de Estruturação (TAOC Fixa)", min_value=0.0, value=138646.07, step=5000.0, format="%.2f")
tx_cdi = st.sidebar.number_input("Rendimento do Caixa Preservado (% a.m. CDI)", min_value=0.1, max_value=3.0, value=0.85, step=0.05) / 100.0

# 2. MOTOR MATEMÁTICO REAL MÊS A MÊS (PRICE E SAC)
credito_bancario = v_obra
s_sac = (credito_bancario / 6) + v_taoc
s_pr = (credito_bancario / 6) + v_taoc

total_p_sac, total_p_price = 0.0, 0.0
ganho_cdi_sac, ganho_cdi_price = 0.0, 0.0

cronograma_data = []

for i in range(m_venda + 1):
    ap_val = (credito_bancario / 6) if (i < 12 and i % 2 == 0 and i > 0) else 0.00
    if i > 0:
        s_sac += ap_val
        s_pr += ap_val

    if i == 0:
        p_sac_v, p_pr_v = 0.00, 0.00
    else:
        # SAC
        j_sac_m = s_sac * tx_juros
        amort_sac_m = s_sac / 240
        p_sac_v = amort_sac_m + j_sac_m
        s_sac -= amort_sac_m

        # PRICE
        j_pr_m = s_pr * tx_juros
        fator_pmt = (tx_juros * ((1 + tx_juros)**240)) / (((1 + tx_juros)**240) - 1)
        p_pr_v = s_pr * fator_pmt
        s_pr -= (p_pr_v - j_pr_m)

    if i <= m_venda:
        if i > 0:
            total_p_sac += p_sac_v
            total_p_price += p_pr_v
            
            caixa_pres_sac = (v_obra / m_venda) * i - total_p_sac
            caixa_pres_prc = (v_obra / m_venda) * i - total_p_price
            if caixa_pres_sac > 0: ganho_cdi_sac += caixa_pres_sac * tx_cdi
            if caixa_pres_prc > 0: ganho_cdi_price += caixa_pres_prc * tx_cdi

        txt_ap = f"R$ {(credito_bancario / 6) if i==0 else ap_val:,.2f}"
        cronograma_data.append({
            "Período": f"Mês {i}",
            "Aporte Obra": txt_ap,
            "Parcela SAC": f"R$ {p_sac_v:,.2f}",
            "Saldo SAC": f"R$ {s_sac:,.2f}",
            "Parcela PRICE": f"R$ {p_pr_v:,.2f}",
            "Saldo PRICE": f"R$ {s_pr:,.2f}"
        })

# Cálculos Consolidados de Indicadores
invest_bolso_proprio = v_terr + v_obra
invest_bolso_sac = v_terr + total_p_sac
invest_bolso_price = v_terr + total_p_price

l_proprio = v_vgv - invest_bolso_proprio
l_sac_tijolo = (v_vgv - s_sac) - invest_bolso_sac
l_price_tijolo = (v_vgv - s_pr) - invest_bolso_price

l_sac_total = l_sac_tijolo + ganho_cdi_sac
l_price_total = l_price_tijolo + ganho_cdi_price

moic_proprio = v_vgv / invest_bolso_proprio
moic_sac = (v_vgv - s_sac + ganho_cdi_sac) / invest_bolso_sac
moic_price = (v_vgv - s_pr + ganho_cdi_price) / invest_bolso_price

# 3. INTERFACE GRÁFICA INTERATIVA (TABS)
tab1, tab2 = st.tabs(["📊 Mesa de Eficiência de Capital", "🧮 Cronograma Mês a Mês Automatizado"])

with tab1:
    st.subheader("Análise Comparativa de Indicadores de Retorno (Mesa de Eficiência)")
    
    df_resumo = pd.DataFrame({
        "Estrutura de Análise de Capital": [
            "Valor de Venda (VGV)", "(-) Quitação da Dívida de Saída", "(=) Receita Líquida pós-Quitação",
            "(-) Investimento Real do Bolso", "   • Aporte de Terreno Próprio", "   • Desembolso de Parcelas (Caixa)",
            "(=) LUCRO OPERACIONAL DO TIJOLO", "   • ROI Operacional do Empreendimento", "   • Rendimento Mensal do Empreendimento",
            "(+) RENDIMENTO DO CAPITAL PRESERVADO (CDI)", "   • ROI Adicional Gerado pelo CDI", "   • Rendimento Mensal Adicional (CDI)",
            "(=) BENEFÍCIO FINANCEIRO COMBINADO", "Múltiplo de Capital Combinado (MOIC)", "🔥 Rendimento Mensal Combinado Total"
        ],
        "Cenário A: Próprio": [
            f"R$ {v_vgv:,.2f}", "R$ 0.00", f"R$ {v_vgv:,.2f}", f"- R$ {invest_bolso_proprio:,.2f}", f"R$ {v_terr:,.2f}", f"R$ {v_obra:,.2f}",
            f"R$ {l_proprio:,.2f}", f"{(l_proprio/invest_bolso_proprio)*100:.2f}%", f"{((l_proprio/invest_bolso_proprio)*100)/m_venda:.2f}%/mês",
            "R$ 0.00", "0.00%", "0.00%/mês", f"R$ {l_proprio:,.2f}", f"{moic_proprio:.2f}x", f"{((l_proprio/invest_bolso_proprio)*100)/m_venda:.2f}%/mês"
        ],
        "Cenário B: SAC": [
            f"R$ {v_vgv:,.2f}", f"- R$ {s_sac:,.2f}", f"R$ {(v_vgv - s_sac):,.2f}", f"- R$ {invest_bolso_sac:,.2f}", f"R$ {v_terr:,.2f}", f"R$ {total_p_sac:,.2f}",
            f"R$ {l_sac_tijolo:,.2f}", f"{(l_sac_tijolo/invest_bolso_sac)*100:.2f}%", f"{((l_sac_tijolo/invest_bolso_sac)*100)/m_venda:.2f}%/mês",
            f"R$ {ganho_cdi_sac:,.2f}", f"{(ganho_cdi_sac/invest_bolso_sac)*100:.2f}%", f"{(ganho_cdi_sac/invest_bolso_sac*100)/m_venda:.2f}%/mês", f"R$ {l_sac_total:,.2f}", f"{moic_sac:.2f}x", f"{(l_sac_total/invest_bolso_sac*100)/m_venda:.2f}%/mês"
        ],
        "Cenário C: PRICE": [
            f"R$ {v_vgv:,.2f}", f"- R$ {s_pr:,.2f}", f"R$ {(v_vgv - s_pr):,.2f}", f"- R$ {invest_bolso_price:,.2f}", f"R$ {v_terr:,.2f}", f"R$ {total_p_price:,.2f}",
            f"R$ {l_price_tijolo:,.2f}", f"{(l_price_tijolo/invest_bolso_price)*100:.2f}%", f"{((l_price_tijolo/invest_bolso_price)*100)/m_venda:.2f}%/mês",
            f"R$ {ganho_cdi_price:,.2f}", f"{(ganho_cdi_price/invest_bolso_price)*100:.2f}%", f"{(ganho_cdi_price/invest_bolso_price*100)/m_venda:.2f}%/mês", f"R$ {l_price_total:,.2f}", f"{moic_price:.2f}x", f"{(l_price_total/invest_bolso_price*100)/m_venda:.2f}%/mês"
        ]
    })
    st.table(df_resumo)

with tab2:
    st.subheader("Evolução Mensal Dinâmica de Amortização e Saldos")
    df_cronograma = pd.DataFrame(cronograma_data)
    st.dataframe(df_cronograma, height=600, use_container_width=True)
