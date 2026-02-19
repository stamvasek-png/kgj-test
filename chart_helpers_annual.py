"""
Additional chart helpers for annual dispatch analysis
Monthly aggregations, yearly PnL overview
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

COLORS = {
    "bg":       "#0D0F14",
    "surface":  "#141720",
    "surface2": "#1C2030",
    "border":   "#2A3050",
    "accent":   "#F0A500",
    "accent2":  "#00D4AA",
    "blue":     "#5B8DEE",
    "purple":   "#9B59B6",
    "green":    "#4CAF88",
    "red":      "#E05555",
    "text":     "#E8EAF0",
    "muted":    "#6B7490",
}

LAYOUT_DEFAULTS = dict(
    paper_bgcolor=COLORS["surface"],
    plot_bgcolor=COLORS["surface2"],
    font=dict(family="IBM Plex Mono, monospace", color=COLORS["text"], size=11),
    margin=dict(l=16, r=16, t=40, b=16),
    legend=dict(
        bgcolor=COLORS["surface"],
        bordercolor=COLORS["border"],
        borderwidth=1,
        font=dict(size=10),
    ),
    xaxis=dict(gridcolor=COLORS["border"], linecolor=COLORS["border"], tickfont=dict(size=10)),
    yaxis=dict(gridcolor=COLORS["border"], linecolor=COLORS["border"], tickfont=dict(size=10)),
)

def apply_layout(fig, title="", height=380):
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=dict(text=title, font=dict(size=12, color=COLORS["muted"]), x=0, xref="paper"),
        height=height,
    )
    return fig


def _normalize_datetime_column(df: pd.DataFrame) -> pd.DataFrame:
    """Parse mixed datetime formats safely for uploaded Excel/CSV inputs."""
    out = df.copy()

    parsed = pd.to_datetime(out["datetime"], errors="coerce", format="mixed")
    # Fallback for day-first records often coming from CZ Excel exports.
    missing_mask = parsed.isna()
    if missing_mask.any():
        parsed_dayfirst = pd.to_datetime(
            out.loc[missing_mask, "datetime"],
            errors="coerce",
            format="mixed",
            dayfirst=True,
        )
        parsed.loc[missing_mask] = parsed_dayfirst

    if parsed.isna().all():
        raise ValueError(
            "Sloupec 'datetime' se nepodařilo převést na datum/čas. "
            "Zkontrolujte prosím formát ve vstupním souboru."
        )

    out["datetime"] = parsed
    return out


# ══════════════════════════════════════════════
# ANNUAL OVERVIEW CHARTS
# ══════════════════════════════════════════════

def annual_pnl_chart(result_df: pd.DataFrame) -> go.Figure:
    """
    Yearly PnL overview with monthly breakdown.
    Main chart for annual dispatch.
    """
    df = _normalize_datetime_column(result_df)
    df['month'] = df['datetime'].dt.to_period('M').astype(str)
    
    monthly = df.groupby('month').agg({
        'Total_profit_EUR': 'sum',
        'EE_Sold_Spot_MWh': 'sum',
        'KGJ_heat_MWh': 'sum',
        'Gas_boiler_heat_MWh': 'sum',
        'Electric_boiler_heat_MWh': 'sum',
    }).reset_index()
    
    monthly['cumulative_profit'] = monthly['Total_profit_EUR'].cumsum()
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.4],
        vertical_spacing=0.08,
        subplot_titles=["Měsíční zisk (EUR)", "Kumulativní zisk (EUR)"],
    )
    
    # Monthly profit bars
    colors_monthly = [COLORS["green"] if v >= 0 else COLORS["red"] for v in monthly['Total_profit_EUR']]
    fig.add_trace(go.Bar(
        x=monthly['month'],
        y=monthly['Total_profit_EUR'],
        name="Měsíční zisk",
        marker_color=colors_monthly,
        marker_line_width=0,
        text=[f"{v:,.0f}" for v in monthly['Total_profit_EUR']],
        textposition="outside",
        textfont=dict(size=9),
    ), row=1, col=1)
    
    fig.add_hline(y=0, line_color=COLORS["border"], line_width=1, row=1, col=1)
    
    # Cumulative profit
    fig.add_trace(go.Scatter(
        x=monthly['month'],
        y=monthly['cumulative_profit'],
        name="Kumulativní",
        mode="lines+markers",
        line=dict(color=COLORS["accent2"], width=3),
        marker=dict(size=8, color=COLORS["accent2"]),
        fill="tozeroy",
        fillcolor="rgba(0,212,170,0.08)",
    ), row=2, col=1)
    
    fig.add_hline(y=0, line_color=COLORS["border"], line_width=1, row=2, col=1)
    
    apply_layout(fig, height=450)
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=9), row=2, col=1)
    fig.update_yaxes(title_text="EUR", row=1, col=1, title_font=dict(size=10))
    fig.update_yaxes(title_text="EUR (kumulativní)", row=2, col=1, title_font=dict(size=10))
    
    return fig


def monthly_production_chart(result_df: pd.DataFrame) -> go.Figure:
    """Monthly heat production breakdown by source."""
    df = _normalize_datetime_column(result_df)
    df['month'] = df['datetime'].dt.to_period('M').astype(str)
    
    monthly = df.groupby('month').agg({
        'KGJ_heat_MWh': 'sum',
        'Gas_boiler_heat_MWh': 'sum',
        'Electric_boiler_heat_MWh': 'sum',
        'Heat_demand_MWh': 'sum',
    }).reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=monthly['month'],
        y=monthly['KGJ_heat_MWh'],
        name="KGJ teplo",
        marker_color=COLORS["accent"],
    ))
    fig.add_trace(go.Bar(
        x=monthly['month'],
        y=monthly['Gas_boiler_heat_MWh'],
        name="Kotel",
        marker_color=COLORS["blue"],
    ))
    fig.add_trace(go.Bar(
        x=monthly['month'],
        y=monthly['Electric_boiler_heat_MWh'],
        name="EKotel",
        marker_color=COLORS["purple"],
    ))
    
    # Demand line
    fig.add_trace(go.Scatter(
        x=monthly['month'],
        y=monthly['Heat_demand_MWh'],
        name="Poptávka",
        mode="lines+markers",
        line=dict(color=COLORS["green"], width=2, dash="dash"),
        marker=dict(size=6),
    ))
    
    apply_layout(fig, "Měsíční výroba tepla (MWh)", height=350)
    fig.update_layout(barmode="stack")
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=9))
    fig.update_yaxes(title_text="MWh", title_font=dict(size=10))
    
    return fig


def ee_revenue_chart(result_df: pd.DataFrame) -> go.Figure:
    """Monthly electricity revenue and volume."""
    df = _normalize_datetime_column(result_df)
    df['month'] = df['datetime'].dt.to_period('M').astype(str)
    df['ee_revenue'] = df['EE_Sold_Spot_MWh'] * df['EE_price_EUR_MWh']
    
    monthly = df.groupby('month').agg({
        'EE_Sold_Spot_MWh': 'sum',
        'ee_revenue': 'sum',
    }).reset_index()
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.5, 0.5],
        vertical_spacing=0.08,
    )
    
    # Revenue
    fig.add_trace(go.Bar(
        x=monthly['month'],
        y=monthly['ee_revenue'],
        name="Příjem z EE",
        marker_color=COLORS["accent"],
        marker_line_width=0,
    ), row=1, col=1)
    
    # Volume
    fig.add_trace(go.Bar(
        x=monthly['month'],
        y=monthly['EE_Sold_Spot_MWh'],
        name="Objem EE",
        marker_color=COLORS["blue"],
        marker_line_width=0,
    ), row=2, col=1)
    
    apply_layout(fig, "Měsíční příjmy a objem elektřiny", height=380)
    fig.update_yaxes(title_text="EUR", row=1, col=1, title_font=dict(size=10))
    fig.update_yaxes(title_text="MWh", row=2, col=1, title_font=dict(size=10))
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=9), row=2, col=1)
    
    return fig


def kgj_utilization_heatmap(result_df: pd.DataFrame) -> go.Figure:
    """Heatmap of KGJ utilization by day and hour."""
    df = _normalize_datetime_column(result_df)
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    
    # Limit to first 90 days for readability
    unique_dates = sorted(df['date'].unique())[:90]
    df_sub = df[df['date'].isin(unique_dates)]
    
    pivot = df_sub.pivot_table(
        index='hour',
        columns='date',
        values='KGJ_load_pct',
        aggfunc='mean'
    )
    
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(d) for d in pivot.columns],
        y=pivot.index,
        colorscale=[
            [0.0, COLORS["surface2"]],
            [0.5, COLORS["accent"]],
            [1.0, COLORS["green"]],
        ],
        showscale=True,
    ))
    
    fig.update_traces(
        colorbar_tickfont_size=9,
        colorbar_thickness=12,
        colorbar_len=0.8,
    )
    
    apply_layout(fig, "Využití KGJ — První 90 dní (% zatížení)", height=350)
    fig.update_xaxes(tickangle=-90, tickfont=dict(size=7))
    fig.update_yaxes(title_text="Hodina", title_font=dict(size=10))
    
    return fig


def hourly_profit_distribution(result_df: pd.DataFrame) -> go.Figure:
    """Distribution of hourly profit."""
    profits = result_df['Total_profit_EUR'].dropna()
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=profits,
        nbinsx=50,
        marker_color=COLORS["accent"],
        marker_line_width=0,
        opacity=0.8,
    ))
    
    # Add mean line
    mean_profit = profits.mean()
    fig.add_vline(
        x=mean_profit,
        line_color=COLORS["green"],
        line_width=2,
        line_dash="dash",
        annotation_text=f"Průměr: {mean_profit:.2f} EUR/h",
        annotation_font=dict(size=10, color=COLORS["green"]),
    )
    
    apply_layout(fig, "Distribuce hodinového zisku", height=280)
    fig.update_xaxes(title_text="Zisk (EUR/h)", title_font=dict(size=10))
    fig.update_yaxes(title_text="Počet hodin", title_font=dict(size=10))
    
    return fig


def forward_ee_price_chart(result_df: pd.DataFrame) -> go.Figure:
    """Forward EE price curve with monthly average."""
    df = _normalize_datetime_column(result_df)
    df['month'] = df['datetime'].dt.to_period('M').astype(str)
    
    monthly_avg = df.groupby('month')['EE_price_EUR_MWh'].mean().reset_index()
    
    fig = go.Figure()
    
    # Monthly average bars
    fig.add_trace(go.Bar(
        x=monthly_avg['month'],
        y=monthly_avg['EE_price_EUR_MWh'],
        name="Průměr měsíce",
        marker_color=COLORS["accent"],
        marker_line_width=0,
    ))
    
    # Overall average line
    overall_avg = df['EE_price_EUR_MWh'].mean()
    fig.add_hline(
        y=overall_avg,
        line_color=COLORS["green"],
        line_width=1.5,
        line_dash="dash",
        annotation_text=f"Roční průměr: {overall_avg:.2f}",
        annotation_font=dict(size=10, color=COLORS["green"]),
    )
    
    apply_layout(fig, "Forward křivka EE — měsíční průměry", height=300)
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=9))
    fig.update_yaxes(title_text="EUR/MWh", title_font=dict(size=10))
    
    return fig
