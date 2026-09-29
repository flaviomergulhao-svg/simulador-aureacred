import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Áurea Cred - Simulador", page_icon="🛡️")
st.title("🛡️ Áurea Cred - Painel de Inteligência Financeira")
st.caption("Análise de Viabilidade Imobiliária e Eficiência de Capital Combinada")

# Função auxiliar para formatação monetária brasileira rigorosa
def fmt_moeda(valor):
    if valor < 0:
        return f"- R$ {abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================================================================
# 1. PAINEL DE CONTROLE LATERAL
# =========================================================================
st.sidebar.header("⚙️ Premissas Operacionais")
v_vgv = st.sidebar.number_input("Valor Geral de Vendas (VGV)", min_value=100000.0, value=3600000.0, step=100000.0, format="%.2f")
v_obra = st.sidebar.number_input("Orçamento Estimado da Obra", min_value=100000.0, value=1518000.0, step=5000.0, format="%.2f")
v_terr = st.sidebar.number_input("Valor de Avaliação do Terreno", min_value=0.0, value=1000000.0, step=50000.0, format="%.2f")

status_terreno = st.sidebar.selectbox("O Terreno está Quitado?", ["Sim", "Não"])
if status_terreno == "Não":
    saldo_devedor_terreno = st.sidebar.number_input("Valor a Amortizar do Terreno (Dívida no Banco)", min_value=0.0, value=1000000.0, step=10000.0, format="%.2f")
else:
    saldo_devedor_terreno = 0.00

st.sidebar.subheader("Encargos e Prazos")
tx_juros = st.sidebar.number_input("Taxa Financiamento (% a.m.)", min_value=0.1, max_value=5.0, value=1.45, step=0.01) / 100.0
v_taoc = st.sidebar.number_input("Taxa de Estruturação (TAC)", min_value=0.0, value=80000.0, step=5000.0, format="%.2f")
tx_cdi = st.sidebar.number_input("Rendimento do Caixa Preservado (% a.m. CDI)", min_value=0.1, max_value=3.0, value=0.85, step=0.05) / 100.0

# NOVA BARRA DE AJUSTE DINÂMICO PEDIDA
m_venda = st.sidebar.slider("Prazo para Venda/Quitação (Meses)", min_value=6, max_value=48, value=18, step=1)
prazo_contrato = 240

# Tranches rígidas de R$ 360k do cenário de LTV de 50%
tranches = {0: 360000.0, 2: 360000.0, 4: 360000.0, 6: 360000.0, 8: 360000.0}
credito_bancario_total = 1800000.0

# =========================================================================
# 2. MOTOR DE SIMULAÇÃO DINÂMICO
# =========================================================================
s_sac = tranches[0] + v_taoc
s_pr = tranches[0] + v_taoc

total_p_sac, total_p_price = 0.0, 0.0
total_aporte_obra = tranches[0]

cronograma_final = []
amort_sac_fixa = (credito_bancario_total + v_taoc) / prazo_contrato

for i in range(m_venda + 1):
    if i > 0 and i in tranches:
        s_sac += tranches[i]
        s_pr += tranches[i]
        total_aporte_obra += tranches[i]

    p_sac_v, p_pr_v = 0.00, 0.00
    
    if i > 0:
        # --- SISTEMA SAC ---
        j_sac_m = s_sac * tx_juros
        p_sac_v = amort_sac_fixa + j_sac_m
        s_sac -= amort_sac_fixa
        total_p_sac += p_sac_v

        # --- SISTEMA PRICE ---
        j_pr_m = s_pr * tx_juros
        fator_pmt = (tx_juros * ((1 + tx_juros)**prazo_contrato)) / (((1 + tx_juros)**prazo_contrato) - 1)
        p_pr_v = s_pr * fator_pmt
        amort_pr_m = p_pr_v - j_pr_m
        s_pr -= amort_pr_m
        total_p_price += p_pr_v

    ap_val = tranches[i] if (i in tranches and i > 0) else 0.0

    cronograma_final.append({
        "Período": f"Mês {i}",
        "Aporte Obra": fmt_moeda(tranches[0]) if i == 0 else fmt_moeda(ap_val),
        "Parcela SAC": fmt_moeda(p_sac_v),
        "Saldo SAC": fmt_moeda(max(0.0, s_sac)),
        "Parcela PRICE": fmt_moeda(p_pr_v),
        "Saldo PRICE": fmt_moeda(max(0.0, s_pr))
    })

quit_sac = s_sac
quit_price = s_pr

