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

st.sidebar.subheader("Encargos e Taxas")
tx_juros = st.sidebar.number_input("Taxa Financiamento (% a.m.)", min_value=0.1, max_value=5.0, value=1.45, step=0.01) / 100.0
v_taoc = st.sidebar.number_input("Taxa de Estruturação (TAC)", min_value=0.0, value=80000.0, step=5000.0, format="%.2f")
tx_cdi = st.sidebar.number_input("Rendimento do Caixa Preservado (% a.m. CDI)", min_value=0.1, max_value=3.0, value=0.85, step=0.05) / 100.0

m_venda = 18 
prazo_contrato = 240

# Tranches rígidas de R$ 360k do cenário de LTV de 50%
tranches = {0: 360000.0, 2: 360000.0, 4: 360000.0, 6: 360000.0, 8: 360000.0}
credito_bancario_total = 1800000.0

# =========================================================================
# 2. MOTOR DE SIMULAÇÃO REESTRUTURADO E CORRIGIDO
# =========================================================================
# O saldo inicial no Mês 0 começa com a primeira tranche (liberada na largada) + TAC embutida
s_sac = tranches[0] + v_taoc
s_pr = tranches[0] + v_taoc

total_p_sac, total_p_price = 0.0, 0.0
total_aporte_obra = 0.0
ganho_cdi_sac, ganho_cdi_price = 0.0, 0.0

list_p_sac = []
list_p_price = []
cronograma_final = []

# Amortização linear fixa do sistema SAC sobre o contrato total estruturado
amort_sac_fixa = (credito_bancario_total + v_taoc) / prazo_contrato

for i in range(m_venda + 1):
    # Se houver nova tranche no mês (Mês 2, 4, 6, 8), adiciona ao saldo ANTES de rodar os juros
    if i > 0 and i in tranches:
        s_sac += tranches[i]
        s_pr += tranches[i]

    p_sac_v, p_pr_v = 0.00, 0.00
    
    if i > 0:
        # --- SISTEMA SAC ---
        j_sac_m = s_sac * tx_juros
        p_sac_v = amort_sac_fixa + j_sac_m
        s_sac -= amort_sac_fixa  # O saldo devedor cai de forma constante

        # --- SISTEMA PRICE ---
        j_pr_m = s_pr * tx_juros
        # Fator calculado sobre o prazo original para manter a consistência metodológica do plano comercial
        fator_pmt = (tx_juros * ((1 + tx_juros)**prazo_contrato)) / (((1 + tx_juros)**prazo_contrato) - 1)
        p_pr_v = s_pr * fator_pmt
        amort_pr_m = p_pr_v - j_pr_m
        s_pr -= amort_pr_m  # O saldo devedor cai conforme a folha de amortização Price

        # Acumuladores e Memória
        total_p_sac += p_sac_v
        total_p_price += p_pr_v
        list_p_sac.append(p_sac_v)
        list_p_price.append(p_pr_v)
        
        # Juros do Caixa Livre (CDI)
        caixa_pres_sac = (v_obra / m_venda) * i - sum(list_p_sac) + (credito_bancario_total - v_obra)
        caixa_pres_prc = (v_obra / m_venda) * i - sum(list_p_price) + (credito_bancario_total - v_obra)
        if status_terreno == "Não":
            caixa_pres_sac += (v_terr - saldo_devedor_terreno)
            caixa_pres_prc += (v_terr - saldo_devedor_terreno)
            
        if caixa_pres_sac > 0: ganho_cdi_sac += caixa_pres_sac * tx_cdi
        if caixa_pres_prc > 0: ganho_cdi_price += caixa_pres_prc * tx_cdi

    ap_val = tranches[i] if i in tranches else 0.0
    total_aporte_obra += ap_val

    cronograma_final.append({
        "Período": f"Mês {i}",
        "Aporte Obra": fmt_moeda(ap_val),
        "Parcela SAC": fmt_moeda(p_sac_v),
        "Saldo SAC": fmt_moeda(max(0.0, s_sac)),
        "Parcela PRICE": fmt_moeda(p_pr_v),
        "Saldo PRICE": fmt_moeda(max(0.0, s_pr))
    })

# O valor real de saída (quitação) no 18º mês é o saldo devedor residual exato
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
# 3. CONCILIAÇÃO DE CAIXA, LUCRO E ROI
# =========================================================================
capital_ja_pago_terreno = v_terr - saldo_devedor_terreno
sobra_caixa_giro = credito_bancario_total - (saldo_devedor_terreno + v_obra)

