import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# ==============================================================================
# 1. Configuración de la página
# ==============================================================================
st.set_page_config(page_title="Dashboard Planta", page_icon="🏭", layout="wide")

st.title("📊 Dashboard de Producción de Alimento")
st.markdown("Monitorización del volumen de alimento fabricado y consumo de materias primas.")

# ==============================================================================
# 2. Carga de Datos Dinámica
# ==============================================================================
archivo_subido = st.file_uploader("Sube tu archivo Excel de producción de alimento", type=["xls", "xlsx"])

@st.cache_data
def cargar_datos(archivo):
    return pd.read_excel(archivo, sheet_name='Datos')

if archivo_subido is not None:
    try:
        df = cargar_datos(archivo_subido)

        # ==============================================================================
        # 3. Procesamiento y Filtros
        # ==============================================================================
        columnas_interes = ['Efectiva', 'Tipo Trans', 'Lín Producto', 'Numero articulo', 'Descripción', 'Cantidad', 'Lote/Serie']
        df_filtrado = df[columnas_interes].copy()

        df_creacion = df_filtrado[
            (df_filtrado['Tipo Trans'] == 'RCT-WO') & 
            (df_filtrado['Lín Producto'] == 15)
        ].copy()

        # ==============================================================================
        # 4. Construcción del Dashboard (KPIs y Gráficos)
        # ==============================================================================
        meses_espanol = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        fecha_referencia = df_creacion['Efectiva'].iloc[0]
        mes_actual = f"{meses_espanol[fecha_referencia.month]} {fecha_referencia.year}"
        
        # --- KPIs ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(label="🗓️ Mes de Producción", value=mes_actual)
        
        with col2:
            total_kilos = df_creacion['Cantidad'].sum()
            st.metric(label="⚖️ Total de Alimento Creado (Kg)", value=f"{int(total_kilos):,}".replace(',', '.'))
        
        st.markdown("---")
        
        # --- Gráficos Lado a Lado ---
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.subheader("Distribución del Total de Alimento Producido según Sector")
            produccion_por_lote = df_creacion.groupby('Lote/Serie')['Cantidad'].sum().reset_index()
            produccion_por_lote = produccion_por_lote.sort_values(by='Cantidad', ascending=False)

            fig1, ax1 = plt.subplots(figsize=(8, 6))
            sns.barplot(data=produccion_por_lote, x='Lote/Serie', y='Cantidad', hue='Lote/Serie', palette='magma', legend=False, ax=ax1)

            ax1.set_ylim(0, ax1.get_ylim()[1] * 1.20)
            ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}".replace(',', '.')))
            
            for p in ax1.patches:
                if p.get_height() > 0:
                    ax1.annotate(f"{int(p.get_height()):,}".replace(',', '.'), 
                                (p.get_x() + p.get_width() / 2., p.get_height()), 
                                ha='center', va='bottom', fontsize=9, color='black', xytext=(0, 5), textcoords='offset points')

            plt.xlabel('Sector', fontsize=12)
            plt.ylabel('Alimento Fabricado (kg)', fontsize=12)
            plt.xticks(rotation=45, ha='right') 
            plt.grid(axis='y', linestyle='--', alpha=0.6)
            plt.tight_layout()

            st.pyplot(fig1)
            plt.close(fig1) # <--- CLAVE PARA EVITAR EL COLAPSO DEL SERVIDOR

        with col_graf2:
            st.subheader("Consumo por Materia Prima")
            df_consumo = df_filtrado[(df_filtrado['Tipo Trans'] == 'ISS-WO')
             & (df_filtrado['Lín Producto'] == 9)].copy()
            df_consumo['Cantidad'] = df_consumo['Cantidad'].abs()
            
            consumo_insumos = df_consumo.groupby('Descripción')['Cantidad'].sum().reset_index()
            consumo_insumos = consumo_insumos.sort_values(by='Cantidad', ascending=False)

            fig2, ax2 = plt.subplots(figsize=(8, 6))
            sns.barplot(data=consumo_insumos, x='Descripción', y='Cantidad', hue='Descripción', palette='viridis', legend=False, ax=ax2)

            ax2.set_ylim(0, ax2.get_ylim()[1] * 1.20)
            ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}".replace(',', '.')))

            for p in ax2.patches:
                if p.get_height() > 0:
                    ax2.annotate(f"{int(p.get_height()):,}".replace(',', '.'), 
                                (p.get_x() + p.get_width() / 2., p.get_height()), 
                                ha='center', va='bottom', fontsize=9, xytext=(0, 5), textcoords='offset points')

            plt.xlabel('Materia Prima', fontsize=12)
            plt.ylabel('Kilos (kg)', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.grid(axis='y', linestyle='--', alpha=0.6)
            plt.tight_layout()
            
            st.pyplot(fig2)
            plt.close(fig2) # <--- CLAVE PARA EVITAR EL COLAPSO DEL SERVIDOR
            
        # --- Tabla de Detalles ---
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("Ver tabla de datos detallada"):
            st.dataframe(df_creacion, use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")

else:
    # Mensaje inicial cuando aún no se sube nada
    st.info("👋 ¡Hola! Por favor, arrastra un archivo de Excel arriba para comenzar a generar tu Dashboard.")

# ==============================================================================
# 5. Pie de Página (Footer)
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
    st.write("🚀 **Versión:** 1.0.0")
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
