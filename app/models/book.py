from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Book:
    id: Optional[int]
    title: str
    author: str
    isbn: str
    quantity: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "quantity": self.quantity
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Book':
        return cls(
            id=data.get('id'),
            title=data['title'],
            author=data['author'],
            isbn=data['isbn'],
            quantity=int(data['quantity'])
        )

    def validate(self) -> Optional[str]:
        if not isinstance(self.title, str) or not self.title.strip():
            return "Title is required"
        if not isinstance(self.author, str) or not self.author.strip():
            return "Author is required"
        if not isinstance(self.isbn, str) or not self.isbn.strip():
            return "ISBN is required"
        if self.quantity < 0:
            return "Quantity cannot be negative"
        return None

