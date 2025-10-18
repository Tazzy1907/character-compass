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

---

# REST API Documentation

## Overview

The Character Compass REST API provides HTTP endpoints for accessing book and character data from your frontend application. The API is built with FastAPI and provides automatic interactive documentation.

## Starting the API Server

```bash
# From the project root
python backend/run_api.py

# Or from the backend directory
cd backend
python run_api.py
```

The server will start on `http://localhost:8000`

### Important Notes
- The API server runs **separately** from the profile generation script
- The server auto-reloads when code changes (useful for development)
- You can now trigger profile generation via the API (see Generation Endpoints below)

### Two Ways to Generate Profiles

**Option 1: Standalone Script (Initial Setup)**
```bash
# Run once to set up RAG system and generate initial profiles
python backend/src/main.py
```
This initializes the RAG system and generates profiles. Run this at least once before using the API generation endpoint.

**Option 2: Via API (On-Demand)**
```bash
# Start the API server
python backend/run_api.py

# Then call the generation endpoint from your frontend or curl
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"book_url": "your-doc-id", "book_name": "Book Title"}'
```
Use this for on-demand generation triggered by your frontend interface.

## Interactive Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
  - Interactive API testing interface
  - Try out endpoints directly in your browser
  - See request/response schemas

- **ReDoc**: http://localhost:8000/redoc
  - Alternative documentation format
  - Clean, readable API reference

## Available Endpoints

### Health Check

#### `GET /`
Check if the API is running.

**Response:**
```json
{
  "message": "Character Compass API",
  "status": "running",
  "docs": "/docs",
  "version": "1.0.0"
}
```

---

### Books Endpoints

#### `GET /api/books`
Get all books in the database.

**Response:**
```json
[
  {
    "url": "1DN04wAju6_XflgjVXj4grRSlsA9w7Xmv_cRVB7w1d84",
    "name": "Sample Book",
    "icon": null
  }
]
```

**Frontend Example:**
```javascript
const response = await fetch('http://localhost:8000/api/books');
const books = await response.json();
console.log(books);
```

#### `GET /api/books/{book_url}`
Get a specific book by its URL/Document ID.

**Parameters:**
- `book_url` (path) - The book's URL or Document ID

**Response:**
```json
{
  "url": "doc123",
  "name": "Sample Book",
  "icon": "/path/to/icon.png"
}
```

**Frontend Example:**
```javascript
const bookUrl = '1DN04wAju6_XflgjVXj4grRSlsA9w7Xmv_cRVB7w1d84';
const response = await fetch(`http://localhost:8000/api/books/${bookUrl}`);
const book = await response.json();
```

---

### Character Endpoints

#### `GET /api/books/{book_url}/characters`
Get all characters (main and side) for a specific book.

**Parameters:**
- `book_url` (path) - The book's URL or Document ID

**Response:**
```json
{
  "characters": [
    {
      "id": 1,
      "name": "John Doe",
      "book_url": "doc123",
      "character_type": "main",
      "age": 30,
      "gender": "male",
      "occupation": "Detective",
      "personality": "Determined and analytical...",
      "appearance": "Tall with dark hair...",
      "backstory": "Former police officer...",
      "relationships": ["Partner with Jane", "Friend of Bob"],
      "goals": ["Solve the case", "Find the truth"],
      "motivations": ["Justice", "Redemption"],
      "created_at": "2025-10-18 10:00:00",
      "updated_at": "2025-10-18 10:00:00"
    }
  ],
  "count": 1
}
```

**Frontend Example:**
```javascript
const bookUrl = 'doc123';
const response = await fetch(
  `http://localhost:8000/api/books/${bookUrl}/characters`
);
const data = await response.json();
console.log(`Found ${data.count} characters`);
console.log(data.characters);
```

#### `GET /api/books/{book_url}/characters/main`
Get only main characters for a specific book.

**Parameters:**
- `book_url` (path) - The book's URL or Document ID

**Response:** Same format as `/characters` but filtered to main characters only.

**Frontend Example:**
```javascript
const bookUrl = 'doc123';
const response = await fetch(
  `http://localhost:8000/api/books/${bookUrl}/characters/main`
);
const mainCharacters = await response.json();
```

#### `GET /api/books/{book_url}/characters/side`
Get only side characters for a specific book.

**Parameters:**
- `book_url` (path) - The book's URL or Document ID

**Response:** Same format as `/characters` but filtered to side characters only.

**Frontend Example:**
```javascript
const bookUrl = 'doc123';
const response = await fetch(
  `http://localhost:8000/api/books/${bookUrl}/characters/side`
);
const sideCharacters = await response.json();
```

#### `GET /api/characters/{character_name}?book_url={book_url}`
Get a specific character by name.

**Parameters:**
- `character_name` (path) - The character's name
- `book_url` (query) - The book's URL or Document ID

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "book_url": "doc123",
  "character_type": "main",
  "age": 30,
  "occupation": "Detective",
  // ... full character details
}
```

