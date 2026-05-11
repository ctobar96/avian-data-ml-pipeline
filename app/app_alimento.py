import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter 
import requests

# Configuración de URL
try:
    API_URL = st.secrets["API_URL"]
except:
    API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Dashboard Planta", page_icon="🏭", layout="wide")
st.title("📊 Dashboard de Producción (Datos de Supabase)")

# ==============================================================================
# 1. Carga de Datos (Envío)
# ==============================================================================
archivo_subido = st.file_uploader("Actualizar base de datos con nuevo Excel", type=["xls", "xlsx"])

if archivo_subido is not None:
    if st.button("🚀 Procesar e Inyectar a Base de Datos"):
        with st.spinner("Sincronizando con Supabase..."):
            try:
                archivos = {"file": (archivo_subido.name, archivo_subido.getvalue(), "application/vnd.ms-excel")}
                res = requests.post(f"{API_URL}/cargar-excel/", files=archivos)
                if res.status_code == 200:
                    st.success(res.json().get("message"))
                else:
                    st.error("Error en la carga.")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

st.divider()

# ==============================================================================
# 2. Visualización (Consulta a la API - La Verdad Centralizada)
# ==============================================================================
with st.spinner("Actualizando Dashboard con datos reales..."):
    try:
        
        # ==============================================================================
        # 2. FILTRO DE FECHAS
        # ==============================================================================
        periodo_seleccionado = None

        try:
            # Le pedimos a la API los meses que ya existen en Supabase
            res_meses = requests.get(f"{API_URL}/listado-meses/")
            if res_meses.status_code == 200:
                lista_periodos = res_meses.json().get("periodos", [])
                
                if lista_periodos:
                    # Seleccionamos el mes (Por defecto el último mes ingresado)
                    periodo_seleccionado = st.selectbox(
                        "🗓️ Selecciona el Mes de Producción que deseas visualizar:",
                        options=lista_periodos,
                        index=0
                    )
                else:
                    st.info("La base de datos está vacía. Sube un archivo para comenzar.")
        except Exception as e:
            st.error(f"Error al conectar con la API para obtener fechas: {e}")
        
        # AQUÍ CONSULTAMOS LA VERDAD A LA API
        res_resumen = requests.get(f"{API_URL}/resumen-produccion/")
        
        if res_resumen.status_code == 200:
            datos = res_resumen.json()
            
            # KPIs de la API
            total_kg = datos["total_kg"]
            mes_actual = datos["mes_actual"] # "Enero 2026"
            
            
            
        try:
            # Le pedimos a la API la lista de meses que realmente existen en Supabase
            res_meses = requests.get(f"{API_URL}/listado-meses/")
            lista_periodos = res_meses.json().get("periodos", [])
            
            if lista_periodos:
                # BOTÓN DE SELECCIÓN
                periodo_seleccionado = st.sidebar.selectbox(
                    "🗓️ Selecciona el Mes de Producción",
                    options=lista_periodos,
                    index=0 # Por defecto el primero
                )
            else:
                periodo_seleccionado = None
                st.sidebar.info("Sube un archivo para ver meses disponibles.")
        except:
            periodo_seleccionado = None
            
