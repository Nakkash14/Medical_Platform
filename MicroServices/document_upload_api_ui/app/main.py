from fastapi import FastAPI, UploadFile, File, Form, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import Base, Upload
from pydantic import BaseModel
import os
import logging
import uuid
from pathlib import Path

# Initialisation de l'application FastAPI
app = FastAPI()

# Configuration du middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000", "http://127.0.0.1:8003", "http://localhost:8003" ],  # Origines autorisées
    allow_credentials=True,
    allow_methods=["*"],  # Autorise toutes les méthodes HTTP
    allow_headers=["*"],  # Autorise tous les en-têtes
)

# Configuration des templates et des fichiers statiques
templates = Jinja2Templates(directory="app/templates")
UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configuration du logger
logging.basicConfig(level=logging.INFO)

# Extensions autorisées
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}

# Dépendance pour la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Création des tables dans la base de données
Base.metadata.create_all(bind=engine)

# Stockage temporaire des données utilisateur (en mémoire)
user_data_store = []

# Modèle Pydantic pour valider les données utilisateur
class UserData(BaseModel):
    user_id: int
    username: str
    email: str
    occupation: str

# Route de test
@app.get("/")
async def read_root(request: Request):
    """
    Rendu du formulaire d'upload sur la page principale.
    """
    return templates.TemplateResponse("index.html", {"request": request})

# Endpoint GET pour afficher les données utilisateur reçues
@app.get("/upload-user-data")
async def get_uploaded_user_data():
    """
    Retourne les données utilisateur qui ont été envoyées via POST.
    """
    if not user_data_store:
        return {"message": "Aucune donnée utilisateur n'a été envoyée."}
    return {"message": "Données utilisateur envoyées", "data": user_data_store}

# Endpoint POST pour recevoir les données utilisateur
@app.post("/upload-user-data")
async def upload_user_data(user_data: UserData):
    """
    Reçoit les données utilisateur envoyées en JSON depuis une autre application.
    """
    try:
        logging.info(f"Données reçues : {user_data}")
        # Stocke les données reçues dans la mémoire temporaire
        user_data_store.append(user_data.dict())
        return {"message": "Données reçues avec succès", "data": user_data.dict()}
    except Exception as e:
        logging.error(f"Erreur lors de la réception des données : {e}")
        return JSONResponse({"error": f"Une erreur est survenue : {e}"}, status_code=500)

# Endpoint pour uploader des fichiers
@app.post("/upload/")
async def upload_file(
    name: str = Form(...),
    description: str = Form(...),
    document: UploadFile = File(...),
    image: UploadFile = File(...),
    user_id: int = Form(None),
    db: Session = Depends(get_db),
):
    """
    Gère l'upload de fichiers (documents et images).
    """
    try:
        # Vérification des formats autorisés
        doc_ext = Path(document.filename).suffix.lower()
        img_ext = Path(image.filename).suffix.lower()

        if doc_ext not in ALLOWED_DOCUMENT_EXTENSIONS:
            return JSONResponse(
                {"error": f"Format invalide pour le document : {document.filename}. Formats autorisés : {', '.join(ALLOWED_DOCUMENT_EXTENSIONS)}"},
                status_code=422,
            )
        if img_ext not in ALLOWED_IMAGE_EXTENSIONS:
            return JSONResponse(
                {"error": f"Format invalide pour l'image : {image.filename}. Formats autorisés : {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"},
                status_code=422,
            )

        # Génération de noms uniques
        unique_doc_name = f"{uuid.uuid4().hex}_{document.filename}"
        unique_img_name = f"{uuid.uuid4().hex}_{image.filename}"

        document_path = os.path.join(UPLOAD_FOLDER, unique_doc_name)
        image_path = os.path.join(UPLOAD_FOLDER, unique_img_name)

        # Enregistrer les fichiers
        with open(document_path, "wb") as doc_file:
            doc_file.write(await document.read())
        with open(image_path, "wb") as img_file:
            img_file.write(await image.read())

        # Enregistrer dans la base de données (si user_id est fourni)
        upload = Upload(
            name=name,
            description=description,
            document_path=f"/uploads/{unique_doc_name}",
            image_path=f"/uploads/{unique_img_name}",
        )
        if user_id:
            upload.user_id = user_id
        db.add(upload)
        db.commit()
        db.refresh(upload)

        logging.info(f"Upload réussi : {name}, {unique_doc_name}, {unique_img_name}")
        return {"message": "Fichiers uploadés avec succès !", "upload_id": upload.id}
    except Exception as e:
        logging.error(f"Erreur : {e}")
        return JSONResponse({"error": f"Une erreur est survenue : {e}"}, status_code=500)

# Endpoint pour lister les uploads
@app.get("/uploads")
def list_uploads(request: Request, db: Session = Depends(get_db)):
    """
    Liste les fichiers uploadés par utilisateur.
    """
    uploads = db.query(Upload).all()

    if not uploads:
        return templates.TemplateResponse("list.html", {"request": request, "uploads_by_user": {}, "message": "Aucun fichier uploadé."})

    uploads_by_user = {}
    for upload in uploads:
        if upload.name not in uploads_by_user:
            uploads_by_user[upload.name] = []
        uploads_by_user[upload.name].append(upload)

    return templates.TemplateResponse("list.html", {"request": request, "uploads_by_user": uploads_by_user})

@app.get("/get-username/{user_id}")
async def get_username(user_id: int):
    """
    Récupère le nom d'utilisateur associé à un user_id.
    """
    # Parcourt les données reçues pour trouver l'utilisateur correspondant
    for user in user_data_store:
        if user["user_id"] == user_id:
            return {"username": user["username"]}
    
    # Si aucun utilisateur n'est trouvé
    return JSONResponse({"error": "Utilisateur non trouvé"}, status_code=404)
