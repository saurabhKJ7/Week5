"""
Generate sample Excel files for testing Excel Sheets Agent
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path


def create_sales_data():
    """Create sample sales data"""
    
    # Generate sample data
    np.random.seed(42)
    
    # Date range
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = pd.date_range(start_date, end_date, freq='D')
    
    # Product categories
    categories = ['Electronics', 'Clothing', 'Books', 'Sports', 'Home']
    products = {
        'Electronics': ['Laptop', 'Phone', 'Tablet', 'Headphones', 'Camera'],
        'Clothing': ['T-Shirt', 'Jeans', 'Jacket', 'Shoes', 'Hat'],
        'Books': ['Fiction', 'Non-Fiction', 'Biography', 'Science', 'History'],
        'Sports': ['Basketball', 'Football', 'Tennis', 'Golf', 'Soccer'],
        'Home': ['Furniture', 'Appliances', 'Decor', 'Kitchen', 'Garden']
    }
    
    # Regions
    regions = ['North', 'South', 'East', 'West', 'Central']
    
    # Sales representatives
    reps = ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Brown', 'Eve Wilson']
    
    # Generate data
    data = []
    for i in range(5000):
        category = random.choice(categories)
        product = random.choice(products[category])
        region = random.choice(regions)
        rep = random.choice(reps)
        date = random.choice(date_range)
        
        # Generate realistic sales data
        base_price = random.uniform(10, 1000)
        quantity = random.randint(1, 20)
        discount = random.uniform(0, 0.3)
        
        revenue = base_price * quantity * (1 - discount)
        cost = revenue * random.uniform(0.4, 0.7)
        profit = revenue - cost
        
        data.append({
            'Date': date,
            'Product Category': category,
            'Product Name': product,
            'Region': region,
            'Sales Rep': rep,
            'Quantity': quantity,
            'Unit Price': round(base_price, 2),
            'Discount': round(discount, 2),
            'Revenue': round(revenue, 2),
            'Cost': round(cost, 2),
            'Profit': round(profit, 2),
            'Customer ID': f'CUST{random.randint(1000, 9999)}',
            'Order ID': f'ORD{random.randint(10000, 99999)}'
        })
    
    return pd.DataFrame(data)


def create_customer_data():
    """Create sample customer data"""
    
    np.random.seed(42)
    
    # Generate customer data
    data = []
    for i in range(1000):
        customer_id = f'CUST{1000 + i}'
        first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Lisa', 'Tom', 'Emma', 'Chris', 'Anna']
        last_names = ['Smith', 'Johnson', 'Brown', 'Davis', 'Wilson', 'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson']
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        data.append({
            'Customer_ID': customer_id,
            'First Name': first_name,
            'Last Name': last_name,
            'Email': f'{first_name.lower()}.{last_name.lower()}@email.com',
            'Phone': f'+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
            'Age': random.randint(18, 80),
            'Gender': random.choice(['Male', 'Female']),
            'City': random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']),
            'State': random.choice(['NY', 'CA', 'IL', 'TX', 'AZ']),
            'Registration Date': datetime(2023, 1, 1) + timedelta(days=random.randint(0, 730)),
            'Total Orders': random.randint(1, 50),
            'Total Spent': round(random.uniform(100, 5000), 2),
            'Status': random.choice(['Active', 'Inactive', 'VIP'])
        })
    
    return pd.DataFrame(data)


def create_inventory_data():
    """Create sample inventory data"""
    
    np.random.seed(42)
    
    # Product data
    categories = ['Electronics', 'Clothing', 'Books', 'Sports', 'Home']
    products = {
        'Electronics': ['Laptop', 'Phone', 'Tablet', 'Headphones', 'Camera'],
        'Clothing': ['T-Shirt', 'Jeans', 'Jacket', 'Shoes', 'Hat'],
        'Books': ['Fiction', 'Non-Fiction', 'Biography', 'Science', 'History'],
        'Sports': ['Basketball', 'Football', 'Tennis', 'Golf', 'Soccer'],
        'Home': ['Furniture', 'Appliances', 'Decor', 'Kitchen', 'Garden']
    }
    
    data = []
    for category in categories:
        for product in products[category]:
            for i in range(random.randint(2, 5)):  # Multiple variants per product
                sku = f'{category[:3].upper()}{product[:3].upper()}{i+1:03d}'
                
                data.append({
                    'SKU': sku,
                    'Product_Name': product,
                    'Category': category,
                    'Brand': random.choice(['Brand A', 'Brand B', 'Brand C', 'Brand D']),
                    'Unit_Cost': round(random.uniform(5, 500), 2),
                    'Selling_Price': round(random.uniform(10, 1000), 2),
                    'Stock_Quantity': random.randint(0, 500),
                    'Reorder_Level': random.randint(10, 50),
                    'Supplier': random.choice(['Supplier X', 'Supplier Y', 'Supplier Z']),
                    'Last_Updated': datetime.now() - timedelta(days=random.randint(0, 30)),
                    'Warehouse': random.choice(['Warehouse A', 'Warehouse B', 'Warehouse C']),
                    'Status': random.choice(['In Stock', 'Low Stock', 'Out of Stock'])
                })
    
    return pd.DataFrame(data)


def create_sample_files():
    """Create sample Excel files"""
    
    # Create sample data directory
    sample_dir = Path("sample_data")
    sample_dir.mkdir(exist_ok=True)
    
    # Create sales data with multiple sheets
    print("Creating sales data...")
    sales_df = create_sales_data()
    customer_df = create_customer_data()
    inventory_df = create_inventory_data()
    
    # Create comprehensive Excel file
    with pd.ExcelWriter(sample_dir / "comprehensive_data.xlsx", engine='openpyxl') as writer:
        sales_df.to_excel(writer, sheet_name='Sales', index=False)
        customer_df.to_excel(writer, sheet_name='Customers', index=False)
        inventory_df.to_excel(writer, sheet_name='Inventory', index=False)
        
        # Create summary sheet
        summary_data = {
            'Metric': ['Total Sales', 'Total Customers', 'Total Products', 'Avg Order Value'],
            'Value': [
                len(sales_df),
                len(customer_df),
                len(inventory_df),
                round(sales_df['Revenue'].mean(), 2)
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    # Create individual files for testing
    sales_df.to_excel(sample_dir / "sales_data.xlsx", index=False)
    customer_df.to_excel(sample_dir / "customer_data.xlsx", index=False)
    inventory_df.to_excel(sample_dir / "inventory_data.xlsx", index=False)
    
    # Create CSV versions
    sales_df.to_csv(sample_dir / "sales_data.csv", index=False)
    customer_df.to_csv(sample_dir / "customer_data.csv", index=False)
    inventory_df.to_csv(sample_dir / "inventory_data.csv", index=False)
    
    print(f"Sample files created in {sample_dir}:")
    print("- comprehensive_data.xlsx (multiple sheets)")
    print("- sales_data.xlsx")
    print("- customer_data.xlsx")
    print("- inventory_data.xlsx")
    print("- CSV versions of all files")
    
    # Display sample queries
    print("\n" + "="*50)
    print("SAMPLE QUERIES TO TRY:")
    print("="*50)
    print("1. 'How many sales records are there?'")
    print("2. 'Show sales data for Electronics category'")
    print("3. 'Calculate total revenue by region'")
    print("4. 'Find customers who spent more than $2000'")
    print("5. 'Create a pivot table showing revenue by category and region'")
    print("6. 'Show top 10 customers by total spent'")
    print("7. 'Find products with low stock levels'")
    print("8. 'Calculate average order value by sales rep'")
    print("9. 'Show sales trends by month'")
    print("10. 'Generate a chart showing revenue by product category'")
    print("="*50)


if __name__ == "__main__":
    create_sample_files() 