from bs4 import BeautifulSoup
from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import requests
import wikipediaapi
import re

# Initialize FastAPI
app = FastAPI()

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

        # Only return the answer if it's **closely** related (adjust threshold as needed)
        if similarity_score < 0.2:
            return best_match

    return None  # No relevant match found


# Function to store new knowledge in the database **only if it doesn't already exist**
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
    page = wiki.page(query)
    if page.exists():
        return page.summary[:500]  # Return first 500 characters for brevity
    return None  # Return None if no relevant Wikipedia page exists


# Function to search DuckDuckGo
def search_duckduckgo(query):
    print(f"Searching DuckDuckGo for: {query}")

    # DuckDuckGo Instant Answer API URL (JSON format)
    search_url = f"https://api.duckduckgo.com/?q={query}&format=json"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx/5xx)

        data = response.json()
        print(f"DuckDuckGo API Response: {data}")  # Print the whole response to inspect it

        # Log the entire response for debugging
        with open("duckduckgo_response.log", "w") as log_file:
            log_file.write(str(data))

        # If the API returns an abstract text, return it
        if "AbstractText" in data and data["AbstractText"]:
            abstract_text = data["AbstractText"]
            print(f"DuckDuckGo Web Search Result (AbstractText): {abstract_text}")
            return abstract_text

        # Check if there are search result links available
        if "Results" in data and data["Results"]:
            for result in data["Results"]:
                if "Text" in result:
                    print(f"Found result in 'Results': {result['Text']}")
                    return result["Text"]

        # If no relevant results found, check for related topics
        if "RelatedTopics" in data and data["RelatedTopics"]:
            for topic in data["RelatedTopics"]:
                if isinstance(topic, dict) and "Text" in topic:
                    print(f"Found related topic: {topic['Text']}")
                    return topic["Text"]

        # Fallback if no useful results found
        print("No relevant results found in DuckDuckGo response.")
        return "Sorry, no information found in DuckDuckGo. Try searching with other keywords or using Wikipedia."
    except requests.RequestException as e:
        print(f"Error during DuckDuckGo search: {e}")
        return "An error occurred while searching DuckDuckGo."
    except ValueError as e:
        print(f"Error parsing DuckDuckGo response: {e}")
        return "An error occurred while processing the search results from DuckDuckGo."
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "An unexpected error occurred while searching DuckDuckGo."

    except requests.RequestException as e:
        print(f"Error during DuckDuckGo search: {e}")
        return "An error occurred while searching DuckDuckGo."
    except ValueError as e:
        print(f"Error parsing DuckDuckGo response: {e}")
        return "An error occurred while processing the search results from DuckDuckGo."
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "An unexpected error occurred while searching DuckDuckGo."


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


# Run the API locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)