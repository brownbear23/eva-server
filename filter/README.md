filter/README.md

-----
## Architecture - MVT 
Model: Just like the Model explanation in the MVC pattern , this also takes the same position as the 
interface or relationship between the data and contains everything related to data access and validation.

Template: This relates to the View in the MVC pattern as it is the presentation layer that handles the 
presentation logic in the framework and basically controls what should be displayed and how it should be 
displayed to the user.

View: This part relates to the Controller in the MVC pattern and handles all the business logic that throws 
down back to the respective templates.It serves as the bridge between the model and the template.

MVC vs MVT
Model - Model
View - Template
Controller - View 

Although this is an API server, a template is implemented for testing purpose

Current: RESTful API
Stateless, Uses Standard HTTP, Client-Server Architecture
-----
## Server setup instructions (Ubuntu)

We use Systemd for background running of Django and Celery.

0. Use Virtual Environment & Tun migrate to create the default Django tables
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
```

1. Download redis, Run Redis, Check whether redis is running
```
#Checking redis running
redis-cli ping
# You should get back
PONG
````

2.1 Create a systemd service for Django
```
sudo vim /etc/systemd/system/django.service
```
```
[Unit]
Description=EVA Django Application
After=network.target

[Service]
User=bitnami
Group=bitnami
WorkingDirectory=/home/bitnami/eva-server
Environment="PATH=/home/bitnami/eva-server/.venv/bin"

# Run migrations before starting the app
ExecStartPre=/home/bitnami/eva-server/.venv/bin/python3 manage.py migrate --noinput

# Collect static files before starting the app
ExecStartPre=/home/bitnami/eva-server/.venv/bin/python3 manage.py collectstatic --noinput

# Start the Django development server
ExecStart=/home/bitnami/eva-server/.venv/bin/python3 manage.py runserver 0.0.0.0:8000

Restart=always

[Install]
WantedBy=multi-user.target
```

2.2 Create a systemd service for Celery
```
sudo vim /etc/systemd/system/celery.service
```
```
[Unit]
Description=Celery Worker
After=network.target django.service

[Service]
User=bitnami
Group=bitnami
WorkingDirectory=/home/bitnami/eva-server
Environment="PATH=/home/bitnami/eva-server/.venv/bin"
ExecStart=/home/bitnami/eva-server/.venv/bin/celery -A config worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```
3. Reload systemd and Start Services
```
# In case systemd is updated
sudo systemctl daemon-reexec

# Reload systemd to recognize new services
sudo systemctl daemon-reload

# Start services
sudo systemctl start django
sudo systemctl start celery

# Enable services to start on boot
sudo systemctl enable django
sudo systemctl enable celery
```

4. Check Service Status
Verify if services are running correctly:
```
sudo systemctl status django
sudo systemctl status celery
```
If any service fails, check logs:
```
journalctl -u django --no-pager --lines=50
journalctl -u celery --no-pager --lines=50
```

5. Manage Services
```
# Restart services
sudo systemctl restart django
sudo systemctl restart celery

# Stop services
sudo systemctl stop django
sudo systemctl stop celery
```

(6. Installing dependencies)
```
# To export pip dependencies from the local:
pip3 freeze > requirements.txt

#To import the dependencies to the new server:
pip3 install -r requirements.txt
```

-----
## Local setup instructions (Mac)

1. Start redis for celery
```
brew services start redis 
brew services stop redis
```
2. Start Django server
```
python manage.py runserver 0.0.0.0:8000
```
3. Start celery
```
celery -A config worker --loglevel=info
```
Within the same network, you can test filter app with:
```
http://{your-ip}:8000/filter/
```

-----
## Update code instructions

If you have updated the model, run:
```
python manage.py makemigrations
python manage.py migrate
```
If you are testing locally and don't mind losing all data, reset the database:
```
python manage.py flush
```
To gather all the static files, run:
```
python manage.py collectstatic 
```
Creating super user:
```
python manage.py createsuperuser
```


-----
## URL info
1. Upload an image
```
curl -X POST -F "image=@path/to/your/image.jpg" http://127.0.0.1:8000/upload/

{
    "id": 1,
    "status": "Processing"
}
```

2. Check the Status
```
curl http://127.0.0.1:8000/status/<int:image_id>/
{
    "id": 1,
    "status": "Processing"
}

or 

{
    "id": 1,
    "status": "Filtered",
    "filtered_image_url": "/media/filtered/image.jpg"
}
```




