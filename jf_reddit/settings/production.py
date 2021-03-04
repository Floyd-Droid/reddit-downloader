from .common import *
import dj_database_url
import os
import sys

DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'jf-reddit-downloader.herokuapp.com']

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

if 'test' in sys.argv or SECRET_KEY=="travis":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        },
    }
else:
    DATABASES = {
        'default': env.db('DATABASE_URL')
    }

    DEFAULT_FILE_STORAGE = 'storage_backends.MediaStorage'

    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

    db_from_env = dj_database_url.config(conn_max_age=500)
    DATABASES['default'].update(db_from_env)
