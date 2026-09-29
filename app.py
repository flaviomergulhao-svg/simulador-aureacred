import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Áurea Cred - Simulador", page_icon="🛡️")
st.title("🛡️ Áurea Cred - Painel de Inteligência Financeira")
st.caption("Apresentação Estruturada de Viabilidade e Eficiência de Capital Passo a Passo")

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

m_venda = 18 # Travado conforme seu horizonte de desinvestimento
prazo_contrato = 240

# =========================================================================
# 2. MOTOR MATEMÁTICO TRAVADO RIGOROSAMENTE NO SEU MODELO DE TRANCHES
# =========================================================================
tranches = {0: 360000.0, 2: 360000.0, 4: 360000.0, 6: 360000.0, 8: 360000.0}
credito_bancario_total = 1800000.0 # 5 * 360k

def simular_sistema(sistema='SAC'):
    saldo_devedor = 0.0
    juros_pagos_total = 0.0
    amortizacao_paga_total = 0.0
    total_parcelas_pagas = 0.0
    ganho_cdi_acumulado = 0.0
    
    cronograma_linhas = []
    
    for mes in range(m_venda + 1):
        aporte_mes_obra = 0.0
        # 1. Adiciona tranche no início do mês, se houver
        if mes in tranches:
            saldo_devedor += tranches[mes]
            aporte_mes_obra = tranches[mes]
        if mes == 0:
            saldo_devedor += v_taoc
            
        if mes == m_venda:
            saldo_quitacao = saldo_devedor
            cronograma_linhas.append([
                f"Mês {mes}", fmt_moeda(0.0), fmt_moeda(0.0), fmt_moeda(saldo_quitacao)
            ])
            break
            
        # 2. Se houver saldo devedor, roda a parcela do mês
        p_mes, j_mes, amort_mes = 0.0, 0.0, 0.0
        if saldo_devedor > 0:
            j_mes = saldo_devedor * tx_juros
            prazo_restante = prazo_contrato - mes
            
            if sistema == 'SAC':
                amort_mes = saldo_devedor / prazo_restante
                p_mes = amort_mes + j_mes
            else: # Price
                p_mes = saldo_devedor * (tx_juros * (1+tx_juros)**prazo_restante) / ((1+tx_juros)**prazo_restante - 1)
                amort_mes = p_mes - j_mes
                
            juros_pagos_total += j_mes
            amortizacao_paga_total += amort_mes
            total_parcelas_pagas += p_mes
            saldo_devedor -= amort_mes
            
        # Cálculo de Caixa Preservado no CDI (Mês a Mês)
        # O investidor captou R$ 1.8M totais + o que ele já tinha de terreno próprio
        # Ele vai gastando a obra real conforme a necessidade (simulado de forma linear R$ 1.518M / 18)
        caixa_preservado = (v_obra / m_venda) * mes - total_parcelas_pagas + (credito_bancario_total - v_obra)
        if status_terreno == "Não":
            caixa_preservado += (v_terr - saldo_devedor_terreno)
            
        if caixa_preservado > 0:
            ganho_cdi_acumulado += caixa_preservado * tx_cdi

        cronograma_linhas.append([
            f"Mês {mes}", fmt_moeda(aporte_mes_obra if mes in tranches else 0.0), fmt_moeda(p_mes), fmt_moeda(saldo_devedor)
        ])
        
    return total_parcelas_pagas, saldo_quitacao, ganho_cdi_acumulado, cronograma_linhas

# Rodando os dois motores baseados estritamente na sua função
parc_sac, quit_sac, cdi_sac, cron_sac = simular_sistema('SAC')
parc_prc, quit_price, cdi_prc, cron_prc = simular_sistema('Price')

# Conciliação do Bolso
capital_ja_pago_terreno = v_terr - saldo_devedor_terreno
sobra_caixa_giro = credito_bancario_total - (saldo_devedor_terreno + v_obra)

# Investimento real do bolso
invest_bolso_proprio = v_terr + v_obra
invest_bolso_sac = capital_ja_pago_terreno + parc_sac - sobra_caixa_giro if sobra_caixa_giro > 0 else capital_ja_pago_terreno + parc_sac
invest_bolso_price = capital_ja_pago_terreno + list(list_p_price:= [parc_prc])[0] - sobra_caixa_giro if sobra_caixa_giro > 0 else capital_ja_pago_terreno + parc_prc

