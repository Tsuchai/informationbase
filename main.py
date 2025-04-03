from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import wikipediaapi
import re
from duckduckgo_search import DDGS
from fastapi.staticfiles import StaticFiles
import threading
import webbrowser

# Initialize FastAPI
app = FastAPI()

# Mount the static files directory under a different path to avoid conflicts
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Initialize ChromaDB and embedding model
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("knowledge_base")
model = SentenceTransformer("all-MiniLM-L6-v2")  # Local embedding model

# Initialize Wikipedia API globally
wiki = wikipediaapi.Wikipedia(language='en', user_agent="InformationBaseApp/1.0 (+https://yourwebsite.com)")

# Function to search the vector database with stricter criteria
def search_knowledge_base(query):
    query_embedding = model.encode([query]).tolist()[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=1)

    if results["documents"] and results["distances"][0]:
        best_match = results["documents"][0][0]
        similarity_score = results["distances"][0][0]  # Lower distance = better match

        # Only return the answer if it's closely related (adjust threshold as needed)
        if similarity_score < 0.2:
            return best_match

    return None  # No relevant match found

# Function to store new knowledge in the database only if it doesn't already exist
def store_knowledge(question, answer):
    # Avoid storing duplicates and placeholder messages
    placeholder_messages = [
        "Sorry, no information found in DuckDuckGo. Try searching with other keywords or using Wikipedia.",
        "No relevant information found.",
        "An error occurred while searching DuckDuckGo.",
        "An error occurred while processing the search results from DuckDuckGo.",
        "An unexpected error occurred while searching DuckDuckGo."
    ]

    if answer not in placeholder_messages:
        existing_answer = search_knowledge_base(question)
        if existing_answer is None:
            embedding = model.encode([question]).tolist()[0]
            collection.add(documents=[answer], metadatas=[{"source": "stored"}], embeddings=[embedding], ids=[question])

# Function to search Wikipedia
def search_wikipedia(query):
    try:
        page = wiki.page(query)

        if page.exists():
            summary = page.summary
            if len(summary) < 500:  # If the summary is too short, fetch more content
                print("Wikipedia summary seems short, attempting to fetch more content.")
                content = page.content  # Fetch full content
                return trim_to_complete_sentence(content, 1000)  # Trim to complete sentence within 1000 chars

            return trim_to_complete_sentence(summary, 500)  # Trim summary within 500 chars

        return None  # No relevant Wikipedia page exists

    except wiki.exceptions.DisambiguationError as e:
        print(f"Disambiguation error: {e}")
        return "Your query is ambiguous. Please be more specific."
    except Exception as e:
        print(f"Error during Wikipedia search: {e}")
        return "An error occurred while searching Wikipedia."

# Function to search DuckDuckGo
def search_duckduckgo(query):
    print(f"Searching DuckDuckGo for: {query}")

    try:
        ddgs = DDGS()
        results = ddgs.text(query, max_results=5)  # Fetch multiple results
        if results:
            snippets = [result['body'] for result in results if 'body' in result]
            combined_snippet = ' '.join(snippets)
            if combined_snippet:
                # Trim to complete sentences
                trimmed_snippet = trim_to_complete_sentence(combined_snippet, 1000)  # Adjust length as needed
                print(f"DuckDuckGo Search Result Snippet: {trimmed_snippet}")
                return trimmed_snippet

        print("No relevant results found in DuckDuckGo response.")
        return "Sorry, no information found in DuckDuckGo. Try searching with other keywords or using Wikipedia."

    except Exception as e:
        print(f"Error during DuckDuckGo search: {e}")
        return "An error occurred while searching DuckDuckGo."

# Function to trim text to the last complete sentence within a given length
def trim_to_complete_sentence(text, max_length):
    if len(text) <= max_length:
        return text
    trimmed_text = text[:max_length]
    last_period = trimmed_text.rfind('.')
    last_exclamation = trimmed_text.rfind('!')
    last_question = trimmed_text.rfind('?')
    last_punctuation = max(last_period, last_exclamation, last_question)
    if last_punctuation == -1:
        return trimmed_text  # No punctuation found, return as is
    return trimmed_text[:last_punctuation+1]  # Include the punctuation

# Define the request model
class Question(BaseModel):
    query: str

def normalize_query(query):
    """
    Removes common question phrases to extract the core topic.
    Example: "What is cheese?" -> "cheese"
    """
    query = query.lower().strip()
    query = re.sub(r"^(what|who|define|tell me about|explain)\s+(is|are|was|were|a|an|the)?\s*", "", query)
    return query

def open_browser():
    webbrowser.open("http://127.0.0.1:8000")

# API endpoint to handle user questions
@app.post("/ask")
async def ask_question(question: Question):
    normalized_query = normalize_query(question.query)

    # Search the vector database with the normalized query
    local_answer = search_knowledge_base(normalized_query)
    if local_answer:
        print(f"Database match: {local_answer}")
        return {"answer": local_answer}

    # Search Wikipedia
    wiki_answer = search_wikipedia(normalized_query)
    if wiki_answer:
        print(f"Wikipedia match: {wiki_answer}")
        store_knowledge(normalized_query, wiki_answer)  # Store only if new
        return {"answer": wiki_answer}

    # Search DuckDuckGo
    web_answer = search_duckduckgo(normalized_query)
    if web_answer:
        print(f"DuckDuckGo match: {web_answer}")
        store_knowledge(normalized_query, web_answer)  # Store only if new
        return {"answer": web_answer}

    return {"answer": "No relevant information found."}

# Test GET endpoint to verify the application is working
@app.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint is working"}

# Run the API locally
if __name__ == "__main__":
    import uvicorn

    threading.Thread(target=lambda: uvicorn.run(app, host="127.0.0.1", port=8000)).start()
    # Open the default web browser to the URL
    open_browser()