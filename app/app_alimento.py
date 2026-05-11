import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter 
import requests

# 1. CONFIGURACIÓN Y URL
try:
    API_URL = st.secrets["API_URL"]
except:
    API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Dashboard Planta", page_icon="🏭", layout="wide")

# ==============================================================================
# 2. SECCIÓN DE CARGA (OPCIONAL/EXPANDER)
# ==============================================================================
st.title("📊 Dashboard de Producción (Datos de Supabase)")

with st.expander("⬆️ Actualizar base de datos con nuevo Excel"):
    archivo_subido = st.file_uploader("Sube tu archivo de producción", type=["xls", "xlsx"])
    if archivo_subido is not None:
        if st.button("🚀 Inyectar a Supabase"):
            with st.spinner("Sincronizando..."):
                try:
                    archivos = {"file": (archivo_subido.name, archivo_subido.getvalue(), "application/vnd.ms-excel")}
                    res = requests.post(f"{API_URL}/cargar-excel/", files=archivos)
                    if res.status_code == 200:
                        st.success(res.json().get("message"))
                        st.rerun() # Forzamos recarga para actualizar el selector de meses
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

st.divider()

# ==============================================================================
# 3. SELECTOR DE MES (CONSULTA A LA API)
# ==============================================================================
periodo_seleccionado = None

try:
    # Obtenemos la lista de meses disponibles en la base de datos
    res_meses = requests.get(f"{API_URL}/listado-meses/")
    if res_meses.status_code == 200:
        lista_periodos = res_meses.json().get("periodos", [])
        
        if lista_periodos:
            # Selector de Mes en la parte principal (o st.sidebar.selectbox si prefieres)
            periodo_seleccionado = st.selectbox(
                "🗓️ Selecciona el Mes de Producción que deseas visualizar:",
                options=lista_periodos,
                index=0
            )
        else:
            st.info("La base de datos está vacía. Sube un archivo para comenzar.")
except Exception as e:
    st.error(f"No se pudo conectar con la API para obtener los periodos: {e}")

# ==============================================================================
# 4. VISUALIZACIÓN DE MÉTRICAS Y GRÁFICO (DATOS DE SUPABASE)
# ==============================================================================
if periodo_seleccionado:
    with st.spinner(f"Consultando datos de {periodo_seleccionado}..."):
        try:
            # Pedimos el resumen filtrado por el periodo seleccionado
            params = {"periodo": periodo_seleccionado}
            res_resumen = requests.get(f"{API_URL}/resumen-produccion/", params=params)
            
            if res_resumen.status_code == 200:
                datos = res_resumen.json()
                total_kg = datos["total_kg"]
                mes_actual = datos["mes_actual"]
                df_grafico = pd.DataFrame(datos["datos_lotes"])

                # --- KPIs ---
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="🗓️ Periodo Visualizado", value=mes_actual)
                with col2:
                    # Formateo con puntos para miles (Estilo Chileno)
                    val_formateado = f"{int(total_kg):,}".replace(',', '.')
                    st.metric(label="⚖️ Total Alimento (Kg)", value=val_formateado)

                # --- GRÁFICO (REPLICA DE IMAGEN OBJETIVO) ---
                if not df_grafico.empty:
                    st.subheader("Distribución de Producción por Sector")
                    
                    df_grafico.columns = ['Lote', 'Cantidad']
                    df_grafico = df_grafico.sort_values(by="Cantidad", ascending=False)
                    
                    sns.set_theme(style="white")
                    fig, ax = plt.subplots(figsize=(16, 6))
                    
                    sns.barplot(
                        data=df_grafico, x="Lote", y="Cantidad", 
                        hue="Lote", palette="magma", legend=False, ax=ax
                    )

                    # Formateador de eje Y
                    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{int(x):,}".replace(",", ".")))
                    ax.set_ylim(0, 320000)
                    
                    # Anotaciones sobre barras
                    for p in ax.patches:
                        if p.get_height() > 0:
                            label = f"{int(p.get_height()):,}".replace(",", ".")
                            ax.annotate(label, (p.get_x() + p.get_width() / 2., p.get_height()), 
                                        ha='center', va='bottom', fontsize=9, xytext=(0, 5), 
                                        textcoords='offset points')

                    plt.xticks(rotation=45, ha='right')
                    plt.grid(axis='y', linestyle='--', alpha=0.7)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close(fig)
            
        except Exception as e:
            st.error(f"Error al procesar visualización: {e}")

# ==============================================================================
# 5. BUSCADOR DE TRAZABILIDAD
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
    with st.spinner("Buscando..."):
        try:
            parametros = {"lote": lote_input.strip(), "fecha": str(fecha_input)}
            res_busqueda = requests.get(f"{API_URL}/buscar-lote/", params=parametros)
            datos_lote = res_busqueda.json()
            
            if datos_lote.get("status") == "success":
                st.success("✅ ¡Lote encontrado!")
                st.info(f"**Lote:** {datos_lote['produccion']['lote']} | **Producto:** {datos_lote['produccion']['descripcion']} | **Total:** {datos_lote['produccion']['cantidad_kg']:,.2f} Kg")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### 🌾 Macros")
                    st.dataframe(pd.DataFrame(datos_lote['macros']), use_container_width=True, hide_index=True)
                with c2:
                    st.markdown("#### 🧪 Micros")
                    st.dataframe(pd.DataFrame(datos_lote['micros']), use_container_width=True, hide_index=True)
            else:
                st.error(datos_lote.get("message", "No encontrado"))
        except Exception as e:
            st.error(f"Error en búsqueda: {e}")

# ==============================================================================
# 6. FOOTER
# ==============================================================================
st.divider()
f1, f2, f3 = st.columns(3)
with f1:
    st.markdown("**Desarrollado por:**")
    st.write("👨‍💻 Cristian Tobar Morales")
with f2:
    st.markdown("**Proyecto:**")
    st.write("🐔 Avian Data ML Pipeline")
with f3:
    st.markdown("**Versión:**")
    st.write("🚀 1.2.0 (Abril 2026)")