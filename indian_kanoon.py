from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
from requests.exceptions import RequestException

app = Flask(__name__)
CORS(app)

load_dotenv()

indiankanoon_api_key = os.getenv("INDIANKANOON_API_KEY")

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    result = search_indiankanoon(query)
    return jsonify(result)

def search_indiankanoon(query):
    try:
        url = "https://api.indiankanoon.org/search/"
        headers = {
            "Authorization": f"Token {indiankanoon_api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "formInput": query,
            "pagenum": 0,
            "format": "json"
        }
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Error searching Indian Kanoon: {str(e)}")
        return {'error': 'Failed to search Indian Kanoon', 'details': str(e)}

@app.route('/api/indiankanoon/document/<docid>', methods=['GET'])
def get_indiankanoon_document(docid):
    try:
        url = f"https://api.indiankanoon.org/doc/{docid}/"
        headers = {"Authorization": f"Token {indiankanoon_api_key}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        print(f"Error fetching document from Indian Kanoon: {str(e)}")
        return jsonify({'error': 'Failed to fetch document from Indian Kanoon'}), 500

@app.route('/api/indiankanoon/docfragment/<docid>', methods=['GET'])
def get_indiankanoon_docfragment(docid):
    query = request.args.get('query', '')
    try:
        url = f"https://api.indiankanoon.org/docfragment/{docid}/?formInput={query}"
        headers = {"Authorization": f"Token {indiankanoon_api_key}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        print(f"Error fetching document fragment from Indian Kanoon: {str(e)}")
        return jsonify({'error': 'Failed to fetch document fragment from Indian Kanoon'}), 500

def run():
    app.run(debug=True, host='0.0.0.0', port=5001)

