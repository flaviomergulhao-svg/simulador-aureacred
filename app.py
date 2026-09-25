import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Áurea Cred - Simulador", page_icon="🛡️")
st.title("🛡️ Áurea Cred - Simulador de Eficiência de Capital")
st.caption("Modelagem Financeira Avançada de Alavancagem Concomitante Progressiva")

# Função auxiliar para formatação monetária brasileira rigorosa
def fmt_moeda(valor):
    if valor < 0:
        return f"- R$ {abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================================================================
# 1. PAINEL DE CONTROLE LATERAL (INPUTS)
# =========================================================================
st.sidebar.header("⚙️ Premissas Operacionais")
v_vgv = st.sidebar.number_input("Valor Geral de Vendas (VGV)", min_value=100000.0, value=3600000.0, step=100000.0, format="%.2f")
v_obra = st.sidebar.number_input("Orçamento Estimado da Obra", min_value=100000.0, value=1518000.0, step=5000.0, format="%.2f")
v_terr = st.sidebar.number_input("Valor de Avaliação do Terreno", min_value=0.0, value=1000000.0, step=50000.0, format="%.2f")

status_terreno = st.sidebar.selectbox("O Terreno está Quitado?", ["Sim", "Não"])
if status_terreno == "Não":
    saldo_devedor_terreno = st.sidebar.number_input("Valor a Amortizar do Terreno (Dívida no Banco)", min_value=0.0, value=v_terr, step=10000.0, format="%.2f")
else:
    saldo_devedor_terreno = 0.00

# Slider dinâmico amarrado ao limite estrito de 50% do VGV
teto_maximo_ltv = v_vgv * 0.50
credito_bancario = st.sidebar.slider(
    "Valor do Crédito Desejado (Limite 50% VGV)", 
    min_value=float(v_obra / 2), 
    max_value=float(teto_maximo_ltv), 
    value=float(teto_maximo_ltv), 
    step=10000.0,
    format="R$ %.2f"
)

m_venda = st.sidebar.slider("Prazo Estimado de Venda (Meses)", min_value=6, max_value=36, value=18, step=1)

st.sidebar.subheader("Encargos e Taxas")
tx_juros = st.sidebar.number_input("Taxa Financiamento (% a.m.)", min_value=0.1, max_value=5.0, value=1.40, step=0.05) / 100.0
v_taoc = st.sidebar.number_input("Taxa de Estruturação (TAOC Fixa)", min_value=0.0, value=138646.07, step=5000.0, format="%.2f")
tx_cdi = st.sidebar.number_input("Rendimento do Caixa Preservado (% a.m. CDI)", min_value=0.1, max_value=3.0, value=0.85, step=0.05) / 100.0

# =========================================================================
# 2. MOTOR DE ENGENHARIA FINANCEIRA RECALIBRADO (CAIXA REAL S/ DUPLICIDADE)
# =========================================================================
demanda_capital_total = saldo_devedor_terreno + v_obra

if demanda_capital_total > credito_bancario:
    recurso_proprio_comp = demanda_capital_total - credito_bancario
    sobra_caixa_giro = 0.00
else:
    recurso_proprio_comp = 0.00
    sobra_caixa_giro = credito_bancario - demanda_capital_total

# Engenharia do Terreno: quanto o cliente já tinha aportado de fato antes (recurso empacotado na terra)
capital_ja_pago_terreno = v_terr - saldo_devedor_terreno

# Crédito bancário remanescente direcionado para abater a dívida do terreno
credito_alocado_terreno = credito_bancario - v_obra if credito_bancario > v_obra else 0.00
if credito_alocado_terreno < 0:
    credito_alocado_terreno = 0.00

# Desembolso imediato na largada para zerar a aquisição: o valor que ele amortiza via contrapartida
desembolso_inicial_largada_terreno = recurso_proprio_comp if status_terreno == "Não" else 0.00

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
            
            # Ajuste dinâmico do Caixa Preservado no CDI (Obra teórica linear menos as parcelas pagas do bolso)
            caixa_pres_sac = (v_obra / m_venda) * i - total_p_sac + sobra_caixa_giro
            caixa_pres_prc = (v_obra / m_venda) * i - total_p_price + sobra_caixa_giro
            
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

# CONCILIAÇÃO EXATA DO BOLSO (Elimina a duplicidade do terreno)
invest_bolso_proprio = v_terr + v_obra
invest_bolso_sac = capital_ja_pago_terreno + total_p_sac + recurso_proprio_comp - sobra_caixa_giro
invest_bolso_price = capital_ja_pago_terreno + total_p_price + recurso_proprio_comp - sobra_caixa_giro

l_proprio = v_vgv - invest_bolso_proprio
l_sac_tijolo = (v_vgv - s_sac) - invest_bolso_sac
l_price_tijolo = (v_vgv - s_pr) - invest_bolso_price

l_sac_total = l_sac_tijolo + ganho_cdi_sac
l_price_total = l_price_tijolo + ganho_cdi_price

