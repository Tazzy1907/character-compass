# System Imports
import os
from dotenv import load_dotenv

# Patch for chromadb compatibility with Pydantic v2
import sys
if not hasattr(sys.modules.get('pydantic', object()), 'BaseSettings'):
    from pydantic_settings import BaseSettings
    import pydantic
    pydantic.BaseSettings = BaseSettings

# Third Party Imports
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import create_retriever_tool
from langchain.agents import create_agent

# Set up API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set")

llm = ChatOpenAI(api_key=api_key, model="gpt-5-mini", stream_usage=True)


# RAG System
try:
    loader = TextLoader("test_data/sample.txt")
    documents = loader.load()

    # Splitting document into chunks.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)

    # Creating embeddings and store in vector store.
    vectorstore = FAISS.from_documents(documents=splits, embedding=OpenAIEmbeddings())

    retriever = vectorstore.as_retriever()
    print("LangChain RAG System Initialized")

except Exception as e:
    print(f"Error initializing RAG system: {e}")
    exit(1)

# Create retriever tool to get infeormation from input text.
if retriever:
    retriever_tool = create_retriever_tool(
        retriever=retriever,
        name="retrieve_book_info",
        description="Search and return relevant information from a book.",
    )

    tools = [retriever_tool]
else:
    print("No retriever found")
    exit(1)

# Create agent using the new LangChain 1.0.0 API
system_prompt = "You are a helpful assistant who is an expert at analysing a book to build character profiles. Use the available tools to find the necessary information."

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)

if __name__ == "__main__":
    if tools:
        # Using the new message-based API
        response = agent.invoke({
            "messages": [{"role": "user", "content": "Create a detailed character profile for the character James Choke"}]
        })

        # Extract the final response from messages
        final_message = response['messages'][-1]
        print(f"\nFINAL RESPONSE:\n{final_message.content}")
    
    else:
        print("Tools are not available")