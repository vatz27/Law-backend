import threading
import chatbot
import indian_kanoon
import news

def run_all():
    chatbot_thread = threading.Thread(target=chatbot.run)
    indian_kanoon_thread = threading.Thread(target=indian_kanoon.run)
    news_thread = threading.Thread(target=news.run)

    chatbot_thread.start()
    indian_kanoon_thread.start()
    news_thread.start()

    chatbot_thread.join()
    indian_kanoon_thread.join()
    news_thread.join()

if __name__ == '__main__':
    run_all()
