# Information Base API

This project implements a FastAPI-based application that provides an information retrieval system using DuckDuckGo, Wikipedia, and a local knowledge base powered by ChromaDB and Sentence Transformers. The application serves a web interface and processes user queries to return relevant information.

## Features

- **DuckDuckGo Search**: Retrieves information from DuckDuckGo search results.
- **Wikipedia Search**: Retrieves information from Wikipedia.
- **Local Knowledge Base**: Stores and retrieves information locally using ChromaDB and Sentence Transformers.
- **Web Interface**: Serves a web interface to interact with the API.
- **Automatic Web Browser Launch**: Automatically opens the web interface in the default web browser when the application starts.

## Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/Tsuchai/informationbase.git
   cd information-base-api
   ```

2. **Install dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application (Make sure you are in the proper directory)**:
   ```sh
   python main.py
   ```



2. **Access the web interface**:
   The application will automatically open the web interface in your default web browser at `http://127.0.0.1:8000/static/`.

## API Endpoints

### `/ask` (POST)
- **Description**: Handles user questions and returns relevant information from DuckDuckGo, Wikipedia, or the local knowledge base.
- **Request Body**:
  ```json
  {
      "query": "string"
  }
  ```
- **Response**:
  ```json
  {
      "answer": "string"
  }
  ```

## Code Overview

### Initialization
- **FastAPI**: Initializes the FastAPI application.
- **Static Files**: Serves the `index.html` file from the `static` directory.
- **ChromaDB**: Initializes the ChromaDB client and collection.
- **Sentence Transformer**: Loads the local embedding model.
- **Wikipedia API**: Initializes the Wikipedia API client.

### Functions
- **search_knowledge_base**: Searches the local knowledge base for relevant information.
- **store_knowledge**: Stores new knowledge in the database if it doesn't already exist.
- **search_wikipedia**: Searches Wikipedia for relevant information.
- **search_duckduckgo**: Searches DuckDuckGo for relevant information.
- **trim_to_complete_sentence**: Trims text to the last complete sentence within a given length.
- **normalize_query**: Normalizes the user query by removing common question phrases.
- **open_browser**: Opens the default web browser to the specified URL.

### API Endpoint
- **/ask**: Handles user questions and returns relevant information from DuckDuckGo, Wikipedia, or the local knowledge base.
