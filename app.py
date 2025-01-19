import re
from flask import Flask, request, jsonify, render_template
from datetime import datetime
from groq import Groq
from langchain.prompts import PromptTemplate
import json
from dotenv import load_dotenv
import openai
import os
from langchain.schema import HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# memory=ConversationBufferMemory()      #initialize memory
# Initialize the Groq client with your API key
groq_api_key = os.getenv("GROQ_API_KEY")

openai.api_key = os.environ['OPENAI_API_KEY']

langchain_api_key = os.getenv("LANGCHAIN_API_KEY")

# Embeddings and Chroma vector store
embeddings = OpenAIEmbeddings(s
    model="text-embedding-ada-002"
)

vector_store = Chroma(
    collection_name="website",
    embedding_function=embeddings,
    persist_directory=r"Database\db\chroma_langchain_db",
)

# Initialize Flask app
app = Flask(__name__)

# Function to detect and convert URLs to clickable links
def convert_urls_to_links(text):
    url_pattern = r'https?://[^\s]+'
    return re.sub(url_pattern, r'<a href="\g<0>" target="_blank">\g<0></a>', text)

# Function to process questions and handle interactions
def process_with_groq(question, detail_level="brief"):
    # Lists for different types of interactions
    greetings = ["hi", "hello", "hey", "how are you", "good morning", "good afternoon", 
    "good evening", "hii", "heyyyy", "hiiiii", "yo", "sup", "what's up", 
    "howdy", "g'day", "hola", "bonjour", "namaste", "salutations", "hey there"]
    farewells = ["thanks", "thank you", "okay, thanks", "ok, bye", "thanks a lot"]
    positive_feedback = ["nice", "good", "great", "amazing", "excellent", "wonderful", "perfect"]
    acknowledgments = ["okay", "ok","okkkkk", "okok", "ookay"]

    # Handle greetings
    if question.strip().lower() in greetings:
        greeting = get_time_of_day_greeting()
        return f"{greeting} It's great to hear from you! How can I assist you today?"

    # Handle acknowledgments like "okay" or "ok"
    if question.strip().lower() in acknowledgments:
        return "Sure! Let me know if there's anything else you'd like to discuss."

    # Handle farewells and gratitude
    if any(farewell in question.lower() for farewell in farewells):
        return ("You're welcome! Feel free to reach out anytime. "
                "By the way, are you interested in exploring any of our other services?")

    # Handle positive feedback
    if any(feedback in question.lower() for feedback in positive_feedback):
        return ("Thank you for your kind words! We appreciate your feedback. "
                "Would you like to learn about any of our other services or offerings?")

    # Retrieve relevant documents from the vector store (your knowledge base)
    retrieve = vector_store.similarity_search_with_relevance_scores(question, k=5)
    data = [doc[0].page_content for doc in retrieve]
    print("QUESTION:", question)
    print("DATA:", data)

    # Generate a response using your knowledge base and Groq API
    prompt_template = PromptTemplate.from_template(
        """Answer the following question using only the provided content: {data}.
        Question: {question}.
        Provide a complete {detail_level} response based on the provided data only (no external sources).
        # If there is a related URL, include it in a clean format without brackets (e.g., []), parentheses (e.g., . ,  ()), or any trailing punctuation (e.g., period, comma, etc.).
        """
        )


    formatted_prompt = prompt_template.format(data=data, question=question, detail_level=detail_level)

    # Send the prompt to the Groq API for processing
    completion = groq_api_key.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": formatted_prompt}],
        temperature=0.3,
        max_tokens=1024,
        top_p=1,
        # memory=memory,
        stream=True,
        stop=None,
    )

    response = ""
    for chunk in completion:
        content = chunk.choices[0].delta.content or ""
        response += content

    # Clean up unwanted symbols
    unwanted_symbols = ['*', '+', '•']
    for symbol in unwanted_symbols:
        response = response.replace(symbol, "").strip()

    # Convert URLs to clickable links
    response = convert_urls_to_links(response)

    # Friendly fallback for unhelpful responses
    if not response.strip() or "no information" in response.lower():
        response = "I'm sorry, I couldn't find an answer to your question. Please ask something else, and I'll do my best to help!"

    return response


# Function to get a greeting based on the current time
def get_time_of_day_greeting():
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        return "Good Morning!"
    elif 12 <= current_hour < 18:
        return "Good Afternoon!"
    else:
        return "Good Evening!"

# Serve the frontend
@app.route('/')
def home():
    greeting = get_time_of_day_greeting()
    return render_template('index.html', greeting=greeting)

# Route to handle question
@app.route('/ask', methods=['POST'])
def ask():
    user_question = request.json.get('question')
    if not user_question:
        return jsonify({"error": "No question provided"}), 400

    # Process the question and provide a response
    answer = process_with_groq(user_question, detail_level="brief")
    return jsonify({"answer": answer})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
