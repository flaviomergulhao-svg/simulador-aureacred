import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Áurea Cred - Intelligence", page_icon="🛡️")

# Cabeçalho focado em Reunião Executiva
st.title("🛡️ Painel de Inteligência Financeira & Eficiência de Capital")
st.subheader("Análise Estratégica para Incorporação de Alto Padrão")
st.caption("Apresentação Dinâmica de Cenários de Alavancagem Patrimonial")

# Função auxiliar para formatação monetária brasileira rigorosa
def fmt_moeda(valor):
    if valor < 0:
        return f"- R$ {abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================================================================
# 1. PAINEL DE CONTROLE LATERAL (Controles dinâmicos ao vivo)
# =========================================================================
st.sidebar.header("⚙️ Premissas Operacionais")
v_vgv = st.sidebar.number_input("Valor Geral de Vendas (VGV)", min_value=100000.0, value=3600000.0, step=100000.0, format="%.2f")
v_obra = st.sidebar.number_input("Orçamento Estimado da Obra", min_value=100000.0, value=1518000.0, step=5000.0, format="%.2f")
v_terr = st.sidebar.number_input("Valor do Terreno", min_value=0.0, value=1000000.0, step=50000.0, format="%.2f")

status_terreno = st.sidebar.selectbox("O Terreno está Quitado?", ["Sim", "Não"])
if status_terreno == "Não":
    saldo_devedor_terreno = st.sidebar.number_input("Valor a Amortizar do Terreno", min_value=0.0, value=1000000.0, step=10000.0, format="%.2f")
else:
    saldo_devedor_terreno = 0.00

st.sidebar.subheader("Encargos e Prazos")
tx_juros = st.sidebar.number_input("Taxa Financiamento (% a.m.)", min_value=0.1, max_value=5.0, value=1.45, step=0.01) / 100.0
v_taoc = st.sidebar.number_input("Taxa de Estruturação (TAC)", min_value=0.0, value=80000.0, step=5000.0, format="%.2f")
tx_cdi = st.sidebar.number_input("Rendimento do Caixa (% a.m. CDI)", min_value=0.1, max_value=3.0, value=0.85, step=0.05) / 100.0

m_venda = st.sidebar.slider("Prazo para Construção / Venda (Meses)", min_value=6, max_value=48, value=18, step=1)
prazo_contrato = 240

# =========================================================================
# 2. CÁLCULO DINÂMICO DO TETO DE CRÉDITO
# =========================================================================
limite_vgv = v_vgv * 0.50
limite_necessidade = v_obra + saldo_devedor_terreno
credito_bancario_total = min(limite_vgv, limite_necessidade)

valor_tranche_dinamica = credito_bancario_total / 5
tranches = {0: valor_tranche_dinamica, 2: valor_tranche_dinamica, 4: valor_tranche_dinamica, 6: valor_tranche_dinamica, 8: valor_tranche_dinamica}

st.sidebar.info(f"💳 **Crédito Máximo Configurado:** {fmt_moeda(credito_bancario_total)}")

# =========================================================================
# 3. MOTOR DE SIMULAÇÃO REESTRUTURADO
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
        # SISTEMA SAC
        j_sac_m = s_sac * tx_juros
        p_sac_v = amort_sac_fixa + j_sac_m
        s_sac -= amort_sac_fixa
        total_p_sac += p_sac_v

        # SISTEMA PRICE
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
# 4. CONCILIAÇÃO FINANCEIRA AVANÇADA (ROI + CAPITAL NOVO)
# =========================================================================
capital_ja_pago_terreno = v_terr - saldo_devedor_terreno
aporte_obra_proprio = max(0.0, (v_obra + saldo_devedor_terreno) - credito_bancario_total)

capital_restante_terreno = v_terr - (credito_bancario_total - v_obra)
custo_projeto_total = v_terr + v_obra

bolso_total_sac = capital_restante_terreno + total_p_sac + aporte_obra_proprio
bolso_total_price = capital_restante_terreno + total_p_price + aporte_obra_proprio

capital_novo_sac = total_p_sac + aporte_obra_proprio
capital_novo_price = total_p_price + aporte_obra_proprio

# Lucros Líquidos Reais
l_proprio = v_vgv - custo_projeto_total
l_sac_real = v_vgv - quit_sac - bolso_total_sac
l_price_real = v_vgv - quit_price - bolso_total_price

# ROI Tradicional
roi_proprio = (l_proprio / custo_projeto_total) * 100
roi_sac = (l_sac_real / bolso_total_sac) * 100
roi_price = (l_price_real / bolso_total_price) * 100

# Retorno sobre o Capital Novo (ROIC)
roic_proprio = (l_proprio / v_obra) * 100 if v_obra > 0 else 0.0
roic_sac = (l_sac_real / capital_novo_sac) * 100 if capital_novo_sac > 0 else 0.0
roic_price = (l_price_real / capital_novo_price) * 100 if capital_novo_price > 0 else 0.0

