from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Initialisation de l'application FastAPI
app = FastAPI()

# Configuration de la base de données
DATABASE_URL = "sqlite:///./dpe_analysis.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modèle pour les DPE enregistrés
class DPE(Base):
    __tablename__ = "dpe_data"
    id = Column(Integer, primary_key=True, index=True)
    numero_dpe = Column(String, unique=True, index=True)
    adresse = Column(String)
    surface = Column(Float)
    chauffage = Column(String)
    isolation = Column(String)
    dpe_note = Column(String)
    consommation_energie = Column(Float)

# Modèle pour les travaux et leur coût estimé
class Travaux(Base):
    __tablename__ = "travaux"
    id = Column(Integer, primary_key=True, index=True)
    type_travaux = Column(String, index=True)
    impact_dpe = Column(Float)
    cout_moyen = Column(Float)
    reduction_consommation = Column(Float)

# Création des tables
Base.metadata.create_all(bind=engine)

# Modèle Pydantic pour les requêtes
class DPECreate(BaseModel):
    numero_dpe: str
    adresse: str
    surface: float
    chauffage: str
    isolation: str
    dpe_note: str
    consommation_energie: float

class TravauxCreate(BaseModel):
    type_travaux: str
    impact_dpe: float
    cout_moyen: float
    reduction_consommation: float

# Dépendance pour la session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Route pour enregistrer un DPE
@app.post("/dpe/")
def create_dpe(dpe: DPECreate, db: Session = Depends(get_db)):
    db_dpe = DPE(**dpe.dict())
    db.add(db_dpe)
    db.commit()
    db.refresh(db_dpe)
    return db_dpe

# Route pour récupérer un DPE
@app.get("/dpe/{numero_dpe}")
def get_dpe(numero_dpe: str, db: Session = Depends(get_db)):
    dpe = db.query(DPE).filter(DPE.numero_dpe == numero_dpe).first()
    if not dpe:
        raise HTTPException(status_code=404, detail="DPE non trouvé")
    return dpe

# Route pour enregistrer un travail
@app.post("/travaux/")
def create_travaux(travaux: TravauxCreate, db: Session = Depends(get_db)):
    db_travaux = Travaux(**travaux.dict())
    db.add(db_travaux)
    db.commit()
    db.refresh(db_travaux)
    return db_travaux

# Route pour récupérer tous les travaux
@app.get("/travaux/")
def get_travaux(db: Session = Depends(get_db)):
    travaux = db.query(Travaux).all()
    return travaux

# Route pour estimer une amélioration DPE avec les règles 3CL 2021
@app.get("/estimation/{numero_dpe}")
def estimate_dpe(numero_dpe: str, db: Session = Depends(get_db)):
    dpe = db.query(DPE).filter(DPE.numero_dpe == numero_dpe).first()
    if not dpe:
        raise HTTPException(status_code=404, detail="DPE non trouvé")
    
    travaux = db.query(Travaux).all()
    reduction_totale = sum([t.reduction_consommation for t in travaux])
    nouvelle_conso = max(0, dpe.consommation_energie - reduction_totale)
    
    # Conversion en notation DPE simplifiée (à ajuster selon les normes exactes)
    if nouvelle_conso < 50:
        dpe_potentiel = "A"
    elif nouvelle_conso < 90:
        dpe_potentiel = "B"
    elif nouvelle_conso < 150:
        dpe_potentiel = "C"
    elif nouvelle_conso < 210:
        dpe_potentiel = "D"
    elif nouvelle_conso < 250:
        dpe_potentiel = "E"
    elif nouvelle_conso < 330:
        dpe_potentiel = "F"
    else:
        dpe_potentiel = "G"
    
    return {
        "numero_dpe": numero_dpe,
        "dpe_actuel": dpe.dpe_note,
        "consommation_actuelle": dpe.consommation_energie,
        "consommation_estimee": nouvelle_conso,
        "dpe_potentiel": dpe_potentiel
    }