l_proprio = v_vgv - invest_bolso_proprio
l_sac_tijolo = (v_vgv - quit_sac) - invest_bolso_sac
l_price_tijolo = (v_vgv - quit_price) - invest_bolso_price

l_sac_total = l_sac_tijolo + cdi_sac
l_price_total = l_price_tijolo + cdi_prc

moic_proprio = v_vgv / invest_bolso_proprio
moic_sac = (v_vgv - quit_sac + cdi_sac) / invest_bolso_sac if invest_bolso_sac > 0 else 0.0
moic_price = (v_vgv - quit_price + cdi_prc) / invest_bolso_price if invest_bolso_price > 0 else 0.0

# =========================================================================
# 3. INTERFACE DE EXPANSORES COMPLETA
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
        fmt_moeda(capital_ja_pago_terreno), fmt_moeda(parc_sac), fmt_moeda(l_sac_tijolo), f"{(l_sac_tijolo/invest_bolso_sac)*100:.2f}%" if invest_bolso_sac>0 else "0.00%", f"{((l_sac_tijolo/invest_bolso_sac)*100)/m_venda:.2f}%/mês" if invest_bolso_sac>0 else "0.00%/mês",
        fmt_moeda(cdi_sac), f"{(cdi_sac/invest_bolso_sac)*100:.2f}%" if invest_bolso_sac>0 else "0.00%", fmt_moeda(l_sac_total), f"{moic_sac:.2f}x", f"{(l_sac_total/invest_bolso_sac*100)/m_venda:.2f}%/mês" if invest_bolso_sac>0 else "0.00%/mês"
    ]
    st.table(pd.DataFrame({"Diretriz de Análise": labels, "Resultado": val_sc}))

with st.expander("▶️ Cenário C: Alavancagem Corporativa Avançada via Sistema PRICE (Seu Modelo)"):
    val_pc = [
        fmt_moeda(v_vgv), fmt_moeda(credito_bancario_total), fmt_moeda(max(0.0, sobra_caixa_giro)), fmt_moeda(quit_price), fmt_moeda(v_vgv - quit_price), fmt_moeda(invest_bolso_price),
        fmt_moeda(capital_ja_pago_terreno), fmt_moeda(parc_prc), fmt_moeda(l_price_tijolo), f"{(l_price_tijolo/invest_bolso_price)*100:.2f}%" if invest_bolso_price>0 else "0.00%", f"{((l_price_tijolo/invest_bolso_price)*100)/m_venda:.2f}%/mês" if invest_bolso_price>0 else "0.00%/mês",
        fmt_moeda(cdi_price:=cdi_prc), f"{(cdi_prc/invest_bolso_price)*100:.2f}%" if invest_bolso_price>0 else "0.00%", fmt_moeda(l_price_total), f"{moic_price:.2f}x", f"{(l_price_total/invest_bolso_price*100)/m_venda:.2f}%/mês" if invest_bolso_price>0 else "0.00%/mês"
    ]
    st.table(pd.DataFrame({"Diretriz de Análise": labels, "Resultado": val_pc}))

st.markdown("---")
st.header("2. Evolução Cronológica Combinada (Mês 0 ao Mês 18)")

c_m, c_ap, c_p_s, c_s_s, c_p_p, c_s_p = [], [], [], [], [], []
for s_row, p_row in zip(cron_sac[:-1], cron_prc[:-1]):
    c_m.append(s_row[0])
    c_ap.append(s_row[1])
    c_p_s.append(s_row[2])
    c_s_s.append(s_row[3])
    c_p_p.append(p_row[2])
    c_s_p.append(p_row[3])

# Adicionando Linha de Totais Estritos
c_m.append("TOTAL")
c_ap.append(fmt_moeda(total_aporte_obra))
c_p_s.append(fmt_moeda(parc_sac))
c_s_s.append("")
c_p_p.append(fmt_moeda(parc_prc))
c_s_p.append("")

st.table(pd.DataFrame({
