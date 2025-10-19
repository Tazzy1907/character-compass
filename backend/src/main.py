# System Imports
import hashlib
import os
import threading
import time
from dotenv import load_dotenv

# Third Party Imports
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import create_retriever_tool
from langchain.agents import create_agent

# Local Imports
from char_info import CharacterProfile, CharacterList
from file_loader import get_story_content, get_file_modified_time, scan_stories_folder
import database

# Tools
RETRIEVER_TOOL = None
TOOLS = [RETRIEVER_TOOL]
# Agents
PROFILE_AGENT = None
LISTER_AGENT = None
AGENTS = [PROFILE_AGENT, LISTER_AGENT]

# Set up API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set")

llm = ChatOpenAI(api_key=api_key, model="gpt-5-mini", stream_usage=True)

# Store state of RAG components.
class RAGState:
    def __init__(self):
        self.vectorstore = None
        self.last_known_mod_time = None
        self.old_split_hashes = set()
        self.lock = threading.Lock()
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.current_doc_id = None
        self.monitor_thread = None
        self.stop_monitoring = threading.Event()

rag_state = RAGState()

def hash_chunk(chunk_text):
    return hashlib.md5(chunk_text.encode('utf-8')).hexdigest()

def initialise_rag_system(file_path: str):
    """
    Performs initialisation of the RAG system, including loading, splitting, embed, and agent creation.
    
    Args:
        file_path: The txt file path (e.g., "story1.txt")
    """
    print(f"Initialising RAG system for file: {file_path}...")

    try:
        # Get initial content from local txt file
        documents_text = get_story_content(file_path)
        
        if not documents_text:
            raise Exception(f"Failed to read file: {file_path}")

        # Split text and create documents with hashed IDs.
        splits = rag_state.text_splitter.split_text(documents_text)
        docs_to_embed = []
        ids_to_embed = []

        for split in splits:
            chunk_hash = hash_chunk(split)
            if chunk_hash not in rag_state.old_split_hashes:
                rag_state.old_split_hashes.add(chunk_hash)
                docs_to_embed.append(split)
                ids_to_embed.append(chunk_hash)

        # Create embeddings and store in vector store.
        rag_state.vectorstore = FAISS.from_texts(
            texts=docs_to_embed,
            embedding=OpenAIEmbeddings(),
            ids=ids_to_embed
        )
        
        # Store file path and modification time
        rag_state.last_known_mod_time = get_file_modified_time(file_path)
        rag_state.current_doc_id = file_path
        print(f"RAG System Initialised. {len(ids_to_embed)} chunks indexed.")

    except Exception as e:
        print(f"Error initializing RAG system: {e}")
        raise e

