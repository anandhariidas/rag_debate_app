from flask import Flask, render_template, request, jsonify
import subprocess
import sys
import os

app = Flask(__name__)

# Path to the cl.py script
CL_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "cl.py")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get the topic from the form
        topic = request.form.get("topic")
        if not topic:
            return render_template("index.html", error="Please enter a debate topic.")

        # Call the debate assistant (cl.py) with the topic
        try:
            # Use subprocess to run cl.py and capture the output
            result = subprocess.run(
                [sys.executable, CL_SCRIPT_PATH, topic],
                capture_output=True,
                text=True,
                timeout=120  # Increase timeout for longer debates
            )
            
            if result.returncode != 0:
                return render_template("index.html", error=f"Error processing debate topic: {result.stderr}")

            # Extract the debate response from the output
            debate_response = result.stdout
            return render_template("index.html", topic=topic, response=debate_response)

        except subprocess.TimeoutExpired:
            return render_template("index.html", error="The debate processing took too long. Please try again with a simpler topic.")
        except Exception as e:
            return render_template("index.html", error=f"An error occurred: {str(e)}")

    # Render the form for GET requests
    return render_template("index.html")

@app.route("/health", methods=["GET"])
def health_check():
    """Simple endpoint to check if the app is running"""
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)