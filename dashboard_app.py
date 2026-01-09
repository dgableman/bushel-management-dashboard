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
    # Streamlit Cloud sets these environment variables or paths
    script_path = str(Path(__file__).absolute())
    return (os.getenv('STREAMLIT_SERVER_PORT') is not None or 
            os.getenv('STREAMLIT_SHARING_MODE') is not None or
            '/mount/src' in script_path or
            'streamlit.app' in os.getenv('STREAMLIT_SERVER_ADDRESS', ''))

# Set up paths based on environment
if is_colab():
    # Colab paths
    PROJECT_PATH = os.getenv('PROJECT_PATH', '/content/drive/MyDrive/Colab_Notebooks/Grain_Manager')
    DB_PATH = os.getenv('DB_PATH', '/content/drive/MyDrive/Colab_Notebooks/Grain_Manager/database/bushel_management.db')
elif is_streamlit_cloud():
    # Streamlit Cloud paths
    # Streamlit Cloud mounts the repo at /mount/src/REPO_NAME
    SCRIPT_DIR = Path(__file__).parent.absolute()
    PROJECT_PATH = str(SCRIPT_DIR)
    
    # Try Streamlit secrets first (recommended for production)
    # Note: st.secrets may not be available at import time, so we'll check it in the main function
    DB_PATH = os.getenv('DB_PATH')  # Check environment variable first
    
    # If not set, try to find the database file
    if not DB_PATH:
        # Try multiple possible paths for the database
        possible_paths = [
            str(SCRIPT_DIR / 'data' / 'bushel_management.db'),  # Standard path
            str(SCRIPT_DIR / 'data' / 'bushel-management.db'),   # Hyphen version
            '/mount/src/bushel-management-dashboard/data/bushel_management.db',  # Absolute Streamlit Cloud path
            '/mount/src/bushel-management-dashboard/data/bushel-management.db',  # Absolute with hyphen
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                DB_PATH = path
                break
        else:
            # Default to the most likely path
            DB_PATH = possible_paths[0]
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
from reports.commodity_utils import (
    normalize_commodity_name,
    get_commodities_for_normalized_name,
    get_all_normalized_commodities
)
from reports.crop_year_utils import get_current_crop_year, get_crop_year_date_range
from reports.crop_year_sales import calculate_crop_year_sales

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
        # Check Streamlit secrets first (for Streamlit Cloud deployment)
        db_path = DB_PATH
        try:
            if hasattr(st, 'secrets') and st.secrets.get("DB_PATH"):
                db_path = st.secrets.get("DB_PATH")
        except (AttributeError, FileNotFoundError, KeyError):
            pass  # Secrets not available or not configured, use default
        
        # Double-check file exists before trying to connect
        db_path_obj = Path(db_path)
        if not db_path_obj.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")
        
        # Try to create the session
        session = create_db_session(db_path)
        return session
    except FileNotFoundError as e:
        st.error(f"❌ {e}")
        st.info(f"**File check:** `os.path.exists('{DB_PATH}')` = {os.path.exists(DB_PATH)}")
        st.info(f"**Path check:** `Path('{DB_PATH}').exists()` = {Path(DB_PATH).exists()}")
        return None
    except Exception as e:
        st.error(f"❌ Database connection error: {type(e).__name__}: {e}")
        import traceback
        with st.expander("🔍 Full error details"):
            st.code(traceback.format_exc())
        return None

def main():
    """Main dashboard application."""
    
    # Title
    st.title("🌾 Bushel Management Dashboard")
    st.markdown("---")
    
    # Show database path (for debugging)
    with st.sidebar.expander("ℹ️ Settings", expanded=True):  # Expanded by default for debugging
        st.write(f"**Environment:** {'Streamlit Cloud' if is_streamlit_cloud() else 'Local' if not is_colab() else 'Colab'}")
        st.write(f"**Database Path:** `{DB_PATH}`")
        st.write(f"**Project Path:** `{PROJECT_PATH}`")
        st.write(f"**Script Location:** `{Path(__file__).absolute()}`")
        
        # Always show file listings for debugging
        data_folder = Path(DB_PATH).parent
        st.write(f"\n**Data folder path:** `{data_folder}`")
        st.write(f"**Data folder exists:** {'✅ Yes' if data_folder.exists() else '❌ No'}")
        
        if data_folder.exists():
            st.write(f"\n**Files in data folder:**")
            try:
                files = list(data_folder.iterdir())
                if files:
                    for f in sorted(files):
                        if f.is_file():
                            size_kb = f.stat().st_size / 1024
                            st.write(f"  📄 {f.name} ({size_kb:.1f} KB)")
                        else:
                            st.write(f"  📁 {f.name}/")
                else:
                    st.write("  (empty folder)")
            except Exception as e:
                st.write(f"  ❌ Error: {e}")
        else:
            st.write(f"  ❌ Data folder does not exist!")
        
        # Also check the project root to see what's there
        st.write(f"\n**Project root:** `{PROJECT_PATH}`")
        st.write(f"**Project root exists:** {'✅ Yes' if Path(PROJECT_PATH).exists() else '❌ No'}")
        try:
            root_files = list(Path(PROJECT_PATH).iterdir())
            st.write(f"**Files/folders in project root (first 20):**")
            for f in sorted(root_files)[:20]:
                if f.is_dir():
                    st.write(f"  📁 {f.name}/")
                else:
                    size_kb = f.stat().st_size / 1024
                    st.write(f"  📄 {f.name} ({size_kb:.1f} KB)")
        except Exception as e:
            st.write(f"  ❌ Error: {e}")
        
        # Check if database file exists
        file_exists_os = os.path.exists(DB_PATH)
        file_exists_path = Path(DB_PATH).exists()
        file_size = os.path.getsize(DB_PATH) / 1024 if file_exists_os else 0
        
        if file_exists_os and file_exists_path:
            st.success(f"✅ Database file found!")
            st.write(f"**File size:** {file_size:.1f} KB")
            st.write(f"**os.path.exists():** ✅")
            st.write(f"**Path().exists():** ✅")
        else:
            st.error(f"⚠️ Database file not found!")
            st.write(f"**Looking for:** `{DB_PATH}`")
            st.write(f"**os.path.exists():** {'✅' if file_exists_os else '❌'}")
            st.write(f"**Path().exists():** {'✅' if file_exists_path else '❌'}")
            if file_exists_os != file_exists_path:
                st.warning("⚠️ Path check mismatch! This might indicate a permission or path resolution issue.")
            st.info("""
            **To fix:**
            1. Check if file is in GitHub: https://github.com/dgableman/bushel-management-dashboard/tree/main/data
            2. If missing, add it and push to GitHub
            3. Reboot Streamlit Cloud app (⋮ menu → Reboot app)
            """)
        
        # Add a button to clear cache and retry
        if st.button("🔄 Clear Cache & Retry Connection"):
            st.cache_resource.clear()
            st.rerun()
    
    # Get database session
    db = get_database_session()
    if db is None:
        st.stop()
    
    # Get all contracts and settlements for calculations
    all_contracts = get_all_contracts(db)
    all_settlements = get_all_settlements(db)
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["🌾 Crop Year Sales", "📥 Export"])
    
    with tab1:
        st.subheader("Crop Year Sales")
        
        # Crop year selector
        current_crop_year = get_current_crop_year()
        selected_crop_year = st.selectbox(
            "Crop Year",
            options=list(range(current_crop_year - 5, current_crop_year + 2)),
            index=5,  # Default to current crop year
            format_func=lambda x: f"{x} (Oct 1, {x} - Sep 30, {x+1})"
        )
        
        start_date, end_date = get_crop_year_date_range(selected_crop_year)
        st.caption(f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
        
        # Calculate sales data
        sales_data = calculate_crop_year_sales(db, selected_crop_year)
        
        if not sales_data:
            st.info("No data found for the selected crop year.")
        else:
            # Crop price inputs
            st.markdown("### Crop Prices")
            crop_prices = {}
            crops = sorted(sales_data.keys())
            
            # Default prices
            default_prices = {
                'Corn': 4.0,
                'Soybeans': 10.0
            }
            
            price_cols = st.columns(min(4, len(crops)))
            for idx, crop in enumerate(crops):
                with price_cols[idx % 4]:
                    default_price = default_prices.get(crop, 0.0)
                    crop_prices[crop] = st.number_input(
                        f"{crop} Price ($/bu)",
                        min_value=0.0,
                        value=default_price,
                        step=0.01,
                        key=f"price_{crop}_{selected_crop_year}"
                    )
            
            # Calculate open revenue with prices
            for crop in crops:
                if crop in crop_prices:
                    sales_data[crop]['open_revenue'] = sales_data[crop]['open_bushels'] * crop_prices[crop]
            
            st.markdown("---")
            
            # Revenue Chart
            revenue_data = []
            total_sold_revenue = 0.0
            total_contracted_revenue = 0.0
            total_open_revenue = 0.0
            
            for crop in crops:
                data = sales_data[crop]
                sold = data['sold_revenue']
                contracted = data['contracted_revenue']
                open_rev = data['open_revenue']
                
                revenue_data.append({
                    'Crop': crop,
                    'Sold': sold,
                    'Contracted': contracted,
                    'Open': open_rev
                })
                
                total_sold_revenue += sold
                total_contracted_revenue += contracted
                total_open_revenue += open_rev
            
            if revenue_data:
                # Add total row to the list (will be last)
                revenue_data.append({
                    'Crop': 'TOTAL',
                    'Sold': total_sold_revenue,
                    'Contracted': total_contracted_revenue,
                    'Open': total_open_revenue
                })
                
                # Create dataframe with crops first, then TOTAL
                df_revenue = pd.DataFrame(revenue_data)
                df_revenue = df_revenue.set_index('Crop')
                
                # Calculate totals for each row
                df_revenue['Total'] = df_revenue['Sold'] + df_revenue['Contracted'] + df_revenue['Open']
                
                
                # Create stacked horizontal bar chart - add in correct order: Sold, Contracted, Open
                fig_revenue = go.Figure()
                
                # Add Sold first (leftmost in bar, first in legend)
                fig_revenue.add_trace(go.Bar(
                    name='Sold',
                    y=df_revenue.index,
                    x=df_revenue['Sold'],
                    orientation='h',
                    marker_color='#2ecc71',
                    hovertemplate='Sold: $%{x:,.2f}<extra></extra>',
                    legendrank=1,
                    showlegend=True
                ))
                # Add Contracted second (middle in bar, second in legend)
                fig_revenue.add_trace(go.Bar(
                    name='Contracted',
                    y=df_revenue.index,
                    x=df_revenue['Contracted'],
                    orientation='h',
                    marker_color='#3498db',
                    hovertemplate='Contracted: $%{x:,.2f}<extra></extra>',
                    legendrank=2,
                    showlegend=True
                ))
                # Add Open last (rightmost in bar, last in legend, shows total at end)
                fig_revenue.add_trace(go.Bar(
                    name='Open',
                    y=df_revenue.index,
                    x=df_revenue['Open'],
                    orientation='h',
                    marker_color='#e74c3c',
                    customdata=df_revenue['Total'],
                    hovertemplate='Open: $%{x:,.2f}<br>Total: $%{customdata:,.2f}<extra></extra>',
                    legendrank=3,
                    showlegend=True
                ))
                
                # Reverse the order so TOTAL appears at bottom
                category_array = list(df_revenue.index)
                category_array.reverse()  # Reverse so TOTAL (last) appears at bottom
                
                fig_revenue.update_layout(
                    barmode='stack',
                    title='Revenue',
                    xaxis_title='Revenue ($)',
                    yaxis_title='',  # Remove crop label
                    height=max(400, (len(crops) + 1) * 50),  # +1 for total row
                    hovermode='y unified',
                    hoverlabel=dict(
                        bgcolor='white',
                        bordercolor='black',
                        font_size=12,
                        namelength=-1
                    ),
                    yaxis=dict(categoryorder='array', categoryarray=category_array, showticklabels=True),
                    legend=dict(
                        traceorder='normal',
                        itemclick=False,
                        itemdoubleclick=False
                    )
                )
                st.plotly_chart(fig_revenue, width='stretch')
            
            st.markdown("---")
            
            # Bushels Chart
            bushels_data = []
            total_sold_bushels = 0
            total_contracted_bushels = 0
            total_open_bushels = 0
            
            for crop in crops:
                data = sales_data[crop]
                sold = data['sold_bushels']
                contracted = data['contracted_bushels']
                open_bu = data['open_bushels']
                
                bushels_data.append({
                    'Crop': crop,
                    'Sold': sold,
                    'Contracted': contracted,
                    'Open': open_bu
                })
                
                total_sold_bushels += sold
                total_contracted_bushels += contracted
                total_open_bushels += open_bu
            
            if bushels_data:
                # Add total row to the list (will be last)
                bushels_data.append({
                    'Crop': 'TOTAL',
                    'Sold': total_sold_bushels,
                    'Contracted': total_contracted_bushels,
                    'Open': total_open_bushels
                })
                
                # Create dataframe with crops first, then TOTAL
                df_bushels = pd.DataFrame(bushels_data)
                df_bushels = df_bushels.set_index('Crop')
                
                # Calculate totals for each row
                df_bushels['Total'] = df_bushels['Sold'] + df_bushels['Contracted'] + df_bushels['Open']
                
                # Create stacked horizontal bar chart - add in correct order: Sold, Contracted, Open
                fig_bushels = go.Figure()
                
                # Add Sold first (leftmost in bar, first in legend)
                fig_bushels.add_trace(go.Bar(
                    name='Sold',
                    y=df_bushels.index,
                    x=df_bushels['Sold'],
                    orientation='h',
                    marker_color='#2ecc71',
                    hovertemplate='Sold: %{x:,.0f} bu<extra></extra>',
                    legendrank=1,
                    showlegend=True
                ))
                # Add Contracted second (middle in bar, second in legend)
                fig_bushels.add_trace(go.Bar(
                    name='Contracted',
                    y=df_bushels.index,
                    x=df_bushels['Contracted'],
                    orientation='h',
                    marker_color='#3498db',
                    hovertemplate='Contracted: %{x:,.0f} bu<extra></extra>',
                    legendrank=2,
                    showlegend=True
                ))
                # Add Open last (rightmost in bar, last in legend, shows total at end)
                fig_bushels.add_trace(go.Bar(
                    name='Open',
                    y=df_bushels.index,
                    x=df_bushels['Open'],
                    orientation='h',
                    marker_color='#e74c3c',
                    customdata=df_bushels['Total'],
                    hovertemplate='Open: %{x:,.0f} bu<br><b>Total: %{customdata:,.0f} bu</b><extra></extra>',
                    legendrank=3,
                    showlegend=True
                ))
                
                # Reverse the order so TOTAL appears at bottom
                category_array = list(df_bushels.index)
                category_array.reverse()  # Reverse so TOTAL (last) appears at bottom
                
                fig_bushels.update_layout(
                    barmode='stack',
                    title='Bushels',
                    xaxis_title='Bushels',
                    yaxis_title='',  # Remove crop label
                    height=max(400, (len(crops) + 1) * 50),  # +1 for total row
                    hovermode='y unified',
                    hoverlabel=dict(
                        bgcolor='white',
                        bordercolor='black',
                        font_size=12,
                        namelength=-1
                    ),
                    yaxis=dict(categoryorder='array', categoryarray=category_array, showticklabels=True),
                    legend=dict(
                        traceorder='normal',
                        itemclick=False,
                        itemdoubleclick=False
                    )
                )
                st.plotly_chart(fig_bushels, width='stretch')
    
    with tab2:
        st.subheader("Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Export to Excel", width='stretch'):
                try:
                    from openpyxl import Workbook
                    from openpyxl.styles import Font, PatternFill, Alignment
                    
                    wb = Workbook()
                    
                    # Contracts sheet
                    if all_contracts:
                        ws_contracts = wb.active
                        ws_contracts.title = "Contracts"
                        headers = ['Contract #', 'Commodity', 'Bushels', 'Price', 'Basis', 'Status', 'Date Sold', 'Buyer']
                        ws_contracts.append(headers)
                        
                        # Style headers
                        header_fill = PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
                        header_font = Font(bold=True, color="FFFFFF")
                        for cell in ws_contracts[1]:
                            cell.fill = header_fill
                            cell.font = header_font
                            cell.alignment = Alignment(horizontal='center')
                        
                        for c in all_contracts:
                            ws_contracts.append([
                                c.contract_number, normalize_commodity_name(db, c.commodity), c.bushels, c.price, 
                                c.basis, c.status, c.date_sold, c.buyer_name
                            ])
                    
                    # Settlements sheet
                    filtered_settlements = [s for s in all_settlements if s.status != 'Header']
                    if filtered_settlements:
                        ws_settlements = wb.create_sheet("Settlements")
                        headers = ['Settlement ID', 'Contract #', 'Bushels', 'Price', 'Date Delivered', 'Bin', 'Buyer', 'Gross Amount', 'Net Amount', 'Adjustments', 'Status']
                        ws_settlements.append(headers)
                        
                        # Style headers
                        for cell in ws_settlements[1]:
                            cell.fill = header_fill
                            cell.font = header_font
                            cell.alignment = Alignment(horizontal='center')
                        
                        for s in filtered_settlements:
                            ws_settlements.append([
                                s.settlement_ID, s.contract_id, s.bushels, s.price,
                                s.date_delivered, s.bin, s.buyer, s.gross_amount,
                                s.net_amount, s.adjustments, s.status
                            ])
                    
                    output_path = f"{PROJECT_PATH}/bushel_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    wb.save(output_path)
                    st.success(f"✓ Excel exported: {output_path}")
                    
                    # Provide download link
                    with open(output_path, 'rb') as f:
                        st.download_button(
                            label="Download Excel File",
                            data=f.read(),
                            file_name=f"bushel_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                except Exception as e:
                    st.error(f"Error exporting to Excel: {e}")
                    import traceback
                    with st.expander("Error details"):
                        st.code(traceback.format_exc())
        
        with col2:
            if st.button("📄 Export to CSV", width='stretch'):
                try:
                    # Create a combined CSV or separate files
                    st.write("**Export Options:**")
                    
                    # Contracts CSV
                    if all_contracts:
                        df_contracts = pd.DataFrame([{
                            'Contract #': c.contract_number,
                            'Commodity': normalize_commodity_name(db, c.commodity),
                            'Bushels': c.bushels,
                            'Price': c.price,
                            'Basis': c.basis,
                            'Status': c.status,
                            'Date Sold': c.date_sold,
                            'Buyer': c.buyer_name
                        } for c in all_contracts])
                        
                        csv_contracts = df_contracts.to_csv(index=False)
                        st.download_button(
                            label="Download Contracts CSV",
                            data=csv_contracts,
                            file_name=f"contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    # Settlements CSV
                    filtered_settlements = [s for s in all_settlements if s.status != 'Header']
                    if filtered_settlements:
                        df_settlements = pd.DataFrame([{
                            'Settlement ID': s.settlement_ID,
                            'Contract #': s.contract_id,
                            'Bushels': s.bushels,
                            'Price': s.price,
                            'Date Delivered': s.date_delivered,
                            'Bin': s.bin,
                            'Buyer': s.buyer,
                            'Gross Amount': s.gross_amount,
                            'Net Amount': s.net_amount,
                            'Adjustments': s.adjustments,
                            'Status': s.status
                        } for s in filtered_settlements])
                        
                        csv_settlements = df_settlements.to_csv(index=False)
                        st.download_button(
                            label="Download Settlements CSV",
                            data=csv_settlements,
                            file_name=f"settlements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    if not all_contracts and not filtered_settlements:
                        st.warning("No data to export.")
                except Exception as e:
                    st.error(f"Error exporting to CSV: {e}")
                    import traceback
                    with st.expander("Error details"):
                        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
