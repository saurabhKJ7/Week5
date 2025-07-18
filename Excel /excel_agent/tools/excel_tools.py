"""
LangChain tools for Excel operations
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json


class ReadWorksheetInput(BaseModel):
    """Input for reading worksheet data"""
    worksheet_name: str = Field(description="Name of the worksheet to read")
    rows: Optional[int] = Field(default=None, description="Number of rows to read (None for all)")
    columns: Optional[List[str]] = Field(default=None, description="Specific columns to read")


class ReadWorksheetTool(BaseTool):
    """Tool for reading worksheet data"""
    name = "read_worksheet"
    description = "Read data from a specific worksheet"
    args_schema = ReadWorksheetInput
    
    def __init__(self, excel_agent):
        super().__init__()
        self.excel_agent = excel_agent
    
    def _run(self, worksheet_name: str, rows: Optional[int] = None, columns: Optional[List[str]] = None) -> str:
        """Execute the tool"""
        try:
            # Set active worksheet
            self.excel_agent.set_active_worksheet(worksheet_name)
            
            # Get data
            df = self.excel_agent.get_current_data()
            
            # Apply row limit
            if rows is not None:
                df = df.head(rows)
            
            # Apply column filter
            if columns is not None:
                available_columns = df.columns.tolist()
                # Use column mapper to find best matches
                mapped_columns = self.excel_agent.column_mapper.map_multiple_columns(columns, available_columns)
                valid_columns = [col for col in mapped_columns.values() if col is not None]
                df = df[valid_columns]
            
            # Return summary
            return f"Read {len(df)} rows and {len(df.columns)} columns from worksheet '{worksheet_name}'"
            
        except Exception as e:
            return f"Error reading worksheet: {str(e)}"


class FilterDataInput(BaseModel):
    """Input for filtering data"""
    condition: str = Field(description="Pandas query condition for filtering")
    columns: Optional[List[str]] = Field(default=None, description="Columns to include in result")


class FilterDataTool(BaseTool):
    """Tool for filtering data based on conditions"""
    name = "filter_data"
    description = "Filter data based on specified conditions"
    args_schema = FilterDataInput
    
    def __init__(self, excel_agent):
        super().__init__()
        self.excel_agent = excel_agent
    
    def _run(self, condition: str, columns: Optional[List[str]] = None) -> str:
        """Execute the tool"""
        try:
            df = self.excel_agent.get_current_data()
            
            # Apply filter
            filtered_df = df.query(condition)
            
            # Apply column selection
            if columns is not None:
                available_columns = filtered_df.columns.tolist()
                mapped_columns = self.excel_agent.column_mapper.map_multiple_columns(columns, available_columns)
                valid_columns = [col for col in mapped_columns.values() if col is not None]
                filtered_df = filtered_df[valid_columns]
            
            # Update current data
            self.excel_agent.set_current_data(filtered_df)
            
            return f"Filtered data: {len(filtered_df)} rows remaining"
            
        except Exception as e:
            return f"Error filtering data: {str(e)}"


class AggregateDataInput(BaseModel):
    """Input for aggregating data"""
    group_by: List[str] = Field(description="Columns to group by")
    aggregations: Dict[str, str] = Field(description="Aggregation operations {column: operation}")


class AggregateDataTool(BaseTool):
    """Tool for aggregating data"""
    name = "aggregate_data"
    description = "Aggregate data by grouping and applying operations"
    args_schema = AggregateDataInput
    
    def __init__(self, excel_agent):
        super().__init__()
        self.excel_agent = excel_agent
    
    def _run(self, group_by: List[str], aggregations: Dict[str, str]) -> str:
        """Execute the tool"""
        try:
            df = self.excel_agent.get_current_data()
            
            # Map column names
            available_columns = df.columns.tolist()
            mapped_group_by = self.excel_agent.column_mapper.map_multiple_columns(group_by, available_columns)
            valid_group_by = [col for col in mapped_group_by.values() if col is not None]
            
            # Map aggregation columns
            mapped_agg = {}
            for col, op in aggregations.items():
                mapped_col = self.excel_agent.column_mapper.map_column(col, available_columns)
                if mapped_col:
                    mapped_agg[mapped_col] = op
            
            # Perform aggregation
            result = df.groupby(valid_group_by).agg(mapped_agg).reset_index()
            
            # Update current data
            self.excel_agent.set_current_data(result)
            
            return f"Aggregated data: {len(result)} groups, {len(result.columns)} columns"
            
        except Exception as e:
            return f"Error aggregating data: {str(e)}"


class SortDataInput(BaseModel):
    """Input for sorting data"""
    columns: List[str] = Field(description="Columns to sort by")
    ascending: Optional[List[bool]] = Field(default=None, description="Sort order for each column")


class SortDataTool(BaseTool):
    """Tool for sorting data"""
    name = "sort_data"
    description = "Sort data by specified columns"
    args_schema = SortDataInput
    
    def __init__(self, excel_agent):
        super().__init__()
        self.excel_agent = excel_agent
    
    def _run(self, columns: List[str], ascending: Optional[List[bool]] = None) -> str:
        """Execute the tool"""
        try:
            df = self.excel_agent.get_current_data()
            
            # Map column names
            available_columns = df.columns.tolist()
            mapped_columns = self.excel_agent.column_mapper.map_multiple_columns(columns, available_columns)
            valid_columns = [col for col in mapped_columns.values() if col is not None]
            
            # Sort data
            sorted_df = df.sort_values(by=valid_columns, ascending=ascending or True)
            
            # Update current data
            self.excel_agent.set_current_data(sorted_df)
            
            return f"Sorted data by {', '.join(valid_columns)}"
            
        except Exception as e:
            return f"Error sorting data: {str(e)}"


class PivotTableInput(BaseModel):
    """Input for creating pivot table"""
    index: List[str] = Field(description="Columns to use as row index")
    columns: List[str] = Field(description="Columns to use as column headers")
    values: List[str] = Field(description="Columns to aggregate")
    aggfunc: str = Field(default="sum", description="Aggregation function")


class PivotTableTool(BaseTool):
    """Tool for creating pivot tables"""
    name = "pivot_table"
    description = "Create pivot table from data"
    args_schema = PivotTableInput
    
    def __init__(self, excel_agent):
        super().__init__()
        self.excel_agent = excel_agent
    
    def _run(self, index: List[str], columns: List[str], values: List[str], aggfunc: str = "sum") -> str:
        """Execute the tool"""
        try:
            df = self.excel_agent.get_current_data()
            
            # Map column names
            available_columns = df.columns.tolist()
            mapped_index = [self.excel_agent.column_mapper.map_column(col, available_columns) for col in index]
            mapped_columns = [self.excel_agent.column_mapper.map_column(col, available_columns) for col in columns]
            mapped_values = [self.excel_agent.column_mapper.map_column(col, available_columns) for col in values]
            
            # Remove None values
            valid_index = [col for col in mapped_index if col is not None]
            valid_columns = [col for col in mapped_columns if col is not None]
            valid_values = [col for col in mapped_values if col is not None]
            
            # Create pivot table
            pivot = pd.pivot_table(
                df, 
                index=valid_index, 
                columns=valid_columns, 
                values=valid_values, 
                aggfunc=aggfunc,
                fill_value=0
            )
            
            # Update current data
            self.excel_agent.set_current_data(pivot.reset_index())
            
            return f"Created pivot table: {len(pivot)} rows, {len(pivot.columns)} columns"
            
        except Exception as e:
            return f"Error creating pivot table: {str(e)}"


class WriteResultsInput(BaseModel):
    """Input for writing results"""
    filename: str = Field(description="Output filename")
    format: str = Field(default="csv", description="Output format (csv, excel)")


class WriteResultsTool(BaseTool):
    """Tool for writing results to file"""
    name = "write_results"
    description = "Write current data to file"
    args_schema = WriteResultsInput
    
    def __init__(self, excel_agent):
        super().__init__()
        self.excel_agent = excel_agent
    
    def _run(self, filename: str, format: str = "csv") -> str:
        """Execute the tool"""
        try:
            df = self.excel_agent.get_current_data()
            
            # Create output directory
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            filepath = output_dir / filename
            
            # Write based on format
            if format.lower() == "csv":
                df.to_csv(filepath, index=False)
            elif format.lower() == "excel":
                df.to_excel(filepath, index=False)
            else:
                return f"Unsupported format: {format}"
            
            return f"Results written to {filepath}"
            
        except Exception as e:
            return f"Error writing results: {str(e)}"


class MergeWorksheetsInput(BaseModel):
    """Input for merging worksheets"""
    worksheets: List[str] = Field(description="List of worksheet names to merge")
    join_type: str = Field(default="outer", description="Type of join (inner, outer, left, right)")
    on: Optional[List[str]] = Field(default=None, description="Columns to join on")


class MergeWorksheetsTool(BaseTool):
    """Tool for merging multiple worksheets"""
    name = "merge_worksheets"
    description = "Merge multiple worksheets into one"
    args_schema = MergeWorksheetsInput
    
    def __init__(self, excel_agent):
        super().__init__()
        self.excel_agent = excel_agent
    
    def _run(self, worksheets: List[str], join_type: str = "outer", on: Optional[List[str]] = None) -> str:
        """Execute the tool"""
        try:
            dataframes = []
            
            # Read all worksheets
            for sheet_name in worksheets:
                df = self.excel_agent.read_worksheet(sheet_name)
                df['_source_sheet'] = sheet_name  # Add source identifier
                dataframes.append(df)
            
            # Merge dataframes
            if len(dataframes) == 1:
                merged_df = dataframes[0]
            else:
                merged_df = dataframes[0]
                for df in dataframes[1:]:
                    if on is not None:
                        merged_df = pd.merge(merged_df, df, on=on, how=join_type)
                    else:
                        merged_df = pd.concat([merged_df, df], ignore_index=True)
            
            # Update current data
            self.excel_agent.set_current_data(merged_df)
            
            return f"Merged {len(worksheets)} worksheets: {len(merged_df)} rows, {len(merged_df.columns)} columns"
            
        except Exception as e:
            return f"Error merging worksheets: {str(e)}"


class DataValidationInput(BaseModel):
    """Input for data validation"""
    checks: List[str] = Field(description="List of validation checks to perform")


class DataValidationTool(BaseTool):
    """Tool for validating data quality"""
    name = "data_validation"
    description = "Validate data quality and identify issues"
    args_schema = DataValidationInput
    
    def __init__(self, excel_agent):
        super().__init__()
        self.excel_agent = excel_agent
    
    def _run(self, checks: List[str]) -> str:
        """Execute the tool"""
        try:
            df = self.excel_agent.get_current_data()
            validation_results = []
            
            for check in checks:
                if check == "null_values":
                    null_counts = df.isnull().sum()
                    validation_results.append(f"Null values: {null_counts.sum()} total")
                
                elif check == "duplicates":
                    duplicate_count = df.duplicated().sum()
                    validation_results.append(f"Duplicate rows: {duplicate_count}")
                
                elif check == "data_types":
                    type_info = df.dtypes.value_counts()
                    validation_results.append(f"Data types: {type_info.to_dict()}")
                
                elif check == "outliers":
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    outlier_count = 0
                    for col in numeric_cols:
                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        outliers = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
                        outlier_count += outliers
                    validation_results.append(f"Outliers: {outlier_count}")
            
            return "; ".join(validation_results)
            
        except Exception as e:
            return f"Error validating data: {str(e)}"


class FormulaEvaluationInput(BaseModel):
    """Input for formula evaluation"""
    formula: str = Field(description="Excel-like formula to evaluate")
    new_column: str = Field(description="Name for the new column")


class FormulaEvaluationTool(BaseTool):
    """Tool for evaluating formulas"""
    name = "formula_evaluation"
    description = "Evaluate Excel-like formulas on data"
    args_schema = FormulaEvaluationInput
    
    def __init__(self, excel_agent):
        super().__init__()
        self.excel_agent = excel_agent
    
    def _run(self, formula: str, new_column: str) -> str:
        """Execute the tool"""
        try:
            df = self.excel_agent.get_current_data()
            
            # Simple formula evaluation (can be expanded)
            if formula.upper().startswith("SUM("):
                col_name = formula[4:-1]  # Extract column name
                mapped_col = self.excel_agent.column_mapper.map_column(col_name, df.columns.tolist())
                if mapped_col:
                    df[new_column] = df[mapped_col].sum()
            
            elif formula.upper().startswith("AVERAGE("):
                col_name = formula[8:-1]
                mapped_col = self.excel_agent.column_mapper.map_column(col_name, df.columns.tolist())
                if mapped_col:
                    df[new_column] = df[mapped_col].mean()
            
            # Update current data
            self.excel_agent.set_current_data(df)
            
            return f"Formula '{formula}' evaluated and added as column '{new_column}'"
            
        except Exception as e:
            return f"Error evaluating formula: {str(e)}"


class ChartGenerationInput(BaseModel):
    """Input for chart generation"""
    chart_type: str = Field(description="Type of chart (bar, line, scatter, pie)")
    x_column: str = Field(description="Column for x-axis")
    y_column: Optional[str] = Field(default=None, description="Column for y-axis")
    title: Optional[str] = Field(default=None, description="Chart title")


class ChartGenerationTool(BaseTool):
    """Tool for generating charts"""
    name = "chart_generation"
    description = "Generate charts from data"
    args_schema = ChartGenerationInput
    
    def __init__(self, excel_agent):
        super().__init__()
        self.excel_agent = excel_agent
    
    def _run(self, chart_type: str, x_column: str, y_column: Optional[str] = None, title: Optional[str] = None) -> str:
        """Execute the tool"""
        try:
            df = self.excel_agent.get_current_data()
            
            # Map column names
            available_columns = df.columns.tolist()
            mapped_x = self.excel_agent.column_mapper.map_column(x_column, available_columns)
            mapped_y = self.excel_agent.column_mapper.map_column(y_column, available_columns) if y_column else None
            
            if not mapped_x:
                return f"Could not find column '{x_column}'"
            
            # Generate chart based on type
            if chart_type.lower() == "bar":
                if mapped_y:
                    fig = px.bar(df, x=mapped_x, y=mapped_y, title=title)
                else:
                    fig = px.bar(df[mapped_x].value_counts().reset_index(), x='index', y=mapped_x, title=title)
            
            elif chart_type.lower() == "line":
                if mapped_y:
                    fig = px.line(df, x=mapped_x, y=mapped_y, title=title)
                else:
                    return "Line chart requires both x and y columns"
            
            elif chart_type.lower() == "scatter":
                if mapped_y:
                    fig = px.scatter(df, x=mapped_x, y=mapped_y, title=title)
                else:
                    return "Scatter chart requires both x and y columns"
            
            elif chart_type.lower() == "pie":
                value_counts = df[mapped_x].value_counts()
                fig = px.pie(values=value_counts.values, names=value_counts.index, title=title)
            
            else:
                return f"Unsupported chart type: {chart_type}"
            
            # Store chart for display
            self.excel_agent.set_current_chart(fig)
            
            return f"Generated {chart_type} chart with {len(df)} data points"
            
        except Exception as e:
            return f"Error generating chart: {str(e)}" 