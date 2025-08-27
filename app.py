import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import csv
from datetime import datetime, date
import os

# Set page configuration
st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# Initialize session state
if 'expenses_updated' not in st.session_state:
    st.session_state.expenses_updated = False

def load_expenses():
    """Load expenses from CSV file into a pandas DataFrame"""
    try:
        if os.path.exists("expenses.csv"):
            df = pd.read_csv("expenses.csv", names=['date', 'category', 'amount'])
            # Filter out empty rows
            df = df.dropna().reset_index(drop=True)
            if not df.empty:
                # Convert amount to numeric and date to datetime
                df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                # Remove rows with invalid data
                df = df.dropna().reset_index(drop=True)
                return df
        return pd.DataFrame(columns=['date', 'category', 'amount'])
    except Exception as e:
        st.error(f"Error loading expenses: {str(e)}")
        return pd.DataFrame(columns=['date', 'category', 'amount'])

def add_expense(expense_date, category, amount):
    """Add a new expense to the CSV file"""
    try:
        # Validate inputs
        if not category.strip():
            st.error("Category cannot be empty!")
            return False
        
        if amount <= 0:
            st.error("Amount must be greater than 0!")
            return False
        
        # Format date as string
        date_str = expense_date.strftime("%Y-%m-%d")
        
        # Append to CSV file
        with open("expenses.csv", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([date_str, category.strip(), amount])
        
        st.success("✅ Expense added successfully!")
        st.session_state.expenses_updated = True
        return True
    except Exception as e:
        st.error(f"Error adding expense: {str(e)}")
        return False

def create_monthly_summary(df):
    """Create monthly summary from expenses DataFrame"""
    if df.empty:
        return pd.DataFrame(columns=['Month', 'Total Amount'])
    
    # Add month column
    df_copy = df.copy()
    df_copy['month'] = df_copy['date'].dt.to_period('M')
    
    # Group by month and sum amounts
    monthly_summary = df_copy.groupby('month')['amount'].sum().reset_index()
    monthly_summary['month'] = monthly_summary['month'].astype(str)
    monthly_summary.columns = ['Month', 'Total Amount']
    
    return monthly_summary

def create_category_summary(df):
    """Create category summary from expenses DataFrame"""
    if df.empty:
        return pd.DataFrame(columns=['Category', 'Total Amount'])
    
    # Group by category and sum amounts
    category_summary = df.groupby('category')['amount'].sum().reset_index()
    category_summary.columns = ['Category', 'Total Amount']
    category_summary = category_summary.sort_values('Total Amount', ascending=False)
    
    return category_summary

def main():
    """Main Streamlit application"""
    
    # Title and description
    st.title("💰 Personal Expense Tracker")
    st.markdown("Track your expenses and visualize your spending patterns with interactive charts.")
    
    # Load expenses data
    df = load_expenses()
    
    # Sidebar for adding expenses
    st.sidebar.header("Add New Expense")
    
    with st.sidebar.form("add_expense_form"):
        expense_date = st.date_input(
            "Date",
            value=date.today(),
            max_value=date.today()
        )
        
        category = st.text_input(
            "Category",
            placeholder="e.g., Food, Travel, Shopping"
        )
        
        amount = st.number_input(
            "Amount (₹)",
            min_value=0.01,
            step=0.01,
            format="%.2f"
        )
        
        submitted = st.form_submit_button("Add Expense")
        
        if submitted:
            if add_expense(expense_date, category, amount):
                st.rerun()
    
    # Main content area
    if df.empty:
        st.info("🚀 No expenses recorded yet! Use the sidebar to add your first expense.")
        return
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Expenses", f"₹{df['amount'].sum():.2f}")
    
    with col2:
        st.metric("Number of Transactions", len(df))
    
    with col3:
        st.metric("Average Transaction", f"₹{df['amount'].mean():.2f}")
    
    with col4:
        unique_categories = df['category'].nunique()
        st.metric("Categories Used", unique_categories)
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Monthly Summary", "🥧 Category Breakdown", "📈 Monthly Chart", "📋 All Expenses"])
    
    with tab1:
        st.header("Monthly Expense Summary")
        monthly_df = create_monthly_summary(df)
        
        if not monthly_df.empty:
            # Format the amounts for display
            monthly_df['Total Amount'] = monthly_df['Total Amount'].apply(lambda x: f"₹{x:.2f}")
            st.dataframe(monthly_df, use_container_width=True)
        else:
            st.info("No monthly data available.")
    
    with tab2:
        st.header("Expenses by Category")
        category_df = create_category_summary(df)
        
        if not category_df.empty:
            # Create pie chart
            fig_pie = px.pie(
                category_df, 
                values='Total Amount', 
                names='Category',
                title="Expense Distribution by Category"
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Display category table
            st.subheader("Category Summary Table")
            category_display = category_df.copy()
            category_display['Total Amount'] = category_display['Total Amount'].apply(lambda x: f"₹{x:.2f}")
            st.dataframe(category_display, use_container_width=True)
        else:
            st.info("No category data available.")
    
    with tab3:
        st.header("Monthly Spending Trends")
        monthly_df = create_monthly_summary(df)
        
        if not monthly_df.empty:
            # Create bar chart
            fig_bar = px.bar(
                monthly_df,
                x='Month',
                y='Total Amount',
                title="Monthly Expense Trends",
                labels={'Total Amount': 'Amount (₹)'}
            )
            fig_bar.update_layout(xaxis_title="Month", yaxis_title="Total Spending (₹)")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No monthly trend data available.")
    
    with tab4:
        st.header("All Expenses")
        
        # Add filtering options
        col1, col2 = st.columns(2)
        
        with col1:
            # Category filter
            categories = ['All'] + sorted(df['category'].unique().tolist())
            selected_category = st.selectbox("Filter by Category:", categories)
        
        with col2:
            # Date range filter
            min_date = df['date'].min().date()
            max_date = df['date'].max().date()
            date_range = st.date_input(
                "Filter by Date Range:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if selected_category != 'All':
            filtered_df = filtered_df[filtered_df['category'] == selected_category]
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df['date'].dt.date >= start_date) & 
                (filtered_df['date'].dt.date <= end_date)
            ]
        
        # Display filtered data
        if not filtered_df.empty:
            # Format for display
            display_df = filtered_df.copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            display_df['amount'] = display_df['amount'].apply(lambda x: f"₹{x:.2f}")
            display_df.columns = ['Date', 'Category', 'Amount']
            
            # Sort by date (most recent first)
            display_df = display_df.sort_values('Date', ascending=False)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Summary of filtered data
            st.info(f"Showing {len(filtered_df)} transactions totaling ₹{filtered_df['amount'].sum():.2f}")
        else:
            st.info("No expenses match the selected filters.")
    
    # Footer
    st.markdown("---")
    st.markdown("💡 **Tip:** Use the sidebar to add new expenses. Data is automatically saved to `expenses.csv`.")

if __name__ == "__main__":
    main()
