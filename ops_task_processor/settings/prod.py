from ops_task_processor.settings.base import *

import os

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('TASK_DATABASE_NAME', ''),
        'USER': os.environ.get('TASK_DATABASE_USER', ''),
        'PASSWORD': os.environ.get('TASK_DATABASE_PASSWORD', ''),
        'HOST': os.environ.get('TASK_DATABASE_HOST', ''),
        'PORT': os.environ.get('TASK_DATABASE_PORT', ''),
    }
}