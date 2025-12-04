"""Input/Output nodes for reading and writing data."""
from pathlib import Path
from typing import Any
import uuid

import pandas as pd

from .base import BaseNode, NodeResult


class ReadCSVNode(BaseNode):
    """Read data from an uploaded CSV file.
    
    Config:
        upload_id (str): ID of the uploaded file
        header (bool): Whether first row contains headers (default: True)
        sep (str): Column separator (default: ',')
    """
    
    node_type = "ReadCSV"
    display_name = "Read CSV"
    description = "Load data from a CSV file"
    
    # Class variable to hold upload directory (set by executor)
    upload_dir: Path | None = None
    
    @property
    def input_count(self) -> int:
        return 0  # Source node, no inputs
    
    def execute(self, inputs: list[pd.DataFrame]) -> NodeResult:
        """Read CSV file and return as DataFrame."""
        upload_id = self.config.get('upload_id')
        if not upload_id:
            return NodeResult(success=False, error="No upload_id specified")
        
        if self.upload_dir is None:
            return NodeResult(success=False, error="Upload directory not configured")
        
        # Find the uploaded file
        file_path = self.upload_dir / f"{upload_id}.csv"
        if not file_path.exists():
            return NodeResult(
                success=False, 
                error=f"Uploaded file not found: {upload_id}"
            )
        
        # Parse options
        header = 0 if self.config.get('header', True) else None
        sep = self.config.get('sep', ',')
        
        try:
            df = pd.read_csv(file_path, header=header, sep=sep)
            return NodeResult(
                success=True,
                data=df,
                metadata={'source': str(file_path), 'upload_id': upload_id}
            )
        except Exception as e:
            return NodeResult(success=False, error=f"Failed to read CSV: {e}")
    
    def validate_config(self) -> tuple[bool, str | None]:
        if not self.config.get('upload_id'):
            return False, "upload_id is required"
        return True, None


class OutputNode(BaseNode):
    """Output node that writes data to a downloadable file.
    
    Config:
        format (str): Output format, currently only 'csv' supported
    """
    
    node_type = "Output"
    display_name = "Output"
    description = "Export data as CSV for download"
    
    # Class variable to hold output directory (set by executor)
    output_dir: Path | None = None
    
    @property
    def output_count(self) -> int:
        return 0  # Sink node, no outputs to other nodes
    
    def execute(self, inputs: list[pd.DataFrame]) -> NodeResult:
        """Write input data to output file."""
        if not inputs:
            return NodeResult(success=False, error="No input data to output")
        
        df = inputs[0]
        
        if self.output_dir is None:
            return NodeResult(success=False, error="Output directory not configured")
        
        output_format = self.config.get('format', 'csv')
        
        if output_format != 'csv':
            return NodeResult(
                success=False, 
                error=f"Unsupported output format: {output_format}"
            )
        
        # Generate unique output filename
        file_id = str(uuid.uuid4())
        file_path = self.output_dir / f"{file_id}.csv"
        
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(file_path, index=False)
            
            return NodeResult(
                success=True,
                data=df,
                metadata={
                    'file_id': file_id,
                    'file_path': str(file_path),
                    'format': output_format
                }
            )
        except Exception as e:
            return NodeResult(success=False, error=f"Failed to write output: {e}")
