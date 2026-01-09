"""
Crop Details Page - Shows detailed information for a selected crop.
Accessed when clicking on a crop bar in the Crop Year Sales chart.
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from reports.contract_queries import get_all_contracts
from reports.settlement_queries import get_all_settlements
from reports.crop_year_utils import get_current_crop_year, get_crop_year_date_range
from reports.commodity_utils import normalize_commodity_name
from dashboard_app import get_drilldown_details, get_database_session

# Page config
st.set_page_config(page_title="Crop Details", page_icon="📋", layout="wide")

def main():
    """Main detail page."""
    st.title("📋 Crop Details")
    
    # Get crop from session state
    if 'drilldown_crop' not in st.session_state or not st.session_state.drilldown_crop:
        st.warning("No crop selected. Please select a crop from the Crop Year Sales page.")
        if st.button("← Back to Crop Year Sales"):
            st.switch_page("dashboard_app.py")
        return
    
    crop = st.session_state.drilldown_crop
    crop_year = st.session_state.get('selected_crop_year', get_current_crop_year())
    
    # Back button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back to Crop Year Sales", type="primary"):
            st.switch_page("dashboard_app.py")
    
    st.markdown(f"### {crop} - Crop Year {crop_year}")
    start_date, end_date = get_crop_year_date_range(crop_year)
    st.caption(f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
    st.markdown("---")
    
    # Get database connection using username
    username = st.session_state.get('username')
    if not username:
        st.error("Username not set. Please go back to the main dashboard and enter your username.")
        st.stop()
    
    db = get_database_session(username)
    if db is None:
        st.error("Could not connect to database. Please check the database path.")
        return
    
    all_contracts = get_all_contracts(db)
    all_settlements = get_all_settlements(db)
    
    # Show all statuses
    for status in ['Sold', 'Contracted', 'Open']:
        st.markdown(f"#### {status}")
        details = get_drilldown_details(
            db,
            crop,
            status,
            crop_year,
            all_contracts,
            all_settlements
        )
        
        if status == 'Sold':
            if details['settlements']:
                # Calculate totals and average price
                total_bushels = sum(s.get('bushels', 0) for s in details['settlements'])
                total_revenue = sum(
                    s.get('net_amount', 0) if s.get('net_amount') else s.get('gross_amount', 0)
                    for s in details['settlements']
                )
                avg_price = total_revenue / total_bushels if total_bushels > 0 else 0.0
                
                # Display summary with average price
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Bushels", f"{total_bushels:,.0f} bu")
                with col2:
                    st.metric("Total Revenue", f"${total_revenue:,.0f}")
                with col3:
                    st.metric("Avg Price/Bu", f"${avg_price:.2f}")
                st.markdown("---")
                # Create DataFrame for settlements
                settlement_data = []
                for s in details['settlements']:
                    settlement_data.append({
                        'settlement_id': s.get('settlement_id', 'N/A'),
                        'contract_id': s.get('contract_id', 'N/A'),
                        'commodity': s.get('commodity', 'N/A'),
                        'bushels': s.get('bushels', 0),
                        'price': s.get('price', 0),
                        'net_amount': s.get('net_amount', 0),
                        'gross_amount': s.get('gross_amount', 0),
                        'date_delivered': s.get('date_delivered').strftime('%Y-%m-%d') if s.get('date_delivered') else 'N/A',
                        'buyer': s.get('buyer', 'N/A')
                    })
                df_settlements = pd.DataFrame(settlement_data)
                
                # Format numeric columns
                if 'net_amount' in df_settlements.columns:
                    df_settlements['net_amount'] = df_settlements['net_amount'].apply(lambda x: f"${x:,.2f}" if x else "N/A")
                if 'gross_amount' in df_settlements.columns:
                    df_settlements['gross_amount'] = df_settlements['gross_amount'].apply(lambda x: f"${x:,.2f}" if x else "N/A")
                if 'price' in df_settlements.columns:
                    df_settlements['price'] = df_settlements['price'].apply(lambda x: f"${x:.2f}" if x else "N/A")
                if 'bushels' in df_settlements.columns:
                    df_settlements['bushels'] = df_settlements['bushels'].apply(lambda x: f"{x:,.0f}" if x else "N/A")
                
                # Rename columns for display
                df_display = df_settlements.rename(columns={
                    'settlement_id': 'Settlement ID',
                    'contract_id': 'Contract #',
                    'commodity': 'Commodity',
                    'bushels': 'Bushels',
                    'price': 'Price',
                    'net_amount': 'Net Amount',
                    'gross_amount': 'Gross Amount',
                    'date_delivered': 'Date Delivered',
                    'buyer': 'Buyer'
                })
                st.dataframe(df_display[['Settlement ID', 'Contract #', 'Commodity', 'Bushels', 'Price', 'Net Amount', 'Gross Amount', 'Date Delivered', 'Buyer']], width='stretch', hide_index=True)
            else:
                st.info("No settlements found for this selection.")
        
        elif status == 'Contracted':
            if details['contracts']:
                # Calculate totals and average price
                total_bushels = sum(c.get('remaining_bushels', 0) for c in details['contracts'])
                total_revenue = sum(c.get('remaining_revenue', 0) for c in details['contracts'])
                avg_price = total_revenue / total_bushels if total_bushels > 0 else 0.0
                
                # Display summary with average price
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Remaining Bushels", f"{total_bushels:,.0f} bu")
                with col2:
                    st.metric("Total Remaining Revenue", f"${total_revenue:,.0f}")
                with col3:
                    st.metric("Avg Price/Bu", f"${avg_price:.2f}")
                st.markdown("---")
                # Create DataFrame for contracts
                contract_data = []
                for c in details['contracts']:
                    contract_data.append({
                        'contract_number': c.get('contract_number', 'N/A'),
                        'commodity': c.get('commodity', 'N/A'),
                        'bushels': c.get('bushels', 0),
                        'price': c.get('price', 0),
                        'remaining_revenue': c.get('remaining_revenue', 0),
                        'remaining_bushels': c.get('remaining_bushels', 0),
                        'fill_status': c.get('fill_status', 'N/A'),
                        'delivery_start': c.get('delivery_start').strftime('%Y-%m-%d') if c.get('delivery_start') else 'N/A',
                        'date_sold': c.get('date_sold').strftime('%Y-%m-%d') if c.get('date_sold') else 'N/A',
                        'buyer': c.get('buyer', 'N/A')
                    })
                df_contracts = pd.DataFrame(contract_data)
                
                # Format numeric columns
                if 'price' in df_contracts.columns:
                    df_contracts['price'] = df_contracts['price'].apply(lambda x: f"${x:.2f}" if x else "N/A")
                if 'remaining_revenue' in df_contracts.columns:
                    df_contracts['remaining_revenue'] = df_contracts['remaining_revenue'].apply(lambda x: f"${x:,.2f}" if x else "N/A")
                if 'bushels' in df_contracts.columns:
                    df_contracts['bushels'] = df_contracts['bushels'].apply(lambda x: f"{x:,.0f}" if x else "N/A")
                if 'remaining_bushels' in df_contracts.columns:
                    df_contracts['remaining_bushels'] = df_contracts['remaining_bushels'].apply(lambda x: f"{x:,.0f}" if x else "N/A")
                
                # Rename columns for display
                df_display = df_contracts.rename(columns={
                    'contract_number': 'Contract #',
                    'commodity': 'Commodity',
                    'bushels': 'Total Bushels',
                    'remaining_bushels': 'Remaining Bushels',
                    'price': 'Price',
                    'remaining_revenue': 'Remaining Revenue',
                    'fill_status': 'Fill Status',
                    'delivery_start': 'Delivery Start',
                    'date_sold': 'Date Sold',
                    'buyer': 'Buyer'
                })
                st.dataframe(df_display[['Contract #', 'Commodity', 'Total Bushels', 'Remaining Bushels', 'Price', 'Remaining Revenue', 'Fill Status', 'Delivery Start', 'Date Sold', 'Buyer']], width='stretch', hide_index=True)
            else:
                st.info("No contracts found for this selection.")
        
        elif status == 'Open':
            if 'summary' in details:
                summary = details['summary']
                
                # Calculate average price from contracts for this crop (if available)
                # This gives an estimate - actual price is set on the main page
                avg_price = 0.0
                contract_prices = []
                for contract in all_contracts:
                    if contract.commodity:
                        normalized = normalize_commodity_name(db, contract.commodity)
                        if normalized == crop and contract.price and contract.price > 0:
                            contract_prices.append(contract.price)
                
                if contract_prices:
                    avg_price = sum(contract_prices) / len(contract_prices)
                    open_revenue = summary['open_bushels'] * avg_price
                else:
                    open_revenue = 0.0
                
                # Display summary with average price
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Starting Bushels", f"{summary['starting_bushels']:,.0f} bu")
                with col2:
                    st.metric("Sold Bushels", f"{summary['sold_bushels']:,.0f} bu")
                with col3:
                    st.metric("Contracted Bushels", f"{summary['contracted_bushels']:,.0f} bu")
                
                col4, col5, col6 = st.columns(3)
                with col4:
                    st.metric("Open Bushels", f"{summary['open_bushels']:,.0f} bu")
                with col5:
                    if avg_price > 0:
                        st.metric("Est. Avg Price/Bu", f"${avg_price:.2f}", 
                                 help="Estimated from existing contracts. Set actual price on main page.")
                        st.metric("Est. Open Revenue", f"${open_revenue:,.0f}")
                    else:
                        st.metric("Avg Price/Bu", "N/A", 
                                 help="Set crop price on main Crop Year Sales page")
                with col6:
                    st.markdown("")
                    
                if avg_price == 0:
                    st.info("💡 To calculate open revenue, set the crop price on the main 'Crop Year Sales' page.")
            else:
                st.info("Summary information not available.")
        st.markdown("---")
    
    db.close()

if __name__ == "__main__":
    main()
