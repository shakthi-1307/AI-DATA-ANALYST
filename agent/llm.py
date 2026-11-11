from langchain_groq import ChatGroq 
from dotenv import load_dotenv
import os 

load_dotenv()

llm = ChatGroq(
    model = os.getenv("GROQ_MODEL"),
    temperature = 0,
    api_key = os.getenv("GROQ_API_KEY")
)


