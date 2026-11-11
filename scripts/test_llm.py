import os 
from dotenv import load_dotenv 
from langchain_groq import ChatGroq 

load_dotenv()

llm = ChatGroq(
    model = os.getenv("GROQ_MODEL"),
    temperature = 0,
    api_key = os.getenv("GROQ_API_KEY")
)

response = llm.invoke("You are an AI data analyst. Explain what revenue means in e-commerce.")

print("\nLLM Response : ")
print(response.content)