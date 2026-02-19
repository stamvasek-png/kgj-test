"""
KGJ Annual Forward Dispatch
Roční optimalizace pro Běhounkova & Rabasova
Fixed: Plyn 35 EUR/MWh | Teplo 40 EUR/MWh
"""

import io
import streamlit as st
import pandas as pd
import numpy as np

from locations_config import LOCATIONS, get_location
from dispatch_engine import TechParams, compute_margins, best_source, run_dispatch
import chart_helpers as ch
import chart_helpers_annual as cha

# ══════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════

st.set_page_config(
    page_title="KGJ Annual Dispatch",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════

if "selected_location" not in st.session_state:
    st.session_state["selected_location"] = "behounkova"

# ══════════════════════════════════════════════
# CUSTOM CSS
# ══════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

.kgj-header {
    background: linear-gradient(135deg, #141720 0%, #0D0F14 60%, #1a1f2e 100%);
    border-bottom: 1px solid #2A3050;
    padding: 18px 28px 14px 28px;
    margin: -1rem -1rem 1.5rem -1rem;
    display: flex; align-items: center; gap: 16px;
}
.kgj-header-hex {
    width: 38px; height: 38px;
    background: #F0A500;
    clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
}
.kgj-header-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 15px; font-weight: 600;
    letter-spacing: 0.18em; text-transform: uppercase;
    color: #E8EAF0;
}
.kgj-header-title span { color: #F0A500; }
.kgj-header-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px; color: #6B7490;
    letter-spacing: 0.12em; margin-top: 3px;
}
.kgj-tag {
    margin-left: auto;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px; color: #6B7490;
    border: 1px solid #2A3050;
    padding: 4px 12px; border-radius: 2px;
    letter-spacing: 0.1em;
}

.kpi-card {
    background: #141720;
    border: 1px solid #2A3050;
    border-radius: 3px;
    padding: 14px 16px;
    position: relative; overflow: hidden;
}
.kpi-card::before {
    content: ''; position: absolute;
    top: 0; left: 0; width: 3px; height: 100%;
    border-radius: 3px 0 0 3px;
}
.kpi-positive::before { background: #4CAF88; }
.kpi-negative::before { background: #E05555; }
.kpi-neutral::before  { background: #F0A500; }
.kpi-info::before     { background: #5B8DEE; }
.kpi-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px; letter-spacing: 0.18em;
    text-transform: uppercase; color: #6B7490;
    margin-bottom: 6px;
}
.kpi-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 24px; font-weight: 600; line-height: 1;
}
.kpi-pos { color: #4CAF88; }
.kpi-neg { color: #E05555; }
.kpi-acc { color: #F0A500; }
.kpi-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px; color: #6B7490; margin-top: 5px;
}

.section-hd {
    display: flex; align-items: center; gap: 8px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px; letter-spacing: 0.18em;
    text-transform: uppercase; color: #6B7490;
    border-bottom: 1px solid #2A3050;
    padding-bottom: 8px; margin-bottom: 12px;
}
.section-hd .dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #F0A500;
    box-shadow: 0 0 6px rgba(240,165,0,0.5);
}

.info-box {
    background: rgba(91,141,238,0.06);
    border-left: 3px solid #5B8DEE;
    border: 1px solid rgba(91,141,238,0.2);
    border-left-width: 3px;
    padding: 12px 16px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px; color: #6B7490;
    line-height: 1.65; margin-bottom: 12px;
}

.status-chip-ok, .status-chip-err {
    display: inline-flex; align-items: center; gap: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px; padding: 3px 10px; border-radius: 2px;
}
.status-chip-ok  { background: rgba(76,175,136,0.1); border: 1px solid rgba(76,175,136,0.3); color: #4CAF88; }
.status-chip-err { background: rgba(224,85,85,0.1);  border: 1px solid rgba(224,85,85,0.3);  color: #E05555; }

.fixed-price-banner {
    background: linear-gradient(135deg, #1C2030 0%, #141720 100%);
    border: 1px solid #2A3050;
    border-left: 3px solid #00D4AA;
    padding: 12px 16px;
    margin-bottom: 16px;
    border-radius: 3px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #6B7490;
    display: flex;
    align-items: center;
    gap: 12px;
}
.fixed-price-item {
    display: flex;
    align-items: center;
    gap: 6px;
}
.fixed-price-val {
    color: #00D4AA;
    font-weight: 600;
    font-size: 13px;
}

.stPlotlyChart { border: 1px solid #2A3050; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# LOAD CURRENT LOCATION
# ══════════════════════════════════════════════

current_loc = get_location(st.session_state["selected_location"])

# ══════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════

st.markdown(f"""
<div class="kgj-header">
  <div class="kgj-header-hex">{current_loc.icon}</div>
  <div>
    <div class="kgj-header-title">KGJ <span>ANNUAL DISPATCH</span> — {current_loc.display_name.upper()}</div>
    <div class="kgj-header-sub">Roční Forward Optimalizace · Hodinová Data · PnL Analýza</div>
  </div>
  <div class="kgj-tag">{current_loc.short_name} · v4.0</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# LOCATION SWITCHER
# ══════════════════════════════════════════════

st.markdown('<div class="section-hd"><div class="dot"></div> Výběr lokality</div>', unsafe_allow_html=True)

cols = st.columns(len(LOCATIONS))
for idx, (loc_id, loc_config) in enumerate(LOCATIONS.items()):
    with cols[idx]:
        is_active = loc_id == st.session_state["selected_location"]
        if st.button(
            f"{loc_config.icon} {loc_config.display_name}",
            key=f"switch_{loc_id}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state["selected_location"] = loc_id
            st.rerun()

# ══════════════════════════════════════════════
# FIXED PRICES BANNER
# ══════════════════════════════════════════════

st.markdown(f"""
<div class="fixed-price-banner">
  <span style="color:#00D4AA;font-weight:600;">FIXNÍ CENY:</span>
  <div class="fixed-price-item">
    <span>Plyn:</span>
    <span class="fixed-price-val">{current_loc.fixed_gas_price:.1f} EUR/MWh</span>
  </div>
  <div class="fixed-price-item">
    <span>Teplo:</span>
    <span class="fixed-price-val">{current_loc.fixed_heat_price:.1f} EUR/MWh</span>
  </div>
  <span style="margin-left:auto;font-size:10px;">Variabilní: pouze cena EE (forward křivka)</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SIDEBAR — PARAMETERS
# ══════════════════════════════════════════════

with st.sidebar:
    st.markdown(f'<div class="section-hd"><div class="dot"></div> {current_loc.display_name}</div>', unsafe_allow_html=True)
    
    st.info(f"""
    **Technické parametry:**
    - KGJ: {current_loc.kgj_el_output:.3f} MWel | {current_loc.kgj_heat_output:.3f} MWtep
    - Kotel: {current_loc.boiler_max_heat:.2f} MW
    - EKotel: {current_loc.eboiler_max_heat:.3f} MW
    - Min up/down: {current_loc.min_up}/{current_loc.min_down} h
    """)
    
    params = TechParams(
        kgj_heat_output=current_loc.kgj_heat_output,
        kgj_el_output=current_loc.kgj_el_output,
        kgj_heat_eff=current_loc.kgj_heat_output / current_loc.kgj_gas_input,
        kgj_service=current_loc.kgj_service,
        kgj_min_load=current_loc.kgj_min_load,
        boiler_eff=current_loc.boiler_eff,
        boiler_max_heat=current_loc.boiler_max_heat,
        eboiler_eff=current_loc.eboiler_eff,
        eboiler_max_heat=current_loc.eboiler_max_heat,
        ee_dist_cost=current_loc.ee_dist_cost,
        heat_min_cover=current_loc.heat_min_cover,
        min_up=current_loc.min_up,
        min_down=current_loc.min_down,
        initial_state=0,
    )
    
    st.divider()
    st.caption(f"Annual Dispatch · {current_loc.display_name}")

# ══════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════

st.markdown('<div class="section-hd"><div class="dot"></div> Upload Forward Křivky EE + Tepelné Poptávky</div>', unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
📂 Nahrajte <strong>Excel soubor</strong> se 3 sloupci:<br>
&nbsp;&nbsp;1. <code>datetime</code> — časové razítko (hodinové intervaly)<br>
&nbsp;&nbsp;2. <code>ee_price</code> — forward cena EE (EUR/MWh)<br>
&nbsp;&nbsp;3. <code>heat_demand</code> — očekávaná poptávka tepla (MWh)<br><br>
Ceny plynu ({current_loc.fixed_gas_price} EUR/MWh) a tepla ({current_loc.fixed_heat_price} EUR/MWh) jsou <strong>fixní</strong>.
</div>
""".format(current_loc=current_loc), unsafe_allow_html=True)

uploaded = st.file_uploader(
    "📂 Nahrát Forward Data (Excel)",
    type=["xlsx", "xls"],
    key=f"annual_upload_{current_loc.name}"
)

df_input = None

if uploaded is not None:
    try:
        df_raw = pd.read_excel(uploaded)
        df_raw.columns = [c.strip().lower().replace(" ", "_") for c in df_raw.columns]
        
        # Validate columns
        required = ["datetime", "ee_price", "heat_demand"]
        if not all(col in df_raw.columns for col in required):
            st.error(f"❌ Chybí požadované sloupce. Nalezeno: {list(df_raw.columns)}")
        else:
            # Add fixed prices
            df_input = df_raw[required].copy()
            df_input["gas_price"] = current_loc.fixed_gas_price
            df_input["heat_price"] = current_loc.fixed_heat_price
            df_input = df_input.reset_index(drop=True)
            
            st.markdown(f'<span class="status-chip-ok">✓ Načteno {len(df_input):,} hodin ({len(df_input)/8760*365:.0f} dní)</span>', unsafe_allow_html=True)
            
            # Preview
            with st.expander("📋 Náhled dat", expanded=False):
                st.dataframe(df_input.head(100), use_container_width=True, height=200)
                
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                col_stat1.metric("Průměrná cena EE", f"{df_input['ee_price'].mean():.2f} EUR/MWh")
                col_stat2.metric("Průměrná poptávka", f"{df_input['heat_demand'].mean():.3f} MWh/h")
                col_stat3.metric("Celková poptávka", f"{df_input['heat_demand'].sum():,.0f} MWh/rok")
    
    except Exception as e:
        st.error(f"❌ Chyba při načítání: {e}")


# ══════════════════════════════════════════════
# RUN OPTIMIZATION
# ══════════════════════════════════════════════

if df_input is not None:
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("▶ SPUSTIT ROČNÍ OPTIMALIZACI", type="primary", use_container_width=True, key=f"run_{current_loc.name}"):
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        
        status_text.text("⚙ CBC solver pracuje... Může trvat několik minut pro roční data.")
        
        with st.spinner("Optimalizuji..."):
            result_df = run_dispatch(df_input, params)
        
        progress_bar.empty()
        status_text.empty()
        
        if result_df is None:
            st.error("❌ Solver nenašel optimální řešení.")
        else:
            st.session_state[f"result_df_{current_loc.name}"] = result_df
            st.success(f"✅ Optimalizace dokončena — {len(result_df):,} hodin zpracováno")
            st.rerun()

# ══════════════════════════════════════════════
# DISPLAY RESULTS
# ══════════════════════════════════════════════

if f"result_df_{current_loc.name}" in st.session_state:
    result_df = st.session_state[f"result_df_{current_loc.name}"]
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-hd"><div class="dot"></div> Roční Výsledky — Přehled</div>', unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════
    # KEY METRICS
    # ══════════════════════════════════════════════
    
    total_profit      = result_df["Total_profit_EUR"].sum()
    total_revenue_ee  = (result_df["EE_Sold_Spot_MWh"] * result_df["EE_price_EUR_MWh"]).sum()
    total_revenue_heat = (result_df["Heat_demand_MWh"] * current_loc.fixed_heat_price * params.heat_min_cover).sum()
    total_cost_gas    = (result_df["KGJ_heat_MWh"] * params.kgj_gas_per_heat * current_loc.fixed_gas_price).sum() + \
                        (result_df["Gas_boiler_heat_MWh"] / params.boiler_eff * current_loc.fixed_gas_price).sum()
    total_cost_ee_dist = (result_df["EE_to_EBoiler_Grid_MWh"] * (result_df["EE_price_EUR_MWh"] + params.ee_dist_cost)).sum()
    total_cost_service = (result_df["KGJ_on"] * params.kgj_service).sum()
    
    kgj_hours         = result_df["KGJ_on"].sum()
    kgj_starts        = result_df["KGJ_start"].sum()
    avg_kgj_load      = result_df.loc[result_df["KGJ_on"]==1, "KGJ_load_pct"].mean() if kgj_hours > 0 else 0
    
    total_heat_kgj    = result_df["KGJ_heat_MWh"].sum()
    total_heat_boiler = result_df["Gas_boiler_heat_MWh"].sum()
    total_heat_eboiler = result_df["Electric_boiler_heat_MWh"].sum()
    total_heat_total  = total_heat_kgj + total_heat_boiler + total_heat_eboiler
    
    total_ee_sold     = result_df["EE_Sold_Spot_MWh"].sum()
    
    # KPI Cards Row 1
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(f"""<div class="kpi-card {'kpi-positive' if total_profit>=0 else 'kpi-negative'}">
        <div class="kpi-label">Celkový roční zisk</div>
        <div class="kpi-value {'kpi-pos' if total_profit>=0 else 'kpi-neg'}">{total_profit/1000:,.0f}k</div>
        <div class="kpi-sub">EUR / rok</div></div>""", unsafe_allow_html=True)
    
    k2.markdown(f"""<div class="kpi-card kpi-neutral">
        <div class="kpi-label">Příjem z tepla</div>
        <div class="kpi-value kpi-acc">{total_revenue_heat/1000:,.0f}k</div>
        <div class="kpi-sub">EUR / rok</div></div>""", unsafe_allow_html=True)
    
    k3.markdown(f"""<div class="kpi-card kpi-neutral">
        <div class="kpi-label">Příjem z EE</div>
        <div class="kpi-value kpi-acc">{total_revenue_ee/1000:,.0f}k</div>
        <div class="kpi-sub">EUR / rok</div></div>""", unsafe_allow_html=True)
    
    k4.markdown(f"""<div class="kpi-card kpi-negative">
        <div class="kpi-label">Náklad plyn</div>
        <div class="kpi-value kpi-neg">-{total_cost_gas/1000:,.0f}k</div>
        <div class="kpi-sub">EUR / rok</div></div>""", unsafe_allow_html=True)
    
    k5.markdown(f"""<div class="kpi-card kpi-info">
        <div class="kpi-label">KGJ hodiny</div>
        <div class="kpi-value">{int(kgj_hours):,}</div>
        <div class="kpi-sub">z {len(result_df):,} h ({kgj_hours/len(result_df)*100:.1f}%)</div></div>""", unsafe_allow_html=True)
    
    # KPI Cards Row 2
    st.markdown("<br>", unsafe_allow_html=True)
    k6, k7, k8, k9, k10 = st.columns(5)
    
    k6.markdown(f"""<div class="kpi-card kpi-neutral">
        <div class="kpi-label">EE prodáno</div>
        <div class="kpi-value kpi-acc">{total_ee_sold:,.0f}</div>
        <div class="kpi-sub">MWh / rok</div></div>""", unsafe_allow_html=True)
    
    k7.markdown(f"""<div class="kpi-card kpi-info">
        <div class="kpi-label">Teplo z KGJ</div>
        <div class="kpi-value">{total_heat_kgj/total_heat_total*100:.1f}%</div>
        <div class="kpi-sub">{total_heat_kgj:,.0f} MWh</div></div>""", unsafe_allow_html=True)
    
    k8.markdown(f"""<div class="kpi-card kpi-info">
        <div class="kpi-label">Teplo z kotlů</div>
        <div class="kpi-value">{(total_heat_boiler+total_heat_eboiler)/total_heat_total*100:.1f}%</div>
        <div class="kpi-sub">{total_heat_boiler+total_heat_eboiler:,.0f} MWh</div></div>""", unsafe_allow_html=True)
    
    k9.markdown(f"""<div class="kpi-card kpi-neutral">
        <div class="kpi-label">Průměr KGJ zatížení</div>
        <div class="kpi-value kpi-acc">{avg_kgj_load:.1f}%</div>
        <div class="kpi-sub">při běhu</div></div>""", unsafe_allow_html=True)
    
    k10.markdown(f"""<div class="kpi-card kpi-info">
        <div class="kpi-label">KGJ starty</div>
        <div class="kpi-value">{int(kgj_starts)}</div>
        <div class="kpi-sub">za rok</div></div>""", unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════
    # ANNUAL CHARTS
    # ══════════════════════════════════════════════
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-hd"><div class="dot"></div> PnL Analýza — Měsíční & Kumulativní</div>', unsafe_allow_html=True)
    
    st.plotly_chart(cha.annual_pnl_chart(result_df), use_container_width=True)
    
    st.markdown('<div class="section-hd"><div class="dot"></div> Výroba & Příjmy</div>', unsafe_allow_html=True)
    
    col_prod, col_ee = st.columns(2)
    with col_prod:
        st.plotly_chart(cha.monthly_production_chart(result_df), use_container_width=True)
    with col_ee:
        st.plotly_chart(cha.ee_revenue_chart(result_df), use_container_width=True)
    
    st.markdown('<div class="section-hd"><div class="dot"></div> Forward Křivka & Využití</div>', unsafe_allow_html=True)
    
    col_fw, col_util = st.columns(2)
    with col_fw:
        st.plotly_chart(cha.forward_ee_price_chart(result_df), use_container_width=True)
    with col_util:
        st.plotly_chart(cha.hourly_profit_distribution(result_df), use_container_width=True)
    
    st.markdown('<div class="section-hd"><div class="dot"></div> KGJ Využití — Heatmapa (první 90 dní)</div>', unsafe_allow_html=True)
    st.plotly_chart(cha.kgj_utilization_heatmap(result_df), use_container_width=True)
    
    # ══════════════════════════════════════════════
    # DETAILED HOURLY DATA
    # ══════════════════════════════════════════════
    
    with st.expander("📊 Hodinová data — Detailní tabulka"):
        st.markdown('<div class="section-hd"><div class="dot"></div> Filtrování sloupců</div>', unsafe_allow_html=True)
        
        all_cols = list(result_df.columns)
        default_cols = [
            "datetime", "EE_price_EUR_MWh", "Heat_demand_MWh",
            "KGJ_on", "KGJ_load_pct", "KGJ_heat_MWh",
            "Gas_boiler_heat_MWh", "Electric_boiler_heat_MWh",
            "EE_Sold_Spot_MWh", "Total_profit_EUR",
        ]
        sel_cols = st.multiselect(
            "Zobrazit sloupce",
            all_cols,
            default=[c for c in default_cols if c in all_cols],
            key=f"col_sel_{current_loc.name}"
        )
        
        if sel_cols:
            show_df = result_df[sel_cols].copy()
            
            for c in show_df.select_dtypes(include="float").columns:
                show_df[c] = show_df[c].round(4)
            
            float_cols = show_df.select_dtypes(include="float").columns.tolist()
            color_cols = [c for c in float_cols if "profit" in c.lower() or "margin" in c.lower()]
            
            def color_pos_neg(val):
                if isinstance(val, float) and not pd.isna(val):
                    return "color: #4CAF88" if val >= 0 else "color: #E05555"
                return ""
            
            try:
                styled = show_df.style
                if color_cols:
                    styled = styled.map(color_pos_neg, subset=color_cols)
                st.dataframe(styled, use_container_width=True, height=500)
            except Exception:
                st.dataframe(show_df, use_container_width=True, height=500)
    
    # ══════════════════════════════════════════════
    # EXPORT
    # ══════════════════════════════════════════════
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-hd"><div class="dot"></div> Export výsledků</div>', unsafe_allow_html=True)
    
    col_xlsx, col_csv = st.columns(2)
    
    with col_xlsx:
        buf_xlsx = io.BytesIO()
        with pd.ExcelWriter(buf_xlsx, engine="xlsxwriter") as writer:
            result_df.to_excel(writer, index=False, sheet_name="Hourly_Results")
            
            # Summary sheet
            summary = pd.DataFrame({
                "Metrika": [
                    "Celkový roční zisk (EUR)",
                    "Příjem z tepla (EUR)",
                    "Příjem z EE (EUR)",
                    "Náklad plyn (EUR)",
                    "Náklad EE dist (EUR)",
                    "Náklad servis (EUR)",
                    "KGJ hodiny",
                    "KGJ starty",
                    "Průměrné zatížení KGJ (%)",
                    "EE prodáno celkem (MWh)",
                    "Teplo z KGJ (MWh)",
                    "Teplo z kotle (MWh)",
                    "Teplo z elektrokotle (MWh)",
                ],
                "Hodnota": [
                    total_profit,
                    total_revenue_heat,
                    total_revenue_ee,
                    -total_cost_gas,
                    -total_cost_ee_dist,
                    -total_cost_service,
                    int(kgj_hours),
                    int(kgj_starts),
                    avg_kgj_load,
                    total_ee_sold,
                    total_heat_kgj,
                    total_heat_boiler,
                    total_heat_eboiler,
                ]
            })
            summary.to_excel(writer, index=False, sheet_name="Annual_Summary")
        
        st.download_button(
            "⬇ Stáhnout Excel (.xlsx)",
            data=buf_xlsx.getvalue(),
            file_name=f"annual_dispatch_{current_loc.name}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
        )
    
    with col_csv:
        csv_data = result_df.to_csv(index=False, float_format="%.4f").encode("utf-8")
        st.download_button(
            "⬇ Stáhnout CSV",
            data=csv_data,
            file_name=f"annual_dispatch_{current_loc.name}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

else:
    st.info(f"📂 Nahrajte forward data pro lokalitu **{current_loc.display_name}** a spusťte optimalizaci.")
