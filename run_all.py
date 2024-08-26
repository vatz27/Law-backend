import multiprocessing
from chatbot import app as chatbot_app
from indian_kanoon import app as indian_kanoon_app
from news import app as news_app

def run_chatbot():
    chatbot_app.run(debug=False, host='0.0.0.0', port=5000)

def run_indian_kanoon():
    indian_kanoon_app.run(debug=False, host='0.0.0.0', port=5001)

def run_news():
    news_app.run(debug=False, host='0.0.0.0', port=5002)

if __name__ == '__main__':
    processes = [
        multiprocessing.Process(target=run_chatbot),
        multiprocessing.Process(target=run_indian_kanoon),
        multiprocessing.Process(target=run_news)
    ]

    for p in processes:
        p.start()

    for p in processes:
        p.join()
