# ==============================================================================
# Análisis de Producción de Alimento (Planta)
# ==============================================================================
# Este módulo tiene como objetivo procesar los datos históricos de fabricación de alimento 
# para generar indicadores de gestión (BI) y preparar las variables para el modelo de Machine Learning.
# 
# Objetivo: Cálculo de Alimento Creado Mensualmente
# Se desarrolló este análisis para determinar el volumen total de alimento fabricado mes a mes. 
# Esto permite a la gerencia visualizar la capacidad operativa de la planta y correlacionar 
# estos picos de producción con el rendimiento posterior en la granja.
# 
# Lógica de Cálculo:
# 1. Normalización de Fechas: Se transforma la columna 'Efectiva' al formato datetime de Python.
# 2. Periodización: Se agrupan los registros por periodos mensuales (YYYY-MM).
# 3. Agregación: Se realiza la sumatoria de la columna 'Cantidad' (kilos).

# Importar librerías necesarias
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configurar pandas para mostrar todas las columnas
pd.set_option('display.max_columns', None)

# Ruta del archivo
file_path = r'D:\crist\OneDrive\Estudios\Proyectos Para GitHub\avian-data-ml-pipeline\data\raw\AlimentoFabricado\ALIMENTOENERO2026.xls'

# Leer el archivo Excel
try:
    df = pd.read_excel(file_path, sheet_name='Datos')
    print("Archivo leído exitosamente.")
except Exception as e:
    print(f"Error al leer el archivo: {e}")

# ==============================================================================
# Variables a utilizar
# Se seleccionan solamente las variables más importantes para la investigación.
# ==============================================================================

columnas_interes = [
    'Efectiva',
    'Tipo Trans',
    'Lín Producto',
    'Numero articulo',
    'Descripción',
    'Cantidad',
    'Lote/Serie'
]
        
# Filtrar el DataFrame para obtener solo las columnas de interés
df_filtrado = df[columnas_interes].copy()

# ==============================================================================
# Filtros para obtener la producción de alimento
# Tipo de transacción: RCT-WO y linea de producto 15
# Se utiliza este tipo de transacción debido a que es de creación.
# ==============================================================================

# Definir el tipo de transacción y línea que indican creación de alimento
transaccion_creacion = ['RCT-WO']
linea_producto_alimento = [15]

# Filtrar el DataFrame para obtener solo las filas donde el tipo de transacción es 'RCT-WO'
df_creacion = df_filtrado[
    df_filtrado['Tipo Trans'].isin(transaccion_creacion) & 
    df_filtrado['Lín Producto'].isin(linea_producto_alimento)
].copy()

# ==============================================================================
# Suma la cantidad de alimento creado
# ==============================================================================

# Sumar las cantidades
produccion_mensual_aliemnto = df_creacion['Cantidad'].sum()
print(f"Cantidad total de alimento creado en el mes: {produccion_mensual_aliemnto}")

# ==============================================================================
# Visualizaciones: Visualización de cada lote
# ==============================================================================

# 1. Agrupar por Lote y sumar la cantidad
produccion_por_lote = df_creacion.groupby('Lote/Serie')['Cantidad'].sum().reset_index()

# 2. Ordenar de mayor a menor
produccion_por_lote = produccion_por_lote.sort_values(by='Cantidad', ascending=False)

# --- CREAR EL GRÁFICO ---
plt.figure(figsize=(14, 7)) # Un poco más ancho por si tienes muchos lotes

# Crear el gráfico de barras (con ajustes para las nuevas versiones de seaborn)
ax = sns.barplot(
    data=produccion_por_lote, 
    x='Lote/Serie', 
    y='Cantidad', 
    hue='Lote/Serie',   # Asignado a 'hue' para evitar advertencias de depreciación
    palette='magma', 
    legend=False        # Oculta la leyenda generada por el hue
)

# Añadir las etiquetas con los números exactos sobre cada barra
for p in ax.patches:
    ax.annotate(f"{int(p.get_height()):,}".replace(',', '.'), 
                (p.get_x() + p.get_width() / 2., p.get_height()), 
                ha='center', va='bottom', 
                fontsize=10, color='black', xytext=(0, 5), 
                textcoords='offset points')

# Darle formato a los textos y ejes
plt.title('Distribución del Total de Alimento Producido según Sector', fontsize=16, fontweight='bold', pad=15)
plt.xlabel('Sector', fontsize=13)
plt.ylabel('Alimento Fabricado (kg)', fontsize=13)

# Rotar los nombres de los lotes 45 grados por si son códigos muy largos y chocan entre sí
plt.xticks(rotation=45, ha='right') 

plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.tight_layout()

# Mostrar el gráfico
plt.show()