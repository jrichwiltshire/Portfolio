from google import genai
import os

# Setup
api_key = "AIzaSyAbTim8NuemdsTuPikGe96D8zp_LIaDngo"
client = genai.Client(api_key=api_key)

def ask_gemini(prompt):
    try:
        # New syntax: models.generate_content
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        print(f"\n✨ Gemini: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    user_input = input("How can I help with your Austin project? ")
    ask_gemini(user_input)