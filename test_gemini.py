import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Configure API
genai.configure(api_key=API_KEY)

# Initialize the model
model = genai.GenerativeModel("gemini-1.5-flash")  # You can use "gemini-1.5-pro" as well

while True:
    user_input = input("\nEnter your prompt (or type 'exit' to quit): ")
    if user_input.lower() == "exit":
        print("Goodbye! 👋")
        break

    try:
        response = model.generate_content(user_input)
        print("\n💡 AI Response:\n")
        print(response.text)
    except Exception as e:
        print("Error:", e)