moic_proprio = v_vgv / custo_projeto_total
moic_sac = (v_vgv - quit_sac) / bolso_total_sac
moic_price = (v_vgv - quit_price) / bolso_total_price

# =========================================================================
# 5. HIGHLIGHTS DA APRESENTAÇÃO (Cards principais no topo)
# =========================================================================
st.markdown("---")
c_met1, c_met2, c_met3 = st.columns(3)
with c_met1:
    st.metric(label="Lucro Cenário Sem Alavancagem", value=fmt_moeda(l_proprio), help="Execução 100% com recursos próprios.")
with c_met2:
    st.metric(label="Lucro Alavancagem (SAC)", value=fmt_moeda(l_sac_real), delta=f"Eficiência do Caixa: {roic_sac:.2f}%")
with c_met3:
    st.metric(label="Lucro Alavancagem (Price)", value=fmt_moeda(l_price_real), delta=f"Eficiência do Caixa: {roic_price:.2f}%")

# =========================================================================
# 6. TESE CENTRAL DA REUNIÃO: CUSTO DE OPORTUNIDADE (VENDER VS. ALAVANCAR)
# =========================================================================
st.markdown("---")
st.header("🎯 Custo de Oportunidade: Desmobilizar Lote vs. Alavancar Obra")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔴 Estratégia 1: Vender o Lote Hoje")
    st.write(f"• **Decisão Comercial:** Liquidar o patrimônio imobilizado bruto sem agregar valor construtivo.")
    st.write(f"• **Dinheiro Novo do Bolso:** {fmt_moeda(0.0)}")
    st.write(f"• **Liquidez de Retorno (Mês {m_venda}):** {fmt_moeda(v_terr)}")
    st.write(f"• **Lucro Líquido Realizado:** {fmt_moeda(0.0)} *(Apenas recuperou o valor do lote)*")
    st.error("❌ Você deixa 100% do lucro da incorporação e construção na mesa.")

with col2:
    st.subheader("🟢 Estratégia 2: Reter o Lote + Iniciar Alavancagem")
    st.write(f"• **Decisão Comercial:** O banco cobre a obra. O investidor carrega apenas o fluxo de parcelas.")
    st.write(f"• **Dinheiro Novo em Movimento (SAC):** {fmt_moeda(capital_novo_sac)}")
    st.write(f"• **Retorno pós-Quitação do Banco (SAC):** {fmt_moeda(v_vgv - quit_sac)}")
    st.write(f"• **Lucro Real Gerado no Período:** {fmt_moeda(l_sac_real)}")
    st.success(f"🏆 Lucro Realizado com Eficiência Financeira de **{roic_sac:.2f}%** sobre o dinheiro novo.")

st.info(f"💡 **Tese de Investimento para o Cliente:** Ao invés de ficar travado com R$ 1.000.000,00 da venda simples, a **Alavancagem** permite injetar de forma parcelada {fmt_moeda(capital_novo_sac)} ao longo de {m_venda} meses. No final, o investidor **recupera o valor original do terreno e embolsa mais {fmt_moeda(l_sac_real)} de lucro líquido puro**, extraindo a máxima potência sobre cada real investido.")

# =========================================================================
# 7. MATRIZ COMPARATIVA GERAL (UNIFICADA LADO A LADO - CORREÇÃO CRÍTICA)
# =========================================================================
st.markdown("---")
st.header("📊 Comparativo Detalhado de Estruturação de Capital")
st.caption("Visão matricial consolidada para comparação direta de performance entre os cenários de capital.")

# Criando a tabela unificada lado a lado para exibição imediata na tela
diretrizes = [
    "Valor Geral de Vendas (VGV)", 
    "(-) Saldo de Dívida para Quitação Final", 
    "(-) Investimento Total Desembolsado (Bolso Acumulado)", 
    "  • Capital Imobilizado de Entrada (Fração Paga do Terreno)", 
    "  • Fluxo de Capital Novo Injetado (Parcelas + Aportes Obra)",
    "(=) LUCRO LÍQUIDO REALIZADO", 
    "📊 ROI Tradicional (Sobre o Bolso Total)", 
    "🚀 Retorno sobre o Capital Novo (Eficiência do Fluxo)",
    "📈 Múltiplo de Capital Realizado (MOIC)"
]

col_sem_alavancagem = [
    fmt_moeda(v_vgv), fmt_moeda(0.0), fmt_moeda(custo_projeto_total),
    fmt_moeda(v_terr), fmt_moeda(v_obra), fmt_moeda(l_proprio), 
    f"{roi_proprio:.2f}%", f"{roic_proprio:.2f}%", f"{moic_proprio:.2f}x"
]

col_alavancagem_sac = [
    fmt_moeda(v_vgv), fmt_moeda(quit_sac), fmt_moeda(bolso_total_sac),
    fmt_moeda(capital_restante_terreno), fmt_moeda(capital_novo_sac), fmt_moeda(l_sac_real), 
