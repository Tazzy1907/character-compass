"""
FastAPI application for Character Compass API.
Provides REST endpoints for accessing books and character profiles.
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import sys
from pathlib import Path
from datetime import datetime
import threading

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import database
from api_models import (
    BookResponse,
    CharacterResponse,
    CharacterListResponse,
    StatsResponse,
    BookStatsResponse,
    ErrorResponse,
    GenerateRequest,
    GenerateResponse,
    GenerationStatusResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="Character Compass API",
    description="REST API for accessing book and character profile data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS - allows frontend to call API from different origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== GENERATION STATUS TRACKING ====================

# Thread-safe status tracking for profile generation
generation_status = {
    "is_running": False,
    "book_url": None,
    "started_at": None,
    "message": "No generation in progress",
    "lock": threading.Lock()
}


def run_generation_task(book_url: str, book_name: Optional[str], book_icon: Optional[str]):
    """
    Background task to run profile generation.
    Updates the global generation_status dict.
    """
    with generation_status["lock"]:
        generation_status["is_running"] = True
        generation_status["book_url"] = book_url
        generation_status["started_at"] = datetime.now().isoformat()
        generation_status["message"] = f"Generating profiles for book: {book_url}"
    
    try:
        # Import here to avoid circular dependencies and ensure RAG system is initialized
        from main import generate_profiles_for_book
        
        result = generate_profiles_for_book(book_url, book_name, book_icon)
        
        with generation_status["lock"]:
            generation_status["is_running"] = False
            generation_status["book_url"] = None
            generation_status["started_at"] = None
            if result["success"]:
                generation_status["message"] = f"Generation completed successfully. Created {result['profiles_created']} profiles."
            else:
                generation_status["message"] = f"Generation failed: {result.get('error', 'Unknown error')}"
    
    except Exception as e:
        with generation_status["lock"]:
            generation_status["is_running"] = False
            generation_status["book_url"] = None
            generation_status["started_at"] = None
            generation_status["message"] = f"Generation failed with error: {str(e)}"


# ==================== ROOT ENDPOINT ====================

@app.get("/", tags=["Health"])
async def root():
    """
    Health check endpoint.
    Returns a welcome message and API status.
    """
    return {
        "message": "Character Compass API",
        "status": "running",
        "docs": "/docs",
        "version": "1.0.0"
    }


# ==================== BOOK ENDPOINTS ====================

@app.get(
    "/api/books",
    response_model=List[BookResponse],
    tags=["Books"],
    summary="Get all books",
    description="Retrieve a list of all books in the database"
)
async def get_books():
    """
    Get all books from the database.
    
    Returns:
        List of BookResponse objects
    """
    try:
        books = database.get_all_books()
        return books
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get(
    "/api/books/{book_url}",
    response_model=BookResponse,
    tags=["Books"],
    summary="Get book by URL",
    description="Retrieve a specific book by its URL/Document ID",
    responses={404: {"model": ErrorResponse}}
)
async def get_book(book_url: str):
    """
    Get a specific book by URL.
    
    Args:
        book_url: The book's URL/Document ID
        
    Returns:
        BookResponse object
        
    Raises:
        404: If book not found
    """
    try:
        book = database.get_book(book_url)
        if not book:
            raise HTTPException(
                status_code=404,
                detail=f"Book with URL '{book_url}' not found"
            )
        return book
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ==================== CHARACTER ENDPOINTS ====================

@app.get(
    "/api/books/{book_url}/characters",
    response_model=CharacterListResponse,
    tags=["Characters"],
    summary="Get all characters for a book",
    description="Retrieve all characters (main and side) for a specific book"
)
async def get_book_characters(book_url: str):
    """
    Get all characters for a specific book.
    
    Args:
        book_url: The book's URL/Document ID
        
    Returns:
        CharacterListResponse with list of characters
    """
    try:
        # First check if book exists
        book = database.get_book(book_url)
        if not book:
            raise HTTPException(
                status_code=404,
                detail=f"Book with URL '{book_url}' not found"
            )
        
        characters = database.get_characters_by_book(book_url)
        return CharacterListResponse(
            characters=characters,
            count=len(characters)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get(
    "/api/books/{book_url}/characters/main",
    response_model=CharacterListResponse,
    tags=["Characters"],
    summary="Get main characters for a book",
    description="Retrieve only main characters for a specific book"
)
async def get_main_characters(book_url: str):
    """
    Get only main characters for a specific book.
    
    Args:
        book_url: The book's URL/Document ID
        
    Returns:
        CharacterListResponse with list of main characters
    """
    try:
        # First check if book exists
        book = database.get_book(book_url)
        if not book:
            raise HTTPException(
                status_code=404,
                detail=f"Book with URL '{book_url}' not found"
            )
        
        characters = database.get_main_characters(book_url)
        return CharacterListResponse(
            characters=characters,
            count=len(characters)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get(
    "/api/books/{book_url}/characters/side",
    response_model=CharacterListResponse,
    tags=["Characters"],
    summary="Get side characters for a book",
    description="Retrieve only side characters for a specific book"
)
async def get_side_characters(book_url: str):
    """
    Get only side characters for a specific book.
    
    Args:
        book_url: The book's URL/Document ID
        
    Returns:
        CharacterListResponse with list of side characters
    """
    try:
        # First check if book exists
        book = database.get_book(book_url)
        if not book:
            raise HTTPException(
                status_code=404,
                detail=f"Book with URL '{book_url}' not found"
            )
        
        characters = database.get_side_characters(book_url)
        return CharacterListResponse(
            characters=characters,
            count=len(characters)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get(
    "/api/characters/{character_id}",
    response_model=CharacterResponse,
    tags=["Characters"],
    summary="Get specific character",
    description="Retrieve a specific character by their unique ID",
    responses={404: {"model": ErrorResponse}}
)
async def get_character(character_id: int):
    """
    Get a specific character by their ID.
    
    Args:
        character_id: The character's unique ID
        
    Returns:
        CharacterResponse object
        
    Raises:
        404: If character not found
        
    Example:
        GET /api/characters/1
    """
    try:
        character = database.get_character_by_id(character_id)
        if not character:
            raise HTTPException(
                status_code=404,
                detail=f"Character with ID {character_id} not found"
            )
        return character
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ==================== PROFILE GENERATION ENDPOINTS ====================

@app.post(
    "/api/generate",
    response_model=GenerateResponse,
    tags=["Generation"],
    summary="Trigger profile generation",
    description="Start AI-powered character profile generation for a book (runs in background)"
)
async def generate_profiles(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Trigger character profile generation for a book.
    
    This endpoint starts the generation process in the background and returns immediately.
    Use GET /api/generate/status to check if generation is still in progress.
    
    Args:
        request: GenerateRequest with book_url and optional metadata
        background_tasks: FastAPI background tasks manager
        
    Returns:
        GenerateResponse indicating if generation was started
        
    Note:
        - Only one generation can run at a time
        - Generation happens in the background
        - Check /api/generate/status to monitor progress
    """
    with generation_status["lock"]:
        if generation_status["is_running"]:
            return GenerateResponse(
                success=False,
                message=f"Generation already in progress for book: {generation_status['book_url']}",
                book_url=generation_status["book_url"]
            )
    
    # Start generation in background
    background_tasks.add_task(
        run_generation_task,
        request.book_url,
        request.book_name,
        request.book_icon
    )
    
    return GenerateResponse(
        success=True,
        message="Profile generation started in background. Check /api/generate/status for progress.",
        book_url=request.book_url
    )