moic_proprio = v_vgv / invest_bolso_proprio
moic_sac = (v_vgv - s_sac + ganho_cdi_sac) / invest_bolso_sac if invest_bolso_sac > 0 else 0.0
moic_price = (v_vgv - s_pr + ganho_cdi_price) / invest_bolso_price if invest_bolso_price > 0 else 0.0

roi_cdi_sac_pct = (ganho_cdi_sac / invest_bolso_sac) * 100 if invest_bolso_sac > 0 else 0.0
roi_cdi_prc_pct = (ganho_cdi_price / invest_bolso_price) * 100 if invest_bolso_price > 0 else 0.0

# =========================================================================
# 3. INTERFACE GRÁFICA CORRIGIDA (SEM BULLETS VISUAIS E COM MÁSCARA MONETÁRIA)
# =========================================================================
tab1, tab2 = st.tabs(["📊 Mesa de Eficiência de Capital", "🧮 Cronograma Mês a Mês Automatizado"])

with tab1:
    st.subheader("Análise Comparativa de Indicadores de Retorno (Visão Consolidada)")
    
    df_resumo = pd.DataFrame({
        "Estrutura de Análise de Capital": [
            "Valor de Venda (VGV)", 
            "(-) Crédito Estruturado Selecionado", 
            "(-) Capital de Giro Injetado no Caixa", 
            "(-) Quitação da Dívida de Saída", 
            "(=) Receita Líquida pós-Quitação",
            "(-) Investimento Líquido do Bolso", 
            "  Capital de Terreno já Aportado (Passado)", 
            "  Contrapartida Inicial (Gargalo LTV)", 
            "  Desembolso de Parcelas (Caixa)",
            "(=) LUCRO OPERACIONAL DO TIJOLO", 
            "  ROI Operacional do Empreendimento", 
            "  Rendimento Mensal do Empreendimento",
            "(+) RENDIMENTO DO CAPITAL PRESERVADO (CDI)", 
            "  ROI Adicional Gerado pelo CDI", 
            "  Rendimento Mensal Adicional (CDI)",
            "(=) BENEFÍCIO FINANCEIRO COMBINADO", 
            "Múltiplo de Capital Combinado (MOIC)", 
            "🔥 Rendimento Mensal Combinado Total"
        ],
        "Cenário A: Próprio": [
            fmt_moeda(v_vgv), 
            fmt_moeda(0.0), 
            fmt_moeda(0.0), 
            fmt_moeda(0.0), 
            fmt_moeda(v_vgv), 
            fmt_moeda(invest_bolso_proprio), 
            fmt_moeda(v_terr), 
            fmt_moeda(0.0), 
            fmt_moeda(v_obra),
            fmt_moeda(l_proprio), 
            f"{(l_proprio/invest_bolso_proprio)*100:.2f}%", 
            f"{((l_proprio/invest_bolso_proprio)*100)/m_venda:.2f}%/mês",
            fmt_moeda(0.0), 
            "0.00%", 
            "0.00%/mês", 
            fmt_moeda(l_proprio), 
            f"{moic_proprio:.2f}x", 
            f"{((l_proprio/invest_bolso_proprio)*100)/m_venda:.2f}%/mês"
        ],
        "Cenário B: SAC": [
            fmt_moeda(v_vgv), 
            fmt_moeda(credito_bancario), 
            fmt_moeda(sobra_caixa_giro), 
            fmt_moeda(s_sac), 
            fmt_moeda(v_vgv - s_sac), 
            fmt_moeda(invest_bolso_sac), 
            fmt_moeda(capital_ja_pago_terreno), 
            fmt_moeda(recurso_proprio_comp), 
            fmt_moeda(total_p_sac),
            fmt_moeda(l_sac_tijolo), 
            f"{(l_sac_tijolo/invest_bolso_sac)*100:.2f}%" if invest_bolso_sac>0 else "0.00%", 
            f"{((l_sac_tijolo/invest_bolso_sac)*100)/m_venda:.2f}%/mês" if invest_bolso_sac>0 else "0.00%/mês",
            fmt_moeda(ganho_cdi_sac), 
            f"{roi_cdi_sac_pct:.2f}%", 
            f"{roi_cdi_sac_pct/m_venda:.2f}%/mês", 
            fmt_moeda(l_sac_total), 
            f"{moic_sac:.2f}x", 
            f"{(l_sac_total/invest_bolso_sac*100)/m_venda:.2f}%/mês" if invest_bolso_sac>0 else "0.00%/mês"
        ],
        "Cenário C: PRICE": [
            fmt_moeda(v_vgv), 
            fmt_moeda(credito_bancario), 
            fmt_moeda(sobra_caixa_giro), 
            fmt_moeda(s_pr), 
            fmt_moeda(v_vgv - s_pr), 
            fmt_moeda(invest_bolso_price), 
            fmt_moeda(capital_ja_pago_terreno), 
            fmt_moeda(recurso_proprio_comp), 
            fmt_moeda(total_p_price),
            fmt_moeda(l_price_tijolo), 
            f"{(l_price_tijolo/invest_bolso_price)*100:.2f}%" if invest_bolso_price>0 else "0.00%", 
            f"{((l_price_tijolo/invest_bolso_price)*100)/m_venda:.2f}%/mês" if invest_bolso_price>0 else "0.00%/mês",