def check_and_update_document(file_path: str) -> dict:
    """
    Check local file for changes and update vectorstore if needed.
    
    Args:
        file_path: The txt file path to check (e.g., "story1.txt")
        
    Returns:
        dict: Summary of changes made
    """
    try:
        print(f"\n🔍 Checking file {file_path} for changes...")
        
        # If RAG system not initialized or wrong file, initialize it
        if rag_state.vectorstore is None or rag_state.current_doc_id != file_path:
            print(f"⚠️  RAG system not initialized for {file_path}. Initializing...")
            initialise_rag_system(file_path)
            create_tools()
            create_agents()
            print(f"✓ RAG system initialized for {file_path}")
            return {
                "changed": False,
                "chunks_added": 0,
                "chunks_deleted": 0,
                "last_modified": str(rag_state.last_known_mod_time),
                "message": "RAG system initialized"
            }
        
        # Check file modification time
        current_mod_time = get_file_modified_time(file_path)
        
        print(f"📅 Current mod time: {current_mod_time}")
        print(f"📅 Last known mod time: {rag_state.last_known_mod_time}")
        
        # No changes detected
        if current_mod_time == rag_state.last_known_mod_time:
            print("✓ No changes detected (file not modified)")
            return {
                "changed": False,
                "chunks_added": 0,
                "chunks_deleted": 0,
                "last_modified": str(current_mod_time)
            }
        
        print(f"File changed at {current_mod_time}. Reindexing...")
        
        # Get new content from local file
        new_documents_text = get_story_content(file_path)
        if not new_documents_text:
            raise Exception("Failed to fetch document content")
        
        # Split and hash new content
        new_splits = rag_state.text_splitter.split_text(new_documents_text)
        new_split_hashes = set()
        new_split_map = {}
        
        for split in new_splits:
            chunk_hash = hash_chunk(split)
            new_split_hashes.add(chunk_hash)
            new_split_map[chunk_hash] = split
        
        # Calculate diff
        hashes_to_add = new_split_hashes - rag_state.old_split_hashes
        hashes_to_delete = rag_state.old_split_hashes - new_split_hashes
        
        # Store changed chunk text for character filtering
        changed_chunks_text = []
        
        # Update vector store
        with rag_state.lock:
            if hashes_to_delete:
                rag_state.vectorstore.delete(ids=list(hashes_to_delete))
                print(f"Deleted {len(hashes_to_delete)} old chunks.")
            
            if hashes_to_add:
                texts_to_add = [new_split_map[h] for h in hashes_to_add]
                changed_chunks_text = texts_to_add  # Save for character filtering
                ids_to_add = list(hashes_to_add)
                rag_state.vectorstore.add_texts(
                    texts=texts_to_add,
                    ids=ids_to_add
                )
                print(f"Added {len(hashes_to_add)} new chunks.")
            
            # Update state
            rag_state.old_split_hashes = new_split_hashes
            rag_state.last_known_mod_time = current_mod_time
        
        print("Document reindexed successfully.")
        
        return {
            "changed": True,
            "chunks_added": len(hashes_to_add),
            "chunks_deleted": len(hashes_to_delete),
            "last_modified": str(current_mod_time),
            "changed_chunks_text": changed_chunks_text,
            "full_document_text": new_documents_text  # For character cleanup
        }
        
    except Exception as e:
        print(f"Error checking document changes: {e}")
        raise e

# Monitoring functions removed - using manual refresh instead

def reinitialize_rag_for_document(file_path: str):
    """
    Re-initializes the RAG system for a new file.
    Clears the vectorstore and re-indexes the specified file.
    
    Args:
        file_path: The txt file path to index (e.g., "story1.txt")
    """
    print(f"\n{'='*60}")
    print(f"Re-initializing RAG system for file: {file_path}")
    print(f"{'='*60}\n")
    
    # Clear existing state
    with rag_state.lock:
        rag_state.vectorstore = None
        rag_state.last_known_mod_time = None
        rag_state.old_split_hashes = set()
        rag_state.current_doc_id = None
    
    # Initialize with new file
    initialise_rag_system(file_path)
    
    # Recreate tools and agents with new vectorstore
    create_tools()
    create_agents()
    
    print(f"\n{'='*60}")
    print(f"RAG system re-initialized successfully for {file_path}")
    print(f"{'='*60}\n")

# ------------------------------------------------------------ TOOLS ------------------------------------------------------------
def create_tools():
    global RETRIEVER_TOOL
    try: 
        RETRIEVER_TOOL = create_retriever_tool(
            retriever=rag_state.vectorstore.as_retriever(),
            name="retrieve_book_info",
            description="Search and return relevant information from a book.",
        )
    except Exception as e:
        print(f"Error creating retriever tool: {e}")
        exit(1)