invest_bolso_proprio = v_terr + v_obra
invest_bolso_sac = capital_ja_pago_terreno + total_p_sac - (sobra_caixa_giro if sobra_caixa_giro > 0 else 0.0)
invest_bolso_price = capital_ja_pago_terreno + total_p_price - (sobra_caixa_giro if sobra_caixa_giro > 0 else 0.0)

l_proprio = v_vgv - invest_bolso_proprio
l_sac_tijolo = (v_vgv - quit_sac) - invest_bolso_sac
l_price_tijolo = (v_vgv - quit_price) - invest_bolso_price

l_sac_total = l_sac_tijolo + ganho_cdi_sac
l_price_total = l_price_tijolo + ganho_cdi_price

moic_proprio = v_vgv / invest_bolso_proprio
moic_sac = (v_vgv - quit_sac + ganho_cdi_sac) / invest_bolso_sac if invest_bolso_sac > 0 else 0.0
moic_price = (v_vgv - quit_price + ganho_cdi_price) / invest_bolso_price if invest_bolso_price > 0 else 0.0

# =========================================================================
# 4. INTERFACE GRÁFICA DO STREAMLIT
# =========================================================================
st.header("1. Simulação de Cenários de Capital")

labels = [
    "Valor Geral de Vendas (VGV)", 
    "(-) Dívida de Quitação de Saída (Mês 18)", 
    "(-) Investimento Líquido Injetado do Bolso Próprio", 
    "  • Capital do Terreno já Imobilizado", 
    "  • Desembolso de Parcelas Acumuladas",
    "(=) LUCRO OPERACIONAL LÍQUIDO", 
    "  • ROI Real do Empreendedor (s/ Capital Próprio)", 
    "  • Múltiplo de Capital Realizado (MOIC)",
    "(+) RENDIMENTO DO CAIXA PRESERVADO (CDI)", 
    "🔥 BENEFÍCIO FINANCEIRO COMBINADO TOTAL"
]

with st.expander("▶️ Cenário A: Execução Pura com Recursos Próprios (Sem Alavancagem)"):
    val_pr = [
        fmt_moeda(v_vgv), 
        fmt_moeda(0.0), 
        fmt_moeda(invest_bolso_proprio),
        fmt_moeda(v_terr), 
        fmt_moeda(v_obra), 
        fmt_moeda(l_proprio), 
        f"{(l_proprio / invest_bolso_proprio) * 100:.2f}%",
        f"{moic_proprio:.2f}x", 
        fmt_moeda(0.0), 
        fmt_moeda(l_proprio)
    ]
    st.table(pd.DataFrame({"Diretriz de Análise": labels, "Resultado": val_pr}))

with st.expander("▶️ Cenário B: Alavancagem Inteligente via Sistema SAC (Menor Saldo de Saída)"):
    val_sc = [
        fmt_moeda(v_vgv), 
        fmt_moeda(quit_sac), 
        fmt_moeda(invest_bolso_sac),
        fmt_moeda(capital_ja_pago_terreno), 
        fmt_moeda(total_p_sac), 
        fmt_moeda(l_sac_tijolo), 
        f"{(l_sac_tijolo / invest_bolso_sac) * 100:.2f}%",
        f"{moic_sac:.2f}x", 
        fmt_moeda(ganho_cdi_sac), 
        fmt_moeda(l_sac_total)
    ]
    st.table(pd.DataFrame({"Diretriz de Análise": labels, "Resultado": val_sc}))

with st.expander("▶️ Cenário C: Alavancagem Inteligente via Sistema Price (Parcelas Iniciais Leves)"):
    val_prc = [
        fmt_moeda(v_vgv), 
        fmt_moeda(quit_price), 
        fmt_moeda(invest_bolso_price),
        fmt_moeda(capital_ja_pago_terreno), 
        fmt_moeda(total_p_price), 
        fmt_moeda(l_price_tijolo), 
        f"{(l_price_tijolo / invest_bolso_price) * 100:.2f}%",
        f"{moic_price:.2f}x", 
        fmt_moeda(ganho_cdi_price), 
        fmt_moeda(l_price_total)
    ]
    st.table(pd.DataFrame({"Diretriz de Análise": labels, "Resultado": val_prc}))

# =========================================================================
# 5. FLUXO DETALHADO DO CRONOGRAMA MES A MES
# =========================================================================
st.header("2. Evolução Patrimonial e Cronograma Mensal")
st.caption("Visão detalhada do fluxo de aportes, prestações e amortização contínua do saldo devedor de saída.")
df_cronograma = pd.DataFrame(cronograma_final)
st.dataframe(df_cronograma, use_container_width=True, hide_index=True)
