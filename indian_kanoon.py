from flask import Flask, request, jsonify
import requests
from requests.exceptions import RequestException
import os
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get the API key from environment variables
indiankanoon_api_key = os.getenv('INDIANKANOON_API_KEY')

if not indiankanoon_api_key:
    raise ValueError("INDIANKANOON_API_KEY is not set in the environment variables")

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    result = search_indiankanoon(query)
    if 'error' in result:
        return jsonify(result), 500

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
            "sortby": "mostrecent",  # Sort by most recent
            "filter": "docs",  # Filter to get only documents (acts, judgments, etc.)
            "format": "json"
        }
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Error searching Indian Kanoon: {str(e)}")
        return {'error': 'Failed to search Indian Kanoon', 'details': str(e)}

@app.route('/api/indiankanoon/details/<docid>', methods=['GET'])
def get_document_details(docid):
    try:
        # Fetch document details
        doc_url = f"https://api.indiankanoon.org/doc/{docid}/"
        headers = {
            "Authorization": f"Token {indiankanoon_api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        doc_response = requests.post(doc_url, headers=headers)
        doc_response.raise_for_status()
        doc_data = doc_response.json()

        # Fetch document metadata
        meta_url = f"https://api.indiankanoon.org/docmeta/{docid}/"
        meta_response = requests.post(meta_url, headers=headers)
        meta_response.raise_for_status()
        meta_data = meta_response.json()

        # Combine the data
        combined_data = {
            'title': meta_data.get('title', ''),
            'court': meta_data.get('court', ''),
            'judges': meta_data.get('judges', ''),
            'date_of_judgment': meta_data.get('date_of_judgment', ''),
            'case_number': meta_data.get('case_number', ''),
            'petitioner': meta_data.get('petitioner', ''),
            'respondent': meta_data.get('respondent', ''),
            'summary': doc_data.get('excerpt', ''),
            'full_judgment': doc_data.get('doc', ''),
            'href': f"https://indiankanoon.org/doc/{docid}/"
        }

        return jsonify(combined_data)
    except RequestException as e:
        print(f"Error fetching document details from Indian Kanoon: {str(e)}")
        return jsonify({'error': 'Failed to fetch document details from Indian Kanoon', 'details': str(e)}), 500
    except Exception as e:
        print(f"Unexpected error fetching document details: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

@app.route('/api/indiankanoon/court_copy/<docid>', methods=['GET'])
def get_court_copy(docid):
    try:
        url = f"https://api.indiankanoon.org/origdoc/{docid}/"
        headers = {
            "Authorization": f"Token {indiankanoon_api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except RequestException as e:
        print(f"Error fetching court copy from Indian Kanoon: {str(e)}")
        return jsonify({'error': 'Failed to fetch court copy from Indian Kanoon', 'details': str(e)}), 500
    except Exception as e:
        print(f"Unexpected error fetching court copy: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
