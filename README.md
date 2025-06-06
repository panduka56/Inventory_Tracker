# LCY London Inventory Tracker

A Streamlit web application for tracking and managing inventory across multiple LCY London store locations.

## Features

- **Real-time Stock Visibility**: View current stock levels across all locations (Warehouse, Cinnamon Store, Havelock City Store, One Galle Face Store)
- **Smart Filtering**: Filter by brand, location, and sale items
- **Sale Item Detection**: Automatically flags items with high stock levels for potential sales
- **Metrics Dashboard**: View total SKUs, units, sale items, and inventory value
- **Export Functionality**: Download filtered inventory data as CSV
- **Searchable Data Table**: Quickly find specific products

## Installation

1. Clone this repository or download the files
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Navigate to the inventory-app directory:
   ```bash
   cd inventory-app
   ```

2. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

3. The app will open in your default web browser at `http://localhost:8501`

## Data Files

Place your CSV files in the `data/` directory:
- `Master Product Sheet [May 2025] - LCY LONDON - Maxims stock.csv` (Warehouse stock)
- `Master Product Sheet [May 2025] - LCY LONDON - CNM Stock.csv` (Cinnamon Store)
- `Master Product Sheet [May 2025] - LCY LONDON - HCM Stock.csv` (Havelock City Store)
- `Master Product Sheet [May 2025] - LCY LONDON - OGF Stock.csv` (One Galle Face Store)
- `Master Product Sheet [May 2025] - LCY LONDON - Sale Items - May 25.csv` (Sale items reference)

## Configuration

- **Sale Threshold**: Adjust the slider in the sidebar to change the stock level that triggers the sale flag
- **Filters**: Use the sidebar to filter by brand, location, or view only sale items

## Deployment

### Streamlit Cloud
1. Push your code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy your app by connecting your GitHub repository

### Other Platforms
The app can be deployed on any platform that supports Python web applications (Heroku, AWS, Google Cloud, etc.)

## Technical Details

- Built with Streamlit and Pandas
- Handles data inconsistencies between different stock files
- Extracts design numbers from product names for unified tracking
- Calculates sale flags based on total inventory across all locations