import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Job Market Analytics: AI vs IT",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- COLOR PALETTE (Consistent Branding) ---
COLOR_MAP = {
    'AI/ML': '#FF4B4B',      # Red/Orange for Hot/New
    'General IT': '#1F77B4', # Blue for Corporate/Stable
    'Hybrid': '#00CC96',     # Green for Growth/Bridge
    'Uncategorized': '#7F7F7F' # Grey
}

# --- CUSTOM CSS FOR PROFESSIONAL LOOK ---
st.markdown("""
    <style>
        /* Main Background */
        .stApp {
            background-color: #f8f9fa;
        }
        /* Metric Cards */
        div[data-testid="metric-container"] {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        div[data-testid="metric-container"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        /* Typography */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            color: #0f172a;
        }
        .stMarkdown p {
            font-size: 16px;
            color: #334155;
        }
        /* Warning removal */
        .stAlert {
            padding: 10px;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# --- FALLBACK CLASSIFICATION ENGINE ---
def fallback_categorization(title):
    """
    Classifies roles if the notebook logic failed.
    This ensures the dashboard NEVER shows 0% AI.
    """
    title = str(title).lower()
    ai_keywords = ['ai', 'machine learning', 'deep learning', 'nlp', 'llm', 'gpt', 'computer vision', 'data scientist', 'neural']
    hybrid_keywords = ['mlops', 'ai engineer', 'data engineer', 'analytics engineer', 'platform engineer']
    
    if any(k in title for k in hybrid_keywords):
        return 'Hybrid'
    elif any(k in title for k in ai_keywords):
        return 'AI/ML'
    else:
        return 'General IT'

# --- DATA LOADING FUNCTION ---
@st.cache_data
def load_data():
    """
    Loads data and applies emergency categorization if needed.
    """
    # Simulate paths or add your specific path
    file_paths = [
        'notebooks/data/processed/categorized_jobs.csv',
        'notebooks/data/processed/jobs_cleaned.csv',
        'job_data.csv' # Generic fallback
    ]
    
    df = None
    for file_path in file_paths:
        try:
            df = pd.read_csv(file_path)
            break
        except FileNotFoundError:
            continue
    
    if df is None:
        # CREATE DUMMY DATA FOR PORTFOLIO DISPLAY IF FILE NOT FOUND
        # (Remove this block in production if you strictly want to fail)
        dates = pd.date_range(start='2023-10-01', end='2024-10-01', periods=200)
        df = pd.DataFrame({
            'posting_date': np.random.choice(dates, 200),
            'role': np.random.choice(['Software Engineer', 'AI Researcher', 'MLOps Engineer', 'System Admin'], 200),
            'company': np.random.choice(['TechCorp', 'AI-Start', 'OldBank', 'CloudSystems'], 200),
            'location': np.random.choice(['Remote', 'NYC', 'SF', 'Austin'], 200),
            'salary': np.random.randint(80000, 200000, 200)
        })
        st.warning("⚠️ Demo Mode: Using synthetic data because source files were not found.")

    # 1. Date Handling
    date_col = None
    for col in ['posting_date', 'date', 'created_at']:
        if col in df.columns:
            date_col = col
            break
            
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df['Month_Year'] = df[date_col].dt.to_period('M').dt.to_timestamp()
    
    # 2. Emergency Categorization (The Fix for "Uncategorized" Crisis)
    if 'role_category' not in df.columns or df['role_category'].nunique() < 2:
        role_col = 'role' if 'role' in df.columns else 'title'
        if role_col in df.columns:
            df['role_category'] = df[role_col].apply(fallback_categorization)
        else:
            df['role_category'] = 'Uncategorized'

    # 3. Clean Company Names
    if 'company' in df.columns:
        df['company'] = df['company'].fillna('Unknown').astype(str)
        
    return df, date_col

# --- MAIN ANALYTICS ---
def main():
    # Sidebar
    with st.sidebar:
        st.title("📊 Job Market Filters")
        st.markdown("Refine the analysis window.")
        
        df, date_col = load_data()
        
        if df.empty:
            st.error("No data available.")
            st.stop()

        # Date Filter
        if date_col:
            min_date = df[date_col].min().date()
            max_date = df[date_col].max().date()
            date_range = st.slider("Time Period", min_value=min_date, max_value=max_date, value=(min_date, max_date))
            df = df[(df[date_col].dt.date >= date_range[0]) & (df[date_col].dt.date <= date_range[1])]

        st.markdown("---")
        st.caption("Created by **Daniel Berhane**")
        st.caption("Data Source: Aggregated Job Boards")

    # --- HERO SECTION ---
    st.title("Job Market Analytics: The AI Shift")
    st.markdown("""
    ### Executive Summary
    Analyzing the recruitment battle between **AI/ML** and **Traditional IT**.
    * **Core Insight:** While General IT roles provide volume, AI roles command higher strategic focus.
    * **Emerging Trend:** "Hybrid" roles (e.g., MLOps) are bridging the gap between research and production.
    """)
    
    st.markdown("---")

    # --- METRICS ROW (Comparison Logic) ---
    # Calculate metrics
    total_jobs = len(df)
    ai_jobs = len(df[df['role_category'] == 'AI/ML'])
    it_jobs = len(df[df['role_category'] == 'General IT'])
    hybrid_jobs = len(df[df['role_category'] == 'Hybrid'])
    
    ai_share = (ai_jobs / total_jobs * 100) if total_jobs > 0 else 0
    
    # Layout
    m1, m2, m3, m4 = st.columns(4)
    
    m1.metric("Total Analyzed Jobs", f"{total_jobs:,}", "Sample Size")
    m2.metric("AI/ML Market Share", f"{ai_share:.1f}%", "Strategic Value")
    m3.metric("General IT Volume", f"{it_jobs:,}", "Baseline")
    m4.metric("Hybrid Roles (Growth)", f"{hybrid_jobs:,}", "Bridge Roles")

    # --- TABBED ANALYSIS ---
    tab_trends, tab_company, tab_geo, tab_data = st.tabs(["📈 Trends & Growth", "🏢 Company Strategy", "🌍 Geography", "📋 Raw Data"])

    # 1. TRENDS TAB
    with tab_trends:
        st.subheader("Market Evolution")
        
        if date_col:
            # Aggregation for Line Chart
            trend_df = df.groupby(['Month_Year', 'role_category']).size().reset_index(name='Count')
            
            fig_trend = px.line(
                trend_df, 
                x='Month_Year', 
                y='Count', 
                color='role_category',
                color_discrete_map=COLOR_MAP,
                markers=True,
                title="Monthly Hiring Volume by Category"
            )
            fig_trend.update_layout(hovermode="x unified", xaxis_title="Date", yaxis_title="Job Postings")
            st.plotly_chart(fig_trend, use_container_width=True)
            
            st.info("💡 **Insight:** Divergence in lines indicates where market demand is shifting. Note stability in IT vs volatility in AI hiring.")
        else:
            st.warning("Time-series data not available.")

    # 2. COMPANY STRATEGY TAB
    with tab_company:
        st.subheader("Strategic Positioning: Who is Pivoting?")
        
        c1, c2 = st.columns([2, 1])
        
        with c1:
            # Scatter Plot: Volume vs AI Focus
            company_agg = df.groupby('company').agg(
                total_roles=('role_category', 'count'),
                ai_roles=('role_category', lambda x: (x == 'AI/ML').sum())
            ).reset_index()
            
            # Filter noise
            company_agg = company_agg[company_agg['total_roles'] > 1] 
            company_agg['ai_percentage'] = (company_agg['ai_roles'] / company_agg['total_roles']) * 100
            
            fig_scatter = px.scatter(
                company_agg,
                x='total_roles',
                y='ai_percentage',
                size='total_roles',
                color='ai_percentage',
                hover_name='company',
                color_continuous_scale='RdBu_r', # Red for high AI
                title="Company Matrix: Hiring Volume vs. AI Focus",
                labels={'total_roles': 'Total Hiring Volume', 'ai_percentage': '% AI Roles'}
            )
            # Add Quadrant Lines
            fig_scatter.add_hline(y=50, line_dash="dot", annotation_text="AI-First Strategy")
            st.plotly_chart(fig_scatter, use_container_width=True)

        with c2:
            st.markdown("### Leaders")
            top_ai_companies = company_agg.sort_values('ai_percentage', ascending=False).head(5)
            st.table(top_ai_companies[['company', 'ai_percentage']].set_index('company').style.format("{:.1f}%"))

    # 3. GEOGRAPHY TAB
    with tab_geo:
        col_pie, col_bar = st.columns(2)
        
        with col_pie:
            fig_pie = px.pie(
                df, 
                names='role_category', 
                title='Market Composition',
                hole=0.5,
                color='role_category',
                color_discrete_map=COLOR_MAP
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_bar:
            if 'location' in df.columns:
                # Filter out "Remote" for better geo analysis if needed, or keep it
                loc_counts = df['location'].value_counts().head(10).reset_index()
                loc_counts.columns = ['Location', 'Count']
                
                fig_bar = px.bar(
                    loc_counts,
                    x='Count',
                    y='Location',
                    orientation='h',
                    title='Top Hiring Hubs',
                    color='Count',
                    color_continuous_scale='Blues'
                )
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.write("Location data missing.")

    # 4. RAW DATA TAB
    with tab_data:
        st.subheader("Data Explorer")
        st.dataframe(df.sort_values(date_col, ascending=False) if date_col else df, use_container_width=True)

if __name__ == "__main__":
    main()