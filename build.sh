#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py migrate

python manage.py shell << 'EOF'
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

if username and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print("Superusuario creado")
    else:
        print("Superusuario ya existe")
else:
    print("Variables de entorno no definidas")
EOF
