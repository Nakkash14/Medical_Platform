# Medical_Platform

Pour run l'application

1.créer un environnement virtuel 2. pip install -r requirements.txt INSTALLER LES DEPENDANCES

2.lancer python manage.py runserver

3.aller dans api_connect et lancer : uvicorn main:app --reload --port 8001

4.aller dans MicroService/Medical_Summirizer et lancer : python app.py (ceci devra rouler sur
localhost 5000) 5.

3.alller dans Microservice/microservice_8003Upload sur le port 8003

4.aller dans Microservice/HumanBodyAnnotationApp lancer le frontent npm start (3000) et le backend uvicorn main:app --reload --port 8080
