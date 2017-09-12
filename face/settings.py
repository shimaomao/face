import os

mongo = dict(
    host = os.environ.get('MONGO_HOST', 'localhost'),
    port = os.environ.get('MONGO_PORT', 27017),
    db = os.environ.get('MONGO_DATABASE', 'bm-platform')
)
