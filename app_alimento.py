import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================================================
# 1. Configuración de la página
# ==============================================================================
st.set_page_config(page_title="Dashboard Planta", page_icon="🏭", layout="wide")

st.title("📊 Dashboard de Producción de Alimento")
st.markdown("Monitorización del volumen de alimento fabricado y su distribución por lotes de destino.")

# ==============================================================================
# 2. Subida y Carga de Datos Dinámica
# ==============================================================================
# Este widget permite al usuario cargar un archivo Excel desde su máquina local.
archivo_subido = st.file_uploader("Sube tu archivo Excel de producción de alimento", type=["xls", "xlsx"])


@st.cache_data
def cargar_datos(archivo):
    return pd.read_excel(archivo, sheet_name='Datos')

if archivo_subido is not None:
    try:
        # Cargar los datos utilizando la función definida
        df = cargar_datos(archivo_subido)

        # ==============================================================================
        # 3. Procesamiento y Filtros
        # ==============================================================================
        columnas_interes = ['Efectiva', 'Tipo Trans', 'Lín Producto', 'Numero articulo', 'Descripción', 'Cantidad', 'Lote/Serie']
        df_filtrado = df[columnas_interes].copy()

        # Filtros de creación de alimento
        transaccion_creacion = ['RCT-WO']
        linea_producto_alimento = [15]

        df_creacion = df_filtrado[
            df_filtrado['Tipo Trans'].isin(transaccion_creacion) & 
            df_filtrado['Lín Producto'].isin(linea_producto_alimento)
        ].copy()

        # ==============================================================================
        # 4. Construcción del Dashboard (KPIs y Gráficos)
        # ==============================================================================
        # --- Extracción automática del Mes en Español ---
        meses_espanol = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        # Tomamos la primera fecha
        fecha_referencia = df_creacion['Efectiva'].iloc[0]
        
        # Extraemos el número del mes y el año, y lo armamos en español
        mes_actual = f"{meses_espanol[fecha_referencia.month]} {fecha_referencia.year}"
        
        # --- KPI Principal ---
        col1, col2 = st.columns(2) # Dividir en dos columnas para mejor presentación
        
        with col1:
            st.metric(label="🗓️ Mes de Producción", value=mes_actual)
        
        with col2:
            total_kilos = df_creacion['Cantidad'].sum()
            st.metric(label="⚖️ Total de Alimento Creado (Kg)", value=f"{int(total_kilos):,}".replace(',', '.'))
        
        st.markdown("---")
        
        # --- Preparación de datos para el gráfico ---
        produccion_por_lote = df_creacion.groupby('Lote/Serie')['Cantidad'].sum().reset_index()
        produccion_por_lote = produccion_por_lote.sort_values(by='Cantidad', ascending=False)

        # --- Renderizado del Gráfico ---
        st.subheader("Distribución del Total de Alimento Producido según Sector")
        
        fig, ax = plt.subplots(figsize=(14, 6))
        sns.barplot(
            data=produccion_por_lote, 
            x='Lote/Serie', 
            y='Cantidad', 
            hue='Lote/Serie', 
            palette='magma', 
            legend=False,
            ax=ax # Es importante pasar el 'ax' en Streamlit
        )

        # Añadir etiquetas sobre las barras
        for p in ax.patches:
            ax.annotate(f"{int(p.get_height()):,}".replace(',', '.'), 
                        (p.get_x() + p.get_width() / 2., p.get_height()), 
                        ha='center', va='bottom', 
                        fontsize=10, color='black', xytext=(0, 5), 
                        textcoords='offset points')

        plt.xlabel('Sector', fontsize=12)
        plt.ylabel('Alimento Fabricado (kg)', fontsize=12)
        plt.xticks(rotation=45, ha='right') 
        plt.grid(axis='y', linestyle='--', alpha=0.6)
        plt.tight_layout()

        # Inyectar el gráfico en la web
        st.pyplot(fig)

        # --- Tabla de Detalles (Ocultable) ---
        st.markdown("<br>", unsafe_allow_html=True) # Espaciado
        with st.expander("Ver tabla de datos detallada"):
            st.dataframe(df_creacion, use_container_width=True)

    except Exception as e:
        st.error(f"Error al cargar o procesar el archivo: {e}")