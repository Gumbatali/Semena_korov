import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="AgriTech Dashboard", layout="wide", page_icon="🌱")

# Premium Custom CSS
st.markdown("""
<style>
    /* Global styling */
    .stApp {
        background: linear-gradient(135deg, #022c22 0%, #064e3b 100%);
        color: #ecfdf5;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        color: #a7f3d0 !important;
        font-weight: 700 !important;
    }
    
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #047857;
        background-color: rgba(6, 78, 59, 0.6);
    }
    
    div[data-testid="stMetricValue"] {
        color: #34d399;
        font-weight: 800;
        font-size: 2rem !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #a7f3d0 !important;
        font-size: 1rem !important;
    }

    .stPlotlyChart {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("🌱 Semena Korov: Farm Analytics Dashboard")
st.markdown("*Real-time monitoring of dairy farm performance, feed quality, and genetics.*")
st.markdown("---")

@st.cache_data
def load_mock_data():
    dates = pd.date_range(start="2025-01-01", periods=100)
    data = pd.DataFrame({
        "Date": dates,
        "Milk Yield (L)": np.random.normal(25, 3, 100).round(1),
        "Feed Consumption (kg)": np.random.normal(50, 5, 100).round(1),
        "Genetic Quality Index": np.random.uniform(80, 99, 100).round(1),
        "Health Status": np.random.choice(["Excellent", "Good", "Warning"], 100, p=[0.7, 0.25, 0.05])
    })
    return data

df = load_mock_data()

# Top Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Milk Yield", f"{df['Milk Yield (L)'].mean():.1f} L", "+1.2 L")
col2.metric("Feed Efficiency", f"{(df['Milk Yield (L)'].mean() / df['Feed Consumption (kg)'].mean()):.2f}", "+0.05")
col3.metric("Avg Genetic Index", f"{df['Genetic Quality Index'].mean():.1f}", "Top 10%")
col4.metric("Health Warnings", str((df['Health Status'] == 'Warning').sum()), "-2")

st.markdown("---")

c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📈 Yield & Feed Trends")
    fig_line = px.line(df, x="Date", y=["Milk Yield (L)", "Feed Consumption (kg)"],
                       template="plotly_dark", color_discrete_sequence=["#34d399", "#fcd34d"])
    fig_line.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_line, use_container_width=True)

with c2:
    st.subheader("🏥 Herd Health Distribution")
    fig_pie = px.pie(df, names="Health Status", hole=0.4, 
                     color="Health Status", 
                     color_discrete_map={"Excellent": "#10b981", "Good": "#3b82f6", "Warning": "#ef4444"},
                     template="plotly_dark")
    fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("📋 Raw Data Preview")
st.dataframe(df.tail(10), use_container_width=True)
