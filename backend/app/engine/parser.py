"""Safe expression parser for Filter and Formula nodes.

This module provides sandboxed expression evaluation to prevent
arbitrary code execution while still allowing useful data transformations.

Security Approach:
1. Whitelist allowed operations and functions
2. Block dangerous patterns (imports, exec, eval, dunders)
3. Use pandas.eval() with restricted local namespace
4. Validate column references against actual DataFrame columns
"""
import re
import ast
from typing import Any

import pandas as pd
import numpy as np


class ExpressionError(Exception):
    """Raised when expression validation or evaluation fails."""
    pass


class SafeExpressionParser:
    """Parse and evaluate expressions safely within a DataFrame context."""
    
    # Patterns that indicate dangerous operations
    DANGEROUS_PATTERNS = [
        r'\b__\w+__\b',      # Dunders like __import__, __class__
        r'\bexec\s*\(',       # exec()
        r'\beval\s*\(',       # eval() 
        r'\bcompile\s*\(',    # compile()
        r'\bopen\s*\(',       # open()
        r'\bimport\s',        # import statements
        r'\bos\.\w+',         # os module access
        r'\bsys\.\w+',        # sys module access
        r'\bsubprocess',      # subprocess module
        r'\bglobals\s*\(',    # globals()
        r'\blocals\s*\(',     # locals()
        r'\bgetattr\s*\(',    # getattr()
        r'\bsetattr\s*\(',    # setattr()
        r'\bdelattr\s*\(',    # delattr()
        r'\b__builtins__',    # builtins access
        r'\blambda\s',        # lambda expressions (we control these)
    ]
    
    # Allowed functions in expressions
    ALLOWED_FUNCTIONS = {
        # Math functions (from numpy, exposed simply)
        'abs': np.abs,
        'round': np.round,
        'floor': np.floor,
        'ceil': np.ceil,
        'sqrt': np.sqrt,
        'log': np.log,
        'log10': np.log10,
        'exp': np.exp,
        'sin': np.sin,
        'cos': np.cos,
        'tan': np.tan,
        'min': np.minimum,
        'max': np.maximum,
        # String operations (these work on Series)
        'lower': lambda s: s.str.lower(),
        'upper': lambda s: s.str.upper(),
        'len': lambda s: s.str.len(),
        'strip': lambda s: s.str.strip(),
        'contains': lambda s, pat: s.str.contains(pat, na=False),
    }
    
    # Operators allowed in pandas.eval
    ALLOWED_OPERATORS = {'+', '-', '*', '/', '//', '%', '**', 
                         '==', '!=', '<', '>', '<=', '>=',
                         '&', '|', '~', 'and', 'or', 'not',
                         'in', 'not in'}
    
    def __init__(self):
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS
        ]
    
    def validate(self, expression: str) -> tuple[bool, str | None]:
        """Validate an expression for safety.
        
        Args:
            expression: The expression string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not expression or not expression.strip():
            return False, "Expression cannot be empty"
        
        # Check for dangerous patterns
        for pattern in self._compiled_patterns:
            if pattern.search(expression):
                return False, f"Expression contains forbidden pattern: {pattern.pattern}"
        
        # Try to parse as AST to check syntax
        try:
            ast.parse(expression, mode='eval')
        except SyntaxError as e:
            return False, f"Invalid expression syntax: {e}"
        
        return True, None
    
    def validate_columns(
        self, 
        expression: str, 
        available_columns: list[str]
    ) -> tuple[bool, str | None]:
        """Validate that expression only references available columns.
        
        Args:
            expression: The expression to check
            available_columns: List of valid column names
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Extract potential column references (simple heuristic)
        # This looks for word characters not followed by (
        words = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b(?!\s*\()', expression)
        
        # Filter out known functions and keywords
        keywords = {'and', 'or', 'not', 'in', 'True', 'False', 'None'}
        keywords.update(self.ALLOWED_FUNCTIONS.keys())
        
        for word in words:
            if word not in keywords and word not in available_columns:
                # Could be a literal, check if it looks like a column reference
                if not re.match(r'^\d', word):  # Not starting with digit
                    return False, f"Unknown column reference: '{word}'"
        
        return True, None
    
    def evaluate_filter(
        self, 
        df: pd.DataFrame, 
        expression: str
    ) -> pd.DataFrame:
        """Evaluate a filter expression and return filtered DataFrame.
        
        Args:
            df: Input DataFrame
            expression: Filter expression (e.g., "age > 18 and status == 'active'")
            
        Returns:
            Filtered DataFrame
            
        Raises:
            ExpressionError: If expression is invalid or evaluation fails
        """
        # Validate safety
        is_valid, error = self.validate(expression)
        if not is_valid:
            raise ExpressionError(error)
        
        # Convert common comparison operators to Python/Pandas
        expr = self._normalize_expression(expression)
        
        try:
            # Use DataFrame.query() which is safer than raw eval
            result = df.query(expr, local_dict=self.ALLOWED_FUNCTIONS)
            return result
        except Exception as e:
            # Fall back to pandas eval for boolean mask
            try:
                mask = df.eval(expr, local_dict=self.ALLOWED_FUNCTIONS)
                return df[mask]
            except Exception as e2:
                raise ExpressionError(f"Failed to evaluate filter: {e2}")
    
    def evaluate_formula(
        self, 
        df: pd.DataFrame, 
        expression: str,
        new_column: str
    ) -> pd.DataFrame:
        """Evaluate a formula expression and add result as new column.
        
        Args:
            df: Input DataFrame
            expression: Formula expression (e.g., "price * quantity * 1.1")
            new_column: Name for the new column
            
        Returns:
            DataFrame with new column added
            
        Raises:
            ExpressionError: If expression is invalid or evaluation fails
        """
        # Validate safety
        is_valid, error = self.validate(expression)
        if not is_valid:
            raise ExpressionError(error)
        
        # Normalize the expression
        expr = self._normalize_expression(expression)
        
        try:
            # Create a copy to avoid modifying original
            result = df.copy()
            # Evaluate and assign to new column
            result[new_column] = df.eval(expr, local_dict=self.ALLOWED_FUNCTIONS)
            return result
        except Exception as e:
            raise ExpressionError(f"Failed to evaluate formula: {e}")
    
    def _normalize_expression(self, expression: str) -> str:
        """Normalize expression syntax for pandas compatibility.
        
        Converts:
        - && to and
        - || to or  
        - ! to not (when not !=)
        - == 'value' is kept as-is
        """
        expr = expression.strip()
        
        # Replace logical operators
        expr = expr.replace('&&', ' and ')
        expr = expr.replace('||', ' or ')
        
        # Replace ! with not (but not !=)
        expr = re.sub(r'!(?!=)', ' not ', expr)
        
        # Clean up extra whitespace
        expr = re.sub(r'\s+', ' ', expr).strip()
        
        return expr


# Module-level instance for convenience
default_parser = SafeExpressionParser()
