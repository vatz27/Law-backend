from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from werkzeug.utils import secure_filename
import PyPDF2
import docx
import tempfile

app = Flask(__name__)
CORS(app)

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
indian_kanoon_api_key = os.getenv("INDIAN_KANOON_API_KEY")

chat = ChatOpenAI(api_key=openai_api_key)

system_template = """As a highly qualified Legal Advisor specializing in Indian law, your role is to provide expert, accurate, and comprehensive responses to legal inquiries. Utilize your extensive knowledge of Indian jurisprudence, including statutes, case law, and legal principles to formulate your answers. When responding:

1. Conduct a thorough analysis of the query to identify key legal issues and relevant areas of law.
2. Provide clear, concise explanations of applicable laws, acts, and legal concepts, citing specific sections where appropriate.
3. Reference relevant case precedents and judicial pronouncements, including citations and brief summaries of their significance.
4. Offer insights into potential legal strategies or courses of action, considering both short-term and long-term implications.
5. Explain the practical applications of the law in the context of the query, including any potential challenges or considerations.
6. Highlight any ambiguities, areas of legal debate, or recent developments in the law that may impact the situation.
7. Where applicable, mention any relevant statutes of limitations or procedural requirements.
8. Conclude with a succinct summary of key points, critical information, and recommended next steps if appropriate.

Your responses should be authoritative, insightful, and actionable, enhancing the user's understanding of their legal situation. Maintain a professional and objective tone throughout your response, and ensure all information provided is up-to-date and accurately reflects current Indian law."""

human_template = "Query: {question}\n\nRelevant Indian Kanoon Information: {kanoon_info}"

system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file):
    filename = secure_filename(file.filename)
    file_extension = filename.rsplit('.', 1)[1].lower()
    
    if file_extension == 'pdf':
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    elif file_extension in ['doc', 'docx']:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            file.save(temp_file.name)
            doc = docx.Document(temp_file.name)
            text = "\n".join([para.text for para in doc.paragraphs])
        os.unlink(temp_file.name)
    elif file_extension == 'txt':
        text = file.read().decode('utf-8')
    else:
        raise ValueError("Unsupported file format")
    
    return text

def fetch_indian_kanoon_info(query):
    url = "https://api.indiankanoon.org/search/"
    params = {
        "formInput": query,
        "filter": "on",
        "pagenum": 1
    }
    headers = {
        "Authorization": f"Token {indian_kanoon_api_key}"
    }
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        # Extract relevant information from the API response
        relevant_info = []
        for doc in data.get('docs', [])[:3]:  # Limit to top 3 results
            title = doc.get('title', '')
            snippet = doc.get('snippet', '')
            relevant_info.append(f"Title: {title}\nSnippet: {snippet}\n")
        
        return "\n".join(relevant_info)
    else:
        return "Unable to fetch information from Indian Kanoon API."

@app.route('/chat', methods=['POST'])
def chatbot():
    data = request.json
    question = data.get('message')

    if not question:
        return jsonify({'error': 'No message provided'}), 400

    try:
        kanoon_info = fetch_indian_kanoon_info(question)
        
        messages = chat_prompt.format_messages(question=question, kanoon_info=kanoon_info)
        result = chat(messages)
        response = result.content

        return jsonify({'response': response})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-document', methods=['POST'])
def analyze_document():
    if 'document' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['document']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        try:
            document_text = extract_text_from_file(file)
            
            kanoon_info = fetch_indian_kanoon_info(document_text[:500])  # Use first 500 characters for API query
            
            analysis_prompt = f"""Analyze the following legal document and provide a comprehensive summary, highlighting relevant legal sections:

            Document Content:
            {document_text}

            Relevant Indian Kanoon Information:
            {kanoon_info}

            Please provide:
            1. A concise summary of the document's content and purpose
            2. Key legal points or sections, with references to specific laws or regulations
            3. Relevant laws, regulations, or case law mentioned or applicable
            4. Potential legal implications or actions to consider
            5. Any areas of ambiguity or potential legal challenges
            6. Recommendations for further legal review or action, if necessary"""
            
            messages = chat_prompt.format_messages(question=analysis_prompt, kanoon_info=kanoon_info)
            result = chat(messages)
            analysis = result.content
            
            return jsonify({'analysis': analysis})
        
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file format'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
