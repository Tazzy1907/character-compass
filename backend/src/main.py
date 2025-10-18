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
from char_info import CharacterProfile
from docs_api import get_doc_content, get_drive_service

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
        self.agent = None
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

        # Create retriever and agent.
        retriever = rag_state.vectorstore.as_retriever()
        retriever_tool = create_retriever_tool(
            retriever=retriever,
            name="retrieve_book_info",
            description="Search and return relevant information from a book.",
        )

        system_prompt = """
            You are a helpful assistant who is an expert at analysing a book to build
            character profiles. Use the available tools to find the necessary information.
            **ONLY** get information from the book.
            If the information does not exist, do not make it up.
            """

        rag_state.agent = create_agent(
            model=llm,
            tools=[retriever_tool],
            system_prompt=system_prompt,
            response_format=CharacterProfile
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
                print("No changes detected.")
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



# Main loop.
if __name__ == "__main__":
    # Startup
    initialise_rag_system()

    # Separate monitoring thread in the background.
    monitor_thread = threading.Thread(target=monitor_document_changes, daemon=True)
    monitor_thread.start()

    print("\n--- Live Character Profile Assistant ---")
    print("The system is monitoring the Google Doc for changes in the background.")

    while True:
        try:
            with rag_state.lock:
                if rag_state.agent:
                    response = rag_state.agent.invoke({
                        "messages": [{"role": "user", "content": "Create a detailed character profile for the character James Choke"}]
                    })

                    # Extract the final response from messages
                    final_message = response['messages'][-1]
                    print(f"\nFINAL RESPONSE:\n{final_message.content}")

                else:
                    print("Agent is not ready yet")

                time.sleep(60)

        except KeyboardInterrupt:
            print("\nExiting...")
            exit(0)