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
# 1. PAINEL DE CONTROLE LATERAL (INPUTS CONFORME SEU SCRIPT)
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

st.sidebar.subheader("Encargos e Taxas (Seu Código)")
tx_juros = st.sidebar.number_input("Taxa Financiamento (% a.m.)", min_value=0.1, max_value=5.0, value=1.45, step=0.01) / 100.0
v_taoc = st.sidebar.number_input("Taxa de Estruturação (TAC)", min_value=0.0, value=80000.0, step=5000.0, format="%.2f")
tx_cdi = st.sidebar.number_input("Rendimento do Caixa Preservado (% a.m. CDI)", min_value=0.1, max_value=3.0, value=0.85, step=0.05) / 100.0

m_venda = 18 
prazo_contrato = 240

# Tranches rígidas de R$ 360k do seu cenário de LTV de 50%
tranches = {0: 360000.0, 2: 360000.0, 4: 360000.0, 6: 360000.0, 8: 360000.0}
credito_bancario_total = 1800000.0

# =========================================================================
# 2. MOTOR DE SIMULAÇÃO REESTRUTURADO (SAC E PRICE CONCOMITANTES)
# =========================================================================
s_sac = (credito_bancario_total / 6) + v_taoc
s_pr = (credito_bancario_total / 6) + v_taoc

total_p_sac, total_p_price = 0.0, 0.0
total_aporte_obra = 0.0
ganho_cdi_sac, ganho_cdi_price = 0.0, 0.0

# Memória das parcelas para o custo de oportunidade
list_p_sac = []
list_p_price = []

# Nova lista unificada que guardará o cronograma sem erro de Syntax
cronograma_final = []

for i in range(m_venda + 1):
    ap_val = tranches[i] if i in tranches else 0.0
    if i > 0:
        s_sac += ap_val
        s_pr += ap_val

    p_sac_v, p_pr_v = 0.00, 0.00
    
    if i > 0:
        # SAC
        j_sac_m = s_sac * tx_juros
        amort_sac_m = s_sac / (prazo_contrato - i + 1)
        p_sac_v = amort_sac_m + j_sac_m
        s_sac -= amort_sac_m

        # PRICE
        j_pr_m = s_pr * tx_juros
        fator_pmt = (tx_juros * ((1 + tx_juros)**(prazo_contrato - i + 1))) / (((1 + tx_juros)**(prazo_contrato - i + 1)) - 1)
        p_pr_v = s_pr * fator_pmt
        s_pr -= (p_pr_v - j_pr_m)

        # Acumuladores
        total_p_sac += p_sac_v
        total_p_price += p_pr_v
        list_p_sac.append(p_sac_v)
        list_p_price.append(p_pr_v)
        total_aporte_obra += ap_val
        
        # Juros do Caixa Livre (CDI)
        caixa_pres_sac = (v_obra / m_venda) * i - sum(list_p_sac) + (credito_bancario_total - v_obra)
        caixa_pres_prc = (v_obra / m_venda) * i - sum(list_p_price) + (credito_bancario_total - v_obra)
        if status_terreno == "Não":
            caixa_pres_sac += (v_terr - saldo_devedor_terreno)
            caixa_pres_prc += (v_terr - saldo_devedor_terreno)
            
        if caixa_pres_sac > 0: ganho_cdi_sac += caixa_pres_sac * tx_cdi
        if caixa_pres_prc > 0: ganho_cdi_price += caixa_pres_prc * tx_cdi
    else:
        total_aporte_obra += (credito_bancario_total / 6)

    # Injeção direta linha por linha com strings formatadas como moeda
    cronograma_final.append({
        "Período": f"Mês {i}",
        "Aporte Obra": fmt_moeda(ap_val) if i > 0 else fmt_moeda(credito_bancario_total / 6),
        "Parcela SAC": fmt_moeda(p_sac_v),
        "Saldo SAC": fmt_moeda(s_sac) if i < m_venda else fmt_moeda(s_sac + amort_sac_m),
        "Parcela PRICE": fmt_moeda(p_pr_v),
        "Saldo PRICE": fmt_moeda(s_pr) if i < m_venda else fmt_moeda(s_pr + (p_pr_v - j_pr_m))
    })

# Captura exata do saldo de quitação antes de quebrar o loop no mês 18
quit_sac = s_sac + amort_sac_m
quit_price = s_pr + (p_pr_v - j_pr_m)

# Injeção segura da linha de totalizadores no rodapé da tabela
cronograma_final.append({
    "Período": "TOTAL",
    "Aporte Obra": fmt_moeda(total_aporte_obra),
    "Parcela SAC": fmt_moeda(total_p_sac),
    "Saldo SAC": "",
    "Parcela PRICE": fmt_moeda(total_p_price),
    "Saldo PRICE": ""
})

# Conciliação das premissas de bolso corporativo
capital_ja_pago_terreno = v_terr - saldo_devedor_terreno
sobra_caixa_giro = credito_bancario_total - (saldo_devedor_terreno + v_obra)

invest_bolso_proprio = v_terr + v_obra
invest_bolso_sac = capital_ja_pago_terreno + total_p_sac - sobra_caixa_giro if sobra_caixa_giro > 0 else capital_ja_pago_terreno + total_p_sac
invest_bolso_price = capital_ja_pago_terreno + total_p_price - sobra_caixa_giro if sobra_caixa_giro > 0 else capital_ja_pago_terreno + total_p_price

l_proprio = v_vgv - invest_bolso_proprio
l_sac_tijolo = (v_vgv - quit_sac) - invest_bolso_sac
l_price_tijolo = (v_vgv - quit_price) - invest_bolso_price

