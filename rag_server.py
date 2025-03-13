from flask import Flask, request, jsonify
import requests
from duckduckgo_search import DDGS
import time

app = Flask(__name__)

def search_web_simple(query, max_results=3):
    """
    A simplified web search that only uses DuckDuckGo snippets without fetching full pages
    """
    search_results = []
    try:
        with DDGS() as ddgs:
            # Only get a few results and use just the snippets
            results = ddgs.text(query, max_results=max_results)
            
            for result in results:
                search_results.append({
                    "url": result['href'],
                    "content": result.get('body', ''),
                    "title": result.get('title', '')
                })
                
    except Exception as e:
        print(f"Search error: {str(e)}")
    
    return search_results

@app.route('/rag', methods=['POST'])
def rag():
    try:
        start_time = time.time()
        data = request.json
        if 'text_query' not in data:
            return jsonify({"error": "No text_query provided"}), 400

        query_text = data['text_query']
        
        # Simple web search
        web_results = search_web_simple(query_text, max_results=3)
        
        # Prepare content for response
        content = f"Information about: {query_text}\n\n"
        
        if web_results:
            for i, result in enumerate(web_results):
                content += f"{i+1}. {result['title']}\n"
                content += f"   {result['content']}\n"
                content += f"   Source: {result['url']}\n\n"
        else:
            content = "No specific information found on this topic."
        
        process_time = time.time() - start_time
        print(f"Processed '{query_text}' in {process_time:.2f} seconds")
        
        return jsonify({
            "content": content,
            "sources": [result['url'] for result in web_results],
            "process_time": process_time
        })

    except Exception as e:
        print(f"Error in RAG server: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting simplified RAG server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)