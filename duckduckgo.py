import requests
import urllib.parse
import json

def test_duckduckgo(query):
    # URL encode the query string
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://duckduckgo.com/?q={encoded_query}&format=json&no_redirect=1&no_html=1&skip_disambig=1"

    try:
        response = requests.get(search_url)
        response.raise_for_status()  # Raise an error for bad responses (4xx/5xx)
        data = response.json()
        print(json.dumps(data, indent=4))  # Pretty print the whole response to inspect it

        # Extract the first relevant answer from the search results
        if "AbstractText" in data and data["AbstractText"]:
            snippet = data["AbstractText"]
            print(f"DuckDuckGo Search Result Snippet: {snippet}")
            return snippet

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

# Example usage
if __name__ == "__main__":
    query = "sdafstring"
    result = test_duckduckgo(query)
    print(f"Result: {result}")