@app.get(
    "/api/generate/status",
    response_model=GenerationStatusResponse,
    tags=["Generation"],
    summary="Check generation status",
    description="Check if profile generation is currently in progress"
)
async def get_generation_status():
    """
    Check the status of profile generation.
    
    Returns:
        GenerationStatusResponse with current status
        
    Use this endpoint to:
    - Check if generation is running
    - See which book is being processed
    - Get status messages about the last generation
    """
    with generation_status["lock"]:
        return GenerationStatusResponse(
            is_running=generation_status["is_running"],
            book_url=generation_status["book_url"],
            started_at=generation_status["started_at"],
            message=generation_status["message"]
        )


# ==================== STATISTICS ENDPOINT ====================

@app.get(
    "/api/stats",
    response_model=StatsResponse,
    tags=["Statistics"],
    summary="Get database statistics",
    description="Retrieve statistics about books and characters in the database"
)
async def get_stats():
    """
    Get database statistics including total counts and per-book breakdowns.
    
    Returns:
        StatsResponse with database statistics
    """
    try:
        books = database.get_all_books()
        all_characters = database.get_all_characters()
        
        book_stats = []
        for book in books:
            total = database.get_character_count_by_book(book['url'])
            main = len(database.get_main_characters(book['url']))
            side = len(database.get_side_characters(book['url']))
            
            book_stats.append(BookStatsResponse(
                url=book['url'],
                name=book['name'],
                total_characters=total,
                main_characters=main,
                side_characters=side
            ))
        
        return StatsResponse(
            total_books=len(books),
            total_characters=len(all_characters),
            books=book_stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ==================== STARTUP EVENT ====================

@app.on_event("startup")
async def startup_event():
    """
    Run initialization tasks when the API server starts.
    Ensures database is initialized.
    """
    print("\n" + "="*60)
    print("🚀 Character Compass API Starting...")
    print("="*60)
    
    try:
        # Initialize database
        database.initialize_database()
        print("✅ Database initialized")
        
        # Display available books
        books = database.get_all_books()
        print(f"📚 Books in database: {len(books)}")
        for book in books:
            char_count = database.get_character_count_by_book(book['url'])
            print(f"   • {book['name']}: {char_count} characters")
        
        print("\n📖 API Documentation: http://localhost:8000/docs")
        print("🔄 Interactive API: http://localhost:8000/redoc")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        raise


if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )

