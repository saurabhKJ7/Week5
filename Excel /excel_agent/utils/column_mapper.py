"""
Column mapping utilities for handling different naming conventions
"""

from typing import Dict, List, Optional, Tuple
from fuzzywuzzy import fuzz, process
import re


class ColumnMapper:
    """Handles column name mapping and fuzzy matching"""
    
    def __init__(self, threshold: int = 80):
        self.threshold = threshold
        self.synonym_dict = self._build_synonym_dict()
    
    def _build_synonym_dict(self) -> Dict[str, List[str]]:
        """Build dictionary of common business term synonyms"""
        return {
            # Quantity/Amount
            'quantity': ['qty', 'amount', 'count', 'number', 'num', 'vol', 'volume'],
            'amount': ['amt', 'value', 'sum', 'total', 'quantity', 'qty'],
            
            # Sales/Revenue
            'revenue': ['sales', 'income', 'earnings', 'proceeds', 'receipts'],
            'sales': ['revenue', 'sold', 'purchases', 'orders'],
            'price': ['cost', 'rate', 'value', 'amount', 'charge'],
            
            # Time/Date
            'date': ['time', 'timestamp', 'created', 'modified', 'updated'],
            'year': ['yr', 'annual'],
            'month': ['mth', 'monthly'],
            'quarter': ['qtr', 'q'],
            
            # Customer/Client
            'customer': ['client', 'buyer', 'purchaser', 'user'],
            'customer_id': ['client_id', 'user_id', 'buyer_id'],
            'customer_name': ['client_name', 'user_name', 'buyer_name'],
            
            # Product/Item
            'product': ['item', 'article', 'goods', 'merchandise'],
            'product_id': ['item_id', 'sku', 'code', 'product_code'],
            'product_name': ['item_name', 'description', 'title'],
            
            # Location
            'region': ['area', 'zone', 'territory', 'district'],
            'country': ['nation', 'state'],
            'city': ['town', 'location'],
            
            # Financial
            'profit': ['margin', 'earnings', 'gain'],
            'cost': ['expense', 'expenditure', 'price'],
            'discount': ['reduction', 'deduction', 'rebate'],
            
            # Status/Category
            'status': ['state', 'condition', 'stage'],
            'category': ['type', 'class', 'group', 'segment'],
            'priority': ['importance', 'urgency', 'level']
        }
    
    def normalize_column_name(self, column_name: str) -> str:
        """Normalize column name to standard format"""
        # Remove special characters and convert to lowercase
        normalized = re.sub(r'[^\w\s]', '', column_name.lower())
        
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Convert to snake_case
        normalized = normalized.replace(' ', '_')
        
        return normalized
    
    def find_similar_columns(self, 
                           query_column: str, 
                           available_columns: List[str]) -> List[Tuple[str, int]]:
        """Find similar column names using fuzzy matching"""
        results = []
        query_normalized = self.normalize_column_name(query_column)
        
        for col in available_columns:
            col_normalized = self.normalize_column_name(col)
            
            # Direct match
            if query_normalized == col_normalized:
                results.append((col, 100))
                continue
            
            # Fuzzy match
            similarity = fuzz.ratio(query_normalized, col_normalized)
            if similarity >= self.threshold:
                results.append((col, similarity))
                continue
            
            # Check synonyms
            for synonym_key, synonyms in self.synonym_dict.items():
                if query_normalized in synonyms or query_normalized == synonym_key:
                    for synonym in synonyms + [synonym_key]:
                        if synonym in col_normalized:
                            similarity = max(similarity, 85)  # High similarity for synonym matches
                            break
                    
                    if similarity >= self.threshold:
                        results.append((col, similarity))
                        break
        
        # Sort by similarity score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def map_column(self, 
                   query_column: str, 
                   available_columns: List[str]) -> Optional[str]:
        """Map a query column to the best matching available column"""
        similar_columns = self.find_similar_columns(query_column, available_columns)
        
        if similar_columns:
            best_match, score = similar_columns[0]
            if score >= self.threshold:
                return best_match
        
        return None
    
    def map_multiple_columns(self, 
                           query_columns: List[str], 
                           available_columns: List[str]) -> Dict[str, Optional[str]]:
        """Map multiple query columns to available columns"""
        mapping = {}
        
        for query_col in query_columns:
            mapped_col = self.map_column(query_col, available_columns)
            mapping[query_col] = mapped_col
        
        return mapping
    
    def suggest_columns(self, 
                       query: str, 
                       available_columns: List[str],
                       max_suggestions: int = 5) -> List[Tuple[str, int]]:
        """Suggest relevant columns based on query text"""
        query_words = query.lower().split()
        suggestions = []
        
        for col in available_columns:
            col_normalized = self.normalize_column_name(col)
            max_score = 0
            
            # Check if any query word matches column name
            for word in query_words:
                if len(word) > 2:  # Ignore very short words
                    score = fuzz.partial_ratio(word, col_normalized)
                    max_score = max(max_score, score)
            
            # Check synonym matches
            for word in query_words:
                if len(word) > 2:
                    for synonym_key, synonyms in self.synonym_dict.items():
                        if word in synonyms or word == synonym_key:
                            if synonym_key in col_normalized or any(syn in col_normalized for syn in synonyms):
                                max_score = max(max_score, 80)
            
            if max_score >= 60:  # Lower threshold for suggestions
                suggestions.append((col, max_score))
        
        # Sort by score and return top suggestions
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:max_suggestions]
    
    def get_column_variations(self, column_name: str) -> List[str]:
        """Get possible variations of a column name"""
        variations = [column_name]
        normalized = self.normalize_column_name(column_name)
        
        # Add normalized version
        if normalized != column_name:
            variations.append(normalized)
        
        # Add camelCase version
        camel_case = self._to_camel_case(normalized)
        if camel_case not in variations:
            variations.append(camel_case)
        
        # Add PascalCase version
        pascal_case = self._to_pascal_case(normalized)
        if pascal_case not in variations:
            variations.append(pascal_case)
        
        # Add space-separated version
        spaced = normalized.replace('_', ' ')
        if spaced not in variations:
            variations.append(spaced)
        
        # Add title case version
        title_case = spaced.title()
        if title_case not in variations:
            variations.append(title_case)
        
        return variations
    
    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase"""
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    def _to_pascal_case(self, snake_str: str) -> str:
        """Convert snake_case to PascalCase"""
        components = snake_str.split('_')
        return ''.join(x.title() for x in components)
    
    def validate_column_mapping(self, 
                              mapping: Dict[str, Optional[str]], 
                              required_columns: List[str]) -> Tuple[bool, List[str]]:
        """Validate that all required columns are mapped"""
        missing_columns = []
        
        for req_col in required_columns:
            if req_col not in mapping or mapping[req_col] is None:
                missing_columns.append(req_col)
        
        is_valid = len(missing_columns) == 0
        return is_valid, missing_columns
    
    def get_mapping_confidence(self, 
                             query_column: str, 
                             mapped_column: str, 
                             available_columns: List[str]) -> float:
        """Get confidence score for a column mapping"""
        similar_columns = self.find_similar_columns(query_column, available_columns)
        
        for col, score in similar_columns:
            if col == mapped_column:
                return score / 100.0
        
        return 0.0 