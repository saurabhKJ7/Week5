"""
Helper functions for Excel Sheets Agent
"""

import streamlit as st
from typing import Dict, Any, List


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'config' not in st.session_state:
        st.session_state.config = None
    
    if 'excel_agent' not in st.session_state:
        st.session_state.excel_agent = None
    
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if 'results' not in st.session_state:
        st.session_state.results = None
    
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []


def display_sample_queries():
    """Display sample queries for user guidance"""
    st.markdown("""
    ### Try these sample queries:
    
    **Basic Operations:**
    - "How many rows are in the data?"
    - "What columns are available?"
    - "Show me the first 10 rows"
    
    **Filtering & Analysis:**
    - "Show sales data for Q3 2024 where revenue > 50000"
    - "Find customers who haven't ordered in 6 months"
    - "Filter products with price between 100 and 500"
    
    **Aggregations:**
    - "Calculate total sales by region"
    - "Show average price by product category"
    - "Create pivot table of sales by month and region"
    
    **Advanced:**
    - "Compare sales performance year over year"
    - "Identify top 10 customers by revenue"
    - "Show quarterly trends for the last 2 years"
    """)


def format_query_result(result: Dict[str, Any]) -> str:
    """Format query result for display"""
    if not result:
        return "No results to display"
    
    formatted_parts = []
    
    if result.get('summary'):
        formatted_parts.append(f"**Summary:** {result['summary']}")
    
    if result.get('data') is not None:
        rows = len(result['data'])
        cols = len(result['data'].columns) if hasattr(result['data'], 'columns') else 0
        formatted_parts.append(f"**Data:** {rows} rows, {cols} columns")
    
    if result.get('reasoning'):
        formatted_parts.append(f"**Steps:** {len(result['reasoning'])} reasoning steps")
    
    return "\n".join(formatted_parts) if formatted_parts else "Result processed successfully"


def validate_file_upload(file, max_size_mb: int = 200) -> tuple[bool, str]:
    """Validate uploaded file"""
    if file is None:
        return False, "No file uploaded"
    
    # Check file size
    file_size_mb = len(file.getvalue()) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File size ({file_size_mb:.1f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
    
    # Check file extension
    allowed_extensions = ['.xlsx', '.xls']
    file_extension = '.' + file.name.split('.')[-1].lower()
    if file_extension not in allowed_extensions:
        return False, f"File type {file_extension} not supported. Allowed types: {', '.join(allowed_extensions)}"
    
    return True, "File validation successful"


def display_error_message(error: Exception, context: str = ""):
    """Display formatted error message"""
    error_type = type(error).__name__
    error_message = str(error)
    
    st.error(f"""
    **Error in {context}:**
    
    **Type:** {error_type}
    
    **Message:** {error_message}
    
    Please try again or contact support if the issue persists.
    """)


def display_processing_stats(stats: Dict[str, Any]):
    """Display processing statistics"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Processing Time",
            f"{stats.get('processing_time', 0):.2f}s"
        )
    
    with col2:
        st.metric(
            "Rows Processed",
            f"{stats.get('rows_processed', 0):,}"
        )
    
    with col3:
        st.metric(
            "Memory Used",
            f"{stats.get('memory_used_mb', 0):.1f} MB"
        )


def create_download_link(data, filename: str, file_format: str = "csv"):
    """Create download link for processed data"""
    if file_format.lower() == "csv":
        csv = data.to_csv(index=False)
        st.download_button(
            label=f"Download {filename}.csv",
            data=csv,
            file_name=f"{filename}.csv",
            mime="text/csv"
        )
    elif file_format.lower() == "excel":
        # This would require additional logic for Excel export
        st.info("Excel export functionality to be implemented")


def get_column_suggestions(available_columns: List[str], query: str) -> List[str]:
    """Get column suggestions based on query text"""
    suggestions = []
    query_lower = query.lower()
    
    for col in available_columns:
        col_lower = col.lower()
        if any(word in col_lower for word in query_lower.split()):
            suggestions.append(col)
    
    return suggestions[:5]  # Return top 5 suggestions


def display_column_info(column_info: Dict[str, Any]):
    """Display column information in a formatted way"""
    st.subheader("Column Information")
    
    for col_name, info in column_info.items():
        with st.expander(f"📊 {col_name}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Type:** {info.get('dtype', 'Unknown')}")
                st.write(f"**Non-null Count:** {info.get('non_null_count', 0)}")
                st.write(f"**Null Count:** {info.get('null_count', 0)}")
            
            with col2:
                if info.get('unique_values'):
                    st.write(f"**Unique Values:** {info['unique_values']}")
                if info.get('sample_values'):
                    st.write(f"**Sample Values:** {', '.join(map(str, info['sample_values'][:3]))}")
                if info.get('min_value') is not None:
                    st.write(f"**Min:** {info['min_value']}")
                if info.get('max_value') is not None:
                    st.write(f"**Max:** {info['max_value']}") 