**Frontend Example:**
```javascript
const characterName = 'John Doe';
const bookUrl = 'doc123';
const response = await fetch(
  `http://localhost:8000/api/characters/${encodeURIComponent(characterName)}?book_url=${bookUrl}`
);
const character = await response.json();
```

---

### Statistics Endpoint

#### `GET /api/stats`
Get database statistics including total counts and per-book breakdowns.

**Response:**
```json
{
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
```

**Frontend Example:**
```javascript
const response = await fetch('http://localhost:8000/api/stats');
const stats = await response.json();
console.log(`Total books: ${stats.total_books}`);
console.log(`Total characters: ${stats.total_characters}`);
```

---

### Profile Generation Endpoints

#### `POST /api/generate`
Trigger AI-powered character profile generation for a book (runs in background).

**Request Body:**
```json
{
  "book_url": "1DN04wAju6_XflgjVXj4grRSlsA9w7Xmv_cRVB7w1d84",
  "book_name": "My Book Title",
  "book_icon": "/path/to/icon.png"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile generation started in background. Check /api/generate/status for progress.",
  "book_url": "1DN04wAju6_XflgjVXj4grRSlsA9w7Xmv_cRVB7w1d84"
}
```

**Frontend Example:**
```javascript
// Trigger profile generation
const response = await fetch('http://localhost:8000/api/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    book_url: '1DN04wAju6_XflgjVXj4grRSlsA9w7Xmv_cRVB7w1d84',
    book_name: 'Harry Potter',
    book_icon: null
  })
});

const result = await response.json();
if (result.success) {
  console.log('Generation started!');
  // Poll status endpoint to check progress
}
```

**Important Notes:**
- Generation runs in the **background** - the endpoint returns immediately
- Only **one generation** can run at a time
- Use `GET /api/generate/status` to check if generation is complete
- The RAG system must be initialized first (by running `main.py` standalone once)

#### `GET /api/generate/status`
Check if profile generation is currently in progress.

**Response (when running):**
```json
{
  "is_running": true,
  "book_url": "doc123",
  "started_at": "2025-10-18T15:30:00",
  "message": "Generating profiles for book: doc123"
}
```

**Response (when complete):**
```json
{
  "is_running": false,
  "book_url": null,
  "started_at": null,
  "message": "Generation completed successfully. Created 5 profiles."
}
```

**Frontend Example (Polling):**
```javascript
// Function to check status
async function checkGenerationStatus() {
  const response = await fetch('http://localhost:8000/api/generate/status');
  return await response.json();
}

// Trigger generation
await fetch('http://localhost:8000/api/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ book_url: 'doc123' })
});

// Poll status every 5 seconds
const pollInterval = setInterval(async () => {
  const status = await checkGenerationStatus();
  console.log(status.message);
  
  if (!status.is_running) {
    clearInterval(pollInterval);
    console.log('Generation complete!');
    // Refresh character list
  }
}, 5000);
```

---

## Error Responses

All endpoints return standard HTTP status codes:

- **200 OK** - Successful request
- **404 Not Found** - Resource not found
- **500 Internal Server Error** - Server error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

**Frontend Error Handling Example:**
```javascript
try {
  const response = await fetch('http://localhost:8000/api/books/invalid');
  if (!response.ok) {
    const error = await response.json();
    console.error('Error:', error.detail);
  } else {
    const data = await response.json();
    console.log(data);
  }
} catch (error) {
  console.error('Network error:', error);
}
```

---

## CORS Configuration

The API is configured to accept requests from any origin (`*`) for development purposes. 

**For production**, update the CORS settings in `backend/src/api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Complete Frontend Integration Example

Here's a complete example of how your frontend might use the API:

```javascript
// API base URL
const API_BASE = 'http://localhost:8000';

// Fetch all books
async function getBooks() {
  const response = await fetch(`${API_BASE}/api/books`);
  return await response.json();
}

// Fetch characters for a specific book
async function getBookCharacters(bookUrl) {
  const response = await fetch(
    `${API_BASE}/api/books/${bookUrl}/characters`
  );
  return await response.json();
}

// Example usage in your app
async function displayBookCharacters() {
  try {
    // Get all books
    const books = await getBooks();
    console.log('Available books:', books);
    
    // User selects a book
    const selectedBook = books[0];
    
    // Get characters for that book
    const { characters, count } = await getBookCharacters(selectedBook.url);
    console.log(`${selectedBook.name} has ${count} characters`);
    
    // Display characters in UI
    characters.forEach(char => {
      console.log(`${char.name} (${char.character_type})`);
      console.log(`  Occupation: ${char.occupation}`);
      console.log(`  Personality: ${char.personality}`);
    });
    
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}

displayBookCharacters();
```

---

## Testing the API

### Using cURL

```bash
# Get all books
curl http://localhost:8000/api/books

# Get characters for a book
curl http://localhost:8000/api/books/doc123/characters

# Get a specific character
curl "http://localhost:8000/api/characters/John%20Doe?book_url=doc123"

# Get statistics
curl http://localhost:8000/api/stats
```

### Using the Interactive Docs

1. Start the server: `python backend/run_api.py`
2. Open http://localhost:8000/docs in your browser
3. Click on any endpoint to expand it
4. Click "Try it out"
5. Fill in parameters (if needed)
6. Click "Execute"
7. View the response

This is the easiest way to test endpoints without writing any code!

---

## API Development Notes

- The API runs on port 8000 by default
- Auto-reload is enabled in development mode
- All responses are in JSON format
- The database is automatically initialized on startup
- The API provides detailed logging in the console