# ==============================================================================
# 2. Consulta a la API con el Filtro Seleccionado
# ==============================================================================
        with st.spinner(f"Consultando datos de {periodo_seleccionado}..."):
            try:
                # Enviamos el mes seleccionado como parámetro a la API
                params = {"periodo": periodo_seleccionado}
                res_resumen = requests.get(f"{API_URL}/resumen-produccion/", params=params)
                
                if res_resumen.status_code == 200:
                    datos = res_resumen.json()
                    total_kg = datos["total_kg"]
                    mes_actual = datos["mes_actual"] # Esto será "Enero 2026"
                    
                    # Dibujamos las métricas
                    col1, col2 = st.columns(2)
                    with col1: st.metric(label="🗓️ Periodo Visualizado", value=mes_actual)
                    with col2: st.metric(label="⚖️ Total Alimento (Kg)", 
                            value=f"{int(total_kg):,}".replace(',', '.'))
                    
                    # --- PREPARACIÓN DEL DATAFRAME DE LA API PARA EL GRÁFICO ---
                    # datos["datos_lotes"] viene de api.py como [{"Lote": "...", "Cantidad": ...}, ...]
                    df_grafico = pd.DataFrame(datos["datos_lotes"])
                    df_grafico.columns = ['Lote', 'Cantidad'] # Aseguramos nombres de columna limpios
                    
                    # ORDENAMIENTO CRÍTICO: Descendente por cantidad
                    df_grafico = df_grafico.sort_values(by="Cantidad", ascending=False)

                    # ==============================================================================
                    # EL GRÁFICO PROFESIONAL AJUSTADO (REPLICA LA IMAGEN OBJETIVO)
                    # ==============================================================================
                    if not df_grafico.empty:
                        st.subheader("Distribución de Producción por Sector (Datos Validados)")
                        
                        # 1. Configuración de estética Matplotlib/Seaborn (Fondo blanco)
                        sns.set_theme(style="white") 
                        
                        # 2. Figura Panorámica WIDE (replicando la imagen)
                        fig, ax = plt.subplots(figsize=(16, 6)) # Wide aspect ratio

                        # 3. Creación del Barplot profesional con paleta 'magma' secuencial
                        # El hack de hue='Lote' asegura un color secuencial distinto por barra rankeada
                        barplot = sns.barplot(
                            data=df_grafico,
                            x="Lote",
                            y="Cantidad",
                            hue="Lote", # DIFERENTE COLOR POR RANGO DE BARRA
                            palette="magma", # Gradiente secuencial exacto de la imagen
                            legend=False,
                            ax=ax
                        )

                        # 4. Formateo de Ticks Y (Chilean style: separador de miles '.')
                        def format_chilean(x, pos):
                            return f"{int(x):,}".replace(",", ".")

                        ax.yaxis.set_major_formatter(FuncFormatter(format_chilean))
                        
                        # Establecemos límites de Y para dar headroom (aprox como la imagen)
                        ax.set_ylim(0, 320000) 
                        ax.set_yticks([0, 50000, 100000, 150000, 200000, 250000, 300000])

                        # 5. Etiquetas de Ejes exactas
                        ax.set_xlabel("Sector", fontsize=12)
                        ax.set_ylabel("Alimento Fabricado (kg)", fontsize=12)

                        # 6. Cuadrícula Horizontal Discontinua (Dashed Grid)
                        ax.grid(axis='y', linestyle='--', color='lightgray', alpha=0.7)

                        # 7. Anotaciones de Valor formateadas sobre cada barra ('259.430')
                        for container in ax.containers:
                            for bar in container:
                                height = bar.get_height()
                                if height > 0:
                                    # Formateamos kilos enteros con puntos chilenos
                                    formatted_val = f"{int(height):,}".replace(",", ".")
                                    ax.annotate(
                                        formatted_val,
                                        xy=(bar.get_x() + bar.get_width() / 2, height),
                                        xytext=(0, 5), # Label 5 puntos arriba del top de la barra
                                        textcoords="offset points",
                                        ha='center', va='bottom',
                                        fontsize=9, color='black'
                                    )

                        # 8. Rotación de Etiquetas X (45 grados derecha)
                        plt.xticks(rotation=45, ha='right') # ha='right' alinea texto rotado
                        
                        # Ajuste de layout tight para que nada se corte
                        plt.tight_layout()

                        # Mostrar en Streamlit
                        st.pyplot(fig)
                        plt.close(fig) # Liberamos memoria
                    
                    else:
                        st.info("No hay datos históricos disponibles en la base de datos.")

            except Exception as e:
                st.error(f"Error al sincronizar dashboard con la API: {e}")    

    except Exception as e:
        st.error(f"Error al conectar con la API: {e}") 

# ==============================================================================
# 5. Buscador de Trazabilidad (Conectado a FastAPI)
# ==============================================================================
st.markdown("---")
st.title("🔍 Buscador de Trazabilidad por Lote")          

col_busq1, col_busq2, col_busq3 = st.columns([2, 2, 1])
with col_busq1:
    fecha_input = st.date_input("🗓️ Fecha de Producción")
with col_busq2:
    lote_input = st.text_input("📦 Código de Lote", placeholder="Ej: PICH5ACO")
with col_busq3:
    st.markdown("<br>", unsafe_allow_html=True) 
    boton_buscar = st.button("Buscar Registro", type="primary", use_container_width=True)

if boton_buscar and lote_input:
    with st.spinner("Buscando en la base de datos..."):
        parametros = {"lote": lote_input.strip(), "fecha": str(fecha_input)}
        try:
            respuesta_busqueda = requests.get(f"{API_URL}/buscar-lote/", params=parametros)
            datos_lote = respuesta_busqueda.json()
            
            if datos_lote.get("status") == "success":
                st.success("✅ ¡Lote encontrado con éxito!")
                st.subheader("📋 Información de Producción")
                st.info(f"**Lote:** {datos_lote['produccion']['lote']} | **Producto:** {datos_lote['produccion']['descripcion']} | **Total Fabricado:** {datos_lote['produccion']['cantidad_kg']:,.2f} Kg")
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown("#### 🌾 Macros Consumidos")
                    if datos_lote['macros']:
                        st.dataframe(pd.DataFrame(datos_lote['macros']), use_container_width=True, hide_index=True)
                    else:
                        st.warning("No hay macros registrados.")
                with col_m2:
                    st.markdown("#### 🧪 Micros Consumidos")
                    if datos_lote['micros']:
                        st.dataframe(pd.DataFrame(datos_lote['micros']), use_container_width=True, hide_index=True)
                    else:
                        st.warning("No hay micros registrados.")
            else:
                st.error(datos_lote.get("message", "Error desconocido."))
                
        except Exception as e:
            st.error(f"Error de conexión con la API: {e}")

# ==============================================================================
# 6. Pie de Página (Footer)
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
st.divider()

f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    st.markdown("#### **Desarrollado por:**")
    st.write("👨‍💻 **Cristian Tobar Morales**")
    st.caption("Magíster en Data Science")

with f_col2:
    st.markdown("#### **Proyecto:**")
    st.write("🐔 *Avian Data ML Pipeline*")
    st.caption("Análisis y Modelado de Datos")

with f_col3:
    st.markdown("#### **Información:**")
    st.write("🚀 **Versión:** 1.2.0")
    st.caption("Última actualización: Abril 2026")

st.markdown(
    """
    <div style='text-align: center; color: grey; padding-top: 20px;'>
        <p>© 2026 <b>Cristian Tobar Morales</b>. <br> 
        Todos los derechos reservados. | Esta aplicación es de uso estrictamente profesional y privado.</p>
    </div>
    """, 
    unsafe_allow_html=True
)          
            