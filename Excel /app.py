import streamlit as st
import pandas as pd
import os
from pathlib import Path
from excel_agent.main import ExcelAgent
from excel_agent.utils.config import Config
from excel_agent.utils.helpers import initialize_session_state, display_sample_queries

# Page configuration
st.set_page_config(
    page_title="Excel Sheets Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main Streamlit application"""
    st.title("🤖 Excel Sheets Agent")
    st.markdown("**Intelligent Excel processing with natural language queries**")
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # LLM Provider selection
        llm_provider = st.selectbox(
            "Select LLM Provider",
            ["OpenAI", "Anthropic"],
            index=0
        )
        
        # API Key input
        api_key_label = f"{llm_provider} API Key"
        api_key = st.text_input(
            api_key_label,
            type="password",
            help=f"Enter your {llm_provider} API key"
        )
        
        # Model selection
        if llm_provider == "OpenAI":
            model = st.selectbox(
                "Select Model",
                ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                index=0
            )
        else:
            model = st.selectbox(
                "Select Model", 
                ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
                index=0
            )
        
        st.divider()
        
        # Processing options
        st.header("Processing Options")
        chunk_size = st.slider(
            "Chunk Size (rows)",
            min_value=1000,
            max_value=10000,
            value=5000,
            step=1000,
            help="Number of rows to process at once for large files"
        )
        
        use_fuzzy_matching = st.checkbox(
            "Enable Fuzzy Column Matching",
            value=True,
            help="Use fuzzy matching to handle column name variations"
        )
        
        # Save settings
        if st.button("Save Settings"):
            config = Config(
                llm_provider=llm_provider,
                api_key=api_key,
                model=model,
                chunk_size=chunk_size,
                use_fuzzy_matching=use_fuzzy_matching
            )
            st.session_state.config = config
            st.success("Settings saved!")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📁 Upload Excel File")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an Excel file",
            type=['xlsx', 'xls'],
            help="Upload Excel files up to 200MB"
        )
        
        if uploaded_file is not None:
            # Save uploaded file
            file_path = f"temp/{uploaded_file.name}"
            os.makedirs("temp", exist_ok=True)
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"File uploaded: {uploaded_file.name}")
            
            # Initialize Excel Agent
            if hasattr(st.session_state, 'config') and st.session_state.config.api_key:
                try:
                    agent = ExcelAgent(
                        config=st.session_state.config,
                        file_path=file_path
                    )
                    st.session_state.excel_agent = agent
                    
                    # Display file info
                    st.subheader("📋 File Information")
                    file_info = agent.get_file_info()
                    
                    info_col1, info_col2 = st.columns(2)
                    with info_col1:
                        st.metric("Worksheets", file_info['worksheet_count'])
                        st.metric("Total Rows", file_info['total_rows'])
                    with info_col2:
                        st.metric("Total Columns", file_info['total_columns'])
                        st.metric("File Size", f"{file_info['file_size_mb']:.1f} MB")
                    
                    # Worksheet selection
                    st.subheader("📊 Select Worksheet")
                    worksheet_names = agent.get_worksheet_names()
                    selected_worksheet = st.selectbox(
                        "Choose worksheet",
                        worksheet_names,
                        index=0
                    )
                    
                    if selected_worksheet:
                        agent.set_active_worksheet(selected_worksheet)
                        
                        # Display preview
                        st.subheader("👀 Data Preview")
                        preview_df = agent.get_preview(rows=10)
                        st.dataframe(preview_df, use_container_width=True)
                        
                        # Column information
                        st.subheader("📋 Column Information")
                        column_info = agent.get_column_info()
                        st.json(column_info)
                        
                except Exception as e:
                    st.error(f"Error initializing Excel Agent: {str(e)}")
            else:
                st.warning("Please configure API key in the sidebar first.")
    
    with col2:
        st.header("💡 Sample Queries")
        display_sample_queries()
    
    # Query interface
    if hasattr(st.session_state, 'excel_agent'):
        st.header("🤖 Natural Language Query Interface")
        
        # Query input
        query = st.text_area(
            "Enter your query:",
            height=100,
            placeholder="e.g., 'Show sales data for Q3 2024 where revenue > 50000'"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🔍 Execute Query", type="primary"):
                if query:
                    with st.spinner("Processing query..."):
                        try:
                            result = st.session_state.excel_agent.process_query(query)
                            
                            # Display results
                            st.subheader("📊 Results")
                            
                            if result.get('data') is not None:
                                st.dataframe(result['data'], use_container_width=True)
                            
                            if result.get('visualization'):
                                st.plotly_chart(result['visualization'], use_container_width=True)
                            
                            if result.get('summary'):
                                st.info(result['summary'])
                                
                            # Show reasoning steps
                            if result.get('reasoning'):
                                with st.expander("🧠 Reasoning Steps"):
                                    for step in result['reasoning']:
                                        st.write(f"**{step['step']}:** {step['description']}")
                                        if step.get('code'):
                                            st.code(step['code'], language='python')
                                            
                        except Exception as e:
                            st.error(f"Error processing query: {str(e)}")
                else:
                    st.warning("Please enter a query.")
        
        with col2:
            if st.button("🧹 Clear Results"):
                st.session_state.results = None
                st.rerun()
        
        # Query history
        st.subheader("📝 Query History")
        if hasattr(st.session_state, 'query_history') and st.session_state.query_history:
            for i, historical_query in enumerate(reversed(st.session_state.query_history[-5:])):
                with st.expander(f"Query {len(st.session_state.query_history) - i}: {historical_query[:50]}..."):
                    st.write(historical_query)
                    if st.button(f"Rerun", key=f"rerun_{i}"):
                        st.session_state.current_query = historical_query
                        st.rerun()
        else:
            st.info("No queries executed yet.")

if __name__ == "__main__":
    main() 