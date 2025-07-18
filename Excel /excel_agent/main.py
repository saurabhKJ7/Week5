"""
Main Excel Agent class that orchestrates all components
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import sqlite3
import json
import time
from datetime import datetime
import os

# LangChain imports with fallbacks
try:
    from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
    from langchain.agents import AgentType
    from langchain_openai import ChatOpenAI
    from langchain_community.llms import OpenAI
    from langchain_experimental.tools import PythonREPLTool
    from langchain.agents import initialize_agent
    from langchain.tools import Tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    # Fallback to deprecated imports if new ones aren't available
    try:
        from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
        from langchain.agents import AgentType
        from langchain.llms import OpenAI
        from langchain.chat_models import ChatOpenAI
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        print("LangChain not available. Using basic functionality.")

# Local imports
from .utils.config import Config
from .utils.column_mapper import ColumnMapper
from .utils.chunking import DataChunker


class ExcelAgent:
    """Main Excel Agent class"""
    
    def __init__(self, config: Config, file_path: str):
        """
        Initialize Excel Agent
        
        Args:
            config: Configuration object
            file_path: Path to Excel file
        """
        self.config = config
        self.file_path = file_path
        self.worksheets = {}
        self.current_worksheet = None
        self.current_data = None
        self.current_chart = None
        self.query_history = []
        
        # Initialize components
        self.column_mapper = ColumnMapper(threshold=config.fuzzy_threshold)
        self.chunker = DataChunker(chunk_size=config.chunk_size)
        
        # Initialize LLM if available
        self.llm = None
        self.agent = None
        if LANGCHAIN_AVAILABLE:
            self.llm = self._initialize_llm()
            if self.llm is None:
                print("LLM initialization failed")
        
        # Initialize database
        self.db_path = config.database_path
        self._initialize_database()
        
        # Load Excel file
        self._load_excel_file()
    
    def _initialize_llm(self):
        """Initialize Language Model"""
        if not LANGCHAIN_AVAILABLE:
            return None
            
        llm_config = self.config.get_llm_config()
        
        try:
            if llm_config['provider'] == 'OpenAI':
                os.environ['OPENAI_API_KEY'] = llm_config['api_key']
                return ChatOpenAI(
                    temperature=llm_config['temperature'],
                    model=llm_config['model'],  # Changed from model_name to model
                    max_tokens=1000,  # Limit tokens to prevent long loops
                    timeout=30  # Add timeout
                )
            else:
                # Fallback to basic OpenAI
                os.environ['OPENAI_API_KEY'] = llm_config['api_key']
                return OpenAI(
                    temperature=llm_config['temperature'],
                    max_tokens=1000,
                    timeout=30
                )
        except Exception as e:
            print(f"Error initializing LLM: {e}")
            return None
    
    def _initialize_database(self):
        """Initialize SQLite database for caching"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT UNIQUE,
                query TEXT,
                result TEXT,
                timestamp DATETIME,
                file_path TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT,
                rows_processed INTEGER,
                processing_time REAL,
                memory_used REAL,
                timestamp DATETIME
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_excel_file(self):
        """Load Excel file and analyze structure"""
        try:
            # Read Excel file
            excel_file = pd.ExcelFile(self.file_path)
            
            # Load all worksheets
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                self.worksheets[sheet_name] = df
            
            # Set first worksheet as current
            if self.worksheets:
                first_sheet = list(self.worksheets.keys())[0]
                self.set_active_worksheet(first_sheet)
                
        except Exception as e:
            raise ValueError(f"Error loading Excel file: {str(e)}")
    
    def get_file_info(self) -> Dict[str, Any]:
        """Get information about the Excel file"""
        total_rows = sum(len(df) for df in self.worksheets.values())
        total_columns = sum(len(df.columns) for df in self.worksheets.values())
        file_size = Path(self.file_path).stat().st_size / (1024 * 1024)  # MB
        
        return {
            'worksheet_count': len(self.worksheets),
            'total_rows': total_rows,
            'total_columns': total_columns,
            'file_size_mb': file_size,
            'worksheets': list(self.worksheets.keys())
        }
    
    def get_worksheet_names(self) -> List[str]:
        """Get list of worksheet names"""
        return list(self.worksheets.keys())
    
    def set_active_worksheet(self, worksheet_name: str):
        """Set active worksheet"""
        if worksheet_name not in self.worksheets:
            raise ValueError(f"Worksheet '{worksheet_name}' not found")
        
        self.current_worksheet = worksheet_name
        self.current_data = self.worksheets[worksheet_name].copy()
        
        # Create agent for current data if LangChain is available
        if LANGCHAIN_AVAILABLE and self.llm and self.current_data is not None:
            try:
                self.agent = create_pandas_dataframe_agent(
                    self.llm,
                    self.current_data,
                    verbose=True,
                    agent_type=AgentType.OPENAI_FUNCTIONS,  # Use OpenAI functions instead
                    allow_dangerous_code=True,
                    max_iterations=5,  # Limit iterations to prevent infinite loops
                    max_execution_time=30,  # Add timeout
                    early_stopping_method="force"  # Force stop if needed
                )
            except Exception as e:
                print(f"Error creating agent: {e}")
                # Fallback to basic approach
                try:
                    self.agent = create_pandas_dataframe_agent(
                        self.llm,
                        self.current_data,
                        verbose=False,
                        allow_dangerous_code=True
                    )
                except Exception as e2:
                    print(f"Fallback agent creation failed: {e2}")
                    self.agent = None
    
    def get_current_data(self) -> pd.DataFrame:
        """Get current working data"""
        if self.current_data is None:
            return pd.DataFrame()
        return self.current_data
    
    def set_current_data(self, df: pd.DataFrame):
        """Set current working data"""
        self.current_data = df
        
        # Recreate agent with new data
        if LANGCHAIN_AVAILABLE and self.llm:
            try:
                self.agent = create_pandas_dataframe_agent(
                    self.llm,
                    df,
                    verbose=True,
                    agent_type=AgentType.OPENAI_FUNCTIONS,  # Use OpenAI functions instead
                    allow_dangerous_code=True,
                    max_iterations=5,  # Limit iterations to prevent infinite loops
                    max_execution_time=30,  # Add timeout
                    early_stopping_method="force"  # Force stop if needed
                )
            except Exception as e:
                print(f"Error recreating agent: {e}")
                # Fallback to basic approach
                try:
                    self.agent = create_pandas_dataframe_agent(
                        self.llm,
                        df,
                        verbose=False,
                        allow_dangerous_code=True
                    )
                except Exception as e2:
                    print(f"Fallback agent creation failed: {e2}")
                    self.agent = None
    
    def get_current_chart(self):
        """Get current chart"""
        return self.current_chart
    
    def set_current_chart(self, chart):
        """Set current chart"""
        self.current_chart = chart
    
    def read_worksheet(self, worksheet_name: str) -> pd.DataFrame:
        """Read specific worksheet"""
        if worksheet_name not in self.worksheets:
            raise ValueError(f"Worksheet '{worksheet_name}' not found")
        return self.worksheets[worksheet_name].copy()
    
    def get_preview(self, rows: int = 10) -> pd.DataFrame:
        """Get preview of current data"""
        if self.current_data is None:
            return pd.DataFrame()
        return self.current_data.head(rows)
    
    def get_column_info(self) -> Dict[str, Any]:
        """Get information about columns in current data"""
        if self.current_data is None:
            return {}
        
        column_info = {}
        for col in self.current_data.columns:
            dtype = str(self.current_data[col].dtype)
            non_null_count = self.current_data[col].count()
            null_count = self.current_data[col].isnull().sum()
            
            info = {
                'dtype': dtype,
                'non_null_count': non_null_count,
                'null_count': null_count,
                'unique_values': self.current_data[col].nunique()
            }
            
            # Add sample values
            sample_values = self.current_data[col].dropna().head(3).tolist()
            if sample_values:
                info['sample_values'] = sample_values
            
            # Add min/max for numeric columns
            if self.current_data[col].dtype in ['int64', 'float64']:
                info['min_value'] = self.current_data[col].min()
                info['max_value'] = self.current_data[col].max()
            
            column_info[col] = info
        
        return column_info
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query"""
        start_time = time.time()
        
        try:
            # Check cache first
            if self.config.cache_enabled:
                cached_result = self._get_cached_result(query)
                if cached_result:
                    return cached_result
            
            # Process query with agent if available
            if self.agent is not None:
                result = self.agent.run(query)
                
                # Prepare response
                response = {
                    'query': query,
                    'summary': result,
                    'data': self.current_data.copy() if self.current_data is not None else None,
                    'visualization': self.current_chart,
                    'reasoning': [{'step': 'Agent Processing', 'description': 'Used pandas agent to process query'}],
                    'processing_time': time.time() - start_time
                }
            else:
                # Fallback to basic processing
                response = self._process_query_fallback(query)
                response['processing_time'] = time.time() - start_time
            
            # Cache result
            if self.config.cache_enabled:
                self._cache_result(query, response)
            
            # Add to history
            self.query_history.append(query)
            
            # Record stats
            self._record_processing_stats(
                operation="query_processing",
                rows_processed=len(self.current_data) if self.current_data is not None else 0,
                processing_time=response['processing_time'],
                memory_used=self._get_memory_usage()
            )
            
            return response
            
        except Exception as e:
            return {
                'query': query,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _process_query_fallback(self, query: str) -> Dict[str, Any]:
        """Fallback query processing without LangChain"""
        query_lower = query.lower()
        
        if self.current_data is None:
            return {
                'query': query,
                'summary': 'No data available',
                'data': None,
                'visualization': None,
                'reasoning': [{'step': 'Error', 'description': 'No data loaded'}]
            }
        
        # Basic query processing
        if 'how many' in query_lower and 'rows' in query_lower:
            summary = f"The dataset has {len(self.current_data)} rows."
        elif 'columns' in query_lower:
            summary = f"The dataset has {len(self.current_data.columns)} columns: {', '.join(self.current_data.columns)}"
        elif 'preview' in query_lower or 'first' in query_lower:
            summary = f"Showing first 10 rows of data"
        else:
            summary = f"Basic information: {len(self.current_data)} rows, {len(self.current_data.columns)} columns"
        
        return {
            'query': query,
            'summary': summary,
            'data': self.current_data.copy(),
            'visualization': None,
            'reasoning': [{'step': 'Basic Processing', 'description': 'Used basic pandas operations'}]
        }
    
    def _get_cached_result(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached result if available"""
        query_hash = hash(query + self.file_path)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT result FROM query_cache 
            WHERE query_hash = ? AND file_path = ?
            AND timestamp > datetime('now', '-1 hour')
        """, (str(query_hash), self.file_path))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def _cache_result(self, query: str, result: Dict[str, Any]):
        """Cache query result"""
        query_hash = hash(query + self.file_path)
        
        # Remove non-serializable objects
        cacheable_result = {
            'query': result['query'],
            'summary': result['summary'],
            'processing_time': result['processing_time']
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO query_cache 
            (query_hash, query, result, timestamp, file_path)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(query_hash),
            query,
            json.dumps(cacheable_result),
            datetime.now(),
            self.file_path
        ))
        
        conn.commit()
        conn.close()
    
    def _record_processing_stats(self, operation: str, rows_processed: int, processing_time: float, memory_used: float):
        """Record processing statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO processing_stats 
            (operation, rows_processed, processing_time, memory_used, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (operation, rows_processed, processing_time, memory_used, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT operation, AVG(rows_processed), AVG(processing_time), AVG(memory_used)
            FROM processing_stats
            GROUP BY operation
        """)
        
        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = {
                'avg_rows_processed': row[1],
                'avg_processing_time': row[2],
                'avg_memory_used': row[3]
            }
        
        conn.close()
        return stats
    
    def cleanup(self):
        """Clean up resources"""
        # Clear data
        self.current_data = None
        self.current_chart = None
        
        # Clear worksheets
        self.worksheets.clear() 