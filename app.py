import streamlit as st
import pandas as pd
import re
from pathlib import Path

# Configure Streamlit page
st.set_page_config(
    page_title="LCY London Inventory Tracker",
    page_icon="📦",
    layout="wide"
)

@st.cache_data
def load_and_process_data():
    """Load all CSV files and process them into a unified DataFrame"""
    
    # Define data directory
    data_dir = Path("data")
    
    # Load Maxims (Warehouse) stock - uses SKU format like "LN 197"
    maxims_df = pd.read_csv(data_dir / "Master Product Sheet [May 2025] - LCY LONDON - Maxims stock.csv")
    maxims_df['location'] = 'Warehouse'
    maxims_df['design_number'] = maxims_df['SKU'].str.strip().str.upper().str.replace(' ', '')
    maxims_df['on_hand'] = pd.to_numeric(maxims_df['Stock QTY'], errors='coerce').fillna(0).astype(int)
    maxims_df['product_name'] = maxims_df['Description'].fillna('')
    maxims_df['brand'] = 'LCY LONDON'  # Default brand
    
    # Load store stock files - use Item Code/Item Name format
    store_files = {
        'CNM': ('Cinnamon Store', 'Master Product Sheet [May 2025] - LCY LONDON - CNM Stock.csv'),
        'HCM': ('Havelock City Store', 'Master Product Sheet [May 2025] - LCY LONDON - HCM Stock.csv'),
        'OGF': ('One Galle Face Store', 'Master Product Sheet [May 2025] - LCY LONDON - OGF Stock.csv')
    }
    
    store_dfs = []
    
    for code, (location_name, filename) in store_files.items():
        df = pd.read_csv(data_dir / filename)
        df['location'] = location_name
        
        # Extract design number from Item Name (e.g., "Ln120 - Polo White 2xl" -> "LN120")
        def extract_design_number(item_name):
            if pd.isna(item_name):
                return None
            match = re.search(r'(LN\d+)', item_name.upper())
            if match:
                return match.group(1)
            return None
        
        df['design_number'] = df['Item Name'].apply(extract_design_number)
        df['on_hand'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0).astype(int)
        df['product_name'] = df['Item Name'].fillna('')
        df['item_code'] = df['Item Code'].astype(str)
        df['brand'] = 'LCY LONDON'  # Default brand
        
        # Extract price
        df['price_lk'] = df['Selling Price'].str.replace(',', '').str.replace('"', '').astype(float)
        
        store_dfs.append(df[['design_number', 'location', 'on_hand', 'product_name', 'item_code', 'brand', 'price_lk']])
    
    # Combine all stock data
    # First, prepare maxims data with matching columns
    maxims_clean = maxims_df[['design_number', 'location', 'on_hand', 'product_name', 'brand']].copy()
    maxims_clean['item_code'] = ''
    maxims_clean['price_lk'] = 0  # No price in Maxims file
    
    # Combine all dataframes
    all_stock = pd.concat([maxims_clean] + store_dfs, ignore_index=True)
    
    # Remove rows without design numbers
    all_stock = all_stock[all_stock['design_number'].notna()]
    
    # Load sale items data to get additional product info
    sale_df = pd.read_csv(data_dir / "Master Product Sheet [May 2025] - LCY LONDON - Sale Items - May 25.csv")
    sale_df['design_number'] = sale_df['product_code'].str.strip().str.upper().str.replace(' ', '')
    sale_df['mrp'] = pd.to_numeric(sale_df['MRP'], errors='coerce')
    sale_df['sale_percentage'] = pd.to_numeric(sale_df['Sale %'].str.replace('%', ''), errors='coerce')
    
    # Merge with sale data to get MRP where available
    all_stock = all_stock.merge(
        sale_df[['design_number', 'mrp', 'sale_percentage']],
        on='design_number',
        how='left'
    )
    
    # Use MRP as price where price_lk is 0
    all_stock['price_lk'] = all_stock.apply(
        lambda row: row['mrp'] if row['price_lk'] == 0 and pd.notna(row['mrp']) else row['price_lk'],
        axis=1
    )
    
    # Calculate sale price
    all_stock['sale_price'] = all_stock.apply(
        lambda row: row['price_lk'] * (1 - row['sale_percentage'] / 100) if pd.notna(row['sale_percentage']) else row['price_lk'],
        axis=1
    )
    
    return all_stock