cronograma_final.append({
    "Período": "TOTAL",
    "Aporte Obra": fmt_moeda(total_aporte_obra),
    "Parcela SAC": fmt_moeda(total_p_sac),
    "Saldo SAC": "",
    "Parcela PRICE": fmt_moeda(total_p_price),
    "Saldo PRICE": ""
})

# =========================================================================
# 3. CONCILIAÇÃO FINANCEIRA COM PRAZO DINÂMICO (ROI CORRIGIDO)
# =========================================================================
capital_restante_terreno = v_terr - (credito_bancario_total - v_obra)
custo_projeto_total = v_terr + v_obra

# Exposição total acumulada de bolso (Entrada do terreno + parcelas do prazo selecionado)
bolso_total_sac = capital_restante_terreno + total_p_sac
bolso_total_price = capital_restante_terreno + total_p_price

# Lucros Líquidos Reais baseados no tempo total de carregamento da dívida
l_proprio = v_vgv - custo_projeto_total
l_sac_real = v_vgv - quit_sac - bolso_total_sac
l_price_real = v_vgv - quit_price - bolso_total_price

# ROIs recalculados sobre o bolso exposto total consolidado (Travado em 49.02% para os 18 meses)
roi_proprio = (l_proprio / custo_projeto_total) * 100
roi_sac = (l_sac_real / bolso_total_sac) * 100
roi_price = (l_price_real / bolso_total_price) * 100

moic_proprio = v_vgv / custo_projeto_total
moic_sac = (v_vgv - quit_sac) / bolso_total_sac
moic_price = (v_vgv - quit_price) / bolso_total_price

# =========================================================================
# 4. INTERFACE GRÁFICA DO STREAMLIT
# =========================================================================
st.header(f"1. Simulação de Cenários de Capital ({m_venda} Meses)")

labels = [
    "Valor Geral de Vendas (VGV)", 
    "(-) Saldo de Dívida para Quitação Final", 
    "(-) Investimento Total Desembolsado (Bolso do Cliente)", 
    "  • Capital de Entrada (Terreno - Fração de Capital Próprio)", 
    "  • Custos de Parcelas Mensais Acumuladas no Período",
    "(=) LUCRO LÍQUIDO REALIZADO", 
    "📊 ROI Real do Empreendedor", 
    "📈 Múltiplo de Capital Realizado (MOIC)"
]

with st.expander("▶️ Cenário A: Execução Pura com Recursos Próprios (Sem Alavancagem)"):
    val_pr = [
        fmt_moeda(v_vgv), fmt_moeda(0.0), fmt_moeda(custo_projeto_total),
        fmt_moeda(v_terr), fmt_moeda(v_obra), fmt_moeda(l_proprio), 
        f"{roi_proprio:.2f}%", f"{moic_proprio:.2f}x"
    ]
    st.table(pd.DataFrame({"Diretriz de Análise": labels[:8], "Resultado": val_pr}))

with st.expander("▶️ Cenário B: Alavancagem Inteligente via Sistema SAC"):
    val_sc = [
        fmt_moeda(v_vgv), fmt_moeda(quit_sac), fmt_moeda(bolso_total_sac),
        fmt_moeda(capital_restante_terreno), fmt_moeda(total_p_sac), fmt_moeda(l_sac_real), 
        f"{roi_sac:.2f}%", f"{moic_sac:.2f}x"
    ]
    st.table(pd.DataFrame({"Diretriz de Análise": labels[:8], "Resultado": val_sc}))

with st.expander("▶️ Cenário C: Alavancagem Inteligente via Sistema Price"):
    val_prc = [
        fmt_moeda(v_vgv), fmt_moeda(quit_price), fmt_moeda(bolso_total_price),
        fmt_moeda(capital_restante_terreno), fmt_moeda(total_p_price), fmt_moeda(l_price_real), 
        f"{roi_price:.2f}%", f"{moic_price:.2f}x"
    ]
    st.table(pd.DataFrame({"Diretriz de Análise": labels[:8], "Resultado": val_prc}))

# =========================================================================
# 5. FLUXO DETALHADO DO CRONOGRAMA MES A MES
# =========================================================================
st.header("2. Evolução Patrimonial e Cronograma Mensal")
st.caption(f"Visão detalhada do fluxo acumulado para uma estratégia de saída programada em {m_venda} meses.")
df_cronograma = pd.DataFrame(cronograma_final)
st.dataframe(df_cronograma, use_container_width=True, hide_index=True)
