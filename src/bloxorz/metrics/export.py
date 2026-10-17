"""Export benchmark metrics to CSV format."""
import csv
from pathlib import Path
from typing import List, Dict, Any

def export_to_csv(data: List[Dict[str, Any]], output_path: Path):
    """Write list of metric dictionaries to a CSV file."""
    if not data:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(data[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
