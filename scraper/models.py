"""Data models for SFJAZZ event scraping."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import json


@dataclass
class Event:
    """Represents a jazz event from SFJAZZ."""

    title: str
    date: str
    time: Optional[str] = None
    venue: str = "SFJAZZ Center"
    artists: list[str] = field(default_factory=list)
    description: Optional[str] = None
    ticket_url: Optional[str] = None
    price: Optional[str] = None
    status: Optional[str] = None  # e.g., "Sold Out", "On Sale"
    series: Optional[str] = None  # e.g., "UpSwing Series"
    image_url: Optional[str] = None
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """Create Event from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def __hash__(self):
        """Hash based on title and date for deduplication."""
        return hash((self.title, self.date))

    def __eq__(self, other):
        """Events are equal if title and date match."""
        if not isinstance(other, Event):
            return False
        return self.title == other.title and self.date == other.date
