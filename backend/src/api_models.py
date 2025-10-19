"""
Pydantic models for FastAPI request and response schemas.
These models define the structure of data sent to/from the API.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class BookResponse(BaseModel):
    """Response model for book data."""
    url: str = Field(..., description="Book URL/Document ID")
    name: str = Field(..., description="Book title")
    icon: Optional[str] = Field(None, description="Icon/image path")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "1DN04wAju6_XflgjVXj4grRSlsA9w7Xmv_cRVB7w1d84",
                "name": "Sample Book",
                "icon": "/path/to/icon.png"
            }
        }


class CharacterResponse(BaseModel):
    """Response model for character profile data."""
    id: int = Field(..., description="Character ID")
    name: str = Field(..., description="Character name")
    book_url: str = Field(..., description="Book this character belongs to")
    character_type: str = Field(..., description="Character type: main or side")
    age: Optional[int] = Field(None, description="Character age")
    gender: Optional[str] = Field(None, description="Character gender")
    sex: Optional[str] = Field(None, description="Character sex")
    race: Optional[str] = Field(None, description="Character race")
    occupation: Optional[str] = Field(None, description="Character occupation")
    personality: Optional[str] = Field(default="", description="Personality description")
    appearance: Optional[str] = Field(default="", description="Physical appearance description")
    backstory: Optional[str] = Field(default="", description="Character backstory")
    relationships: Optional[List[str]] = Field(default_factory=list, description="List of relationships")
    goals: Optional[List[str]] = Field(default_factory=list, description="List of goals")
    motivations: Optional[List[str]] = Field(default_factory=list, description="List of motivations")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "John Doe",
                "book_url": "doc123",
                "character_type": "main",
                "age": 30,
                "gender": "male",
                "occupation": "Detective",
                "personality": "Determined and analytical",
                "appearance": "Tall with dark hair",
                "backstory": "Former police officer",
                "relationships": ["Partner with Jane", "Friend of Bob"],
                "goals": ["Solve the case", "Find the truth"],
                "motivations": ["Justice", "Redemption"],
                "created_at": "2025-10-18 10:00:00",
                "updated_at": "2025-10-18 10:00:00"
            }
        }


class CharacterListResponse(BaseModel):
    """Response model for a list of characters."""
    characters: List[CharacterResponse]
    count: int = Field(..., description="Number of characters returned")
    
    class Config:
        json_schema_extra = {
            "example": {
                "characters": [],
                "count": 0
            }
        }


class BookStatsResponse(BaseModel):
    """Response model for book statistics."""
    url: str
    name: str
    total_characters: int
    main_characters: int
    side_characters: int


class StatsResponse(BaseModel):
    """Response model for database statistics."""
    total_books: int = Field(..., description="Total number of books")
    total_characters: int = Field(..., description="Total number of characters")
    books: List[BookStatsResponse] = Field(default_factory=list, description="Per-book statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_books": 2,
                "total_characters": 10,
                "books": [
                    {
                        "url": "doc123",
                        "name": "Book 1",
                        "total_characters": 5,
                        "main_characters": 2,
                        "side_characters": 3
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Response model for error messages."""
    detail: str = Field(..., description="Error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Resource not found"
            }
        }


class GenerateRequest(BaseModel):
    """Request model for triggering profile generation."""
    book_url: str = Field(..., description="Google Doc ID/URL for the book")
    book_name: Optional[str] = Field(None, description="Book title (optional)")
    book_icon: Optional[str] = Field(None, description="Book icon path (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "book_url": "1DN04wAju6_XflgjVXj4grRSlsA9w7Xmv_cRVB7w1d84",
                "book_name": "My Book Title",
                "book_icon": "/path/to/icon.png"
            }
        }


class GenerateResponse(BaseModel):
    """Response model for profile generation trigger."""
    success: bool = Field(..., description="Whether generation was triggered successfully")
    message: str = Field(..., description="Status message")
    book_url: Optional[str] = Field(None, description="Book URL being processed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Profile generation started in background",
                "book_url": "doc123"
            }
        }


class GenerationStatusResponse(BaseModel):
    """Response model for generation status check."""
    is_running: bool = Field(..., description="Whether generation is currently in progress")
    book_url: Optional[str] = Field(None, description="Book URL being processed (if any)")
    started_at: Optional[str] = Field(None, description="When generation started (if running)")
    message: str = Field(..., description="Current status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_running": True,
                "book_url": "doc123",
                "started_at": "2025-10-18 15:30:00",
                "message": "Generating profiles for book: doc123"
            }
        }

