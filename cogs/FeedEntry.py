from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class FeedEntry:
    book_id: int
    title: str
    author: Optional[str]
    cover_image_url: Optional[str]
    goodreads_url: str
    shelf: str
    rating: Optional[int]
    average_rating: Optional[float]
    review: Optional[str]
    published: datetime