from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import snowflake.connector
import logging
import os
import shutil
from datetime import datetime

# Configuration de FastAPI
app = FastAPI()

# Configuration du middleware CORS pour autoriser les requêtes du frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],  # Adresse du frontend (par exemple, Django ou une autre app)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration des logs pour détecter les erreurs
logging.basicConfig(level=logging.DEBUG)

# Répertoire pour sauvegarder les fichiers localement
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Fonction pour se connecter à Snowflake
def get_snowflake_connection():
    conn = snowflake.connector.connect(
        user="PROJETRCW",
        password="Projet2024",
        account="pphdwnf-ro24832",
        role="ACCOUNTADMIN",
        warehouse="COMPUTE_WH",
        database="MED_IT_DB",
        schema="PUBLIC"
    )
    return conn

# Endpoint pour tester la connexion
@app.get("/api/test-connection")
def test_connection():
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_TIMESTAMP;")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return {"message": "Connexion réussie", "timestamp": result[0]}
    except Exception as e:
        logging.error(f"Erreur de connexion : {e}")
        raise HTTPException(status_code=500, detail="Erreur de connexion à Snowflake")

# Endpoint pour récupérer tous les utilisateurs
@app.get("/api/users")
def get_users():
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        query = "SELECT id, username, email, date_joined FROM AUTH_USER;"
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "date_joined": row[3].strftime("%Y-%m-%d %H:%M:%S")
            }
            for row in results
        ]
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des utilisateurs : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")

# Endpoint pour récupérer le profil d'un utilisateur par son ID
@app.get("/api/user-profile/{user_id}")
def get_user_profile(user_id: int):
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        query = """
        SELECT user_id, firstname, lastname, age, dob, gender, email, address, occupation, licence, speciality
        FROM MAIN_USERPROFILE
        WHERE USER_ID = %s
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        if result:
            keys = ['user_id', 'firstname', 'lastname', 'age', 'dob', 'gender', 'email', 'address', 'occupation', 'licence', 'speciality']
            return dict(zip(keys, result))
        else:
            raise HTTPException(status_code=404, detail=f"No profile found for user_id {user_id}")
    except Exception as e:
        logging.error(f"Erreur interne : {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        cursor.close()
        conn.close()

# Endpoint pour téléverser un document
@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    description: str = Form(...),
    user_id: int = Form(...)
):
    try:
        # Sauvegarder le fichier localement
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logging.info(f"Fichier téléversé : {file_path} par l'utilisateur {user_id}")

        # Enregistrer dans Snowflake
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO DOCUMENTS (USER_ID, FILE_PATH, DESCRIPTION, UPLOAD_DATE, STATUS, ORIGINAL_FILENAME)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            user_id,           # Associe l'ID utilisateur
            file_path,         # Chemin local du fichier
            description,       # Description donnée par l'utilisateur
            datetime.now(),    # Date d'upload
            "UPLOADED",        # Statut
            file.filename      # Nom original du fichier
        ))
        conn.commit()

        cursor.close()
        conn.close()

        return {"message": "Fichier téléversé avec succès", "file_path": file_path}
    except Exception as e:
        logging.error(f"Erreur lors du téléversement : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne : {e}")

# Endpoint pour récupérer les documents téléversés par un utilisateur
@app.get("/api/user-documents/{user_id}")
def get_user_documents(user_id: int):
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        query = """
        SELECT DOCUMENT_ID, FILE_PATH, DESCRIPTION, UPLOAD_DATE, STATUS, ORIGINAL_FILENAME
        FROM DOCUMENTS
        WHERE USER_ID = %s
        ORDER BY UPLOAD_DATE DESC;
        """
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return [
            {
                "document_id": row[0],
                "file_path": row[1],
                "description": row[2],
                "upload_date": row[3],
                "status": row[4],
                "original_filename": row[5]
            }
            for row in results
        ]
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des documents : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")
