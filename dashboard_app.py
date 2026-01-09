"""
Standalone Bushel Management Dashboard Application
Run this script to launch the interactive dashboard in a web browser.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, date
import streamlit as st
import yfinance as yf

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
    # Default local database path - use the main Bushel_Management project database
    # This allows the reporting project to always use the most up-to-date database
    default_local_db = Path.home() / 'PycharmProjects' / 'Bushel_Management' / 'data' / 'bushel_management.db'
    # Fallback to local data folder if main project database doesn't exist
    if not default_local_db.exists():
        default_local_db = SCRIPT_DIR / 'data' / 'bushel_management.db'
    DB_PATH = os.getenv('DB_PATH', str(default_local_db))

# Add project to path
if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

from database.db_connection import create_db_session
from reports.contract_queries import get_all_contracts, get_active_contracts
from reports.settlement_queries import get_all_settlements
from reports.bin_queries import get_bins_with_storage_by_crop
from reports.commodity_utils import (
    normalize_commodity_name,
    get_commodities_for_normalized_name,
    get_all_normalized_commodities
)
from reports.vendor_utils import normalize_vendor_name, get_all_normalized_vendors
from reports.crop_year_utils import get_current_crop_year, get_crop_year_date_range, get_crop_year_from_date
from reports.crop_year_sales import calculate_crop_year_sales
from reports.monthly_deliveries import (
    calculate_monthly_deliveries,
    get_month_name_for_crop_year
)

# Set page config for full-width layout
st.set_page_config(
    page_title="Bushel Management Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_drilldown_details(
    db,
    crop: str,
    status: str,
    crop_year: int,
    all_contracts,
    all_settlements
):
    """
    Get detailed contract and settlement data for drill-down view.
    
    Args:
        db: Database session
        crop: Normalized crop name
        status: Status to filter ('Sold', 'Contracted', 'Open')
        crop_year: Crop year
        all_contracts: List of all contracts
        all_settlements: List of all settlements
        
    Returns:
        Dictionary with 'contracts' and 'settlements' lists
    """
    from reports.crop_year_utils import (
        is_date_in_crop_year, 
        calculate_settlement_revenue, 
        calculate_partial_contract_remaining,
        get_starting_bushels,
        get_crop_year_date_range
    )
    from reports.commodity_utils import normalize_commodity_name, get_commodities_for_normalized_name
    
    start_date, end_date = get_crop_year_date_range(crop_year)
    
    # Get commodities that map to this normalized crop
    crop_aliases = get_commodities_for_normalized_name(db, crop)
    
    details = {
        'contracts': [],
        'settlements': []
    }
    
    if status == 'Sold':
        # Show all settlement lines (not just headers) for this crop and crop year
        # Group by settlement ID and contract ID, sum bushels and amounts
        settlement_groups = {}  # Key: (settlement_ID, contract_id), Value: aggregated data
        
        for settlement in all_settlements:
            # Skip header rows - we want the actual line items
            if settlement.status == 'Header':
                continue
            if not settlement.date_delivered or not is_date_in_crop_year(settlement.date_delivered, crop_year):
                continue
            if not settlement.commodity:
                continue
            normalized = normalize_commodity_name(db, settlement.commodity)
            if normalized != crop:
                continue
            
            # Get contract ID - if None, empty, or "none", it's an Open Sale
            contract_id = settlement.contract_id
            if contract_id is None:
                contract_id = 'none'
            elif isinstance(contract_id, str) and contract_id.strip().lower() in ['none', '', 'null']:
                contract_id = 'none'
            else:
                contract_id = str(contract_id).strip()
            
            settlement_id = settlement.settlement_ID
            
            # Create key for grouping (settlement_ID, contract_id)
            group_key = (settlement_id, contract_id)
            
            if group_key not in settlement_groups:
                settlement_groups[group_key] = {
                    'settlement_id': settlement_id,
                    'contract_id': 'Open Sale' if contract_id == 'none' else contract_id,
                    'date_delivered': settlement.date_delivered,
                    'bushels': 0,
                    'price': settlement.price,
                    'gross_amount': 0.0,
                    'net_amount': 0.0,
                    'buyer': settlement.buyer,
                    'commodity': settlement.commodity
                }
            
            # Sum bushels and amounts for this group
            settlement_groups[group_key]['bushels'] += (settlement.bushels or 0)
            settlement_groups[group_key]['gross_amount'] += (settlement.gross_amount or 0.0)
            # For net_amount, prefer net_amount, fall back to gross_amount
            if settlement.net_amount:
                settlement_groups[group_key]['net_amount'] += settlement.net_amount
            elif settlement.gross_amount:
                settlement_groups[group_key]['net_amount'] += settlement.gross_amount
        
        # Convert grouped data to list
        for group_data in settlement_groups.values():
            details['settlements'].append(group_data)
    
    elif status == 'Contracted':
        # Show active open or partial contracts for this crop and crop year
        from reports.crop_year_utils import calculate_partial_contract_remaining
        
        for contract in all_contracts:
            # Filter by status='Active'
            contract_status = (contract.status or '').strip()
            if contract_status.lower() != 'active':
                continue
            
            if not contract.delivery_start or not is_date_in_crop_year(contract.delivery_start, crop_year):
                continue
            if not contract.commodity:
                continue
            normalized = normalize_commodity_name(db, contract.commodity)
            if normalized != crop:
                continue
            
            fill_status = contract.fill_status or 'None'
            if fill_status not in ['None', 'Partial']:
                continue
            
            # Calculate remaining if partial
            if fill_status == 'None':
                remaining_bushels = contract.bushels or 0
                remaining_revenue = remaining_bushels * (contract.price or 0.0)
            else:
                remaining_revenue, remaining_bushels = calculate_partial_contract_remaining(
                    contract, all_settlements
                )
            
            if remaining_bushels > 0:
                details['contracts'].append({
                    'contract_number': contract.contract_number,
                    'commodity': contract.commodity,
                    'bushels': contract.bushels or 0,
                    'remaining_bushels': remaining_bushels,
                    'price': contract.price,
                    'remaining_revenue': remaining_revenue,
                    'fill_status': fill_status,
                    'delivery_start': contract.delivery_start,
                    'buyer': contract.buyer_name,
                    'date_sold': contract.date_sold
                })
    
    elif status == 'Open':
        # Calculate Open bushels: Starting - Sold - Contracted
        from reports.crop_year_utils import get_starting_bushels, is_date_in_crop_year, calculate_partial_contract_remaining
        
        starting_bushels = get_starting_bushels(db, crop_year, crop)
        
        # Calculate sold bushels (all settlement header rows for this crop/year)
        # Use same logic as calculate_crop_year_sales
        sold_bushels = 0
        for settlement in all_settlements:
            # Check status - handle case-insensitive and various formats
            status = (settlement.status or '').strip()
            if status.lower() != 'header':
                continue
            if not settlement.date_delivered or not is_date_in_crop_year(settlement.date_delivered, crop_year):
                continue
            if not settlement.commodity:
                continue
            normalized = normalize_commodity_name(db, settlement.commodity)
            if normalized == crop:
                if settlement.bushels:
                    sold_bushels += settlement.bushels
        
        # Calculate contracted bushels (remaining bushels on active open/partial contracts for this crop/year)
        contracted_bushels = 0
        for contract in all_contracts:
            # Filter by status='Active'
            contract_status = (contract.status or '').strip()
            if contract_status.lower() != 'active':
                continue
            
            if not contract.delivery_start or not is_date_in_crop_year(contract.delivery_start, crop_year):
                continue
            if not contract.commodity:
                continue
            normalized = normalize_commodity_name(db, contract.commodity)
            if normalized != crop:
                continue
            
            fill_status = contract.fill_status or 'None'
            if fill_status not in ['None', 'Partial']:
                continue
            
            if fill_status == 'None':
                remaining_bushels = contract.bushels or 0
            else:
                _, remaining_bushels = calculate_partial_contract_remaining(contract, all_settlements)
            
            if remaining_bushels > 0:
                contracted_bushels += remaining_bushels
        
        open_bushels = max(0, starting_bushels - sold_bushels - contracted_bushels)
        
        details['summary'] = {
            'starting_bushels': starting_bushels,
            'sold_bushels': sold_bushels,
            'contracted_bushels': contracted_bushels,
            'open_bushels': open_bushels
        }
    
    return details


@st.cache_resource
def get_database_session(_username):
    """
    Create and cache database session using username-based database path.
    
    Args:
        _username: Username (prefixed with _ to indicate it's used for caching)
    """
    try:
        if not _username:
            return None  # Username not set yet
        
        # Construct database path based on username
        # Use the same directory as the default DB_PATH but with username prefix
        default_db_path = Path(DB_PATH)
        db_dir = default_db_path.parent
        db_filename = f"{_username}_bushel_management.db"
        db_path = str(db_dir / db_filename)
        
        # Check Streamlit secrets first (for Streamlit Cloud deployment)
        # This can override the username-based path if needed
        try:
            if hasattr(st, 'secrets') and st.secrets.get("DB_PATH"):
                db_path = st.secrets.get("DB_PATH")
        except (AttributeError, FileNotFoundError, KeyError):
            pass  # Secrets not available or not configured, use username-based path
        
        # Double-check file exists before trying to connect
        db_path_obj = Path(db_path)
        if not db_path_obj.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")
        
        # Try to create the session
        session = create_db_session(db_path)
        return session
    except FileNotFoundError as e:
        st.error(f"❌ {e}")
        st.info(f"**Expected database path:** `{db_path}`")
        st.info(f"**File exists:** {Path(db_path).exists()}")
        return None
    except Exception as e:
        st.error(f"❌ Database connection error: {type(e).__name__}: {e}")
        import traceback
        with st.expander("🔍 Full error details"):
            st.code(traceback.format_exc())
        return None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_market_prices():
    """
    Fetch current market prices from Yahoo Finance.
    Returns default prices with fallback if API fails.
    Futures prices are in cents, so divide by 100 to get dollars per bushel.
    """
    default_prices = {
        'Corn': 4.0,
        'Soybeans': 10.0
    }
    
    try:
        # Fetch corn futures price (ZC=F)
        corn_ticker = yf.Ticker("ZC=F")
        corn_data = corn_ticker.history(period="1d")
        if not corn_data.empty:
            corn_price_cents = float(corn_data['Close'].iloc[-1])
            corn_price_dollars = corn_price_cents / 100.0
            default_prices['Corn'] = max(0.0, corn_price_dollars - 0.30)  # Divide by 100, then subtract 30 cents
        
        # Fetch soybean futures price (ZS=F)
        bean_ticker = yf.Ticker("ZS=F")
        bean_data = bean_ticker.history(period="1d")
        if not bean_data.empty:
            bean_price_cents = float(bean_data['Close'].iloc[-1])
            bean_price_dollars = bean_price_cents / 100.0
            default_prices['Soybeans'] = max(0.0, bean_price_dollars - 0.45)  # Divide by 100, then subtract 45 cents
    except Exception as e:
        # If yfinance fails, use default values
        # Silently fail and use hardcoded defaults
        pass
    
    return default_prices


def main():
    """Main dashboard application."""
    
    # Require username input
    if 'username' not in st.session_state or not st.session_state.username:
        st.title("🌾 Bushel Management Dashboard")
        st.markdown("---")
        st.markdown("### Please enter your username to continue")
        
        username = st.text_input(
            "Username:",
            key="username_input",
            placeholder="Enter your username",
            help="This will be used to load your database file: {username}_bushel_management.db"
        )
        
        if username and username.strip():
            # Store username in session state
            st.session_state.username = username.strip()
            st.rerun()  # Rerun to load the dashboard with the username
        else:
            st.info("👆 Please enter a username above to access the dashboard.")
            st.stop()
    
    # Title
    st.title("🌾 Bushel Management Dashboard")
    st.markdown("---")
    
    # Show database path (for debugging)
    username = st.session_state.get('username', 'Not set')
    default_db_path = Path(DB_PATH)
    db_dir = default_db_path.parent
    user_db_path = db_dir / f"{username}_bushel_management.db"
    
    with st.sidebar.expander("ℹ️ Settings", expanded=True):  # Expanded by default for debugging
        st.write(f"**Username:** `{username}`")
        
        # Allow user to change username
        if st.button("🔄 Change Username", key="change_username_btn"):
            st.session_state.username = None
            st.rerun()
        
        st.write(f"**Environment:** {'Streamlit Cloud' if is_streamlit_cloud() else 'Local' if not is_colab() else 'Colab'}")
        st.write(f"**Database Path:** `{user_db_path}`")
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
    # Get database session using username
    username = st.session_state.get('username')
    db = get_database_session(username) if username else None
    if db is None:
        st.stop()
    
    # Get all contracts and settlements for calculations
    all_contracts = get_all_contracts(db)
    all_settlements = get_all_settlements(db)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🌾 Crop Year Sales", "📅 Deliveries by Month", "📦 Bins", "📦 Bins 2 (Not Working)", "📋 Contracts", "📥 Export"])
    
    with tab1:
        st.subheader("Crop Year Sales")
        
        # Initialize drill-down session state
        if 'drilldown_crop' not in st.session_state:
            st.session_state.drilldown_crop = None
        if 'drilldown_status' not in st.session_state:
            st.session_state.drilldown_status = None
        if 'drilldown_status' not in st.session_state:
            st.session_state.drilldown_status = None
        
        # Crop year selector
        current_crop_year = get_current_crop_year()
        selected_crop_year = st.selectbox(
            "Crop Year",
            options=list(range(current_crop_year - 5, current_crop_year + 2)),
            index=5,  # Default to current crop year
            format_func=lambda x: f"{x} (Oct 1, {x} - Sep 30, {x+1})"
        )
        
        # Clear drill-down if crop year changes
        if 'last_crop_year' not in st.session_state:
            st.session_state.last_crop_year = selected_crop_year
        elif st.session_state.last_crop_year != selected_crop_year:
            st.session_state.drilldown_crop = None
            st.session_state.drilldown_status = None
            st.session_state.last_crop_year = selected_crop_year
        
        start_date, end_date = get_crop_year_date_range(selected_crop_year)
        st.caption(f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
        
        # Calculate sales data
        sales_data = calculate_crop_year_sales(db, selected_crop_year)
        
        # Debug: Show raw data
        if st.checkbox("🔍 Show raw sales data", key="debug_sales_data"):
            st.write("**Sales Data:**")
            st.json(sales_data)
        
        if not sales_data:
            st.info("No data found for the selected crop year.")
        else:
            # Crop price inputs
            st.markdown("### Crop Prices")
            crop_prices = {}
            crops = sorted(sales_data.keys())
            
            # Get default prices from market data (yfinance)
            default_prices = get_market_prices()
            
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
                    hovertemplate='Sold: $%{x:,.0f}<extra></extra>',
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
                    hovertemplate='Contracted: $%{x:,.0f}<extra></extra>',
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
                    hovertemplate='Open: $%{x:,.0f}<br>Total: $%{customdata:,.0f}<extra></extra>',
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
                        itemclick='toggle',
                        itemdoubleclick=False
                    ),
                    clickmode='event+select'
                )
                # Debug toggle (temporary)
                debug_selection = st.checkbox("🔍 Show selection debug info", key="debug_revenue_selection")
                
                # Handle chart selection - Streamlit stores selection in session state
                chart_revenue = st.plotly_chart(fig_revenue, width='stretch', on_select="rerun", key="revenue_chart")
                
                # Check for selection - prioritize session state key first
                # IMPORTANT: Check immediately after chart render, before any other processing
                selection_data = None
                selection_key_found = None
                
                # First, check the session state key directly (this is where Streamlit stores it)
                if 'revenue_chart' in st.session_state:
                    chart_state = st.session_state['revenue_chart']
                    if isinstance(chart_state, dict) and 'selection' in chart_state:
                        sel = chart_state['selection']
                        # Check if there are actual points selected (not empty)
                        if isinstance(sel, dict):
                            points_list = sel.get('points', [])
                            # Only process if points array is not empty
                            if points_list and len(points_list) > 0:
                                selection_data = sel
                                selection_key_found = 'revenue_chart'
                
                # Fallback: Check if chart_revenue return value has selection
                if selection_data is None and chart_revenue is not None:
                    if isinstance(chart_revenue, dict) and 'selection' in chart_revenue:
                        sel = chart_revenue['selection']
                        if isinstance(sel, dict):
                            points_list = sel.get('points', [])
                            if points_list and len(points_list) > 0:
                                selection_data = sel
                    elif hasattr(chart_revenue, 'selection'):
                        sel = chart_revenue.selection
                        if hasattr(sel, 'points') and sel.points and len(sel.points) > 0:
                            selection_data = sel
                
                if debug_selection:
                    st.write("**Debug Info:**")
                    st.write(f"- chart_revenue type: {type(chart_revenue)}")
                    st.write(f"- chart_revenue value: {chart_revenue}")
                    st.write(f"- session_state['revenue_chart']: {st.session_state.get('revenue_chart', 'NOT FOUND')}")
                    st.write(f"- selection_data: {selection_data}")
                    st.write(f"- selection_key_found: {selection_key_found}")
                    if selection_data and 'points' in selection_data:
                        st.write(f"- points count: {len(selection_data.get('points', []))}")
                        st.write(f"- points: {selection_data.get('points', [])}")
                
                # Process selection if found (only if points exist)
                if selection_data is not None:
                    # Extract points from selection data
                    points = None
                    if isinstance(selection_data, dict):
                        points = selection_data.get('points', [])
                    elif hasattr(selection_data, 'points'):
                        points = selection_data.points
                    elif isinstance(selection_data, list):
                        points = selection_data
                    
                    if points and len(points) > 0:
                        # Get crop name from the first point (all points at same y-position have same crop name)
                        crop_name = None
                        if isinstance(points[0], dict):
                            crop_name = points[0].get('y') or points[0].get('label')
                        else:
                            crop_name = getattr(points[0], 'y', None) or getattr(points[0], 'label', None)
                        
                        if debug_selection:
                            st.write(f"**Processing selection:**")
                            st.write(f"- Total points selected: {len(points)}")
                            st.write(f"- crop_name: {crop_name}")
                            st.write(f"- All points: {points}")
                        
                        # Ignore clicks on TOTAL - clear selection and do nothing else
                        if isinstance(crop_name, str) and crop_name == 'TOTAL':
                            if 'revenue_chart' in st.session_state:
                                del st.session_state['revenue_chart']
                            # Don't process further for TOTAL
                        # Navigate to detail page for this crop (only if not TOTAL)
                        elif isinstance(crop_name, str) and crop_name != 'TOTAL':
                            st.session_state.drilldown_crop = crop_name
                            st.session_state.drilldown_status = None  # None means show all statuses
                            st.session_state.selected_crop_year = selected_crop_year  # Store for detail page
                            
                            # Clear selection AFTER processing to prevent re-triggering
                            if 'revenue_chart' in st.session_state:
                                del st.session_state['revenue_chart']
                            
                            # Navigate to detail page
                            st.switch_page("pages/crop_details.py")
            
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
                        itemclick='toggle',
                        itemdoubleclick=False
                    ),
                    clickmode='event+select'
                )
                # Debug toggle (temporary)
                debug_selection_bushels = st.checkbox("🔍 Show selection debug info", key="debug_bushels_selection")
                
                # Handle chart selection - Streamlit stores selection in session state
                chart_bushels = st.plotly_chart(fig_bushels, width='stretch', on_select="rerun", key="bushels_chart")
                
                # Check for selection - try multiple approaches
                selection_data = None
                selection_key_found = None
                
                # Approach 1: Check if chart_bushels return value is the selection
                if chart_bushels is not None:
                    if isinstance(chart_bushels, dict):
                        if 'selection' in chart_bushels:
                            selection_data = chart_bushels['selection']
                        elif 'points' in chart_bushels:
                            selection_data = chart_bushels
                    elif hasattr(chart_bushels, 'selection'):
                        selection_data = chart_bushels.selection
                    elif hasattr(chart_bushels, 'points'):
                        selection_data = chart_bushels
                
                # Approach 2: Check session state for selection keys
                if selection_data is None:
                    all_keys = list(st.session_state.keys())
                    # Try common key patterns
                    possible_keys = [
                        "bushels_chart.selection",
                        "bushels_chart_selection", 
                        "bushels_chart",
                        f"bushels_chart.selection.{selected_crop_year}"
                    ]
                    
                    for key in possible_keys:
                        if key in st.session_state:
                            val = st.session_state[key]
                            if val is not None and (hasattr(val, 'points') or isinstance(val, (dict, list))):
                                selection_data = val
                                selection_key_found = key
                                break
                    
                    # Also check all keys containing 'bushels' and 'selection'
                    if selection_data is None:
                        for key in all_keys:
                            if 'bushels_chart' in key.lower() and 'selection' in key.lower():
                                val = st.session_state[key]
                                if val is not None:
                                    selection_data = val
                                    selection_key_found = key
                                    break
                
                if debug_selection_bushels:
                    st.write("**Debug Info:**")
                    st.write(f"- chart_bushels type: {type(chart_bushels)}")
                    st.write(f"- chart_bushels value: {chart_bushels}")
                    st.write(f"- selection_data: {selection_data}")
                    st.write(f"- selection_key_found: {selection_key_found}")
                    st.write("**All session state keys:**")
                    for key in sorted(st.session_state.keys()):
                        if 'bushels' in key.lower() or 'selection' in key.lower():
                            st.write(f"- `{key}`: {st.session_state[key]}")
                
                # Also check if chart_bushels return value has selection
                if selection_data is None:
                    if hasattr(chart_bushels, 'selection'):
                        selection_data = chart_bushels.selection
                    elif isinstance(chart_bushels, dict) and 'selection' in chart_bushels:
                        selection_data = chart_bushels['selection']
                    elif chart_bushels is not None:
                        # chart_bushels might be the selection data itself
                        if hasattr(chart_bushels, 'points') or isinstance(chart_bushels, (list, dict)):
                            selection_data = chart_bushels
                
                # Process selection if found
                if selection_data is not None:
                    # Extract points from selection data
                    points = None
                    if isinstance(selection_data, dict):
                        points = selection_data.get('points', [])
                    elif hasattr(selection_data, 'points'):
                        points = selection_data.points
                    elif isinstance(selection_data, list):
                        points = selection_data
                    
                    if points and len(points) > 0:
                        # Get crop name from the first point (all points at same y-position have same crop name)
                        crop_name = None
                        if isinstance(points[0], dict):
                            crop_name = points[0].get('y') or points[0].get('label')
                        else:
                            crop_name = getattr(points[0], 'y', None) or getattr(points[0], 'label', None)
                        
                        # Ignore clicks on TOTAL - clear selection and do nothing else
                        if isinstance(crop_name, str) and crop_name == 'TOTAL':
                            if 'bushels_chart' in st.session_state:
                                del st.session_state['bushels_chart']
                            # Don't process further for TOTAL - exit early
                            pass
                        # Navigate to detail page for this crop (only if not TOTAL)
                        elif isinstance(crop_name, str) and crop_name != 'TOTAL':
                            st.session_state.drilldown_crop = crop_name
                            st.session_state.drilldown_status = None  # None means show all statuses
                            st.session_state.selected_crop_year = selected_crop_year  # Store for detail page
                            
                            # Clear selection AFTER processing to prevent re-triggering
                            if 'bushels_chart' in st.session_state:
                                del st.session_state['bushels_chart']
                            
                            # Navigate to detail page
                            st.switch_page("pages/crop_details.py")
            
    
    with tab2:
        st.subheader("Deliveries by Month")
        
        # Crop year selector (same as Crop Year Sales tab)
        current_crop_year = get_current_crop_year()
        selected_crop_year = st.selectbox(
            "Crop Year",
            options=list(range(current_crop_year - 5, current_crop_year + 2)),
            index=5,  # Default to current crop year
            format_func=lambda x: f"{x} (Oct 1, {x} - Sep 30, {x+1})",
            key="deliveries_crop_year"
        )
        
        start_date, end_date = get_crop_year_date_range(selected_crop_year)
        st.caption(f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
        
        # Calculate monthly deliveries data
        monthly_data = calculate_monthly_deliveries(
            db, 
            selected_crop_year,
            all_contracts=all_contracts,
            all_settlements=all_settlements
        )
        
        if not monthly_data:
            st.info("No data found for the selected crop year.")
        else:
            # Find the first month with data across all crops
            all_months = set()
            for crop_data in monthly_data.values():
                all_months.update(crop_data.keys())
            
            if not all_months:
                st.info("No monthly data available.")
            else:
                first_month = min(all_months)
                months_to_show = sorted([m for m in all_months if m >= first_month])
                
                # Get all month names in crop year order for proper x-axis ordering
                all_month_names_in_order = [get_month_name_for_crop_year(m) for m in months_to_show]
                
                # Create chart data
                crops = sorted(monthly_data.keys())
                
                # Create figure with dual y-axis
                fig = go.Figure()
                
                # Prepare data for each crop
                for crop in crops:
                    crop_months = monthly_data[crop]
                    
                    # Only include months from first_month onwards
                    months = [m for m in months_to_show if m in crop_months]
                    
                    if not months:
                        continue
                    
                    # Get month names for x-axis (in crop year order)
                    month_names = [get_month_name_for_crop_year(m) for m in months]
                    
                    # Get prices and bushels
                    prices = [crop_months[m]['price'] for m in months]
                    bushels = [crop_months[m]['bushels'] for m in months]
                    
                    # Add price line with diamond markers (left y-axis)
                    fig.add_trace(go.Scatter(
                        x=month_names,
                        y=prices,
                        mode='lines+markers',
                        marker=dict(symbol='diamond', size=10),
                        name=f'{crop} Price',
                        yaxis='y',
                        line=dict(width=2),
                        hovertemplate=f'<b>{crop} Price</b><br>Month: %{{x}}<br>Price: $%{{y:.2f}}/bu<extra></extra>'
                    ))
                    
                    # Add bushels line with square markers (right y-axis)
                    fig.add_trace(go.Scatter(
                        x=month_names,
                        y=bushels,
                        mode='lines+markers',
                        marker=dict(symbol='square', size=10),
                        name=f'{crop} Bushels',
                        yaxis='y2',
                        line=dict(width=2, dash='dot'),
                        hovertemplate=f'<b>{crop} Bushels</b><br>Month: %{{x}}<br>Bushels: %{{y:,.0f}} bu<extra></extra>'
                    ))
                
                # Update layout with dual y-axes - ensure months stay in crop year order
                fig.update_layout(
                    title='Deliveries by Month',
                    xaxis=dict(
                        title='Month',
                        tickangle=-45 if len(months_to_show) > 6 else 0,
                        categoryorder='array',
                        categoryarray=all_month_names_in_order
                    ),
                    yaxis=dict(
                        title='Price ($/bu)',
                        side='left',
                        showgrid=True
                    ),
                    yaxis2=dict(
                        title='Bushels',
                        side='right',
                        overlaying='y',
                        showgrid=False
                    ),
                    hovermode='x unified',
                    height=600,
                    legend=dict(
                        traceorder='normal',
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=1.01
                    )
                )
                
                st.plotly_chart(fig, width='stretch')
                
                # Cumulative Deliveries Chart
                st.markdown("### Cumulative Deliveries by Month")
                
                # Create cumulative chart
                fig_cumulative = go.Figure()
                
                # Prepare cumulative data for each crop
                for crop in crops:
                    crop_months = monthly_data[crop]
                    
                    # Only include months from first_month onwards
                    months = [m for m in months_to_show if m in crop_months]
                    
                    if not months:
                        continue
                    
                    # Get month names for x-axis (in crop year order)
                    month_names = [get_month_name_for_crop_year(m) for m in months]
                    
                    # Calculate cumulative bushels
                    cumulative_bushels = []
                    running_total = 0
                    for m in months:
                        running_total += crop_months[m]['bushels']
                        cumulative_bushels.append(running_total)
                    
                    # Add cumulative line
                    fig_cumulative.add_trace(go.Scatter(
                        x=month_names,
                        y=cumulative_bushels,
                        mode='lines+markers',
                        marker=dict(size=10),
                        name=f'{crop} Cumulative',
                        line=dict(width=2),
                        hovertemplate=f'<b>{crop} Cumulative</b><br>Month: %{{x}}<br>Cumulative Bushels: %{{y:,.0f}} bu<extra></extra>'
                    ))
                
                # Update layout for cumulative chart
                fig_cumulative.update_layout(
                    title='Cumulative Deliveries by Month',
                    xaxis=dict(
                        title='Month',
                        tickangle=-45 if len(months_to_show) > 6 else 0,
                        categoryorder='array',
                        categoryarray=all_month_names_in_order
                    ),
                    yaxis=dict(
                        title='Cumulative Bushels',
                        showgrid=True
                    ),
                    hovermode='x unified',
                    height=500,
                    legend=dict(
                        traceorder='normal',
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=1.01
                    )
                )
                
                st.plotly_chart(fig_cumulative, width='stretch')
                
                # Show summary data
                with st.expander("📊 View Monthly Data Summary"):
                    for crop in crops:
                        st.markdown(f"**{crop}**")
                        crop_months = monthly_data[crop]
                        
                        summary_data = []
                        for month_num in sorted(crop_months.keys()):
                            if month_num >= first_month:
                                data = crop_months[month_num]
                                summary_data.append({
                                    'Month': get_month_name_for_crop_year(month_num),
                                    'Bushels': f"{data['bushels']:,.0f}",
                                    'Gross Amount': f"${data['gross_amount']:,.2f}",
                                    'Price': f"${data['price']:.2f}/bu"
                                })
                        
                        if summary_data:
                            df_summary = pd.DataFrame(summary_data)
                            st.dataframe(df_summary, width='stretch', hide_index=True)
                            st.markdown("---")
    
    with tab3:
        st.subheader("Bins")
        
        # Crop year selector (same as other tabs)
        current_crop_year = get_current_crop_year()
        selected_crop_year = st.selectbox(
            "Crop Year",
            options=list(range(current_crop_year - 5, current_crop_year + 2)),
            index=5,  # Default to current crop year
            format_func=lambda x: f"{x} (Oct 1, {x} - Sep 30, {x+1})",
            key="bins_crop_year"
        )
        
        # Get bins grouped by crop
        bins_by_crop = get_bins_with_storage_by_crop(db, selected_crop_year)
        
        # Debug: Show what crops were found
        if st.checkbox("🔍 Debug: Show bin data", key="debug_bins"):
            st.write(f"**Crops found:** {list(bins_by_crop.keys())}")
            for crop, bins_list in bins_by_crop.items():
                st.write(f"**{crop}:** {len(bins_list)} bins")
                for bin_name, crop_storage in bins_list:
                    st.write(f"  - {bin_name.location} - {bin_name.bin_name}: capacity={bin_name.capacity}, current={crop_storage.current_content}")
        
        if not bins_by_crop:
            st.info("No bins with storage found for the selected crop year.")
        else:
            # Create a chart for each crop
            crops = sorted(bins_by_crop.keys())
            
            for crop in crops:
                st.markdown(f"### {crop}")
                
                crop_bins = bins_by_crop[crop]
                
                # Prepare data for stacked bar chart
                bin_labels = []
                current_storage = []  # x - bushels in bin
                available_capacity = []  # y - available bushels to store
                total_capacity = []  # z - total capacity
                
                for bin_name, crop_storage in sorted(crop_bins, key=lambda b: (b[0].location, b[0].bin_name)):
                    # Create bin label
                    bin_label = f"{bin_name.location} - {bin_name.bin_name}"
                    bin_labels.append(bin_label)
                    
                    # x: Current storage bushels from crop_storage
                    current = crop_storage.current_content or 0
                    current_storage.append(float(current))
                    
                    # z: Total capacity from bin_name
                    capacity = bin_name.capacity or 0
                    total_capacity.append(float(capacity))
                    
                    # y: Available capacity (z - x)
                    # If capacity is 0, it's infinite capacity - available is always 0 (don't show available)
                    if capacity == 0:
                        available = 0.0  # Infinite capacity bins - no available capacity to show
                    else:
                        available = max(0.0, float(capacity) - float(current))
                    available_capacity.append(available)
                
                # Calculate bins per row - aim for ~2 inches per bin (assuming ~12 inch wide screen)
                # Approximately 4-5 bins per row to allow for ~2 inch width each
                bins_per_row = 4
                num_rows = (len(bin_labels) + bins_per_row - 1) // bins_per_row  # Ceiling division
                
                # Uniform bar width - Parameters that determine bin width:
                # 1. uniform_bar_width: Relative width of each bar (0.0-1.0, where 1.0 = full category spacing)
                #    - Smaller values = narrower bars
                #    - Set in the width parameter of go.Bar()
                # 2. bargap: Gap between bars (0.0-1.0, where 1.0 = full category spacing between bars)
                #    - Larger values = more space between bars = narrower appearance
                #    - Set in fig.update_layout(bargap=...)
                # 3. Number of bins: More bins = less space per bin (automatic)
                # Adjust based on number of bins to prevent fat bars
                num_bins = len(bin_labels)
                if num_bins == 1:
                    uniform_bar_width = 0.2  # Very narrow for single bin
                elif num_bins == 2:
                    uniform_bar_width = 0.35
                elif num_bins <= 4:
                    uniform_bar_width = 0.4
                else:
                    uniform_bar_width = 0.5  # Wider for more bins
                
                # Determine colors based on crop
                if crop.lower() == 'corn':
                    current_color = '#FFD700'  # Yellow
                    current_line_color = '#FFA500'  # Darker yellow/orange for border
                elif crop.lower() == 'soybeans':
                    current_color = '#8B4513'  # Brown
                    current_line_color = '#654321'  # Darker brown for border
                else:
                    current_color = '#3498db'  # Default blue
                    current_line_color = '#2980b9'
                
                # Calculate percentage full for text labels (current/capacity)
                percentages_full = []
                for i, bin_label in enumerate(bin_labels):
                    capacity_val = total_capacity[i]
                    current_val = current_storage[i]
                    if capacity_val > 0:
                        pct = (current_val / capacity_val) * 100
                        percentages_full.append(f"{pct:.0f}% full")
                    else:
                        percentages_full.append("Unlimited")  # Infinite capacity
                
                # Create subplots if multiple rows needed, otherwise single figure
                if num_rows > 1:
                    from plotly.subplots import make_subplots
                    
                    # Create subplots with num_rows rows
                    fig_bins = make_subplots(
                        rows=num_rows,
                        cols=1,
                        subplot_titles=None,  # No row titles - cleaner look
                        vertical_spacing=0.15,
                        shared_yaxes=True
                    )
                    
                    # Add bars for each row
                    for row_idx in range(num_rows):
                        start_idx = row_idx * bins_per_row
                        end_idx = min(start_idx + bins_per_row, len(bin_labels))
                        
                        if start_idx < len(bin_labels):
                            row_bin_labels = bin_labels[start_idx:end_idx]
                            row_current = current_storage[start_idx:end_idx]
                            row_available = available_capacity[start_idx:end_idx]
                            
                            # Current storage (crop-specific color)
                            row_percentages = percentages_full[start_idx:end_idx]
                            fig_bins.add_trace(go.Bar(
                                x=row_bin_labels,
                                y=row_current,
                                name='Current Storage' if row_idx == 0 else '',
                                orientation='v',
                                marker=dict(
                                    color=current_color,
                                    line=dict(color=current_line_color, width=1),
                                    cornerradius=0.2
                                ),
                                hovertemplate='<b>%{x}</b><br>Current Storage: %{y:,.0f} bu<extra></extra>',
                                showlegend=(row_idx == 0),
                                width=[uniform_bar_width] * len(row_bin_labels),  # Uniform width
                                text=[f'{row_percentages[i] if i < len(row_percentages) else ""}' for i in range(len(row_bin_labels))],
                                textposition='inside',
                                textfont=dict(color='black', size=16, family='Arial Black')
                            ), row=row_idx+1, col=1)
                            
                            # Available capacity (green)
                            fig_bins.add_trace(go.Bar(
                                x=row_bin_labels,
                                y=row_available,
                                name='Available Capacity' if row_idx == 0 else '',
                                orientation='v',
                                marker=dict(
                                    color='#2ecc71',
                                    line=dict(color='#27ae60', width=1),
                                    cornerradius=0.2
                                ),
                                hovertemplate='<b>%{x}</b><br>Available Capacity: %{y:,.0f} bu<extra></extra>',
                                showlegend=(row_idx == 0),
                                width=[uniform_bar_width] * len(row_bin_labels),  # Uniform width
                                text=[''] * len(row_bin_labels)  # No text on available capacity
                            ), row=row_idx+1, col=1)
                    
                    # Update layout
                    fig_bins.update_layout(
                        title=f'{crop} - Bin Storage Capacity',
                        barmode='stack',
                        hovermode='x unified',
                        height=350 * num_rows,  # Adjust height based on number of rows
                        legend=dict(
                            traceorder='normal',
                            yanchor="top",
                            y=0.99,
                            xanchor="left",
                            x=1.01
                        ),
                        bargap=0.4 if len(bin_labels) <= 4 else 0.2  # More gap for fewer bins to prevent fat bars
                    )
                    
                    # Update x-axes for all subplots
                    for row_idx in range(num_rows):
                        start_idx = row_idx * bins_per_row
                        end_idx = min(start_idx + bins_per_row, len(bin_labels))
                        row_bin_labels = bin_labels[start_idx:end_idx] if start_idx < len(bin_labels) else []
                        
                        fig_bins.update_xaxes(
                            title='',  # Remove "Bin Name" label
                            tickangle=-45 if len(row_bin_labels) > 3 else 0,
                            tickfont=dict(size=14, family='Arial Black', color='black'),  # Bold and larger
                            row=row_idx+1, col=1
                        )
                    
                    # Update y-axis (only need to update one since shared_yaxes=True)
                    fig_bins.update_yaxes(title='Bushels', row=(num_rows + 1) // 2, col=1)
                    
                else:
                    # Single row - create regular figure
                    fig_bins = go.Figure()
                    
                    # Bottom stack: Current storage (crop-specific color)
                    fig_bins.add_trace(go.Bar(
                        x=bin_labels,
                        y=current_storage,
                        name='Current Storage',
                        orientation='v',
                        marker=dict(
                            color=current_color,
                            line=dict(color=current_line_color, width=1),
                            cornerradius=0.2
                        ),
                        hovertemplate='<b>%{x}</b><br>Current Storage: %{y:,.0f} bu<extra></extra>',
                        width=[uniform_bar_width] * len(bin_labels),  # Uniform width for all bars
                        text=percentages_full,  # Add percentage text
                        textposition='inside',
                        textfont=dict(color='black', size=16, family='Arial Black')
                    ))
                    
                    # Top stack: Available capacity (green)
                    fig_bins.add_trace(go.Bar(
                        x=bin_labels,
                        y=available_capacity,
                        name='Available Capacity',
                        orientation='v',
                        marker=dict(
                            color='#2ecc71',
                            line=dict(color='#27ae60', width=1),
                            cornerradius=0.2
                        ),
                        hovertemplate='<b>%{x}</b><br>Available Capacity: %{y:,.0f} bu<extra></extra>',
                        width=[uniform_bar_width] * len(bin_labels),  # Uniform width for all bars
                        text=[''] * len(bin_labels)  # No text on available capacity
                    ))
                    
                    # Update layout - for single or few bins, use larger gap to prevent fat bars
                    num_bins = len(bin_labels)
                    gap_size = 0.6 if num_bins == 1 else (0.5 if num_bins == 2 else (0.4 if num_bins <= 4 else 0.2))
                    
                    fig_bins.update_layout(
                        title=f'{crop} - Bin Storage Capacity',
                        xaxis=dict(
                            title='',  # Remove "Bin Name" label
                            tickangle=-45 if len(bin_labels) > 4 else 0,
                            tickfont=dict(size=14, family='Arial Black', color='black')  # Bold and larger
                        ),
                        yaxis=dict(
                            title='Bushels',
                            showgrid=True
                        ),
                        barmode='stack',
                        hovermode='x unified',
                        height=500,
                        legend=dict(
                            traceorder='normal',
                            yanchor="top",
                            y=0.99,
                            xanchor="left",
                            x=1.01
                        ),
                        bargap=gap_size  # Larger gap for fewer bins to prevent fat bars
                    )
                
                st.plotly_chart(fig_bins, width='stretch')
                
                # Summary table for this crop
                with st.expander(f"📊 View {crop} Bin Details"):
                    summary_data = []
                    for bin_name, crop_storage in sorted(crop_bins, key=lambda b: (b[0].location, b[0].bin_name)):
                        current = crop_storage.current_content or 0
                        capacity = bin_name.capacity or 0
                        available = float(current) if capacity == 0 else max(0.0, float(capacity) - float(current))
                        
                        summary_data.append({
                            'Location': bin_name.location or 'N/A',
                            'Bin Name': bin_name.bin_name or 'N/A',
                            'Current Storage (bu)': f"{current:,.0f}",
                            'Available Capacity (bu)': f"{available:,.0f}",
                            'Total Capacity (bu)': f"{capacity:,.0f}",
                            'Preferred Crop': bin_name.preferred_crop or 'N/A',
                            'Load Status': crop_storage.load_status or 'N/A'
                        })
                    
                    if summary_data:
                        df_bins = pd.DataFrame(summary_data)
                        st.dataframe(df_bins, width='stretch', hide_index=True)
                
                st.markdown("---")
    
    with tab4:
        st.subheader("Bins 2 (3D Cylinder Test)")
        
        # Crop year selector
        current_crop_year = get_current_crop_year()
        selected_crop_year = st.selectbox(
            "Crop Year",
            options=list(range(current_crop_year - 5, current_crop_year + 2)),
            index=5,
            format_func=lambda x: f"{x} (Oct 1, {x} - Sep 30, {x+1})",
            key="bins2_crop_year"
        )
        
        # Get bins grouped by crop
        bins_by_crop = get_bins_with_storage_by_crop(db, selected_crop_year)
        
        if not bins_by_crop:
            st.info("No bins with storage found for the selected crop year.")
        else:
            # Crop color mapper
            crop_colors = {
                'Corn': 'gold',  # #FFD700
                'Soybeans': 'saddlebrown',  # #8B4513
            }
            
            # Function to generate cylinder using Surface (better approach)
            def cylinder(r, h, a=0, nt=100, nv=50):
                """
                Parametrize the cylinder of radius r, height h, base point a
                """
                theta = np.linspace(0, 2*np.pi, nt)
                v = np.linspace(a, a+h, nv)
                theta, v = np.meshgrid(theta, v)
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                z = v
                return x, y, z
            
            def boundary_circle(r, h, nt=100):
                """
                r - boundary circle radius
                h - height above xOy-plane where the circle is included
                returns the circle parameterization
                """
                theta = np.linspace(0, 2*np.pi, nt)
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                z = h * np.ones(theta.shape)
                return x, y, z
            
            # Create a chart for each crop
            crops = sorted(bins_by_crop.keys())
            
            for crop in crops:
                st.markdown(f"### {crop}")
                
                crop_bins = bins_by_crop[crop]
                
                # Prepare data
                bin_labels = []
                current_storage_list = []
                available_capacity_list = []
                total_capacity_list = []
                
                for bin_name, crop_storage in sorted(crop_bins, key=lambda b: (b[0].location, b[0].bin_name)):
                    bin_label = f"{bin_name.location} - {bin_name.bin_name}"
                    bin_labels.append(bin_label)
                    
                    current = float(crop_storage.current_content or 0)
                    capacity = float(bin_name.capacity or 0)
                    available = 0.0 if capacity == 0 else max(0.0, capacity - current)
                    
                    current_storage_list.append(current)
                    available_capacity_list.append(available)
                    total_capacity_list.append(capacity)
                
                # Build the 3D figure
                fig = go.Figure()
                
                bin_spacing = 3  # Space bins apart on x-axis
                radius = 1  # Fixed radius
                
                # Find max value for scaling
                max_bushels = max(max(current_storage_list) if current_storage_list else [0],
                                 max([c + a for c, a in zip(current_storage_list, available_capacity_list)]) if available_capacity_list else [0])
                
                # Scale factor to normalize heights
                scale_factor = 0.01 if max_bushels > 0 else 0.001
                if max_bushels > 0:
                    scale_factor = 20.0 / max_bushels  # Scale so max is about 20 units tall
                
                # Get crop color
                stored_color = crop_colors.get(crop, 'sienna')
                
                # Track legend entries
                current_added = False
                available_added = False
                
                for idx, bin_label in enumerate(bin_labels):
                    x_pos = idx * bin_spacing
                    current_val = current_storage_list[idx]
                    available_val = available_capacity_list[idx]
                    capacity_val = total_capacity_list[idx]
                    
                    # Bottom: Stored (crop-specific color, solid)
                    if current_val > 0:
                        stored_height = current_val * scale_factor
                        z_bottom = 0
                        
                        # Create cylinder surface
                        x1, y1, z1 = cylinder(radius, stored_height, a=z_bottom, nt=50, nv=30)
                        # Translate to x_pos
                        x1 = x1 + x_pos
                        
                        colorscale_stored = [[0, stored_color], [1, stored_color]]
                        cyl1 = go.Surface(
                            x=x1, y=y1, z=z1,
                            colorscale=colorscale_stored,
                            showscale=False,
                            opacity=0.8,
                            name='Current Storage' if not current_added else '',
                            showlegend=(not current_added)
                        )
                        fig.add_trace(cyl1)
                        
                        # Add boundary circles for stored cylinder
                        xb_low, yb_low, zb_low = boundary_circle(radius, h=z_bottom, nt=50)
                        xb_up, yb_up, zb_up = boundary_circle(radius, h=z_bottom + stored_height, nt=50)
                        xb_low = xb_low + x_pos
                        xb_up = xb_up + x_pos
                        
                        bcircles1 = go.Scatter3d(
                            x=xb_low.tolist() + [None] + xb_up.tolist(),
                            y=yb_low.tolist() + [None] + yb_up.tolist(),
                            z=zb_low.tolist() + [None] + zb_up.tolist(),
                            mode='lines',
                            line=dict(color=stored_color, width=2),
                            opacity=0.9,
                            showlegend=False
                        )
                        fig.add_trace(bcircles1)
                        
                        if not current_added:
                            current_added = True
                    
                    # Top: Available (translucent gray)
                    if capacity_val > 0 and available_val > 0:
                        avail_height = available_val * scale_factor
                        stored_height = current_val * scale_factor
                        z_bottom_avail = stored_height
                        
                        # Create cylinder surface for available
                        x2, y2, z2 = cylinder(radius, avail_height, a=z_bottom_avail, nt=50, nv=30)
                        # Translate to x_pos
                        x2 = x2 + x_pos
                        
                        colorscale_avail = [[0, 'lightgray'], [1, 'lightgray']]
                        cyl2 = go.Surface(
                            x=x2, y=y2, z=z2,
                            colorscale=colorscale_avail,
                            showscale=False,
                            opacity=0.5,
                            name='Available Capacity' if not available_added else '',
                            showlegend=(not available_added)
                        )
                        fig.add_trace(cyl2)
                        
                        # Add boundary circles for available cylinder
                        xb_low, yb_low, zb_low = boundary_circle(radius, h=z_bottom_avail, nt=50)
                        xb_up, yb_up, zb_up = boundary_circle(radius, h=z_bottom_avail + avail_height, nt=50)
                        xb_low = xb_low + x_pos
                        xb_up = xb_up + x_pos
                        
                        bcircles2 = go.Scatter3d(
                            x=xb_low.tolist() + [None] + xb_up.tolist(),
                            y=yb_low.tolist() + [None] + yb_up.tolist(),
                            z=zb_low.tolist() + [None] + zb_up.tolist(),
                            mode='lines',
                            line=dict(color='gray', width=2),
                            opacity=0.6,
                            showlegend=False
                        )
                        fig.add_trace(bcircles2)
                        
                        if not available_added:
                            available_added = True
                
                # Layout: 3D scene
                max_height = max_bushels * scale_factor if max_bushels > 0 else 20
                x_range_max = (len(bin_labels) - 1) * bin_spacing + 2
                
                # Layout with orthographic projection (as in user's example)
                layout = go.Layout(
                    scene=dict(
                        xaxis_visible=False,
                        yaxis_visible=False,
                        zaxis_visible=False,
                        aspectmode='cube',
                        camera=dict(eye=dict(x=1.5, y=1.5, z=0.55))
                    ),
                    title=f'{crop} - 3D Bin Storage (Test View)',
                    height=600,
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=1.01
                    )
                )
                fig.update_layout(layout)
                fig.layout.scene.camera.projection.type = "orthographic"
                
                st.plotly_chart(fig, width='stretch')
                st.markdown("---")
    
    with tab5:
        st.subheader("Contracts")
        
        # Get all contracts to determine available filter options
        all_contracts = get_all_contracts(db)
        
        if not all_contracts:
            st.info("No contracts found in the database.")
        else:
            # Determine available filter options
            # 1. Crop years (from delivery_start dates)
            crop_years = set()
            for contract in all_contracts:
                if contract.delivery_start:
                    try:
                        crop_year = get_crop_year_from_date(contract.delivery_start)
                        if crop_year:
                            crop_years.add(crop_year)
                    except Exception:
                        pass
            crop_years = sorted(list(crop_years), reverse=True)
            
            # 2. Delivery months (from delivery_start dates)
            delivery_months = set()
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            for contract in all_contracts:
                if contract.delivery_start:
                    try:
                        # Format as "Oct 2025"
                        month_key = f"{month_names[contract.delivery_start.month - 1]} {contract.delivery_start.year}"
                        delivery_months.add(month_key)
                    except Exception:
                        pass
            # Sort by year, then by month
            delivery_months = sorted(list(delivery_months), key=lambda x: (int(x.split()[1]), month_names.index(x.split()[0])))
            
            # 3. Crop types (normalized names)
            crop_types = set()
            for contract in all_contracts:
                if contract.commodity:
                    normalized = normalize_commodity_name(db, contract.commodity)
                    crop_types.add(normalized)
            crop_types = sorted(list(crop_types))
            
            # 4. Vendors (normalized buyer names)
            vendors = get_all_normalized_vendors(db, all_contracts)
            
            # 5. Fill statuses
            fill_statuses = ['None', 'Partial', 'Filled', 'Over']
            
            # Filter checkboxes
            st.markdown("### Filters")
            filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)
            
            with filter_col1:
                st.markdown("**Crop Year**")
                selected_crop_years = []
                for cy in crop_years:
                    if st.checkbox(f"{cy}", key=f"contract_crop_year_{cy}", value=True):
                        selected_crop_years.append(cy)
            
            with filter_col2:
                st.markdown("**Delivery Month**")
                selected_delivery_months = []
                for dm in delivery_months:
                    if st.checkbox(f"{dm}", key=f"contract_delivery_month_{dm}", value=True):
                        selected_delivery_months.append(dm)
            
            with filter_col3:
                st.markdown("**Crop Type**")
                selected_crop_types = []
                for ct in crop_types:
                    if st.checkbox(f"{ct}", key=f"contract_crop_type_{ct}", value=True):
                        selected_crop_types.append(ct)
            
            with filter_col4:
                st.markdown("**Vendor**")
                selected_vendors = []
                for vendor in vendors:
                    if st.checkbox(f"{vendor}", key=f"contract_vendor_{vendor}", value=True):
                        selected_vendors.append(vendor)
            
            with filter_col5:
                st.markdown("**Fill Status**")
                selected_fill_statuses = []
                for fs in fill_statuses:
                    if st.checkbox(f"{fs}", key=f"contract_fill_status_{fs}", value=True):
                        selected_fill_statuses.append(fs)
            
            # Filter contracts based on selections
            filtered_contracts = []
            for contract in all_contracts:
                # Filter by crop year
                contract_crop_year = None
                if contract.delivery_start:
                    try:
                        contract_crop_year = get_crop_year_from_date(contract.delivery_start)
                    except Exception:
                        pass
                if selected_crop_years and contract_crop_year not in selected_crop_years:
                    continue
                
                # Filter by delivery month
                if contract.delivery_start:
                    try:
                        contract_month_key = f"{month_names[contract.delivery_start.month - 1]} {contract.delivery_start.year}"
                        if selected_delivery_months and contract_month_key not in selected_delivery_months:
                            continue
                    except Exception:
                        # If we can't parse the month, skip if delivery months are selected
                        if selected_delivery_months:
                            continue
                elif selected_delivery_months:
                    # No delivery_start date but delivery months are selected, skip
                    continue
                
                # Filter by crop type
                if contract.commodity:
                    normalized_crop = normalize_commodity_name(db, contract.commodity)
                    if selected_crop_types and normalized_crop not in selected_crop_types:
                        continue
                elif selected_crop_types:
                    continue
                
                # Filter by vendor
                if contract.buyer_name:
                    normalized_vendor = normalize_vendor_name(db, contract.buyer_name)
                    if selected_vendors and normalized_vendor not in selected_vendors:
                        continue
                elif selected_vendors:
                    continue
                
                # Filter by fill status
                contract_fill_status = contract.fill_status or 'None'
                if selected_fill_statuses and contract_fill_status not in selected_fill_statuses:
                    continue
                
                filtered_contracts.append(contract)
            
            st.markdown("---")
            
            if not filtered_contracts:
                st.info("No contracts match the selected filters.")
            else:
                # Prepare data for stacked bar chart
                # Group by vendor + crop type combination and fill status
                chart_data = {}  # {vendor_crop_key: {fill_status: bushels}}
                
                for contract in filtered_contracts:
                    vendor = normalize_vendor_name(db, contract.buyer_name or 'Unknown')
                    crop_type = normalize_commodity_name(db, contract.commodity) if contract.commodity else 'Unknown'
                    fill_status = contract.fill_status or 'None'
                    bushels = contract.bushels or 0
                    
                    # Create combined key: "Vendor X (Corn)"
                    vendor_crop_key = f"{vendor} ({crop_type})"
                    
                    if vendor_crop_key not in chart_data:
                        chart_data[vendor_crop_key] = {}
                    if fill_status not in chart_data[vendor_crop_key]:
                        chart_data[vendor_crop_key][fill_status] = 0
                    chart_data[vendor_crop_key][fill_status] += bushels
                
                # Create stacked bar chart
                if chart_data:
                    vendor_crop_list = sorted(chart_data.keys())
                    fill_status_colors = {
                        'None': '#3498db',
                        'Partial': '#f39c12',
                        'Filled': '#2ecc71',
                        'Over': '#e74c3c'
                    }
                    
                    # Control bar width like bins tab
                    num_bars = len(vendor_crop_list)
                    if num_bars == 1:
                        uniform_bar_width = 0.2  # Very narrow for single bar
                    elif num_bars == 2:
                        uniform_bar_width = 0.35
                    elif num_bars <= 4:
                        uniform_bar_width = 0.4
                    else:
                        uniform_bar_width = 0.5  # Wider for more bars
                    
                    # Determine gap size
                    gap_size = 0.6 if num_bars == 1 else (0.5 if num_bars == 2 else (0.4 if num_bars <= 4 else 0.2))
                    
                    fig = go.Figure()
                    
                    # Add a trace for each fill status
                    for fill_status in fill_statuses:
                        if fill_status not in selected_fill_statuses:
                            continue
                        
                        bushels_by_vendor_crop = [chart_data.get(vendor_crop, {}).get(fill_status, 0) for vendor_crop in vendor_crop_list]
                        
                        fig.add_trace(go.Bar(
                            name=fill_status,
                            x=vendor_crop_list,
                            y=bushels_by_vendor_crop,
                            marker=dict(color=fill_status_colors.get(fill_status, '#95a5a6')),
                            hovertemplate='%{fullData.name}: %{y:,.0f} bu<extra></extra>',
                            width=[uniform_bar_width] * len(vendor_crop_list)  # Uniform width for all bars
                        ))
                    
                    fig.update_layout(
                        title='Bushels by Vendor and Crop Type (Stacked by Fill Status)',
                        xaxis_title='',
                        yaxis_title='Bushels',
                        barmode='stack',
                        hovermode='x unified',
                        height=500,
                        bargap=gap_size,  # Gap between bars
                        xaxis=dict(
                            tickangle=-45 if len(vendor_crop_list) > 5 else 0,
                            tickfont=dict(size=12, family='Arial Black', color='black')  # Bold and larger
                        )
                    )
                    
                    st.plotly_chart(fig, width='stretch')
                    st.markdown("---")
                
                # Display contracts table
                st.markdown("### Contract Details")
                
                # Prepare table data
                table_data = []
                for contract in filtered_contracts:
                    contract_crop_year = None
                    if contract.delivery_start:
                        try:
                            contract_crop_year = get_crop_year_from_date(contract.delivery_start)
                        except Exception:
                            pass
                    
                    normalized_crop = normalize_commodity_name(db, contract.commodity) if contract.commodity else 'Unknown'
                    normalized_vendor = normalize_vendor_name(db, contract.buyer_name) if contract.buyer_name else 'Unknown'
                    
                    table_data.append({
                        'Contract Number': contract.contract_number,
                        'Crop Year': contract_crop_year if contract_crop_year else '',
                        'Crop Type': normalized_crop,
                        'Vendor': normalized_vendor,
                        'Bushels': contract.bushels or 0,
                        'Price ($/bu)': f"${contract.price:.2f}" if contract.price else '',
                        'Fill Status': contract.fill_status or 'None',
                        'Status': contract.status or 'Active',
                        'Date Sold': contract.date_sold.strftime('%Y-%m-%d') if contract.date_sold else '',
                        'Delivery Start': contract.delivery_start.strftime('%Y-%m-%d') if contract.delivery_start else '',
                        'Delivery End': contract.delivery_end.strftime('%Y-%m-%d') if contract.delivery_end else ''
                    })
                
                df_contracts = pd.DataFrame(table_data)
                st.dataframe(df_contracts, width='stretch', hide_index=True)
    
    with tab6:
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