def calculate_sale_flag(df):
    """Mark items as sale based on the sale items CSV data"""
    
    # Calculate total stock per design number
    total_stock = df.groupby('design_number')['on_hand'].sum().reset_index()
    total_stock.columns = ['design_number', 'total_on_hand']
    
    # Items are on sale if they have a sale_percentage value (from the sale items CSV)
    # or if they were marked as "To Clear"
    df = df.merge(total_stock[['design_number', 'total_on_hand']], on='design_number', how='left')
    
    # Mark as sale if sale_percentage exists and is not null
    df['sale_flag'] = df['sale_percentage'].notna()
    
    return df

def main():
    st.title("🏬 LCY London Inventory Tracker")
    st.markdown("Real-time stock management across all locations")
    
    # Load data
    with st.spinner("Loading inventory data..."):
        df = load_and_process_data()
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Apply sale flag calculation (based on sale items CSV data)
    df = calculate_sale_flag(df)
    
    # Brand filter (multi-select)
    all_brands = sorted(df['brand'].unique())
    selected_brands = st.sidebar.multiselect(
        "Select Brands",
        options=all_brands,
        default=all_brands
    )
    
    # Location filter (multi-select)
    all_locations = sorted(df['location'].unique())
    selected_locations = st.sidebar.multiselect(
        "Select Locations",
        options=all_locations,
        default=all_locations
    )
    
    # Sale items only checkbox
    sale_items_only = st.sidebar.checkbox("Show sale items only", value=False)
    
    # Apply filters
    filtered_df = df[
        (df['brand'].isin(selected_brands)) &
        (df['location'].isin(selected_locations))
    ]
    
    if sale_items_only:
        filtered_df = filtered_df[filtered_df['sale_flag'] == True]
    
    # Add stock value columns to filtered_df BEFORE creating sale_df
    filtered_df['stock_value'] = filtered_df['on_hand'] * filtered_df['price_lk']
    filtered_df['sale_value'] = filtered_df['on_hand'] * filtered_df['sale_price']
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        unique_skus = filtered_df['design_number'].nunique()
        st.metric("Total SKUs", f"{unique_skus:,}")
    
    with col2:
        total_units = filtered_df['on_hand'].sum()
        st.metric("Total Units", f"{total_units:,}")
    
    with col3:
        sale_items = filtered_df[filtered_df['sale_flag'] == True]['design_number'].nunique()
        st.metric("Sale Items", f"{sale_items:,}")
    
    with col4:
        total_value = (filtered_df['on_hand'] * filtered_df['price_lk']).sum()
        st.metric("Total Value (LKR)", f"{total_value:,.0f}")
    
    # Add second row of metrics for sale analysis
    st.markdown("### 💰 Sale Impact Analysis")
    col5, col6, col7, col8 = st.columns(4)
    
    # Calculate values
    original_value = (filtered_df['on_hand'] * filtered_df['price_lk']).sum()
    sale_value = (filtered_df['on_hand'] * filtered_df['sale_price']).sum()
    potential_loss = original_value - sale_value
    loss_percentage = (potential_loss / original_value * 100) if original_value > 0 else 0
    
    # Sale items specific calculations
    sale_df = filtered_df[filtered_df['sale_flag'] == True]
    sale_units = sale_df['on_hand'].sum()
    sale_original_value = (sale_df['on_hand'] * sale_df['price_lk']).sum()
    sale_discounted_value = (sale_df['on_hand'] * sale_df['sale_price']).sum()
    
    with col5:
        st.metric("Original Value", f"LKR {original_value:,.0f}")
    
    with col6:
        st.metric("After Sale Value", f"LKR {sale_value:,.0f}")
    
    with col7:
        st.metric("Potential Revenue Loss", f"LKR {potential_loss:,.0f}", 
                  f"-{loss_percentage:.1f}%", delta_color="inverse")
    
    with col8:
        st.metric("Sale Items Stock", f"{sale_units:,} units",
                  f"LKR {sale_original_value:,.0f} → {sale_discounted_value:,.0f}")
    
    # Main data table
    st.subheader("Inventory Details")
    
    # Prepare display dataframe
    display_df = filtered_df[[
        'design_number', 'product_name', 'brand', 'location', 
        'on_hand', 'price_lk', 'sale_price', 'total_on_hand', 'sale_flag', 'sale_percentage'
    ]].copy()
    
    # Calculate stock values
    display_df['stock_value'] = display_df['on_hand'] * display_df['price_lk']
    display_df['sale_value'] = display_df['on_hand'] * display_df['sale_price']
    
    # Rename columns for display
    display_df.columns = [
        'Design Number', 'Product Name', 'Brand', 'Location',
        'On Hand', 'Original Price', 'Sale Price', 'Total Stock', 'Sale Item', 'Sale %',
        'Stock Value', 'Sale Value'
    ]
    
    # Format sale percentage
    display_df['Sale %'] = display_df['Sale %'].apply(lambda x: f"{x:.0f}%" if pd.notna(x) else "")
    
    # Sort by sale flag (descending) and on_hand (descending)
    display_df = display_df.sort_values(['Sale Item', 'On Hand'], ascending=[False, False])
    
    # Format price columns
    display_df['Original Price'] = display_df['Original Price'].apply(lambda x: f"{x:,.0f}" if x > 0 else "N/A")
    display_df['Sale Price'] = display_df['Sale Price'].apply(lambda x: f"{x:,.0f}" if x > 0 else "N/A")
    display_df['Stock Value'] = display_df['Stock Value'].apply(lambda x: f"{x:,.0f}" if x > 0 else "N/A")
    display_df['Sale Value'] = display_df['Sale Value'].apply(lambda x: f"{x:,.0f}" if x > 0 else "N/A")
    
    # Display the dataframe with search functionality
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Sale Item": st.column_config.CheckboxColumn(
                "Sale Item",
                help="Items marked for sale due to high stock levels"
            )
        }
    )
    
    # Management Insights
    if sale_df.shape[0] > 0:
        st.subheader("📊 Management Insights")
        
        # Create two columns for insights
        insight_col1, insight_col2 = st.columns(2)
        
        with insight_col1:
            st.markdown("#### 🏷️ Sale Items Summary")
            
            # Group by sale percentage
            sale_summary = sale_df.groupby('sale_percentage').agg({
                'design_number': 'nunique',
                'on_hand': 'sum',
                'stock_value': 'sum',
                'sale_value': 'sum'
            }).reset_index()
            
            for _, row in sale_summary.iterrows():
                discount = row['sale_percentage']
                items = row['design_number']
                units = row['on_hand']
                loss = row['stock_value'] - row['sale_value']
                
                st.markdown(f"""
                **{discount:.0f}% Discount**
                - Items: {items} SKUs
                - Units: {units:,}
                - Revenue Loss: LKR {loss:,.0f}
                """)
        
        with insight_col2:
            st.markdown("#### 📍 Location-wise Sale Stock")
            
            # Group by location
            location_summary = sale_df.groupby('location').agg({
                'on_hand': 'sum',
                'stock_value': 'sum',
                'sale_value': 'sum'
            }).reset_index()
            
            location_summary['potential_loss'] = location_summary['stock_value'] - location_summary['sale_value']
            location_summary = location_summary.sort_values('on_hand', ascending=False)
            
            for _, row in location_summary.iterrows():
                st.markdown(f"""
                **{row['location']}**
                - Sale Units: {row['on_hand']:,}
                - Value at Risk: LKR {row['potential_loss']:,.0f}
                """)
        
        # Top sale items by value
        st.markdown("#### 🔝 Top 10 Sale Items by Value at Risk")
        top_items = sale_df.groupby(['design_number', 'product_name', 'sale_percentage']).agg({
            'on_hand': 'sum',
            'stock_value': 'sum',
            'sale_value': 'sum'
        }).reset_index()
        
        top_items['value_at_risk'] = top_items['stock_value'] - top_items['sale_value']
        top_items = top_items.sort_values('value_at_risk', ascending=False).head(10)
        
        # Display as a simple table
        st.dataframe(
            top_items[['design_number', 'product_name', 'sale_percentage', 'on_hand', 'value_at_risk']].rename(columns={
                'design_number': 'Design #',
                'product_name': 'Product',
                'sale_percentage': 'Discount %',
                'on_hand': 'Total Units',
                'value_at_risk': 'Value at Risk (LKR)'
            }),
            hide_index=True,
            use_container_width=True
        )
    
    # Export functionality
    st.subheader("Export Data")
    
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name="lcy_london_inventory_export.csv",
        mime="text/csv"
    )
    
    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

if __name__ == "__main__":
    main()