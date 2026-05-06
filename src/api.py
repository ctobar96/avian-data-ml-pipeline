# Agrega estos imports al inicio de tu api.py
from sqlalchemy.orm import sessionmaker
from database import engine
from models_db import ProduccionAlimento

# Creamos el generador de sesiones para hablar con Supabase
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==============================================================================
# NUEVO ENDPOINT: Buscador de Lotes
# ==============================================================================
@app.get("/buscar-lote/")
def buscar_lote(lote: str, fecha: str):
    # Abrimos una sesión temporal con la base de datos
    db = SessionLocal()
    
    try:
        # 1. Buscamos el Lote Padre
        produccion = db.query(ProduccionAlimento).filter(
            ProduccionAlimento.lote_destino == lote,
            ProduccionAlimento.fecha_efectiva == fecha
        ).first() # .first() trae el primer resultado que coincida

        # 2. Si no existe, devolvemos un error amigable
        if not produccion:
            return {"status": "error", "message": "No se encontraron registros para este lote y fecha."}

        # 3. Si existe, armamos el JSON con el Padre y sus Hijos (Macros y Micros)
        return {
            "status": "success",
            "produccion": {
                "lote": produccion.lote_destino,
                "fecha": str(produccion.fecha_efectiva),
                "descripcion": produccion.descripcion,
                "cantidad_kg": produccion.cantidad_kg
            },
            "macros": [{"Materia Prima": m.materia_prima, "Cantidad (Kg)": m.cantidad_consumida} for m in produccion.macros],
            "micros": [{"Materia Prima": m.materia_prima, "Cantidad (Kg)": m.cantidad_consumida} for m in produccion.micros]
        }
        
    finally:
        # SIEMPRE cerramos la conexión para no saturar el Pooler
        db.close()
        
        
