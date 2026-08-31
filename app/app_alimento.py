import streamlit as st
import requests

# Importamos tus nuevos módulos
import resumenProduccion
import consumoInsumos
import auditoria

# ==============================================================================
# CONFIGURACIÓN Y URL
# ==============================================================================
try:
    API_URL = st.secrets["API_URL"]
except:
    API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Dashboard Planta", page_icon="🏭", layout="wide")

st.title("📊 Dashboard de Producción de Alimento")
st.markdown("Monitorización del volumen de alimento fabricado y consumo de materias primas.")

col_actualizar, col_selector = st.columns(2)

with col_actualizar:
    st.subheader("Actualización de Datos")
    with st.expander("⬆️ Actualizar base de datos con nuevo Excel"):
        archivo_subido = st.file_uploader("Carga tu archivo de producción", type=["xls", "xlsx"])
        if archivo_subido is not None:
            if st.button("🚀 Inyectar a la base de datos"):
                with st.spinner("Sincronizando..."):
                    try:
                        archivos = {"file": (archivo_subido.name, archivo_subido.getvalue(), "application/vnd.ms-excel")}
                        res = requests.post(f"{API_URL}/cargar-excel/", files=archivos)
                        if res.status_code == 200:
                            st.success(res.json().get("message"))
                            st.rerun() 
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

with col_selector:  
    st.subheader("Selecciona el Mes a Analizar")
    periodo_seleccionado = None
    try:
        res_meses = requests.get(f"{API_URL}/listado-meses/")  
        if res_meses.status_code == 200:
            lista_periodos = res_meses.json().get("periodos", []) 
            if lista_periodos:
                periodo_seleccionado = st.selectbox("Selecciona período", options=lista_periodos, index=0, label_visibility="collapsed")
            else:
                st.info("La base de datos está vacía.")
    except Exception as e:
        st.error(f"No se pudo conectar con la API: {e}")

st.divider()

# ==============================================================================
# SISTEMA DE PESTAÑAS (Llamando a los módulos)
# ==============================================================================
tab_produccion, tab_insumos, tab_trazabilidad = st.tabs([
    "🏭 Resumen de Producción", 
    "🌾 Consumo de Insumos", 
    "🔍 Auditoría por Lote"
])

with tab_produccion:
    resumenProduccion.mostrar(periodo_seleccionado, API_URL)

with tab_insumos:
    consumoInsumos.mostrar(periodo_seleccionado, API_URL)

with tab_trazabilidad:
    auditoria.mostrar(API_URL)

# ==============================================================================
# 6. FOOTER
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
    st.write("🚀 **Versión:** 1.1.3")
    st.caption("Última actualización: Agosto 2026")

st.markdown(
    """
    <div style='text-align: center; color: grey; padding-top: 20px;'>
        <p>© 2026 <b>Cristian Tobar Morales</b>. <br> 
         Todos los derechos reservados. | Esta aplicación es de uso estrictamente profesional y privado.</p>
    </div>
    """, 
     unsafe_allow_html=True
)
