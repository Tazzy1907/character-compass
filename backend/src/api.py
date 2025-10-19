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
    CharacterSummaryResponse,
    CharacterListResponse,
    StatsResponse,
    BookStatsResponse,
    ErrorResponse,
    GenerateRequest,
    GenerateResponse,
    GenerationStatusResponse,
    DocumentChangeResponse
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
    "error": None,
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
        generation_status["error"] = None
    
    try:
        # Import here to avoid circular dependencies and ensure RAG system is initialized
        from main import generate_profiles_for_book
        
        result = generate_profiles_for_book(book_url, book_name, book_icon)
        
        with generation_status["lock"]:
            generation_status["is_running"] = False
            generation_status["book_url"] = book_url  # Keep book_url so frontend knows which book finished
            generation_status["started_at"] = None
            if result["success"]:
                generation_status["message"] = f"Generation completed successfully. Created {result['profiles_created']} profiles."
                generation_status["error"] = None
            else:
                error_msg = result.get('error', 'Unknown error')
                generation_status["message"] = f"Generation failed: {error_msg}"
                generation_status["error"] = error_msg
    
    except Exception as e:
        with generation_status["lock"]:
            generation_status["is_running"] = False
            generation_status["book_url"] = book_url  # Keep book_url so frontend knows which book failed
            generation_status["started_at"] = None
            error_msg = str(e)
            generation_status["message"] = f"Generation failed with error: {error_msg}"
            generation_status["error"] = error_msg


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
    description="Retrieve all characters (main and side) for a specific book (summary view)"
)
async def get_book_characters(book_url: str):
    """
    Get all characters for a specific book (returns only id, name, and character_type).
    
    Args:
        book_url: The book's URL/Document ID
        
    Returns:
        CharacterListResponse with list of character summaries
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
        
        # Transform to summary view (only id, name, character_type)
        character_summaries = [
            CharacterSummaryResponse(
                id=char['id'],
                name=char['name'],
                character_type=char['character_type']
            )
            for char in characters
        ]
        
        return CharacterListResponse(
            characters=character_summaries,
            count=len(character_summaries)
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
    description="Retrieve only main characters for a specific book (summary view)"
)
async def get_main_characters(book_url: str):
    """
    Get only main characters for a specific book (returns only id, name, and character_type).
    
    Args:
        book_url: The book's URL/Document ID
        
    Returns:
        CharacterListResponse with list of main character summaries
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
        
        # Transform to summary view (only id, name, character_type)
        character_summaries = [
            CharacterSummaryResponse(
                id=char['id'],
                name=char['name'],
                character_type=char['character_type']
            )
            for char in characters
        ]
        
        return CharacterListResponse(
            characters=character_summaries,
            count=len(character_summaries)
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
    description="Retrieve only side characters for a specific book (summary view)"
)
async def get_side_characters(book_url: str):
    """
    Get only side characters for a specific book (returns only id, name, and character_type).
    
    Args:
        book_url: The book's URL/Document ID
        
    Returns:
        CharacterListResponse with list of side character summaries
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
        
        # Transform to summary view (only id, name, character_type)
        character_summaries = [
            CharacterSummaryResponse(
                id=char['id'],
                name=char['name'],
                character_type=char['character_type']
            )
            for char in characters
        ]
        
        return CharacterListResponse(
            characters=character_summaries,
            count=len(character_summaries)
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
            message=generation_status["message"],
            error=generation_status.get("error")
        )


# ==================== ACTIVE MONITORING ENDPOINT ====================

@app.post(
    "/api/books/{book_url}/check-changes",
    response_model=DocumentChangeResponse,
    tags=["Monitoring"],
    summary="Check document for changes",
    description="Check if a Google Doc has changed and update character profiles if needed"
)
async def check_document_changes(book_url: str):
    """
    Check a document for changes and update character profiles.
    
    This endpoint is used for active monitoring by the frontend.
    It will:
    1. Check if profile generation is running (abort if yes)
    2. Check the document for changes via Google Drive API
    3. Re-index only changed chunks
    4. Update existing character profiles if changes detected
    
    Args:
        book_url: The Google Doc ID to check
        
    Returns:
        DocumentChangeResponse with change summary
        
    Note:
        - Cannot run while profile generation is in progress
        - Only updates existing characters (doesn't find new ones)
        - Uses hash-based change detection for efficiency
    """
    print(f"\n{'='*60}")
    print(f"📡 API: Check changes request for book: {book_url}")
    print(f"{'='*60}")
    
    try:
        # Check if profile generation is currently running
        with generation_status["lock"]:
            if generation_status["is_running"]:
                return DocumentChangeResponse(
                    changed=False,
                    chunks_added=0,
                    chunks_deleted=0,
                    characters_updated=[],
                    last_modified="",
                    message="Profile generation in progress",
                    error="Cannot check changes while profile generation is running"
                )
        
        # Import here to avoid circular dependencies
        from main import check_and_update_document, update_existing_profiles, rag_state, reinitialize_rag_for_document
        
        # Check if this book is currently indexed
        # If not, re-initialize RAG for this book (unless it's being used for generation)
        if rag_state.current_doc_id != book_url:
            print(f"Switching RAG context to monitored book: {book_url}")
            try:
                reinitialize_rag_for_document(book_url)
            except Exception as e:
                return DocumentChangeResponse(
                    changed=False,
                    chunks_added=0,
                    chunks_deleted=0,
                    characters_updated=[],
                    last_modified="",
                    message="Failed to switch to monitored book",
                    error=f"Could not index book {book_url}: {str(e)}"
                )
        
        # Check for document changes
        change_result = check_and_update_document(book_url)
        
        characters_updated = []
        
        # If changes detected, update character profiles
        if change_result["changed"]:
            print(f"✨ Changes detected! Updating character profiles...")
            
            # Get changed chunks for character filtering
            changed_chunks = change_result.get("changed_chunks_text", [])
            
            # Pass changed chunks to filter relevant characters
            update_result = update_existing_profiles(book_url, changed_chunks)
            
            print(f"📊 Update result: {update_result}")
            
            if update_result["success"]:
                characters_updated = update_result.get("characters_updated", [])
                print(f"✅ Successfully updated {len(characters_updated)} characters")
        
        return DocumentChangeResponse(
            changed=change_result["changed"],
            chunks_added=change_result["chunks_added"],
            chunks_deleted=change_result["chunks_deleted"],
            characters_updated=characters_updated,
            last_modified=change_result["last_modified"],
            message=f"Check complete. {'Changes detected and profiles updated.' if change_result['changed'] else 'No changes detected.'}",
            error=None
        )
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error checking document changes: {error_msg}")
        return DocumentChangeResponse(
            changed=False,
            chunks_added=0,
            chunks_deleted=0,
            characters_updated=[],
            last_modified="",
            message="Error checking document",
            error=error_msg
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

