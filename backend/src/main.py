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

llm = ChatOpenAI(api_key=api_key, model="gpt-5", stream_usage=True)

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

rag_state = RAGState()

def hash_chunk(chunk_text):
    return hashlib.md5(chunk_text.encode('utf-8')).hexdigest()

def initialise_rag_system():
    """
    Performs initialisation of the RAG system, including loading, splitting, embed, and agent creation.
    """
    print("Initialising RAG system...")

    try:
        client = get_drive_service()
        file_metadata = client.files().get(fileId=DOC_ID, fields='modifiedTime').execute()

        # Get initial content.
        documents_text = get_doc_content(DOC_ID)

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
        print(f"RAG System Initialised. {len(ids_to_embed)} chunks indexed.")

    except Exception as e:
        print(f"Error initializing RAG system: {e}")
        exit(1)

def monitor_document_changes():
    """
    A loop that runs in the background and monitors the document for changes.
    """
    client = get_drive_service()

    while True:
        try:
            time.sleep(DOC_POLL_INTERVAL)

            # Check for changes.
            file_metadata = client.files().get(fileId=DOC_ID, fields='modifiedTime').execute()
            current_mod_time = file_metadata.get('modifiedTime')

            if current_mod_time == rag_state.last_known_mod_time:
                continue

            print(f"Document changed at {current_mod_time}. Reindexing...")

            new_documents_text = get_doc_content(DOC_ID)

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

            # Get update lock.
            with rag_state.lock:
                # Update vector store.
                if hashes_to_delete:
                    rag_state.vectorstore.delete(ids=hashes_to_delete)
                    print(f"Deleted {len(hashes_to_delete)} old chunks.")
                
                if hashes_to_add:
                    texts_to_add = [new_split_map[h] for h in hashes_to_add]
                    ids_to_add = list(hashes_to_add)
                    rag_state.vectorstore.add_texts(
                        texts=texts_to_add,
                        ids=ids_to_add
                    )
                    print(f"Added {len(hashes_to_add)} new chunks.")

                # Update state for next poll
                rag_state.old_split_hashes = new_split_hashes
                rag_state.last_known_mod_time = current_mod_time

            print("Document reindexed successfully.")

        except Exception as e:
            print(f"Error monitoring document changes: {e}")
            continue

def begin_change_monitoring():
    """
    Begins monitoring the document for changes.
    """
    monitor_thread = threading.Thread(target=monitor_document_changes, daemon=True)
    monitor_thread.start()

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
            """,
            response_format=CharacterList
        )

    except Exception as e:
        print(f"Error creating agents: {e}")
        exit(1)

# Main loop.
if __name__ == "__main__":
    # Startup
    initialise_rag_system()
    # Separate monitoring thread in the background.
    begin_change_monitoring()

    # Create tools and agents.
    create_tools()
    create_agents()

    print("\n--- Live Character Profile Assistant ---")

    # --- MAIN ORCHESTRATION LOOP ---
    while True:
        try:
            # Get list of main characters.
            if not LISTER_AGENT or not PROFILE_AGENT:
                print("Agents not ready yet. Waiting for initialization...")
                time.sleep(10)
                continue
            
            print("Getting list of main characters...")
            list_response = LISTER_AGENT.invoke({
                "messages": [{"role": "user", "content": "Use your retriever tool to find the characters of note from the book that has been indexed."}]
            })
            
            characters = list_response.get('structured_response')
            main_chars = characters.main_characters
            side_chars = characters.side_characters

            print("--- Characters Identified ---")
            print(f"Main characters: {main_chars}")
            print(f"Side characters: {side_chars}")

            # Loop through the main characters and call the profile agent on each.
            for char_name in main_chars:
                print(f"Creating profile for {char_name}...")
                profile_response = PROFILE_AGENT.invoke({
                    "messages": [{"role": "user", "content": f"Create a detailed character profile for the character {char_name}. Use your retriever tool to find information from the book. If information is not available, use None or empty values."}]
                })
                
                character_profile = profile_response.get('structured_response')

                if isinstance(character_profile, CharacterProfile):
                    print(character_profile.model_dump_json(indent=2))
                else:
                    print(f"Error: Did not recieve a profile response for {char_name}")
                
                time.sleep(5) # Avoid API response times.
            
            print("\n=== All character profiles created successfully! ===")
            break

        except KeyboardInterrupt:
            print("\nExiting...")
            exit(0)
