# importaciones
from fastapi import FastAPI, UploadFile, File
import pandas as pd
import io
from sqlalchemy.orm import sessionmaker
from src.database import engine
from src.models_db import ProduccionAlimento, ConsumoInsumosMacros, ConsumoInsumosMicros
from sqlalchemy import extract # Importante para filtrar por mes/año

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


        # ==============================================================================
        # LIMPIEZA EXTREMA CON PANDAS (Antes de procesar)
        # ==============================================================================
        # Forzamos el redondeo a 2 decimales en toda la columna de una sola vez
        df_padres['Cantidad'] = df_padres['Cantidad'].astype(float).round(2)
        
        # Eliminamos cualquier fila gemela directamente en el DataFrame
        df_padres = df_padres.drop_duplicates(subset=['Lote_Asignado', 'Efectiva', 'Cantidad'])
        

        lista_lotes = []
        lotes_guardados = 0
        #lotes_en_memoria = set() # Mantenemos el guardia de seguridad por precaución
        
        # iteramos por cada lote de alimento creado
        for index, row_padre in df_padres.iterrows():
            lote_actual = str(row_padre['Lote_Asignado']).strip()
            fecha_actual = pd.to_datetime(row_padre['Efectiva']).date()
            cantidad_padre = float(row_padre['Cantidad'])
        
            # Evitar duplicados
            existe = db.query(ProduccionAlimento).filter_by(
                lote_destino=lote_actual, 
                fecha_efectiva=fecha_actual,
                cantidad_kg=cantidad_padre
            ).first()
        
            if existe:
                continue 
            
            # 1. Guardar la Cabecera (Padre) SOLO EN MEMORIA
            nueva_produccion = ProduccionAlimento(
                fecha_efectiva=fecha_actual,
                lote_destino=lote_actual,
                numero_articulo=row_padre['Numero articulo'],
                descripcion=str(row_padre['Descripción']).strip(),
                cantidad_kg=cantidad_padre
            )
            
            # 2. Buscar los Insumos (Hijos)
            df_hijos = df[(df['Tipo Trans'] == 'ISS-WO') & (df['Lote_Asignado'] == lote_actual)]
            
            for _, row_hijo in df_hijos.iterrows():
                cantidad_consumida = abs(float(row_hijo['Cantidad']))
                linea_prod = str(row_hijo['Lín Producto']).strip().zfill(2)
                
                # 3. Separar y anidar DIRECTAMENTE al objeto padre
                if linea_prod == '09':
                    nuevo_macro = ConsumoInsumosMacros(
                        numero_articulo=row_hijo['Numero articulo'],
                        materia_prima=str(row_hijo['Descripción']).strip(),
                        cantidad_consumida=cantidad_consumida
                    )
                    # Magia del ORM: conectamos el hijo sin necesitar el ID todavía
                    nueva_produccion.macros.append(nuevo_macro)
                
                elif linea_prod == '07':
                    nuevo_micro = ConsumoInsumosMicros(
                        numero_articulo=row_hijo['Numero articulo'],
                        materia_prima=str(row_hijo['Descripción']).strip(),
                        cantidad_consumida=cantidad_consumida
                    )
                    # Magia del ORM: conectamos el hijo sin necesitar el ID todavía
                    nueva_produccion.micros.append(nuevo_micro)
            
            # 4. Metemos el Lote completo (con sus hijos ya anidados) a la caja
            lista_lotes.append(nueva_produccion)
            lotes_guardados += 1
        
        # ====================================================================
        # 5. EL VIAJE ÚNICO A LA BASE DE DATOS (TOTALMENTE FUERA DE LOS CICLOS)
        # ====================================================================
        if lista_lotes: # Si la caja tiene lotes nuevos
            db.add_all(lista_lotes)
            db.commit() # SQLAlchemy le asignará los IDs a padres e hijos automáticamente
        
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
from sqlalchemy import func # Importante agregar esto arriba


# ==============================================================================
# ENDPOINT 3: Listado de meses disponibles
# ==============================================================================
@app.get("/listado-meses/")
def obtener_meses():
    db = SessionLocal()
    try:
        # Buscamos combinaciones únicas de Mes y Año en la base de datos
        periodos = db.query(
            extract('month', ProduccionAlimento.fecha_efectiva).label('mes'),
            extract('year', ProduccionAlimento.fecha_efectiva).label('anio')
        ).distinct().all()
        
        meses_nombres = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
            7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        # Formateamos para el selector de Streamlit: "Enero 2026"
        resultado = [f"{meses_nombres[int(p.mes)]} {int(p.anio)}" for p in periodos]
        return {"status": "success", "periodos": resultado}
    finally:
        db.close()


# ==============================================================================
# ENDPOINT 4: RESUMEN (GET)
# ==============================================================================

@app.get("/resumen-produccion/")
def obtener_resumen(periodo: str = None): # Recibe "Enero 2026"
    db = SessionLocal()
    try:
        query = db.query(ProduccionAlimento)
        
        if periodo:
            # Separamos "Enero 2026" en mes (1) y año (2026)
            nombre_mes, anio = periodo.split()
            meses_inv = {v: k for k, v in {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}.items()}
            
            query = query.filter(
                extract('month', ProduccionAlimento.fecha_efectiva) == meses_inv[nombre_mes],
                extract('year', ProduccionAlimento.fecha_efectiva) == int(anio)
            )

        total_kg = db.query(func.sum(query.subquery().c.cantidad_kg)).scalar() or 0
        produccion_lotes = db.query(
            query.subquery().c.lote_destino, 
            func.sum(query.subquery().c.cantidad_kg)
        ).group_by(query.subquery().c.lote_destino).all()
        
        return {
            "status": "success",
            "total_kg": float(total_kg),
            "mes_actual": periodo or "Todos",
            "datos_lotes": [{"Lote": row[0], "Cantidad": row[1]} for row in produccion_lotes]
        }
    finally:
        db.close()
  
  
