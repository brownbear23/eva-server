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
## Setup instructions

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
## Update instructions

If you have updated the model, run:
```
python manage.py makemigrations
python manage.py migrate
```
If you are testing locally and don't mind losing all data, reset the database:
```
python manage.py flush
```


-----
## URL info
1. Upload an image
```
curl -X POST -F "image=@path/to/your/image.jpg" http://127.0.0.1:8000/api/upload/

{
    "id": 1,
    "status": "Processing"
}
```

2. Check the Status
```
curl http://127.0.0.1:8000/api/status/102/eva1234
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




