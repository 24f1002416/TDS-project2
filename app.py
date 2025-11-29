"""
TDS Project 2: LLM Analysis Quiz Solver
Flask API server that receives quiz URLs and solves them using LLMs
"""

from flask import Flask, request, jsonify, render_template_string
import os
import asyncio
from dotenv import load_dotenv
from quiz_solver import QuizSolver
import logging

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
SECRET = os.getenv('SECRET_KEY', 'your-secret-here')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

quiz_solver = QuizSolver(OPENAI_API_KEY)

HOME_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>TDS Project 2 - Quiz Solver API</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .status {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
            text-align: center;
        }
        .endpoint {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .endpoint h3 {
            margin-top: 0;
            color: #667eea;
        }
        .method {
            display: inline-block;
            padding: 4px 8px;
            background: #667eea;
            color: white;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 10px;
        }
        .method.post {
            background: #28a745;
        }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }
        pre {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .test-btn {
            display: inline-block;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 10px;
            transition: background 0.3s;
        }
        .test-btn:hover {
            background: #5568d3;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 TDS Project 2</h1>
        <p class="subtitle">LLM Analysis Quiz Solver API</p>

        <div class="status">
            ✅ Server is running successfully!
        </div>

        <div class="endpoint">
            <h3><span class="method">GET</span> /health</h3>
            <p>Check if the server is running</p>
            <a href="/health" class="test-btn" target="_blank">Test Health Endpoint</a>
        </div>

        <div class="endpoint">
            <h3><span class="method post">POST</span> /quiz</h3>
            <p>Submit a quiz URL for processing</p>
            <p><strong>Required Headers:</strong></p>
            <code>Content-Type: application/json</code>

            <p style="margin-top: 15px;"><strong>Request Body:</strong></p>
            <pre>{
  "email": "your@email.com",
  "secret": "your-secret-key",
  "url": "https://quiz-url.com/quiz-123"
}</pre>

            <p><strong>Example using curl:</strong></p>
            <pre>curl -X POST http://localhost:5000/quiz \\
  -H "Content-Type: application/json" \\
  -d '{"email":"test@email.com","secret":"{{ secret }}","url":"https://tds-llm-analysis.s-anand.net/demo"}'</pre>
        </div>

        <div class="endpoint">
            <h3>📋 Available Endpoints</h3>
            <ul>
                <li><code>GET /</code> - This page</li>
                <li><code>GET /health</code> - Health check</li>
                <li><code>POST /quiz</code> - Process quiz</li>
            </ul>
        </div>

        <div class="endpoint">
            <h3>📚 Documentation</h3>
            <p>For complete documentation, see:</p>
            <ul>
                <li><strong>START_HERE.md</strong> - Quick start guide</li>
                <li><strong>README.md</strong> - Technical documentation</li>
                <li><strong>SUBMISSION_GUIDE.md</strong> - Deployment guide</li>
            </ul>
        </div>

        <div class="footer">
            <p>Built for Tools in Data Science (TDS) Course</p>
            <p>IIT Madras</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    """Home page with API documentation"""
    return render_template_string(HOME_PAGE, secret=SECRET[:10] + "...")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


@app.route('/quiz', methods=['POST'])
def handle_quiz():
    """
    Main endpoint to receive and solve quiz tasks
    Expected payload:
    {
        "email": "student@email.com",
        "secret": "secret-string",
        "url": "https://example.com/quiz-123"
    }
    """
    try:
        # Parse JSON payload
        data = request.get_json()

        if not data:
            logger.error("Invalid JSON payload")
            return jsonify({"error": "Invalid JSON"}), 400

        # Validate required fields
        email = data.get('email')
        secret = data.get('secret')
        url = data.get('url')

        if not all([email, secret, url]):
            logger.error("Missing required fields")
            return jsonify({"error": "Missing required fields: email, secret, url"}), 400

        # Verify secret
        if secret != SECRET:
            logger.error(f"Invalid secret provided: {secret}")
            return jsonify({"error": "Invalid secret"}), 403

        # Log the request
        logger.info(f"Received quiz request for: {url}")

        # Solve the quiz asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(quiz_solver.solve_quiz_chain(email, secret, url))
        loop.close()

        logger.info(f"Quiz solved successfully: {result}")

        return jsonify({
            "status": "success",
            "message": "Quiz processing started",
            "initial_url": url
        }), 200

    except Exception as e:
        logger.error(f"Error handling quiz: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
