# System Imports
import os
from dotenv import load_dotenv

# Third Party Imports
from langchain_openai import ChatOpenAI


# Local Imports

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set")

llm = ChatOpenAI(api_key=api_key, model="gpt-5-mini", stream_usage=True)

messages = [
    (
        "system",
        "You are a helpful assistant that translates English to French. Translate the user sentence to French.",
    ),
    (
        "human",
        "Hello World!"
    ),
]

ai_msg = llm.invoke(messages)
print(ai_msg.content)