# ------------------------------------------------------------ AGENTS ------------------------------------------------------------
def create_agents():
    global PROFILE_AGENT, LISTER_AGENT
    try:
        # Character Profile Agent
        # Utility: Creating an in-depth profile of a character from a given text.
        # 
        # @return: A CharacterProfile object.
        PROFILE_AGENT = create_agent(
            model=llm,
            tools=[RETRIEVER_TOOL],
            system_prompt="""
            You are a helpful assistant who is an expert at analysing a book to build
            character profiles. Use the available tools to find the necessary information.
            **ONLY** get information from the book.
            If the information does not exist, do not make it up.
            """,
            response_format=CharacterProfile
        )

        # Character Lister Agent
        # Utility: Listing characters of note within a given text. Should only find the main character,
        # and ones which may play a part in the story.
        # 
        # @return: A list of character names.
        LISTER_AGENT = create_agent(
            model=llm,
            tools=[RETRIEVER_TOOL],
            system_prompt="""
            You are a helpful assistant who is an expert at analysing a book
            to find all characters and categorize them.
            Your goal is to identify 'main_characters' and 'side_characters'.
            Use the available tools to find the necessary information from the book.

            You must ONLY use information available gotten from the retriever tool. NOWHERE ELSE.
            """,
            response_format=CharacterList
        )

    except Exception as e:
        print(f"Error creating agents: {e}")
        exit(1)

# ------------------------------------------------------------ PROFILE GENERATION ------------------------------------------------------------
def generate_profiles_for_book(book_url: str, book_name: str = None, book_icon: str = None):
    """
    Generate character profiles for a specific book.
    This function can be called from the API or run standalone.
    
    Args:
        book_url: The txt file path for the book (e.g., "story1.txt")
        book_name: Optional book name (defaults to filename without extension)
        book_icon: Optional book icon path
        
    Returns:
        dict: Status information about the generation process
    """
    try:
        print(f"\n{'='*60}")
        print(f"Starting profile generation for book: {book_url}")
        print(f"{'='*60}\n")
        
        # Ensure database is initialized
        database.initialize_database()
        
        # If no book name provided, use filename without extension
        if not book_name:
            from pathlib import Path
            book_name = Path(book_url).stem  # e.g., "story1.txt" -> "story1"
        
        # Add/update book in database
        database.add_or_update_book(
            url=book_url,
            name=book_name,
            icon=book_icon
        )
        
        # Re-initialize RAG system for this specific document
        reinitialize_rag_for_document(book_url)
        
        # Check if agents are ready
        if not LISTER_AGENT or not PROFILE_AGENT:
            return {
                "success": False,
                "error": "Agents not initialized. Please ensure the RAG system is set up first."
            }
        
        print("Getting list of characters from book...")
        list_response = LISTER_AGENT.invoke({
            "messages": [{"role": "user", "content": "Use your retriever tool to find the characters of note from the book that has been indexed."}]
        })
        
        # Get characters from response and split into main and side
        characters = list_response.get('structured_response')
        main_chars = characters.main_characters
        side_chars = characters.side_characters

        print("\n--- Characters Identified ---")
        print(f"Main characters: {main_chars}")
        print(f"Side characters: {side_chars}\n")

        profiles_created = 0
        profiles_failed = 0

        # Loop through the main characters and call the profile agent on each
        for char_name in main_chars:
            print(f"Creating profile for {char_name}...")
            try:
                profile_response = PROFILE_AGENT.invoke({
                    "messages": [{
                        "role": "user",
                        "content": f"Create a detailed character profile for the character {char_name}. Use your retriever tool to find information from the book. If information is not available, use None or empty values."
                    }]
                })
                
                character_profile = profile_response.get('structured_response')

                if isinstance(character_profile, CharacterProfile):
                    print(character_profile.model_dump_json(indent=2))
                    
                    # Save character profile to database
                    database.add_or_update_character(
                        profile=character_profile,
                        book_url=book_url,
                        character_type="main"
                    )
                    profiles_created += 1
                else:
                    print(f"Error: Did not receive a profile response for {char_name}")
                    profiles_failed += 1
                
                time.sleep(5)  # Avoid API rate limits
            except Exception as e:
                print(f"Error creating profile for {char_name}: {e}")
                profiles_failed += 1
        
        # Loop through side characters and save them as well
        for char_name in side_chars:
            print(f"Creating profile for side character {char_name}...")
            try:
                profile_response = PROFILE_AGENT.invoke({
                    "messages": [{
                        "role": "user",
                        "content": f"Create a detailed character profile for the character {char_name}. Use your retriever tool to find information from the book. If information is not available, use None or empty values."
                    }]
                })
                
                character_profile = profile_response.get('structured_response')

                if isinstance(character_profile, CharacterProfile):
                    print(character_profile.model_dump_json(indent=2))
                    
                    # Save side character profile to database
                    database.add_or_update_character(
                        profile=character_profile,
                        book_url=book_url,
                        character_type="side"
                    )
                    profiles_created += 1
                else:
                    print(f"Error: Did not receive a profile response for {char_name}")
                    profiles_failed += 1
                
                time.sleep(5)  # Avoid API rate limits
            except Exception as e:
                print(f"Error creating profile for {char_name}: {e}")
                profiles_failed += 1
        
        print(f"\n{'='*60}")
        print(f"Profile generation complete!")
        print(f"Created: {profiles_created} | Failed: {profiles_failed}")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "profiles_created": profiles_created,
            "profiles_failed": profiles_failed,
            "main_characters": main_chars,
            "side_characters": side_chars
        }
        
    except Exception as e:
        error_msg = f"Error during profile generation: {str(e)}"
        print(f"\n❌ {error_msg}\n")
        return {
            "success": False,
            "error": error_msg
        }

