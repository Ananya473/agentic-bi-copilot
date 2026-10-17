
import os
from dotenv import load_dotenv
from google import genai

# Load the API key from the project's .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY was not found. Check your .env file."
    )

# Create the Gemini client
client = genai.Client(api_key=api_key)

# Send a small test request
response = client.models.generate_content(
    model="gemini-3.7-flash",
    contents="Reply with exactly: Gemini connection successful",
)

print("Gemini response:")
print(response.text)
