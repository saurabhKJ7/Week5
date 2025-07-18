"""
Data chunking utilities for memory-efficient processing of large Excel files
"""

import pandas as pd
import numpy as np
from typing import Iterator, List, Dict, Any, Optional, Tuple
import psutil
import os
from pathlib import Path


class DataChunker:
    """Handles chunking of large datasets for memory-efficient processing"""
    
    def __init__(self, chunk_size: int = 5000, max_memory_usage: float = 0.8):
        """
        Initialize DataChunker
        
        Args:
            chunk_size: Number of rows per chunk
            max_memory_usage: Maximum memory usage as a fraction (0.8 = 80%)
        """
        self.chunk_size = chunk_size
        self.max_memory_usage = max_memory_usage
        self.memory_threshold = self._calculate_memory_threshold()
    
    def _calculate_memory_threshold(self) -> int:
        """Calculate memory threshold in bytes"""
        total_memory = psutil.virtual_memory().total
        return int(total_memory * self.max_memory_usage)
    
    def _get_current_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
    
    def _estimate_chunk_memory(self, df: pd.DataFrame) -> int:
        """Estimate memory usage of a DataFrame chunk"""
        return df.memory_usage(deep=True).sum()
    
    def adaptive_chunk_size(self, df_sample: pd.DataFrame) -> int:
        """Calculate optimal chunk size based on available memory"""
        if len(df_sample) == 0:
            return self.chunk_size
        
        # Estimate memory per row
        sample_memory = self._estimate_chunk_memory(df_sample)
        memory_per_row = sample_memory / len(df_sample)
        
        # Calculate available memory
        available_memory = self.memory_threshold - self._get_current_memory_usage()
        
        # Calculate optimal chunk size (reserve some memory for processing)
        safe_memory = available_memory * 0.5  # Use only 50% of available memory
        optimal_chunk_size = int(safe_memory / memory_per_row)
        
        # Ensure minimum chunk size
        optimal_chunk_size = max(100, min(optimal_chunk_size, self.chunk_size))
        
        return optimal_chunk_size
    
    def chunk_dataframe(self, df: pd.DataFrame, chunk_size: Optional[int] = None) -> Iterator[pd.DataFrame]:
        """
        Chunk a DataFrame into smaller pieces
        
        Args:
            df: DataFrame to chunk
            chunk_size: Size of each chunk (uses adaptive size if None)
            
        Yields:
            DataFrame chunks
        """
        if chunk_size is None:
            chunk_size = self.adaptive_chunk_size(df.head(1000))
        
        total_rows = len(df)
        for start_idx in range(0, total_rows, chunk_size):
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk = df.iloc[start_idx:end_idx].copy()
            
            # Add chunk metadata
            chunk.attrs['chunk_info'] = {
                'start_row': start_idx,
                'end_row': end_idx,
                'chunk_size': len(chunk),
                'total_rows': total_rows,
                'chunk_index': start_idx // chunk_size
            }
            
            yield chunk
    
    def chunk_excel_file(self, file_path: str, sheet_name: Optional[str] = None) -> Iterator[pd.DataFrame]:
        """
        Read Excel file in chunks
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet to read (None for first sheet)
            
        Yields:
            DataFrame chunks
        """
        # First, get the total number of rows
        with pd.ExcelFile(file_path) as xls:
            if sheet_name is None:
                sheet_name = xls.sheet_names[0]
            
            # Read a sample to determine optimal chunk size
            sample_df = pd.read_excel(xls, sheet_name=sheet_name, nrows=1000)
            if isinstance(sample_df, dict):
                sample_df = list(sample_df.values())[0]
            optimal_chunk_size = self.adaptive_chunk_size(sample_df)
            
            # Get total rows by reading the sheet
            full_df = pd.read_excel(xls, sheet_name=sheet_name)
            if isinstance(full_df, dict):
                full_df = list(full_df.values())[0]
            total_rows = len(full_df)
            
            # Chunk the data
            for chunk in self.chunk_dataframe(full_df, optimal_chunk_size):
                yield chunk
    
    def process_chunks(self, 
                      chunks: Iterator[pd.DataFrame], 
                      operation: Any,
                      combine_results: bool = True) -> Any:
        """
        Process chunks with a given operation
        
        Args:
            chunks: Iterator of DataFrame chunks
            operation: Function to apply to each chunk
            combine_results: Whether to combine results from all chunks
            
        Returns:
            Combined results or list of results
        """
        results = []
        
        for i, chunk in enumerate(chunks):
            try:
                result = operation(chunk)
                results.append(result)
                
                # Memory check
                if self._get_current_memory_usage() > self.memory_threshold:
                    print(f"Warning: Memory usage high after processing chunk {i}")
                    
            except Exception as e:
                print(f"Error processing chunk {i}: {str(e)}")
                continue
        
        if combine_results and results:
            return self._combine_results(results)
        
        return results
    
    def _combine_results(self, results: List[Any]) -> Any:
        """Combine results from multiple chunks"""
        if not results:
            return None
        
        # Handle different result types
        if isinstance(results[0], pd.DataFrame):
            return pd.concat(results, ignore_index=True)
        elif isinstance(results[0], dict):
            # Combine dictionaries
            combined = {}
            for result in results:
                for key, value in result.items():
                    if key in combined:
                        if isinstance(value, (int, float)):
                            combined[key] += value
                        elif isinstance(value, list):
                            combined[key].extend(value)
                    else:
                        combined[key] = value
            return combined
        elif isinstance(results[0], (int, float)):
            return sum(results)
        else:
            return results
    
    def filter_chunks(self, 
                     chunks: Iterator[pd.DataFrame], 
                     condition: str) -> Iterator[pd.DataFrame]:
        """
        Filter chunks based on a condition
        
        Args:
            chunks: Iterator of DataFrame chunks
            condition: pandas query condition
            
        Yields:
            Filtered DataFrame chunks
        """
        for chunk in chunks:
            try:
                filtered_chunk = chunk.query(condition)
                if len(filtered_chunk) > 0:
                    yield filtered_chunk
            except Exception as e:
                print(f"Error filtering chunk: {str(e)}")
                continue
    
    def aggregate_chunks(self, 
                        chunks: Iterator[pd.DataFrame], 
                        groupby_cols: List[str],
                        agg_operations: Dict[str, Any]) -> pd.DataFrame:
        """
        Aggregate data across chunks
        
        Args:
            chunks: Iterator of DataFrame chunks
            groupby_cols: Columns to group by
            agg_operations: Aggregation operations to perform
            
        Returns:
            Aggregated DataFrame
        """
        partial_results = []
        
        for chunk in chunks:
            try:
                # Perform aggregation on chunk
                chunk_agg = chunk.groupby(groupby_cols).agg(agg_operations)
                partial_results.append(chunk_agg)
            except Exception as e:
                print(f"Error aggregating chunk: {str(e)}")
                continue
        
        if not partial_results:
            return pd.DataFrame()
        
        # Combine partial results
        combined = pd.concat(partial_results)
        
        # Final aggregation
        final_result = combined.groupby(groupby_cols).agg(agg_operations)
        
        return final_result.reset_index()
    
    def get_chunk_statistics(self, chunks: Iterator[pd.DataFrame]) -> Dict[str, Any]:
        """
        Get statistics about chunks
        
        Args:
            chunks: Iterator of DataFrame chunks
            
        Returns:
            Dictionary with chunk statistics
        """
        stats = {
            'total_chunks': 0,
            'total_rows': 0,
            'memory_usage': 0,
            'chunk_sizes': []
        }
        
        for chunk in chunks:
            stats['total_chunks'] += 1
            stats['total_rows'] += len(chunk)
            stats['memory_usage'] += self._estimate_chunk_memory(chunk)
            stats['chunk_sizes'].append(len(chunk))
        
        if stats['chunk_sizes']:
            stats['avg_chunk_size'] = np.mean(stats['chunk_sizes'])
            stats['min_chunk_size'] = np.min(stats['chunk_sizes'])
            stats['max_chunk_size'] = np.max(stats['chunk_sizes'])
        
        return stats
    
    def save_chunks_to_files(self, 
                           chunks: Iterator[pd.DataFrame], 
                           output_dir: str,
                           prefix: str = "chunk") -> List[str]:
        """
        Save chunks to separate files
        
        Args:
            chunks: Iterator of DataFrame chunks
            output_dir: Directory to save files
            prefix: Prefix for file names
            
        Returns:
            List of saved file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        for i, chunk in enumerate(chunks):
            filename = f"{prefix}_{i:04d}.csv"
            filepath = output_path / filename
            
            chunk.to_csv(filepath, index=False)
            saved_files.append(str(filepath))
        
        return saved_files
    
    def load_chunks_from_files(self, file_paths: List[str]) -> Iterator[pd.DataFrame]:
        """
        Load chunks from saved files
        
        Args:
            file_paths: List of file paths to load
            
        Yields:
            DataFrame chunks
        """
        for filepath in file_paths:
            try:
                chunk = pd.read_csv(filepath)
                yield chunk
            except Exception as e:
                print(f"Error loading chunk from {filepath}: {str(e)}")
                continue 