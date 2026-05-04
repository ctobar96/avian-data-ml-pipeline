# conector en Python
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# 1. Carga las variables de entorno (el archivo .env)
load_dotenv()

# 2. Obtén la URL de conexión desde las variables de entorno
DATABASE_URL = os.getenv('DATABASE_URL')

try:
    # 3. Crea el motor de conexión a la base de datos
    engine = create_engine(DATABASE_URL)
    
    # 4. Prueba la conexión (opcional)
    with engine.connect() as connection:
        print("✅ ¡Conexión exitosa a Supabase (PostgreSQL)!")

except Exception as e:
    print(f"❌ Error al conectar a la base de datos: {e}")