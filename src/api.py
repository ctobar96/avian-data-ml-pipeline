# importaciones
from fastapi import FastAPI, UploadFile, File
import pandas as pd
import io
from sqlalchemy.orm import sessionmaker
from src.database import engine
from src.models_db import ProduccionAlimento, ConsumoInsumosMacros, ConsumoInsumosMicros

# 1. Configuración de FastAPI y Base de Datos
app = FastAPI(title="Avian Data API", version="1.0")
# Creamos el generador de sesiones para hablar con Supabase
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==============================================================================
# ENDPOINT 1: PROCESAR EXCEL Y GUARDAR EN SUPABASE
# ==============================================================================
@app.post("/cargar-excel/")
async def cargar_excel(file: UploadFile = File(...)):
    db = SessionLocal() # Abrimos una sesión temporal con la base de datos
    try:
        # 1. Leemos el archivo Excel en memoria
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), sheet_name='Datos')

        
        # --- EL TRUCO DE INGENIERÍA DE DATOS ---
        # Rellenamos hacia abajo los lotes vacíos para que los insumos sepan a quién pertenecen
        df['Lote_Asignado'] = df['Lote/Serie'].ffill()
        
        # Filtramos solo la creación del Alimento (Cabeceras)
        df_padres = df[(df['Tipo Trans'] == 'RCT-WO') & (df['Lín Producto'] == 15)]

        lotes_guardados = 0
        
        # iteramos por cada lote de alimento creado
        for index, row_padre in df_padres.iterrows():
            lote_actual = str(row_padre['Lote_Asignado']).strip()
            # Convertimos la fecha al formato correcto de base de datos
            fecha_actual = pd.to_datetime(row_padre['Efectiva']).date()
            cantidad_padre = float(row_padre['Cantidad'])
        
            # Evitar duplicados: Verificamos si este lote exacto ya existe
            existe = db.query(ProduccionAlimento).filter_by(
                lote_destino=lote_actual, 
                fecha_efectiva=fecha_actual
            ).first()
        
            if existe:
                continue # Si ya existe, saltamos al siguiente lote para evitar duplicados
            
            # 1. Guardar la Cabecera (Producción)
            nueva_produccion = ProduccionAlimento(
                fecha_efectiva=fecha_actual,
                lote_destino=lote_actual,
                numero_articulo=row_padre['Numero articulo'],
                descripcion=str(row_padre['Descripción']).strip(),
                cantidad_kg=cantidad_padre
            )
            db.add(nueva_produccion)
            db.commit()
            db.refresh(nueva_produccion) # Obtenemos el ID autoincremental (PK) generado
            
            # 2. Buscar los Insumos (Hijos) de este lote específico
            df_hijos = df[(df['Tipo Trans'] == 'ISS-WO') & (df['Lote_Asignado'] == lote_actual)]
            
            for _, row_hijo in df_hijos.iterrows():
                # Absoluto para que no queden en negativo en la BD
                cantidad_consumida = abs(float(row_hijo['Cantidad']))
                linea_prod = str(row_hijo['Lín Producto']).strip().zfill(2) # Asegura que sea '07' o '09'
                
                # 3. Separar y guardar Macros (Línea 09) y Micros (Línea 07)
                if linea_prod == '09':
                    nuevo_macro = ConsumoInsumosMacros(
                        produccion_id=nueva_produccion.id, # Conectamos con el ID del padre
                        numero_articulo=row_hijo['Numero articulo'],
                        materia_prima=str(row_hijo['Descripción']).strip(),
                        cantidad_consumida=cantidad_consumida
                    )
                    db.add(nuevo_macro)
                
                elif linea_prod == '07':
                    nuevo_micro = ConsumoInsumosMicros(
                        produccion_id=nueva_produccion.id, # Conectamos con el ID del padre
                        numero_articulo=row_hijo['Numero articulo'],
                        materia_prima=str(row_hijo['Descripción']).strip(),
                        cantidad_consumida=cantidad_consumida
                    )
                    db.add(nuevo_micro)
                
            db.commit() # Confirmamos la inserción de todos los hijos
            lotes_guardados += 1
        
        return {"status": "success", "message": f"Se procesaron e ingresaron {lotes_guardados} nuevos lotes a la base de datos."}   
            
    except Exception as e:
        db.rollback() # Si hay un error, deshacemos los cambios para no corromper la BD
        return {"status": "error", "message": f"Error procesando el archivo: {str(e)}"}
    finally:
        db.close() # Siempre cerramos la puerta

# ==============================================================================
# ENDPOINT 2: BUSCADOR DE TRAZABILIDAD (GET)
# ==============================================================================
@app.get("/buscar-lote/")
def buscar_lote(lote: str, fecha: str):
    db = SessionLocal()
    try:
        # Buscamos el registro padre exacto
        produccion = db.query(ProduccionAlimento).filter(
            ProduccionAlimento.lote_destino == lote,
            ProduccionAlimento.fecha_efectiva == fecha
        ).first()

        if not produccion:
            return {"status": "error", "message": "No se encontraron registros para este lote y fecha en la base de datos."}

        # Armamos el paquete JSON con el Padre y sus Hijos a través de la relación ORM
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
        db.close()