import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'neighborhood-helper-secret-key-2024'
    
    DB_HOST = '64.83.36.96'
    DB_PORT = '53306'
    DB_USER = 'cp3b5MZxb8PVKvVpN059'
    DB_PASSWORD = 'lsTiBCoLk3cWvQKMZ4Mq'
    DB_NAME = 'ce'
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
