FROM python:3

# Environment variables  
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1  

ENV HOME=/home/app/outsider 

ARG APP_HOME=/app
WORKDIR ${APP_HOME}

# Work directory  
RUN mkdir -p $HOME  
WORKDIR $HOME   

# Copy whole project to docker home directory. 
COPY . $HOME  

# Install dependencies. 
COPY requirements.txt /app
RUN pip install --upgrade pip 
RUN pip install -r requirements.txt 

# Port where the Django app runs  
# EXPOSE 8050 -> Local docker

# Start server on 15.188.198.53:8050 (Static EC2 machine IP)
CMD python manage.py makemigrations && python manage.py migrate && python manage.py runserver 15.188.198.53:8050