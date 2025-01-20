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
from groq import Client 

load_dotenv()

# memory=ConversationBufferMemory()      #initialize memory
# Initialize the Groq client with your API key
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set.")


# Initialize the Groq client
client = Client(api_key=groq_api_key)

openai.api_key = os.environ['OPENAI_API_KEY']

langchain_api_key = os.getenv("LANGCHAIN_API_KEY")

# Embeddings and Chroma vector store
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

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
    greetings = [
     "hi", "hello", "hey", "how are you", "good morning", "good afternoon", 
    "good evening", "hii", "heyyyy", "hiiiii", "yo", "sup", "what's up", 
    "howdy", "g'day", "hola", "bonjour", "namaste", "salutations", "hey there",
    "heyyyyyy", "hellooooo", "hellloooo", "hiiiiiiii", "hiiiiiie", "hiiiiiiiii", 
    "yo yo", "heyyyoooo", "yo yo yo", "heeyyyyyyy", "heyyyyyyyy", "heeeeeeeey", 
    "hiiiiiiiiiiii", "heyyyyyyyyyyyy" ,"hy"]
  
    farewells = [
    "thanks", "thank you", "okay, thanks", "ok, bye", "thanks a lot", 
    "thanks so much", "thanks a million", "thank you so much", "thank youuuu", 
    "okay, bye", "see ya", "later", "goodbye", "bye now", "see you later", 
    "catch ya", "take care"]

    positive_feedback = [
    "nice", "good", "great", "amazing", "excellent", "wonderful", "perfect", 
    "fantastic", "awesome", "incredible", "impressive", "cool", "outstanding", 
    "top-notch", "marvelous", "fabulous"]
    
    acknowledgments = [
    "okay", "ok", "okkkkk", "okok", "ookay", "k", "acknowledged", "roger that", 
    "alright", "got it", "understood", "yep", "yup", "yesss", "yep yep", 
    "okay dokay", "alrighty", "okie dokie", "yessir", "yesss ma'am"]


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
          """Answer the following question using only the provided content but do not mention "provided content" in your response: {data}.

    **Question:**
    {question}

    **Response:**
    Please provide a complete {detail_level} response based on the provided data only  but dont use words like on the provided data or provided content(no external sources).

    - If there is a related URL, include it in a clean format without brackets, parentheses, or 
      any trailing punctuation.
    - Do not add a full stop after links or URLs.
    - Give the full URL and avoid adding unnecessary symbols or punctuation like periods or parentheses.
    - Each new topic should start from a new line with proper bullet points or numbered lists.
    - Organize the response in clear paragraphs, with each new point starting on a new line.
    - Clean related links should not include any additional symbols or punctuation, such as periods or quotation marks.

    - You are an AI chatbot for NeuralTechSoft, designed to assist users with their queries. When someone asks
       'Who are you?', your response should be: 'I am an AI chatbot created to assist and solve user queries 
        effectively.' Avoid giving personal or irrelevant answers, such as details about individuals like directors
        or team members. Always stay professional and focused on solving user queries.

    -Provide a full and accurate PDF link, ensuring all characters such as _, -, %, spaces (as %20), and other symbols are retained exactly as they appear. Ensure the link ends with .pdf and do not modify or omit any part of it. For example, a link like https://www.neuraltechsoft.com/Projects/FC/stress%20testing.pdf should remain unchanged.        """
        
    )


    formatted_prompt = prompt_template.format(data=data, question=question, detail_level=detail_level)

    # Send the prompt to the Groq API for processing
    completion = client.chat.completions.create(
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
