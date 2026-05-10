# Definir la estructura de la tabla (El Esquema)
# Archivo: src/models_db.py
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from src.database import engine

# Creamos la clase base para nuestras tablas
Base = declarative_base()

# ==============================================================================
# TABLA PRINCIPAL: Producción de Alimento (Cabecera)
# ==============================================================================
class ProduccionAlimento(Base):
    __tablename__ = 'produccion_alimento'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha_efectiva = Column(Date, index=True)
    lote_destino = Column(String(100), index=True)
    numero_articulo = Column(String, nullable=True)
    descripcion = Column(String(200))
    cantidad_kg = Column(Float)

    # REGLA DE SEGURIDAD: Evita duplicados exactos si se sube el Excel 2 veces
    __table_args__ = (
        UniqueConstraint('lote_destino', 'fecha_efectiva', 'cantidad_kg', name='uix_lote_fecha_cant'),
    )

    # Relaciones con las tablas hijas
    macros = relationship("ConsumoInsumosMacros", back_populates="produccion", cascade="all, delete-orphan")
    micros = relationship("ConsumoInsumosMicros", back_populates="produccion", cascade="all, delete-orphan")


# ==============================================================================
# TABLA HIJA 1: Consumo de Insumos MACROS (Ej: Maíz, Soya, Trigo)
# ==============================================================================
class ConsumoInsumosMacros(Base):
    __tablename__ = 'consumo_insumos_macros'

    id = Column(Integer, primary_key=True, autoincrement=True)
    produccion_id = Column(Integer, ForeignKey('produccion_alimento.id')) # Tu Llave Foránea
    numero_articulo = Column(String, nullable=True)
    materia_prima = Column(String(200))
    cantidad_consumida = Column(Float)

    # Relación de vuelta hacia el padre
    produccion = relationship("ProduccionAlimento", back_populates="macros")


# ==============================================================================
# TABLA HIJA 2: Consumo de Insumos MICROS (Ej: Vitaminas, Pigmentos)
# ==============================================================================
class ConsumoInsumosMicros(Base):
    __tablename__ = 'consumo_insumos_micros'

    id = Column(Integer, primary_key=True, autoincrement=True)
    produccion_id = Column(Integer, ForeignKey('produccion_alimento.id')) # Tu Llave Foránea
    numero_articulo = Column(String, nullable=True)
    materia_prima = Column(String(200))
    cantidad_consumida = Column(Float)

    # Relación de vuelta hacia el padre
    produccion = relationship("ProduccionAlimento", back_populates="micros")


# ==============================================================================
# FUNCIÓN DE MIGRACIÓN
# ==============================================================================
def crear_tablas():
    print("⏳ Construyendo la nueva estructura relacional en Supabase...")
    # Base.metadata.drop_all(bind=engine) # Descomentar solo si necesitas borrar las tablas viejas
    Base.metadata.create_all(bind=engine)
    print("✅ ¡Estructura de tablas creada con éxito!")

if __name__ == "__main__":
    crear_tablas()