FROM python:3.10-slim
WORKDIR /app
RUN pip install django==4.2.0
RUN django-admin startproject myproject .
ENV DJANGO_SETTINGS_MODULE=myproject.settings
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]