# Job Market Analytics Dashboard
# Streamlit application entry point


import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Job Market Analytics: AI vs IT",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR PROFESSIONAL LOOK ---
st.markdown("""
    <style>
        .main {
            background-color: #f9f9f9;
        }
        .stMetric {
            background-color: #ffffff;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1, h2, h3 {
            font-family: 'Helvetica Neue', sans-serif;
            color: #2c3e50;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- DATA LOADING FUNCTION ---
@st.cache_data
def load_data():
    """
    Loads and preprocesses the job data.
    Tries to load from the local path structure provided in the repo.
    """
    # Path based on your repository structure
    file_path = 'notebooks/data/processed/jobs_with_standardized_companies.csv'
    
    try:
        df = pd.read_csv(file_path)
        
        # Ensure datetime conversion
        # Checking for common date column names based on your report
        date_col = 'posting_date' if 'posting_date' in df.columns else 'date'
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df['Month_Year'] = df[date_col].dt.to_period('M').astype(str)
            
        # Fill missing values for categorical display
        df['role_category'] = df['role_category'].fillna('Unknown')
        df['company'] = df['company'].fillna('Anonymous')
        
        return df, date_col
        
    except FileNotFoundError:
        st.error(f"⚠️ Could not find data at `{file_path}`. Please ensure you are running this script from the root of your repository.")
        return pd.DataFrame(), None

# --- MAIN APP LOGIC ---
def main():
    # Sidebar Information
    with st.sidebar:
        st.image("https://img.icons8.com/clouds/200/000000/bar-chart.png", width=150)
        st.title("Job Market Analytics")
        st.info("Quantifying the evolution of tech talent: AI/ML vs Traditional IT.")
        
        st.markdown("---")
        st.markdown("**Author:** Daniel Berhane")
        st.markdown("[LinkedIn Profile](https://linkedin.com/in/daniel-berhane)")
        st.markdown("[GitHub Repo](https://github.com/yourusername)")
        
        st.markdown("---")
        st.subheader("Filters")
        
    # Load Data
    df, date_col = load_data()
    
    if df.empty:
        st.stop()

    # --- PRE-CALCULATE METRICS ---
    total_jobs = len(df)
    
    # Dynamic Date Filtering
    if date_col:
        min_date = df[date_col].min().date()
        max_date = df[date_col].max().date()
        
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            df_filtered = df[(df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)]
        else:
            df_filtered = df
    else:
        df_filtered = df

    # Category counts for KPIs
    cat_counts = df_filtered['role_category'].value_counts()
    ai_count = cat_counts.get('AI/ML', 0)
    it_count = cat_counts.get('General IT', 0)
    hybrid_count = cat_counts.get('Hybrid', 0)
    
    # --- HERO SECTION ---
    st.title("AI vs. General IT: The Hiring Shift 🚀")
    st.markdown("#### *A longitudinal study analyzing 4,100+ job postings (Oct 2023 - Oct 2024)*")
    st.markdown("This dashboard visualizes the recruitment battle between emerging AI/ML roles and traditional IT positions, highlighting the rise of **Hybrid MLOps** roles.")

    # --- KPI ROW ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs Analyzed", f"{len(df_filtered):,}", delta="13 Months Data")
    with col2:
        share_ai = (ai_count / len(df_filtered)) * 100 if len(df_filtered) > 0 else 0
        st.metric("AI/ML Market Share", f"{share_ai:.1f}%", delta="Growing Segment")
    with col3:
        ratio = it_count / ai_count if ai_count > 0 else 0
        st.metric("General IT Ratio", f"{ratio:.1f}x", delta="Baseline Volume", delta_color="off")
    with col4:
        st.metric("Hybrid Roles", f"{hybrid_count:,}", delta="High Growth", delta_color="normal")

    st.markdown("---")

    # --- TABS FOR DETAILED ANALYSIS ---
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Growth Trends", "🏢 Company Strategy", "📊 Market Composition", "📋 Raw Data"])

    # TAB 1: GROWTH TRENDS
    with tab1:
        st.subheader("Monthly Hiring Trends: AI vs IT")
        
        if date_col:
            # Group by Month and Category
            timeline_df = df_filtered.groupby(['Month_Year', 'role_category']).size().reset_index(name='Count')
            
            # Sort chronologically
            timeline_df['Month_Year_dt'] = pd.to_datetime(timeline_df['Month_Year'])
            timeline_df = timeline_df.sort_values('Month_Year_dt')

            # Line Chart
            fig_trend = px.line(
                timeline_df, 
                x='Month_Year', 
                y='Count', 
                color='role_category',
                markers=True,
                title='Monthly Job Posting Volume by Category',
                color_discrete_map={
                    'AI/ML': '#FF4B4B', 
                    'General IT': '#1F77B4', 
                    'Hybrid': '#FFA15A', 
                    'Non-Tech': '#7F7F7F'
                }
            )
            fig_trend.update_layout(xaxis_title="Month", yaxis_title="Number of Postings", hovermode="x unified")
            st.plotly_chart(fig_trend, use_container_width=True)
            
            st.markdown("""
            **Key Insight:** Observe the spikes in AI/ML hiring versus the steady baseline of General IT. 
            The "Hybrid" line represents the emergence of bridge roles like **MLOps** and **AI Platform Engineers**.
            """)
        else:
            st.warning("Date column not found for trend analysis.")

    # TAB 2: COMPANY STRATEGY
    with tab2:
        st.subheader("Strategic Positioning: Who is betting on AI?")
        
        col_a, col_b = st.columns([2, 1])
        
        with col_a:
            # Scatter Plot Logic (Polarization)
            # Filter out companies with very few jobs to reduce noise
            company_stats = df_filtered.groupby('company')['role_category'].value_counts().unstack(fill_value=0)
            company_stats['Total'] = company_stats.sum(axis=1)
            company_stats['AI_Pct'] = ((company_stats.get('AI/ML', 0) + company_stats.get('Hybrid', 0)) / company_stats['Total']) * 100
            
            # Filter for significant companies (e.g., > 3 postings in the dataset sample)
            significant_companies = company_stats[company_stats['Total'] > 3].reset_index()
            
            fig_scatter = px.scatter(
                significant_companies,
                x="Total",
                y="AI_Pct",
                size="Total",
                color="AI_Pct",
                hover_name="company",
                color_continuous_scale="Viridis",
                title="Market Polarization: Volume vs. AI Focus",
                labels={"Total": "Total Job Postings", "AI_Pct": "% AI/ML & Hybrid Roles"}
            )
            fig_scatter.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="AI-Majority Hiring")
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with col_b:
            st.markdown("#### Landscape Analysis")
            st.info("""
            **Top Right (High Volume, High AI):** AI-First Market Leaders.
            
            **Top Left (Low Volume, High AI):** Specialized AI Startups.
            
            **Bottom Right (High Volume, Low AI):** Traditional Enterprise / Maintenance.
            """)
            
            st.markdown("### Top AI Hirers")
            top_ai = significant_companies.sort_values('AI_Pct', ascending=False).head(5)
            st.table(top_ai[['company', 'AI_Pct', 'Total']].style.format({'AI_Pct': "{:.1f}%"}))

    # TAB 3: MARKET COMPOSITION
    with tab3:
        col_pie, col_bar = st.columns(2)
        
        with col_pie:
            fig_pie = px.pie(
                df_filtered, 
                names='role_category', 
                title='Overall Market Share',
                hole=0.4,
                color_discrete_map={
                    'AI/ML': '#FF4B4B', 
                    'General IT': '#1F77B4', 
                    'Hybrid': '#FFA15A', 
                    'Non-Tech': '#7F7F7F'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_bar:
            # Top Locations Analysis (if available)
            if 'location' in df_filtered.columns:
                top_locs = df_filtered['location'].value_counts().head(10).reset_index()
                top_locs.columns = ['Location', 'Count']
                fig_bar = px.bar(
                    top_locs, 
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
                st.write("Location data not available.")

    # TAB 4: RAW DATA
    with tab4:
        st.subheader("Dataset Explorer")
        st.write("Filter and explore the raw dataset used for this analysis.")
        
        # Filters for the table
        selected_cat = st.multiselect("Filter by Category", options=df_filtered['role_category'].unique(), default=df_filtered['role_category'].unique())
        search_term = st.text_input("Search Company or Role", "")
        
        table_df = df_filtered[df_filtered['role_category'].isin(selected_cat)]
        
        if search_term:
            table_df = table_df[
                table_df['company'].str.contains(search_term, case=False) | 
                table_df['role'].str.contains(search_term, case=False)
            ]
            
        st.dataframe(
            table_df[['posting_date', 'company', 'role', 'role_category', 'location']].sort_values('posting_date', ascending=False),
            use_container_width=True,
            height=500
        )

    # --- FOOTER ---
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888;">
        Built with Streamlit & Plotly | Data Source: Hacker News & Adzuna API
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()