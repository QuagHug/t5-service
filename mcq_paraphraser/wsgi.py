"""
WSGI config for mcq_paraphraser project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mcq_paraphraser.settings')

application = get_wsgi_application()

# Pre-load the model during application startup
from paraphraser.services.paraphraser import MCQParaphraser
print("Pre-loading ML model at application startup...")
paraphraser = MCQParaphraser()
paraphraser.load_model()
print("ML model pre-loaded successfully")
