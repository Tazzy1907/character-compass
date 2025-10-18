# Character Compass Database Integration

## Overview

Character Compass now stores character profiles and book metadata in a SQLite database for persistence and easy querying.

## Database Schema

### Books Table
Stores metadata about books being analyzed.

| Column | Type | Description |
|--------|------|-------------|
| url | TEXT (PK) | Google Doc ID/URL |
| name | TEXT | Book title |
| icon | TEXT | Icon/image path (optional) |

### Characters Table
Stores detailed character profiles.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-incrementing ID |
| name | TEXT | Character name |
| book_url | TEXT (FK) | References books.url |
| character_type | TEXT | "main" or "side" |
| age | INTEGER | Character age (nullable) |
| gender | TEXT | Gender (nullable) |
| sex | TEXT | Sex (nullable) |
| race | TEXT | Race (nullable) |
| occupation | TEXT | Occupation (nullable) |
| personality | TEXT | Personality description |
| appearance | TEXT | Physical appearance |
| backstory | TEXT | Character backstory |
| relationships | TEXT | JSON array of relationships |
| goals | TEXT | JSON array of goals |
| motivations | TEXT | JSON array of motivations |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

**Unique Constraint**: (name, book_url) - prevents duplicate characters for the same book

## Usage

### Running the Main Application

When you run `main.py`, it will:
1. Initialize the RAG system
2. Create/connect to the database
3. Add the book metadata to the database
4. Extract characters from the book
5. Generate profiles for both main and side characters
6. Save all profiles to the database (with upsert logic)

```bash
cd backend/src
python main.py
```

### Querying the Database

Use the `query_db.py` utility script to view stored data:

```bash
cd backend/src
python query_db.py
```

Options:
1. View all books
2. View all characters
3. View characters by book
4. View character detail
5. View statistics

### Programmatic Access

Import the database module in your Python scripts:

```python
import database

# Initialize database (creates tables if they don't exist)
database.initialize_database()

# Add/update a book
database.add_or_update_book(
    url="doc_id_123",
    name="My Book Title",
    icon="/path/to/icon.png"
)

# Get all books
books = database.get_all_books()

# Add/update a character profile
from char_info import CharacterProfile

profile = CharacterProfile(
    name="John Doe",
    age=30,
    personality="Brave and determined",
    # ... other fields
)

database.add_or_update_character(
    profile=profile,
    book_url="doc_id_123",
    character_type="main"
)

# Query characters
characters = database.get_characters_by_book("doc_id_123")
main_chars = database.get_main_characters("doc_id_123")
side_chars = database.get_side_characters("doc_id_123")

# Get specific character
character = database.get_character("John Doe", "doc_id_123")
```

## Key Features

### Upsert Logic
When saving character profiles, the system uses "INSERT OR REPLACE" logic based on the (name, book_url) combination. This means:
- If the character doesn't exist, it's created
- If the character already exists, it's updated with new information
- The `updated_at` timestamp is automatically refreshed on updates

### JSON Storage
List fields (relationships, goals, motivations) are stored as JSON strings and automatically converted back to Python lists when retrieved.

### Foreign Key Constraints
The characters table has a foreign key relationship with the books table. If a book is deleted, all associated characters are automatically deleted (CASCADE).

## Database Location

The SQLite database file is automatically created in the `backend/` directory:
```
backend/character_compass.db
```

The path is dynamically resolved relative to the `database.py` file location, making the project portable across different systems and directories. The database file will be created in the same directory regardless of where you run the script from.

This file is excluded from git via `.gitignore`.

## Updating Book Metadata

To change the book name or add an icon, update the following lines in `main.py`:

```python
database.add_or_update_book(
    url=DOC_ID,
    name="Your Book Title Here",  # Update this
    icon="/path/to/icon.png"       # Update this
)
```

## API Functions Reference

### Book Operations
- `initialize_database()` - Create tables if they don't exist
- `add_or_update_book(url, name, icon)` - Add/update book
- `get_book(url)` - Get book by URL
- `get_all_books()` - Get all books

### Character Operations
- `add_or_update_character(profile, book_url, character_type)` - Add/update character
- `get_character(name, book_url)` - Get specific character
- `get_characters_by_book(book_url)` - Get all characters for a book
- `get_all_characters()` - Get all characters
- `get_main_characters(book_url)` - Get main characters only
- `get_side_characters(book_url)` - Get side characters only
- `delete_character(name, book_url)` - Delete a character
- `delete_characters_by_book(book_url)` - Delete all characters for a book

### Utility Functions
- `get_character_count_by_book(book_url)` - Count characters for a book

## Notes

- The database is created automatically on first run
- All database operations are wrapped in transactions for data integrity
- The database uses SQLite's `row_factory` for easy column access by name
- Timestamps use SQLite's `CURRENT_TIMESTAMP` function

