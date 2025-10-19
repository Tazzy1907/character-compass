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
from docs_api import get_doc_content, get_drive_service
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

# EXAMPLE DOCUMENT ID.
DOC_ID = '1DN04wAju6_XflgjVXj4grRSlsA9w7Xmv_cRVB7w1d84'
DOC_POLL_INTERVAL = 60 # Check the google doc for changes every 60 seconds.

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

def initialise_rag_system(doc_id: str):
    """
    Performs initialisation of the RAG system, including loading, splitting, embed, and agent creation.
    
    Args:
        doc_id: The Google Doc ID to index
    """
    print(f"Initialising RAG system for document {doc_id}...")

    try:
        client = get_drive_service()
        file_metadata = client.files().get(fileId=doc_id, fields='modifiedTime').execute()

        # Get initial content.
        documents_text = get_doc_content(doc_id)

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
        
        rag_state.last_known_mod_time = file_metadata.get('modifiedTime')
        rag_state.current_doc_id = doc_id
        print(f"RAG System Initialised. {len(ids_to_embed)} chunks indexed.")

    except Exception as e:
        print(f"Error initializing RAG system: {e}")
        raise e

def check_and_update_document(doc_id: str) -> dict:
    """
    Check document for changes and update vectorstore if needed.
    
    Args:
        doc_id: The Google Doc ID to check
        
    Returns:
        dict: Summary of changes made
    """
    try:
        print(f"\n🔍 Checking document {doc_id} for changes...")
        client = get_drive_service()
        
        # Check for changes
        file_metadata = client.files().get(fileId=doc_id, fields='modifiedTime').execute()
        current_mod_time = file_metadata.get('modifiedTime')
        
        print(f"📅 Current mod time: {current_mod_time}")
        print(f"📅 Last known mod time: {rag_state.last_known_mod_time}")
        
        # No changes detected
        if current_mod_time == rag_state.last_known_mod_time:
            print("✓ No changes detected")
            return {
                "changed": False,
                "chunks_added": 0,
                "chunks_deleted": 0,
                "last_modified": current_mod_time
            }
        
        print(f"Document changed at {current_mod_time}. Reindexing...")
        
        # Get new content
        new_documents_text = get_doc_content(doc_id)
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
            "last_modified": current_mod_time,
            "changed_chunks_text": changed_chunks_text
        }
        
    except Exception as e:
        print(f"Error checking document changes: {e}")
        raise e

def monitor_document_changes():
    """
    A loop that runs in the background and monitors the document for changes.
    """
    while not rag_state.stop_monitoring.is_set():
        try:
            time.sleep(DOC_POLL_INTERVAL)

            # Check if monitoring should stop
            if rag_state.stop_monitoring.is_set():
                break

            # Check if we have a document to monitor
            if not rag_state.current_doc_id:
                continue

            # Use refactored function to check and update
            check_and_update_document(rag_state.current_doc_id)

        except Exception as e:
            print(f"Error monitoring document changes: {e}")
            continue

def begin_change_monitoring():
    """
    Begins monitoring the document for changes.
    """
    rag_state.stop_monitoring.clear()
    rag_state.monitor_thread = threading.Thread(target=monitor_document_changes, daemon=True)
    rag_state.monitor_thread.start()

def stop_change_monitoring():
    """
    Stops the document monitoring thread.
    """
    if rag_state.monitor_thread and rag_state.monitor_thread.is_alive():
        print("Stopping document monitoring...")
        rag_state.stop_monitoring.set()
        rag_state.monitor_thread.join(timeout=5)
        print("Document monitoring stopped.")

def reinitialize_rag_for_document(doc_id: str):
    """
    Re-initializes the RAG system for a new document.
    This stops any existing monitoring, clears the vectorstore, and re-indexes the new document.
    
    Args:
        doc_id: The Google Doc ID to index
    """
    print(f"\n{'='*60}")
    print(f"Re-initializing RAG system for document: {doc_id}")
    print(f"{'='*60}\n")
    
    # Stop existing monitoring
    stop_change_monitoring()
    
    # Clear existing state
    with rag_state.lock:
        rag_state.vectorstore = None
        rag_state.last_known_mod_time = None
        rag_state.old_split_hashes = set()
        rag_state.current_doc_id = None
    
    # Initialize with new document
    initialise_rag_system(doc_id)
    
    # Recreate tools and agents with new vectorstore
    create_tools()
    create_agents()
    
    # Start monitoring the new document
    begin_change_monitoring()
    
    print(f"\n{'='*60}")
    print(f"RAG system re-initialized successfully for {doc_id}")
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
        book_url: The Google Doc ID/URL for the book
        book_name: Optional book name (defaults to "Sample Book")
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
        
        # Add/update book in database
        database.add_or_update_book(
            url=book_url,
            name=book_name or "Sample Book",
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
            
            # Only update characters mentioned in changed chunks
            characters_to_update = [
                char for char in existing_characters
                if char['name'].lower() in changed_text
            ]
            
            print(f"📝 Filtered to {len(characters_to_update)} characters mentioned in changed chunks:")
            for char in characters_to_update:
                print(f"   - {char['name']}")
        else:
            # No chunk info, update all (fallback)
            characters_to_update = existing_characters
            print(f"⚠️  No changed chunk info - updating all {len(characters_to_update)} characters")
        
        updated_characters = []
        failed_updates = []
        
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
                    database.add_or_update_character(
                        profile=character_profile,
                        book_url=book_url,
                        character_type=char_type
                    )
                    updated_characters.append(char_name)
                    print(f"✓ Updated {char_name}")
                else:
                    print(f"✗ Failed to get valid profile for {char_name}")
                    failed_updates.append(char_name)
                
                # Rate limiting
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

# Main loop.
if __name__ == "__main__":
    # Startup
    initialise_rag_system(DOC_ID)
    # Separate monitoring thread in the background.
    begin_change_monitoring()

    # Create tools and agents.
    create_tools()
    create_agents()

    print("\n--- Live Character Profile Assistant ---")

    # Run profile generation
    try:
        result = generate_profiles_for_book(
            book_url=DOC_ID,
            book_name="Sample Book",  # TODO: Update with actual book title
            book_icon=None  # TODO: Add book icon path if available
        )
        
        if result["success"]:
            print("\n=== All character profiles created successfully! ===")
        else:
            print(f"\n❌ Profile generation failed: {result.get('error')}")
            
    except KeyboardInterrupt:
        print("\nExiting...")
        stop_change_monitoring()
        exit(0)
