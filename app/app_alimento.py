import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter 
import requests

# Configuración de URL (Render o Local)
try:
    API_URL = st.secrets["API_URL"]
except:
    API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Dashboard Planta", page_icon="🏭", layout="wide")

# ==============================================================================
# 1. ENCABEZADO Y CARGA (Para actualizar datos)
# ==============================================================================
st.title("📊 Dashboard de Producción (Datos de Supabase)")

with st.expander("⬆️ Actualizar base de datos con nuevo Excel"):
    archivo_subido = st.file_uploader("Sube el archivo aquí", type=["xls", "xlsx"])
    if archivo_subido is not None:
        if st.button("🚀 Inyectar Datos a Supabase"):
            with st.spinner("Subiendo..."):
                archivos = {"file": (archivo_subido.name, archivo_subido.getvalue(), "application/vnd.ms-excel")}
                res = requests.post(f"{API_URL}/cargar-excel/", files=archivos)
                if res.status_code == 200:
                    st.success("¡Base de datos actualizada con éxito!")
                    st.rerun() # Recargamos para que el filtro detecte el nuevo mes

st.divider()

# ==============================================================================
# 2. FILTRO DE FECHAS (Siempre visible)
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

# ==============================================================================
# 3. VISUALIZACIÓN DE DATOS EXISTENTES
# ==============================================================================
if periodo_seleccionado:
    with st.spinner(f"Cargando datos de {periodo_seleccionado}..."):
        try:
            # Consultamos el resumen para ese mes específico
            params = {"periodo": periodo_seleccionado}
            res_resumen = requests.get(f"{API_URL}/resumen-produccion/", params=params)
            
            if res_resumen.status_code == 200:
                datos = res_resumen.json()
                total_kg = datos["total_kg"]
                df_grafico = pd.DataFrame(datos["datos_lotes"])

                # --- KPIs ---
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="🗓️ Periodo", value=periodo_seleccionado)
                with col2:
                    st.metric(
                        label="⚖️ Total Alimento Creado (Kg)", 
                        value=f"{int(total_kg):,}".replace(',', '.')
                    )

                # --- GRÁFICO (REPLICA EXACTA DE TU IMAGEN) ---
                if not df_grafico.empty:
                    df_grafico = df_grafico.sort_values(by="Cantidad", ascending=False)
                    
                    fig, ax = plt.subplots(figsize=(16, 6))
                    sns.set_theme(style="white")
                    
                    sns.barplot(
                        data=df_grafico, x="Lote", y="Cantidad", 
                        hue="Lote", palette="magma", legend=False, ax=ax
                    )

                    # Formato chileno (puntos para miles)
                    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{int(x):,}".replace(",", ".")))
                    
                    # Etiquetas sobre las barras
                    for p in ax.patches:
                        ax.annotate(f"{int(p.get_height()):,}".replace(",", "."), 
                                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                                    ha='center', va='bottom', fontsize=9, xytext=(0, 5), textcoords='offset points')

                    plt.xticks(rotation=45, ha='right')
                    plt.grid(axis='y', linestyle='--', alpha=0.7)
                    st.pyplot(fig)
            
        except Exception as e:
            st.error(f"Error al obtener resumen: {e}")

# ==============================================================================
# 4. BUSCADOR DE TRAZABILIDAD (Abajo de todo)
# ==============================================================================
st.markdown("---")
st.title("🔍 Buscador de Trazabilidad por Lote")
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
            