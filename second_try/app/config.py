import os
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    return {
        'BOT_TOKEN': os.getenv('BOT_TOKEN'),
        'ADMIN_CHAT_ID': os.getenv('ADMIN_CHAT_ID')
    }