def cleanup_removed_characters(book_url: str, full_document_text: str) -> dict:
    """
    Remove characters from database that are no longer mentioned in the document.
    
    Args:
        book_url: The Google Doc ID/URL for the book
        full_document_text: The complete current text of the document
        
    Returns:
        dict: Summary of characters removed
    """
    try:
        print(f"\n🧹 Checking for characters to remove from {book_url}...")
        
        # Get all existing characters for this book
        existing_characters = database.get_characters_by_book(book_url)
        
        if not existing_characters:
            print("No characters in database to check.")
            return {
                "success": True,
                "characters_removed": [],
                "message": "No characters to check"
            }
        
        document_text_lower = full_document_text.lower()
        characters_to_remove = []
        
        # Check each character to see if they're still mentioned
        for char in existing_characters:
            char_name = char['name']
            
            # Check if character name appears in the document
            if char_name.lower() not in document_text_lower:
                characters_to_remove.append(char_name)
                print(f"   ❌ '{char_name}' no longer in document - will remove")
            else:
                print(f"   ✓ '{char_name}' still present")
        
        # Remove characters that are no longer in the document
        removed_characters = []
        for char_name in characters_to_remove:
            try:
                database.delete_character(char_name, book_url)
                removed_characters.append(char_name)
                print(f"   🗑️  Removed '{char_name}' from database")
            except Exception as e:
                print(f"   ⚠️  Failed to remove '{char_name}': {e}")
        
        if removed_characters:
            print(f"\n🧹 Cleanup complete: Removed {len(removed_characters)} character(s)")
        else:
            print(f"\n✓ No characters need to be removed")
        
        return {
            "success": True,
            "characters_removed": removed_characters,
            "message": f"Removed {len(removed_characters)} characters no longer in document"
        }
        
    except Exception as e:
        error_msg = f"Error during character cleanup: {str(e)}"
        print(f"\n❌ {error_msg}\n")
        return {
            "success": False,
            "error": error_msg,
            "characters_removed": []
        }

