"""
Database module for storing book metadata and character profiles.
Uses SQLite for persistence with support for CRUD operations.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from pathlib import Path

from char_info import CharacterProfile

# Database file path - dynamically resolved relative to this file's location
# This ensures portability across different systems and locations
DB_PATH = os.path.join(
    Path(__file__).parent.parent,  # Go up to backend/ directory
    "character_compass.db"
)


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def initialize_database():
    """Create database tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create books table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                url TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                icon TEXT
            )
        """)
        
        # Create characters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                book_url TEXT NOT NULL,
                character_type TEXT,
                age INTEGER,
                gender TEXT,
                sex TEXT,
                race TEXT,
                occupation TEXT,
                personality TEXT,
                appearance TEXT,
                backstory TEXT,
                relationships TEXT,
                goals TEXT,
                motivations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_url) REFERENCES books(url) ON DELETE CASCADE,
                UNIQUE(name, book_url)
            )
        """)
        
        conn.commit()
        print("Database initialized successfully.")


# ==================== BOOKS TABLE OPERATIONS ====================

def add_or_update_book(url: str, name: str, icon: Optional[str] = None):
    """
    Add a new book or update an existing one.
    
    Args:
        url: Google Doc ID or URL (primary key)
        name: Book title
        icon: Icon/image path (optional)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO books (url, name, icon)
            VALUES (?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                name = excluded.name,
                icon = excluded.icon
        """, (url, name, icon))
        print(f"Book '{name}' added/updated in database.")


def get_book(url: str) -> Optional[Dict[str, Any]]:
    """Retrieve a book by URL."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE url = ?", (url,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_books() -> List[Dict[str, Any]]:
    """Retrieve all books."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books")
        return [dict(row) for row in cursor.fetchall()]


# ==================== CHARACTERS TABLE OPERATIONS ====================

def add_or_update_character(
    profile: CharacterProfile,
    book_url: str,
    character_type: str = "main"
):
    """
    Add a new character profile or update an existing one.
    Uses upsert logic based on (name, book_url) combination.
    
    Args:
        profile: CharacterProfile object
        book_url: The book URL this character belongs to
        character_type: "main" or "side"
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Convert list fields to JSON
        relationships_json = json.dumps(profile.relationships)
        goals_json = json.dumps(profile.goals)
        motivations_json = json.dumps(profile.motivations)
        
        cursor.execute("""
            INSERT INTO characters (
                name, book_url, character_type, age, gender, sex, race,
                occupation, personality, appearance, backstory,
                relationships, goals, motivations, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name, book_url) DO UPDATE SET
                character_type = excluded.character_type,
                age = excluded.age,
                gender = excluded.gender,
                sex = excluded.sex,
                race = excluded.race,
                occupation = excluded.occupation,
                personality = excluded.personality,
                appearance = excluded.appearance,
                backstory = excluded.backstory,
                relationships = excluded.relationships,
                goals = excluded.goals,
                motivations = excluded.motivations,
                updated_at = CURRENT_TIMESTAMP
        """, (
            profile.name, book_url, character_type, profile.age,
            profile.gender, profile.sex, profile.race, profile.occupation,
            profile.personality, profile.appearance, profile.backstory,
            relationships_json, goals_json, motivations_json
        ))
        
        print(f"Character '{profile.name}' saved to database.")


def get_character(name: str, book_url: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a character by name and book URL.
    Converts JSON fields back to lists.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM characters
            WHERE name = ? AND book_url = ?
        """, (name, book_url))
        row = cursor.fetchone()
        
        if row:
            character = dict(row)
            # Parse JSON fields back to lists
            character['relationships'] = json.loads(character['relationships'])
            character['goals'] = json.loads(character['goals'])
            character['motivations'] = json.loads(character['motivations'])
            return character
        return None


def get_characters_by_book(book_url: str) -> List[Dict[str, Any]]:
    """
    Retrieve all characters for a specific book.
    Converts JSON fields back to lists.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM characters
            WHERE book_url = ?
            ORDER BY character_type, name
        """, (book_url,))
        
        characters = []
        for row in cursor.fetchall():
            character = dict(row)
            character['relationships'] = json.loads(character['relationships'])
            character['goals'] = json.loads(character['goals'])
            character['motivations'] = json.loads(character['motivations'])
            characters.append(character)
        
        return characters


def get_all_characters() -> List[Dict[str, Any]]:
    """
    Retrieve all characters across all books.
    Converts JSON fields back to lists.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM characters ORDER BY book_url, name")
        
        characters = []
        for row in cursor.fetchall():
            character = dict(row)
            character['relationships'] = json.loads(character['relationships'])
            character['goals'] = json.loads(character['goals'])
            character['motivations'] = json.loads(character['motivations'])
            characters.append(character)
        
        return characters


def delete_character(name: str, book_url: str):
    """Delete a character by name and book URL."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM characters
            WHERE name = ? AND book_url = ?
        """, (name, book_url))
        print(f"Character '{name}' deleted from database.")


def delete_characters_by_book(book_url: str):
    """Delete all characters for a specific book."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM characters WHERE book_url = ?", (book_url,))
        print(f"All characters for book '{book_url}' deleted.")


# ==================== UTILITY FUNCTIONS ====================

def get_character_count_by_book(book_url: str) -> int:
    """Get the count of characters for a specific book."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM characters WHERE book_url = ?
        """, (book_url,))
        return cursor.fetchone()['count']


def get_main_characters(book_url: str) -> List[Dict[str, Any]]:
    """Retrieve only main characters for a specific book."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM characters
            WHERE book_url = ? AND character_type = 'main'
            ORDER BY name
        """, (book_url,))
        
        characters = []
        for row in cursor.fetchall():
            character = dict(row)
            character['relationships'] = json.loads(character['relationships'])
            character['goals'] = json.loads(character['goals'])
            character['motivations'] = json.loads(character['motivations'])
            characters.append(character)
        
        return characters


def get_side_characters(book_url: str) -> List[Dict[str, Any]]:
    """Retrieve only side characters for a specific book."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM characters
            WHERE book_url = ? AND character_type = 'side'
            ORDER BY name
        """, (book_url,))
        
        characters = []
        for row in cursor.fetchall():
            character = dict(row)
            character['relationships'] = json.loads(character['relationships'])
            character['goals'] = json.loads(character['goals'])
            character['motivations'] = json.loads(character['motivations'])
            characters.append(character)
        
        return characters

