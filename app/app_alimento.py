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
# 2. Visualización (Consulta a la API - La Fuente de Verdad)
# ==============================================================================
with st.spinner("Consultando datos reales desde la API..."):
    try:
        res_resumen = requests.get(f"{API_URL}/resumen-produccion/")
        
        if res_resumen.status_code == 200:
            datos = res_resumen.json()
            total_kg = datos["total_kg"]
            df_grafico = pd.DataFrame(datos["datos_lotes"])

            # KPIs con datos de la API
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="⚖️ Total De Alimento Fabricado (Kg)", value=f"{int(total_kg):,}".replace(',', '.'))
            with col2:
                st.metric(label="📦 Lotes Registrados", value=len(df_grafico))

            # Gráfico con datos de la API
            if not df_grafico.empty:
                st.subheader("Distribución de Producción por Sector (Datos Validados)")
                fig, ax = plt.subplots(figsize=(14, 6))
                sns.barplot(data=df_grafico, x='Lote', y='Cantidad', palette='magma', ax=ax)
                
                ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}".replace(',', '.')))
                plt.xticks(rotation=45)
                st.pyplot(fig)
        else:
            st.info("No hay datos disponibles en la base de datos. Por favor, sube un archivo.")

    except Exception as e:
        st.error(f"No se pudo obtener el resumen de la API: {e}")        

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
            