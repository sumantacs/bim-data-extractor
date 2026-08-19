"""Output schema for extracted fields.

Each field includes text, confidence (0..1), and bounding_polygon (list of points).
"""
from dataclasses import dataclass
from typing import List, Tuple, Optional

Point = Tuple[int,int]

@dataclass
class ExtractedField:
    text: str
    confidence: float
    bounding_polygon: List[Point]
    field_type: Optional[str] = None  # e.g., 'room_label', 'dimension', 'annotation'
    source: Optional[str] = None  # engine or preprocessing steps

    def to_dict(self):
        return {
            'text': self.text,
            'confidence': float(self.confidence),
            'bounding_polygon': self.bounding_polygon,
            'field_type': self.field_type,
            'source': self.source,
        }
