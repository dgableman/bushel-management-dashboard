"""
Standalone Bushel Management Dashboard Application
Run this script to launch the interactive dashboard in a web browser.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, date
import streamlit as st

# Detect environment (Colab, Streamlit Cloud, or local)
def is_colab():
    """Check if running in Google Colab."""
    try:
        import google.colab
        return True
    except ImportError:
        return False

def is_streamlit_cloud():
    """Check if running on Streamlit Cloud."""
    # Streamlit Cloud sets this environment variable
    return os.getenv('STREAMLIT_SERVER_PORT') is not None

# Set up paths based on environment
if is_colab():
    # Colab paths
    PROJECT_PATH = os.getenv('PROJECT_PATH', '/content/drive/MyDrive/Colab_Notebooks/Grain_Manager')
    DB_PATH = os.getenv('DB_PATH', '/content/drive/MyDrive/Colab_Notebooks/Grain_Manager/database/bushel_management.db')
elif is_streamlit_cloud():
    # Streamlit Cloud paths
    SCRIPT_DIR = Path(__file__).parent.absolute()
    PROJECT_PATH = str(SCRIPT_DIR)
    # For Streamlit Cloud, database should be in the repo or set via environment variable
    # Option 1: Database in repo at data/bushel_management.db
    # Option 2: Set DB_PATH via Streamlit Cloud secrets (recommended for production)
    DB_PATH = os.getenv('DB_PATH', str(SCRIPT_DIR / 'data' / 'bushel_management.db'))
else:
    # Local paths - adjust these to match your local setup
    # Get the directory where this script is located
    SCRIPT_DIR = Path(__file__).parent.absolute()
    PROJECT_PATH = str(SCRIPT_DIR)
    # Default local database path - database is in the 'data' folder
    DB_PATH = os.getenv('DB_PATH', str(SCRIPT_DIR / 'data' / 'bushel_management.db'))
    # Alternative: if database is in the main Bushel_Management project:
    # DB_PATH = os.getenv('DB_PATH', '/path/to/Bushel_Management/data/bushel_management.db')

# Add project to path
if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

from database.db_connection import create_db_session
from reports.contract_queries import get_all_contracts, get_active_contracts
from reports.settlement_queries import get_all_settlements
from reports.bin_queries import get_all_bins

# Set page config for full-width layout
st.set_page_config(
    page_title="Bushel Management Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_database_session():
    """Create and cache database session."""
    try:
        return create_db_session(DB_PATH)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.info(f"Make sure the database file exists at: {DB_PATH}")
        return None

def main():
    """Main dashboard application."""
    
    # Title
    st.title("🌾 Bushel Management Dashboard")
    st.markdown("---")
    
    # Show database path (for debugging)
    with st.sidebar.expander("ℹ️ Settings", expanded=False):
        st.write(f"**Database:** `{DB_PATH}`")
        st.write(f"**Project:** `{PROJECT_PATH}`")
        if not os.path.exists(DB_PATH):
            st.error(f"⚠️ Database file not found!")
            st.write(f"**Looking for:** `{DB_PATH}`")
            
            # Check if data folder exists
            data_folder = Path(DB_PATH).parent
            if data_folder.exists():
                st.write(f"✅ Data folder exists: `{data_folder}`")
                st.write(f"**Files in data folder:**")
                try:
                    files = list(data_folder.iterdir())
                    if files:
                        for f in files:
                            st.write(f"  - {f.name} ({f.stat().st_size / 1024:.1f} KB)")
                    else:
                        st.write("  (empty)")
                except Exception as e:
                    st.write(f"  Error listing files: {e}")
            else:
                st.write(f"❌ Data folder not found: `{data_folder}`")
            
            st.info("""
            **To fix this:**
            1. Make sure `bushel_management.db` is in the `data/` folder in your GitHub repo
            2. Check: https://github.com/dgableman/bushel-management-dashboard/tree/main/data
            3. If file is missing, add it and push to GitHub
            4. Streamlit Cloud will auto-redeploy
            """)
    
    # Get database session
    db = get_database_session()
    if db is None:
        st.stop()
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Get all contracts for filter options
    all_contracts = get_all_contracts(db)
    all_settlements = get_all_settlements(db)
    all_bins = get_all_bins(db)
    
    # Filter options
    commodities = ['All'] + sorted(list(set([c.commodity for c in all_contracts if c.commodity])))
    statuses = ['All'] + sorted(list(set([c.status for c in all_contracts if c.status])))
    
    selected_commodity = st.sidebar.selectbox("Commodity", commodities, index=0)
    selected_status = st.sidebar.selectbox("Status", statuses, index=0)
    
    date_from = st.sidebar.date_input("From Date", value=None)
    date_to = st.sidebar.date_input("To Date", value=None)
    
    # Filter contracts
    filtered_contracts = all_contracts.copy()
    if selected_commodity != 'All':
        filtered_contracts = [c for c in filtered_contracts if c.commodity == selected_commodity]
    if selected_status != 'All':
        filtered_contracts = [c for c in filtered_contracts if c.status == selected_status]
    if date_from:
        filtered_contracts = [c for c in filtered_contracts if c.date_sold and c.date_sold >= date_from]
    if date_to:
        filtered_contracts = [c for c in filtered_contracts if c.date_sold and c.date_sold <= date_to]
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Contracts", len(filtered_contracts))
    
    with col2:
        active_count = len([c for c in filtered_contracts if c.status == 'Active'])
        st.metric("Active Contracts", active_count)
    
    with col3:
        st.metric("Total Settlements", len(all_settlements))
    
    with col4:
        st.metric("Storage Bins", len(all_bins))
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Contracts", "📈 Charts", "📥 Export"])
    
    with tab1:
        st.subheader("Summary Statistics")
        
        # Convert to DataFrame for easier manipulation
        if filtered_contracts:
            df = pd.DataFrame([{
                'Contract': c.contract_number or 'N/A',
                'Commodity': c.commodity or 'Unknown',
                'Bushels': c.bushels or 0,
                'Price': c.price or 0,
                'Basis': c.basis or 0,
                'Status': c.status or 'Unknown',
                'Date Sold': c.date_sold,
                'Buyer': c.buyer_name or 'N/A'
            } for c in filtered_contracts])
            
            # Summary by commodity
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Bushels by Commodity**")
                if not df.empty:
                    commodity_totals = df.groupby('Commodity')['Bushels'].sum().sort_values(ascending=False)
                    st.bar_chart(commodity_totals)
            
            with col2:
                st.write("**Contracts by Status**")
                if not df.empty:
                    status_counts = df['Status'].value_counts()
                    st.bar_chart(status_counts)
    
    with tab2:
        st.subheader("Contract Details")
        
        if filtered_contracts:
            # Create DataFrame
            df = pd.DataFrame([{
                'Contract #': c.contract_number or 'N/A',
                'Commodity': c.commodity or 'N/A',
                'Bushels': f"{c.bushels or 0:,}",
                'Price': f"${c.price or 0:.2f}",
                'Basis': f"${c.basis or 0:.2f}",
                'Status': c.status or 'N/A',
                'Date Sold': c.date_sold or 'N/A',
                'Buyer': c.buyer_name or 'N/A'
            } for c in filtered_contracts])
            
            st.dataframe(df, height=400)
        else:
            st.info("No contracts match the selected filters.")
    
    with tab3:
        st.subheader("Interactive Charts")
        
        if filtered_contracts:
            df = pd.DataFrame([{
                'Contract': c.contract_number or 'N/A',
                'Commodity': c.commodity or 'Unknown',
                'Bushels': c.bushels or 0,
                'Price': c.price or 0,
                'Basis': c.basis or 0,
                'Status': c.status or 'Unknown',
                'Date Sold': c.date_sold
            } for c in filtered_contracts])
            
            if not df.empty:
                # Chart 1: Bushels by Commodity (Bar)
                fig1 = px.bar(
                    df.groupby('Commodity')['Bushels'].sum().reset_index(),
                    x='Commodity',
                    y='Bushels',
                    title='Total Bushels by Commodity',
                    color='Bushels',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig1, width='stretch')
                
                # Chart 2: Price vs Bushels (Scatter)
                if df['Price'].notna().any() and df['Bushels'].notna().any():
                    fig2 = px.scatter(
                        df,
                        x='Bushels',
                        y='Price',
                        color='Commodity',
                        size='Bushels',
                        hover_data=['Contract'],
                        title='Price vs Bushels',
                        labels={'Price': 'Price per Bushel ($)', 'Bushels': 'Bushels'}
                    )
                    st.plotly_chart(fig2, width='stretch')
                
                # Chart 3: Status Distribution (Pie)
                status_counts = df['Status'].value_counts()
                fig3 = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title='Contracts by Status'
                )
                st.plotly_chart(fig3, width='stretch')
                
                # Chart 4: Contracts Over Time
                if 'Date Sold' in df.columns and df['Date Sold'].notna().any():
                    df['Date Sold'] = pd.to_datetime(df['Date Sold'])
                    daily = df.groupby(df['Date Sold'].dt.date).size().reset_index()
                    daily.columns = ['Date', 'Count']
                    fig4 = px.line(
                        daily,
                        x='Date',
                        y='Count',
                        title='Contracts Over Time',
                        markers=True
                    )
                    st.plotly_chart(fig4, width='stretch')
        else:
            st.info("No contracts to display.")
    
    with tab4:
        st.subheader("Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Export to Excel", width='stretch'):
                try:
                    if filtered_contracts:
                        df = pd.DataFrame([{
                            'Contract #': c.contract_number,
                            'Commodity': c.commodity,
                            'Bushels': c.bushels,
                            'Price': c.price,
                            'Basis': c.basis,
                            'Status': c.status,
                            'Date Sold': c.date_sold,
                            'Buyer': c.buyer_name
                        } for c in filtered_contracts])
                        
                        output_path = f"{PROJECT_PATH}/bushel_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        df.to_excel(output_path, index=False)
                        st.success(f"✓ Excel exported: {output_path}")
                        
                        # Provide download link
                        with open(output_path, 'rb') as f:
                            st.download_button(
                                label="Download Excel File",
                                data=f.read(),
                                file_name=f"bushel_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    else:
                        st.warning("No data to export.")
                except Exception as e:
                    st.error(f"Error exporting to Excel: {e}")
        
        with col2:
            if st.button("📄 Export to CSV", width='stretch'):
                try:
                    if filtered_contracts:
                        df = pd.DataFrame([{
                            'Contract #': c.contract_number,
                            'Commodity': c.commodity,
                            'Bushels': c.bushels,
                            'Price': c.price,
                            'Basis': c.basis,
                            'Status': c.status,
                            'Date Sold': c.date_sold,
                            'Buyer': c.buyer_name
                        } for c in filtered_contracts])
                        
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV File",
                            data=csv,
                            file_name=f"bushel_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("No data to export.")
                except Exception as e:
                    st.error(f"Error exporting to CSV: {e}")

if __name__ == "__main__":
    main()
