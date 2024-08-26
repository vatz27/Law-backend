from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

app = Flask(__name__)
CORS(app)

load_dotenv()

news_api_key = os.getenv("NEWS_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

chat = ChatOpenAI(api_key=openai_api_key)
system_template = """As an expert Legal Advisor specializing in Indian law, your role is to provide accurate, comprehensive, and nuanced responses to legal inquiries. Utilize your extensive knowledge of Indian jurisprudence, including statutes, case law, and legal principles to formulate your answers."""

human_template = "Query: {question}"

system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

def fetch_news(sources, query=None, country=None):
    all_articles = []
    one_month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    for source in sources:
        url = 'https://newsapi.org/v2/everything' if query else 'https://newsapi.org/v2/top-headlines'
        params = {
            'apiKey': news_api_key,
            'language': 'en',
            'from': one_month_ago,
            'sortBy': 'publishedAt',
        }
        if query:
            params['q'] = query
        if country:
            params['country'] = country
        if source:
            params['sources'] = source

        response = requests.get(url, params=params)
        news_data = response.json()
        articles = news_data.get('articles', [])
        all_articles.extend(articles)

    processed_articles = []
    for article in all_articles:
        processed_article = {
            'title': article.get('title', ''),
            'description': article.get('description', ''),
            'content': article.get('content', ''),
            'url': article.get('url', ''),
            'urlToImage': article.get('urlToImage', ''),
            'publishedAt': article.get('publishedAt', ''),
            'source': article.get('source', {}).get('name', '')
        }
        processed_articles.append(processed_article)
    
    processed_articles.sort(key=lambda x: x['publishedAt'], reverse=True)
    return processed_articles

@app.route('/api/news/general', methods=['GET'])
def get_general_news():
    try:
        sources = ['the-times-of-india', 'the-hindu', 'bbc-news', 'cnn', 'reuters']
        articles = fetch_news(sources)
        return jsonify({'articles': articles})
    except Exception as e:
        print(f"Error fetching general news: {str(e)}")
        return jsonify({'error': 'Failed to fetch general news'}), 500

@app.route('/api/news/south-india', methods=['GET'])
def get_south_india_news():
    try:
        sources = ['the-hindu', 'the-times-of-india']
        articles = fetch_news(sources, query='(Tamil Nadu OR Kerala OR Karnataka OR Andhra Pradesh OR Telangana)')
        return jsonify({'articles': articles})
    except Exception as e:
        print(f"Error fetching South India news: {str(e)}")
        return jsonify({'error': 'Failed to fetch South India news'}), 500

@app.route('/api/news/india', methods=['GET'])
def get_india_news():
    try:
        articles = fetch_news(sources=None, country='in')
        return jsonify({'articles': articles})
    except Exception as e:
        print(f"Error fetching India news: {str(e)}")
        return jsonify({'error': 'Failed to fetch India news'}), 500

@app.route('/api/news/world', methods=['GET'])
def get_world_news():
    try:
        sources = ['bbc-news', 'cnn', 'reuters']
        articles = fetch_news(sources)
        return jsonify({'articles': articles})
    except Exception as e:
        print(f"Error fetching world news: {str(e)}")
        return jsonify({'error': 'Failed to fetch world news'}), 500

@app.route('/api/news/<int:article_id>', methods=['GET'])
def get_article_details(article_id):
    try:
        articles = fetch_news(['the-times-of-india', 'the-hindu', 'bbc-news', 'cnn', 'reuters'])

        if article_id < len(articles):
            article = articles[article_id]
            
            analysis_prompt = f"""Provide a detailed analysis of the following news article:

            Title: {article['title']}
            Description: {article['description']}
            Content: {article['content']}

            Please include:
            1. A summary of the article
            2. Key points and their implications
            3. Background information on the topic
            4. Potential future developments
            5. Related articles or resources for further reading
            """

            messages = chat_prompt.format_messages(question=analysis_prompt)
            result = chat(messages)
            detailed_analysis = result.content

            article['detailed_analysis'] = detailed_analysis

            return jsonify(article)
        else:
            return jsonify({'error': 'Article not found'}), 404

    except Exception as e:
        print(f"Error fetching article details: {str(e)}")
        return jsonify({'error': 'Failed to fetch article details'}), 500

def run():
    app.run(debug=True, host='0.0.0.0', port=5002)

if __name__ == '__main__':
    run()