def update_existing_profiles(book_url: str, changed_chunks: list = None) -> dict:
    """
    Update character profiles for existing characters when document changes.
    
    Args:
        book_url: The Google Doc ID/URL for the book
        changed_chunks: List of text chunks that changed (for filtering relevant characters)
        
    Returns:
        dict: Summary of updates made
    """
    try:
        print(f"\n{'='*60}")
        print(f"Updating existing profiles for book: {book_url}")
        print(f"{'='*60}\n")
        
        # Check if agents are ready
        if not PROFILE_AGENT:
            return {
                "success": False,
                "error": "Profile agent not initialized"
            }
        
        # Get existing characters from database
        existing_characters = database.get_characters_by_book(book_url)
        
        if not existing_characters:
            print("No existing characters to update.")
            return {
                "success": True,
                "characters_updated": [],
                "message": "No existing characters to update"
            }
        
        print(f"Found {len(existing_characters)} existing characters in database.")
        
        # Filter characters based on changed chunks
        if changed_chunks:
            # Combine all changed text
            changed_text = " ".join(changed_chunks).lower()
            
            print(f"📄 Changed chunks preview (first 200 chars):")
            print(f"   {changed_text[:200]}...")
            
            # Only update characters mentioned in changed chunks
            characters_to_update = [
                char for char in existing_characters
                if char['name'].lower() in changed_text
            ]
            
            print(f"📝 Filtered to {len(characters_to_update)} characters mentioned in changed chunks:")
            for char in characters_to_update:
                print(f"   - {char['name']}")
            
            # Fallback: If no characters match, update all as a safety measure
            if len(characters_to_update) == 0:
                print(f"⚠️  WARNING: No characters matched the filter!")
                print(f"⚠️  Character names in DB: {[c['name'] for c in existing_characters]}")
                print(f"⚠️  Falling back to updating ALL characters to ensure database stays current")
                characters_to_update = existing_characters
        else:
            # No chunk info, update all (fallback)
            characters_to_update = existing_characters
            print(f"⚠️  No changed chunk info - updating all {len(characters_to_update)} characters")
        
        updated_characters = []
        failed_updates = []
        
        print(f"\n🔄 Starting update loop for {len(characters_to_update)} character(s)...")
        
        # Update each filtered character
        for char_data in characters_to_update:
            char_name = char_data['name']
            char_type = char_data['character_type']
            
            print(f"Updating profile for {char_name}...")
            
            try:
                profile_response = PROFILE_AGENT.invoke({
                    "messages": [{
                        "role": "user",
                        "content": f"Create a detailed character profile for the character {char_name}. Use your retriever tool to find information from the book. If information is not available, use None or empty values."
                    }]
                })
                
                character_profile = profile_response.get('structured_response')
                
                if isinstance(character_profile, CharacterProfile):
                    # Update character in database
                    print(f"💾 Writing {char_name} to database...")
                    database.add_or_update_character(
                        profile=character_profile,
                        book_url=book_url,
                        character_type=char_type
                    )
                    updated_characters.append(char_name)
                    print(f"✓ Successfully updated {char_name} in database")
                else:
                    print(f"✗ Failed to get valid profile for {char_name}")
                    failed_updates.append(char_name)
                
                # Rate limiting - space out OpenAI API calls to avoid rate limits
                # (This is separate from frontend's 60-second monitoring interval)
                time.sleep(3)
                
            except Exception as e:
                print(f"Error updating profile for {char_name}: {e}")
                failed_updates.append(char_name)
        
        print(f"\n{'='*60}")
        print(f"Profile updates complete!")
        print(f"Updated: {len(updated_characters)} | Failed: {len(failed_updates)}")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "characters_updated": updated_characters,
            "characters_failed": failed_updates,
            "message": f"Updated {len(updated_characters)} characters"
        }
        
    except Exception as e:
        error_msg = f"Error updating profiles: {str(e)}"
        print(f"\n❌ {error_msg}\n")
        return {
            "success": False,
            "error": error_msg,
            "characters_updated": []
        }

# Main loop - no longer used with local file system
# Use api.py to start the FastAPI server instead
if __name__ == "__main__":
    print("\n--- Character Compass RAG System ---")
    print("This module provides RAG functionality for character profile generation.")
    print("To use the system, run api.py to start the FastAPI server.")
    print("\nExample: python backend/src/api.py")
    print("\nThen use the frontend to scan stories and generate profiles.")
