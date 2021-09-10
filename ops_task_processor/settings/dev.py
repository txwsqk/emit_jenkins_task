from ops_task_processor.settings.base import *

DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'task_processor',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': '192.168.12.94',
        'PORT': 3306,
    }
}
