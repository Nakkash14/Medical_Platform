from app.database import engine
from app.models import Base

# Supprimer toutes les tables
Base.metadata.drop_all(bind=engine)

# Recréer les tables
Base.metadata.create_all(bind=engine)

print("Base de données réinitialisée.")
