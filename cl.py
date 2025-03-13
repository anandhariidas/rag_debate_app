import ollama
import sys
import requests
import time

def fetch_web_info(topic):
    """Simple function to get web information with a short timeout"""
    try:
        response = requests.post(
            "http://localhost:5000/rag",
            json={"text_query": topic},
            headers={"Content-Type": "application/json"},
            timeout=8  # Short timeout
        )
        
        if response.status_code == 200:
            return response.json().get("content", ""), response.json().get("sources", [])
        
    except Exception as e:
        print(f"Web search error: {str(e)}")
    
    return "", []

def debate_assistant(topic):
    """Simplified debate assistant with minimal dependencies"""
    print(f"Generating debate on: {topic}")
    
    # Get web information (optional)
    print("Searching for information...")
    web_info, sources = fetch_web_info(topic)
    
    if web_info:
        print(f"Found information from {len(sources)} sources")
        print(web_info)
    else:
        print("No web information found. Proceeding with base knowledge only.")
    
    # Prepare the prompt
    system = (
        "You are a debate assistant AI. "
        "Generate well-reasoned arguments, counterarguments, and a summary for the given topic. "
        "If provided with factual information, incorporate it to strengthen your response. "
        "Use evidence-based reasoning and logical structure."
    )
    
    # Build user message
    user_message = f"Topic: {topic}\n\n"
    if web_info:
        user_message += f"Related information:\n{web_info}\n\n"
    
    user_message += "Please provide:\n1. Brief arguments supporting this position\n2. Brief arguments against this position"
    
    # Call Ollama with the prompt
    print("Generating response...")
    try:
        response = ollama.chat(
            model='llama3.2:1b',
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user_message}
            ]
        )
        
        return response['message']['content']
    except Exception as e:
        return f"Error generating debate: {str(e)}"

if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter debate topic: ")
    
    if topic.strip():
        start = time.time()
        result = debate_assistant(topic)
        print("\nRESULT:\n")
        print(result)
        print(f"\nTotal processing time: {time.time() - start:.2f} seconds")
    else:
        print("Error: Empty topic provided.")