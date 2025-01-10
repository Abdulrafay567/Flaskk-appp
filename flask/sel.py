import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request, jsonify
import os
from groq import Groq
import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# Initialize Groq API client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Function to send a query to Groq and get the response
def get_groq_response(user_input):
    try:
        # Send the user input to Groq API
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": user_input}],
            model="llama3-8b-8192",
        )
        # Extract and return the response
        return chat_completion.choices[0].message.content
    except Exception as e:
        # Handle errors gracefully
        return f"Error communicating with Groq API: {str(e)}"

# Default chatbot response function
def chatbot_response(my_input):
    responses = {
        "hello": "Hi there! How can I assist you today?",
        "how are you": "I'm just a bot, but I'm functioning as expected! How about you?",
        "bye": "Goodbye! Have a great day!",
        "time": f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')}.",
        "date": f"Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')}.",
    }
    return responses.get(my_input.lower(), "I'm not sure how to respond to that. Can you try rephrasing?")

# Function to store data in Firestore (example: store chat data)
def store_chat_data(user_input, bot_response):
    try:
        # Reference to Firestore collection (e.g., "chats")
        chats_ref = db.collection("chats")
        # Add a new document with a timestamp
        chat_doc_ref = chats_ref.add({
            'user_input': user_input,
            'bot_response': bot_response,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception as e:
        print(f"Error storing data: {e}")
        return False

# Route for chatbot interaction
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if user_message:
        response = get_groq_response(user_message)
        if "Error" in response:  # Fallback if Groq fails
            response = chatbot_response(user_message)
        
        # Store the interaction in Firestore
        store_chat_data(user_message, response)
        
        return jsonify({"response": response})
    return jsonify({"error": "No message provided"}), 400

# Home route to render the chatbot interface
@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True, port=5005)
