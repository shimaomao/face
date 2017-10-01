import os

mongo = dict(
    uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/bm-platform')
)