l_sac_total = l_sac_tijolo + ganho_cdi_sac
l_price_total = l_price_tijolo + ganho_cdi_price

moic_proprio = v_vgv / invest_bolso_proprio
moic_sac = (v_vgv - quit_sac + ganho_cdi_sac) / invest_bolso_sac if invest_bolso_sac > 0 else 0.0
moic_price = (v_vgv - quit_price + ganho_cdi_price) / invest_bolso_price if invest_bolso_price > 0 else 0.0

# =========================================================================
# 3. INTERFACE DE EXPANSORES COMPLETA (VISÃO CONTÍNUA)
# =========================================================================
st.header("1. Simulação de Cenários de Capital")

labels = [
    "Valor Geral de Vendas (VGV)", "(-) Crédito Estruturado Contratado (5 Tranches)", 
    "(-) Saldo Injetado como Capital de Giro", "(-) Dívida de Quitação (Mês 18)", 
    "(=) Receita Líquida pós-Quitação", "(-) Investimento Líquido Desembolsado do Bolso", 
    "  • Capital de Terreno já Pago (Passado)", "  • Desembolso de Parcelas Acumuladas (Obra)",
    "(=) LUCRO OPERACIONAL DO TIJOLO", "  • ROI Operacional do Empreendimento", "  • Rendimento Mensal do Empreendimento",
    "(+) RENDIMENTO DO CAPITAL PRESERVADO (CDI)", "  • ROI Adicional Gerado pelo CDI", 
    "(=) BENEFÍCIO FINANCEIRO COMBINADO", "Múltiplo de Capital Combinado (MOIC)", "🔥 Rendimento Mensal Combinado Total"
]

with st.expander("▶️ Cenário A: Execução Pura com Recursos Próprios (Sem Alavancagem)"):
    val_pr = [
        fmt_moeda(v_vgv), fmt_moeda(0.0), fmt_moeda(0.0), fmt_moeda(0.0), fmt_moeda(v_vgv), fmt_moeda(invest_bolso_proprio),
        fmt_moeda(v_terr), fmt_moeda(v_obra), fmt_moeda(l_proprio), f"{(l_proprio/invest_bolso_proprio)*100:.2f}%",
        f"{((l_proprio/invest_bolso_proprio)*100)/m_venda:.2f}%/mês", fmt_moeda(0.0), "0.00%", fmt_moeda(l_proprio),
        f"{moic_proprio:.2f}x", f"{((l_proprio/invest_bolso_proprio)*100)/m_venda:.2f}%/mês"
    ]
    st.table(pd.DataFrame({"Diretriz de Análise": labels, "Resultado": val_pr}))

with st.expander("▶️ Cenário B: Alavancagem Inteligente via Sistema SAC (Seu Modelo)"):
    val_sc = [
        fmt_moeda(v_vgv), fmt_moeda(credito_bancario_total), fmt_moeda(max(0.0, sobra_caixa_giro)), fmt_moeda(quit_sac), fmt_moeda(v_vgv - quit_sac), fmt_moeda(invest_bolso_sac),
        fmt_moeda(capital_ja_pago_terreno), fmt_moeda(total_p_sac), fmt_moeda(l_sac_tijolo), f"{(l_sac_tijolo/invest_bolso_sac)*100:.2f}%" if invest_bolso_sac>0 else "0.00%", f"{((l_sac_tijolo/invest_bolso_sac)*100)/m_venda:.2f}%/mês" if invest_bolso_sac>0 else "0.00%/mês",
        fmt_moeda(ganho_cdi_sac), f"{(ganho_cdi_sac/invest_bolso_sac)*100:.2f}%" if invest_bolso_sac>0 else "0.00%", fmt_moeda(l_sac_total), f"{moic_sac:.2f}x", f"{(l_sac_total/invest_bolso_sac*100)/m_venda:.2f}%/mês" if invest_bolso_sac>0 else "0.00%/mês"
    ]
    st.table(pd.DataFrame({"Diretriz de Análise": labels, "Resultado": val_sc}))

with st.expander("▶️ Cenário C: Alavancagem Corporativa Avançada via Sistema PRICE (Seu Modelo)"):
    val_pc = [
        fmt_moeda(v_vgv), fmt_moeda(credito_bancario_total), fmt_moeda(max(0.0, sobra_caixa_giro)), fmt_moeda(quit_price), fmt_moeda(v_vgv - quit_price), fmt_moeda(invest_bolso_price),
        fmt_moeda(capital_ja_pago_terreno), fmt_moeda(total_p_price), fmt_moeda(l_price_tijolo), f"{(l_price_tijolo/invest_bolso_price)*100:.2f}%" if invest_bolso_price>0 else "0.00%", f"{((l_price_tijolo/invest_bolso_price)*100)/m_venda:.2f}%/mês" if invest_bolso_price>0 else "0.00%/mês",
        fmt_moeda(ganho_cdi_price), f"{(ganho_cdi_price/invest_bolso_price)*100:.2f}%" if invest_bolso_price>0 else "0.00%", fmt_moeda(l_price_total), f"{moic_price:.2f}x", f"{(l_price_total/invest_bolso_price*100)/m_venda:.2f}%/mês" if invest_bolso_price>0 else "0.00%/mês"
    ]
    st.table(pd.DataFrame({"Diretriz de Análise": labels, "Resultado": val_pc}))

st.markdown("---")
st.header("2. Evolução Cronológica Mensal Detalhada")

# Renderização direta da lista de dicionários sem chance de quebra estrutural
df_cronograma = pd.DataFrame(cronograma_final)
st.table(df_cronograma)
