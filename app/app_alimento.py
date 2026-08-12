import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter 
import plotly.express as px
import requests
import re
import plotly.graph_objects as go

# 1. CONFIGURACIÓN Y URL
try:
    API_URL = st.secrets["API_URL"]
except:
    API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Dashboard Planta", page_icon="🏭", layout="wide")

# ==============================================================================
# 2. SECCIÓN DE CARGA (OPCIONAL/EXPANDER)
# ==============================================================================
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
                            st.rerun() # Forzamos recarga para actualizar el selector de meses
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")


# ==============================================================================
# 3. SELECTORES DE FILTRO (MES Y SECTOR)
# ==============================================================================
with col_selector:  
    st.subheader("Selecciona el Mes que Deseas Visualizar")
    periodo_seleccionado = None

    try:
        res_meses = requests.get(f"{API_URL}/listado-meses/")  # Obtenemos la lista de meses disponibles en la base de datos
        if res_meses.status_code == 200:
            lista_periodos = res_meses.json().get("periodos", []) # La Api entrega la lista ordenada
            
            if lista_periodos:
                # Selector de Mes en la parte principal (o st.sidebar.selectbox si prefieres)
                periodo_seleccionado = st.selectbox(
                    "Selecciona período",
                    options=lista_periodos,
                    index=0, #El index 0 siempre será el mes más reciente gracias a la API
                    label_visibility="collapsed"
                )
            else:
                st.info("La base de datos está vacía. Sube un archivo para comenzar.")
    except Exception as e:
        st.error(f"No se pudo conectar con la API para obtener los periodos: {e}")

st.divider()

# ==============================================================================
# 4. VISUALIZACIÓN DE MÉTRICAS Y GRÁFICO 
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
                
                if not df_grafico.empty:
                    # Ordenamos de mayor a menor (vital para el gráfico y para el TOP)
                    df_grafico = df_grafico.sort_values(by="Cantidad", ascending=False)
                        
                    # Extraemos el ganador (la fila 0 de la columna 'Lote')
                    sector_top = df_grafico.iloc[0]['Lote']
                else:
                    sector_top = "Sin datos"

                # --- KPIs ---
                st.subheader("📌 Indicadores Generales")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric(label="🗓️ Periodo Visualizado", value=mes_actual)
                    
                with col2:
                    # Formateo con puntos para miles (Estilo Chileno)
                    val_formateado = f"{int(total_kg):,}".replace(',', '.')
                    st.metric(label="⚖️ Total Alimento (Kg)", value=val_formateado)

                with col3:
                    st.metric( "🏭 Sectores", len(datos["datos_lotes"]))
            
                with col4:
                    st.metric("🥇 Sector Top", value= sector_top)
                
                # Variable por defecto por si no hay datos históricos
                variacion_pct = 0
                
                with col5:
                        # 1. Extraemos el valor del mes anterior que nos mandó la API
                        total_kg_anterior = datos.get("total_kg_anterior", 0)
                        
                        # 2. Calculamos el porcentaje
                        if total_kg_anterior > 0:
                            diferencia_kg = total_kg - total_kg_anterior
                            variacion_pct = ((diferencia_kg) / total_kg_anterior) * 100
                            delta_str = f"{variacion_pct:.1f}%"
                            
                            # Formateamos la diferencia en kilos para mostrarla
                            # Si es positiva le ponemos un "+", si es negativa el "-" se pone solo
                            signo = "+" if diferencia_kg > 0 else ""
                            valor_mostrar = f"{signo}{int(diferencia_kg):,}".replace(',', '.') + " Kg"
                            
                        elif total_kg > 0 and total_kg_anterior == 0:
                            valor_mostrar = "+ " + f"{int(total_kg):,}".replace(',', '.') + " Kg"
                            delta_str = "100% (Sin historial)"
                        else:
                            valor_mostrar = "0 Kg"
                            delta_str = None
                        
                        # 3. Dibujamos la métrica con los valores dinámicos
                        st.metric(
                            label="📈 Variación vs Mes Ant.", 
                            value=valor_mostrar, 
                            delta=delta_str,
                            delta_color="normal" 
                        )
                
                # =====================================================
                # ALERTAS AUTOMÁTICAS (Tu código integrado)
                # =====================================================
                # Solo mostramos alertas si realmente hay un mes anterior para comparar
                # en vez de 10 se puede usar desviación estandar
                if total_kg_anterior > 0:
                    if variacion_pct > 10:
                        st.success(f"🚀 ¡Excelente! La producción aumentó un {variacion_pct:.1f}% respecto al mes anterior.")
                    elif variacion_pct < -10:
                        st.error(f"⚠️ Atención: La producción disminuyó un {abs(variacion_pct):.1f}% respecto al mes anterior.")
                    else:
                        st.info(f"📊 La producción se mantuvo relativamente estable con una variación del {variacion_pct:.1f}%.")

                # =====================================================
                # TENDENCIA MENSUAL
                # =====================================================
                st.markdown("---")
                st.subheader("📈 Evolución Mensual")

                with st.spinner("Cargando historial de producción..."):
                    try:
                        res_tendencia = requests.get(f"{API_URL}/tendencia-mensual/")
                        
                        if res_tendencia.status_code == 200:
                            datos_tendencia = res_tendencia.json().get("tendencia", [])
                            
                            if datos_tendencia:
                                df_mensual = pd.DataFrame(datos_tendencia)
                                
                                # Limpieza segura para garantizar que son números
                                df_mensual["Cantidad"] = df_mensual["Cantidad"].astype(str).str.replace(",", "", regex=False)
                                df_mensual["Cantidad"] = pd.to_numeric(df_mensual["Cantidad"], errors="coerce").fillna(0)

                                # ===========================================================
                                # TU ESTILO DE GRÁFICO (Seaborn)
                                # ===========================================================
                                sns.set_theme(style="white")
                                fig_line, ax_line = plt.subplots(figsize=(16, 5))
                                
                                # 1. Reiniciamos estilos previos y preparamos colores para fondo oscuro
                                plt.rcdefaults()
                                plt.rc('axes', edgecolor='#666666', labelcolor='#cccccc')
                                plt.rc('xtick', color='#cccccc')
                                plt.rc('ytick', color='#cccccc')
                                
                                # 2. Creamos figura con FONDO TRANSPARENTE
                                fig_line, ax_line = plt.subplots(figsize=(16, 5))
                                fig_line.patch.set_alpha(0.0) 
                                ax_line.patch.set_alpha(0.0)
                                
                                # Trazamos la línea con marcadores grandes (puntos)
                                sns.lineplot(
                                    data=df_mensual, x="mes", y="Cantidad", 
                                    marker="o", color="#00d4ff", linewidth=3, 
                                    markersize=10, ax=ax_line
                                )

                                # 1. Formateador de eje Y (Tu código exacto)
                                
                                def formato_abreviado(x, pos):
                                    if x >= 1000000:
                                        return f"{x/1000000:.2f}M" # 2.25M
                                    elif x >= 1000:
                                        return f"{x/1000:.0f}K" # 2.3K
                                    else:
                                        return str(int(x)) # 900
                                ax_line.yaxis.set_major_formatter(FuncFormatter(formato_abreviado))
                                
                                # Aseguramos que el gráfico empiece en 0 y le damos un 15% de espacio arriba para que quepan los números
                                min_val = df_mensual["Cantidad"].min()
                                max_val = df_mensual["Cantidad"].max()

                                # Le damos un pequeño margen arriba y abajo
                                margen = (max_val - min_val) * 0.4 if max_val != min_val else max_val * 0.1
                                ax_line.set_ylim(min_val - margen, max_val + margen * 1.5)


                    
                                # 2. Anotaciones sobre los puntos (Equivalente a tu loop de patches)
                                for index, row in df_mensual.iterrows():
                                    label = f"{int(row['Cantidad']):,}".replace(",", ".")
                                    ax_line.annotate(
                                        label, 
                                        (row['mes'], row['Cantidad']), 
                                        ha='center', va='bottom', 
                                        fontsize=11, fontweight='bold', color="white", # Letra blanca
                                        xytext=(0, 15), textcoords='offset points'
                                )

                                # 3. Estilos de grilla y limpieza (Tu código exacto)
                                ax_line.set_ylabel("Total Alimento (Kg)", labelpad=15, fontsize=11)
                                ax_line.set_xlabel("") # Ocultamos el título "mes" para que quede más limpio
                                
                                # Grilla horizontal muy suave para no distraer
                                plt.grid(axis='y', linestyle='--', alpha=0.15, color='#ffffff')
                                sns.despine(left=True, bottom=False) # Eliminamos bordes innecesarios
                                plt.tight_layout()
                             
                                st.pyplot(fig_line)
                                plt.close(fig_line)
                                
                                # Restauramos el estilo blanco por si el gráfico de barras que sigue lo necesita
                                sns.set_theme(style="white")
                                
                            else:
                                st.info("No hay suficientes datos históricos para mostrar una tendencia.")
                        else:
                            st.error("Error en la API al obtener la tendencia.")
                            
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")
                    
                st.markdown("---")
                # --- GRÁFICO ---
                if not df_grafico.empty:
                    # 🛡️ BLINDAJE ÚNICO: Convertimos a número inmediatamente al recibir los datos.
                    # Esto asegura que el ordenamiento de col_graf1 y el nlargest de col_graf2 funcionen perfecto.
                    df_grafico["Cantidad"] = pd.to_numeric(df_grafico["Cantidad"], errors="coerce").fillna(0)

                    col_graf1, col_graf2 = st.columns([6, 4]) 
                    
                    # ==========================================
                    # COLUMNA 1: DISTRIBUCIÓN (BARRAS HORIZONTALES)
                    # ==========================================
                    with col_graf1:
                        st.subheader("🏭 Distribución de Producción por Sector") 
                            
                        # 1. ORDENAR LOS DATOS (Mayor a menor) - Ahora es 100% confiable numéricamente
                        df_grafico = df_grafico.sort_values(by="Cantidad", ascending=False)
                        
                        # 2. ESTILO MODO OSCURO (Fondo transparente)
                        plt.rcdefaults()
                        plt.rc('axes', edgecolor='#666666', labelcolor='#cccccc')
                        plt.rc('xtick', color='#cccccc')
                        plt.rc('ytick', color='#cccccc')

                        # Ajustamos el tamaño (más alto para dar espacio a todas las barras horizontales)
                        fig, ax = plt.subplots(figsize=(12, 8))
                        fig.patch.set_alpha(0.0) 
                        ax.patch.set_alpha(0.0)
                            
                        # 3. GRÁFICO HORIZONTAL (Invertimos X e Y)
                        sns.barplot(
                            data=df_grafico, 
                            x="Cantidad", # Define el largo de la barra
                            y="Lote",     # Eje vertical
                            hue="Lote", 
                            palette="magma", 
                            legend=False, 
                            ax=ax,
                            edgecolor="#cccccc", # Borde claro para evitar que la barra oscura se pierda
                            linewidth=1
                        )

                        # 4. Formateador de eje X
                        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{int(x):,}".replace(",", ".")))
                            
                        # Damos un 15% extra de espacio a la derecha para que las anotaciones no se corten
                        max_val = df_grafico["Cantidad"].max()
                        ax.set_xlim(0, max_val * 1.15)
                            
                        # 5. Anotaciones sobre barras horizontales
                        for p in ax.patches:
                            width = p.get_width() # Medimos el largo de la barra
                            if width > 0:
                                label = f"{int(width):,}".replace(",", ".")
                                ax.annotate(label, 
                                            (width, p.get_y() + p.get_height() / 2.), 
                                            ha='left', va='center', 
                                            fontsize=10, fontweight='bold', color='white', 
                                            xytext=(5, 0), textcoords='offset points')

                        # 6. Limpieza visual
                        ax.set_ylabel("") 
                        ax.set_xlabel("")  
                        
                        # Grilla vertical suave
                        plt.grid(axis='x', linestyle='--', alpha=0.15, color='#ffffff')
                        sns.despine(left=True, bottom=True) 
                        ax.set_xticks([]) 
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)

                    # ==========================================
                    # COLUMNA 2: PARTICIPACIÓN (DONA PLOTLY)
                    # ==========================================
                    with col_graf2:
                        st.subheader("📊 Participación (Top 10)")
                        
                        # 1. Hacemos una copia aislada de las 10 primeras filas (ya ordenadas por el gráfico de barras)
                        top10 = df_grafico.head(10).copy().reset_index(drop=True) 
                        
                        # 2. BLINDAJE EXTREMO PARA PLOTLY
                        # Obligamos a Pandas a ignorar cualquier formato previo y convertir esto en un Float matemático puro.
                        # Si hay algún texto raro o coma flotando, lo forzará a un número limpio.
                        top10["Valor_Plotly"] = top10["Cantidad"].astype(float)
                        
                        # 3. Dibujamos usando NUESTRA NUEVA COLUMNA ("Valor_Plotly")
                        fig_pie = go.Figure(data=[go.Pie(
                            labels=top10["Lote"].tolist(),
                            values=top10["Valor_Plotly"].tolist(),  # ← listas Python puras, sin pandas
                            hole=0.5,
                            textposition='inside',
                            textinfo='percent+label',
                            hovertemplate="<b>%{label}</b><br>Cantidad: %{value:,.0f} Kg<br>Participación: %{percent}<extra></extra>",
                            marker=dict(colors=px.colors.sequential.Plasma)
                        )])

                        fig_pie.update_traces(
                            textposition='inside',
                            textinfo='percent+label',
                            # Le decimos a Plotly que le ponga los puntos de miles solo visualmente al pasar el mouse
                            hovertemplate="<b>%{label}</b><br>Cantidad: %{value:,.0f} Kg<br>Participación: %{percent}<extra></extra>"
                        )

                        fig_pie.update_layout(
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="white"),
                            showlegend=False, 
                            
                            margin=dict(t=30, b=20, l=20, r=20)
                        )

                        st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.error(f"🚨 La API rechazó la petición. Código: {res_resumen.status_code}. Detalle: {res_resumen.text}")


                # ---------------------------------------------------------
                # PARTE C: GRÁFICOS DE MACROS Y MICROS (PLOTLY)
                # ---------------------------------------------------------
                st.markdown("---")
                st.subheader("🌾 Consumo Detallado de Insumos")

                # 1. Diccionario traductor de meses
                meses_texto = {
                    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
                    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
                    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
                }
                
                texto_periodo = str(periodo_seleccionado).lower() 
                
                # 2. Buscamos el año y el mes
                match_anio = re.search(r'\d{4}', texto_periodo)
                anio_consulta = int(match_anio.group()) if match_anio else None
                
                mes_consulta = None
                for nombre_mes, numero_mes in meses_texto.items():
                    if nombre_mes in texto_periodo:
                        mes_consulta = numero_mes
                        break
                
                # 3. Llamada a la API
                if anio_consulta and mes_consulta:
                    res_mensual = requests.get(f"{API_URL}/consumo-mensual/", params={"anio": anio_consulta, "mes": mes_consulta})
                    
                    if res_mensual.status_code == 200:
                        datos_mensuales = res_mensual.json()
                        
                        if datos_mensuales.get("status") == "success":
                            df_macros = pd.DataFrame(datos_mensuales["macros"])
                            df_micros = pd.DataFrame(datos_mensuales["micros"])

                            c_graf1, c_graf2 = st.columns(2)

                            with c_graf1:
                                st.markdown("**Macros Consumidos (Kg)**")
                                if not df_macros.empty:
                                    fig_macros = px.bar(
                                        df_macros, 
                                        x="Cantidad (Kg)", 
                                        y="Materia Prima", 
                                        orientation='h', 
                                        color="Cantidad (Kg)",
                                        color_continuous_scale="viridis", 
                                        text_auto='.2s',
                                        hover_data=["Número Artículo"] 
                                    )
                                    fig_macros.update_layout(yaxis={'categoryorder':'total ascending'})
                                    st.plotly_chart(fig_macros, use_container_width=True)
                                else:
                                    st.info("No hay registros de Macros para este periodo.")

                            with c_graf2:
                                st.markdown("**Micros Consumidos (Kg)**")
                                if not df_micros.empty:
                                    fig_micros = px.bar(
                                        df_micros, 
                                        x="Cantidad (Kg)", 
                                        y="Materia Prima", 
                                        orientation='h',
                                        color="Cantidad (Kg)",
                                        color_continuous_scale="magma", 
                                        text_auto='.2s',
                                        hover_data=["Número Artículo"] 
                                    )
                                    fig_micros.update_layout(yaxis={'categoryorder':'total ascending'})
                                    st.plotly_chart(fig_micros, use_container_width=True)
                                else:
                                    st.info("No hay registros de Micros para este periodo.")
                        else:
                            st.warning(datos_mensuales.get("message", "Error procesando insumos."))
                    else:
                        st.error(f"Error de la API (Código {res_mensual.status_code}): {res_mensual.text}")                
                else:
                    st.warning(f"No pudimos identificar el mes y año en el texto: {periodo_seleccionado}")
                    





                # =====================================================
                # HEATMAP DE PRODUCCIÓN
                # =====================================================
                st.markdown("---")
                st.subheader("Producción por sector y mes")
                with st.spinner("Generando heatmap..."):
                    try:
                        # Llamamamos a la API para obtener los datos del heatmap
                        res_historico = requests.get(f"{API_URL}/historicos-sectores/")

                        if res_historico.status_code == 200:
                            datos_historicos = res_historico.json().get("historico", [])
                            df_heat = pd.DataFrame(datos_historicos)

                            if not df_heat.empty:
                                # 1. Creamos la matriz pivot exactamente igual
                                pivot = df_heat.pivot_table(
                                    values="cantidad",
                                    index="lote_destino",
                                    columns="mes_formateado", 
                                    aggfunc="sum",
                                    fill_value=0
                                )
                                # Cambiar nombre lote_destino para que se vea en el gráfico
                                pivot.index.name = "Sector de Consumo"
                                # ==========================================
                                # AJUSTE NUEVO: Enviar nombres largos al final
                                # ==========================================
                                # Aseguramos que los nombres sean texto para poder contar sus letras
                                pivot.index = pivot.index.astype(str)
                                
                                # 1. Separamos los nombres en dos grupos usando 12 caracteres como límite
                                nombres_normales = [lote for lote in pivot.index if len(lote) <= 12]
                                nombres_largos   = [lote for lote in pivot.index if len(lote) > 12]
                                
                                # 2. Ordenamos cada grupo alfabéticamente por separado
                                nombres_normales.sort()
                                nombres_largos.sort()
                                
                                # 3. Reordenamos la tabla completa usando .loc 
                                # (Ponemos los normales primero y los largos se van al fondo)
                                pivot = pivot.loc[nombres_normales + nombres_largos]

                                formato_chileno = lambda x: f"{int(x):,}".replace(",", ".")

                                # AJUSTE 2: Barra de Leyenda de Calor (HTML)
                                min_val = pivot.values.min()
                                max_val = pivot.values.max()

                                st.markdown(
                                    f"""
                                    <div style="display: flex; justify-content: space-between; font-size: 13px; color: #cccccc; margin-bottom: 5px;">
                                        <span>Menor Producción: <b>{formato_chileno(min_val)} kg</b></span>
                                        <span>Mayor Producción: <b>{formato_chileno(max_val)} kg</b></span>
                                    </div>
                                    <div style="height: 15px; width: 100%; border-radius: 6px; margin-bottom: 15px;
                                         background: linear-gradient(to right, #440154, #31688e, #35b779, #fde725);">
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                
                                estilos_encabezados = [
                                    {
                                        "selector": "th", # "th" significa Table Header (Encabezados)
                                        "props": [
                                            ("font-weight", "bold"),  # Letra en negrita
                                            ("text-align", "center")  # Texto centrado
                                        ]
                                    }
                                ]
                                # Le decimos a Pandas que pinte el fondo de las celdas según su valor
                                # axis=None asegura que el color se calcule usando TODA la tabla
                                pivot_heatmap = (
                                    pivot.style
                                    .background_gradient(cmap="viridis", axis=None)
                                    .format(formato_chileno) # Formateamos con separador de miles y sin decimales
                                    .set_properties(**{"text-align": "center"}) # Centramos los números
                                    .set_table_styles(estilos_encabezados)      # Aplicamos la negrita arriba y a la izquierda
                                )

                                # 2. Lo mostramos usando st.dataframe, que soporta estilos de Pandas
                                st.dataframe(
                                    pivot_heatmap, 
                                    use_container_width=True,
                                    height=600
                                )

                            else:
                                st.warning("No hay suficientes datos históricos para el mapa de calor.")                                
                        else:
                            st.error(f"La API rechazó la petición. Código: {res_historico.status_code}. Detalle: {res_historico.text}")
                    except Exception as e:
                        st.error(f"Error al generar heatmap: {e}")
                    
        except Exception as e:
            st.error(f"Error al procesar visualización: {e}")

# ==============================================================================
# 5. BUSCADOR DE TRAZABILIDAD
# ==============================================================================
st.markdown("---")
st.title("🔍 Buscador de Trazabilidad por Lote")

# Obtenemos la lista de lotes para el selector
lista_lotes = []

# Función de Ordenamiento Natural: Convierte "PICH4A" en ['PICH', 4, 'A'] para ordenar correctamente
def orden_natural(lote):
    return [int(texto) if texto.isdigit() else texto.lower() for texto in re.split(r'(\d+)', lote)]


try:
    res_lotes =  requests.get(f"{API_URL}/listado-lotes/")
    if res_lotes.status_code == 200:
        lista_bruta = res_lotes.json().get("lotes", [])
        lista_lotes = sorted(lista_bruta, key=orden_natural)
        if not lista_lotes:
            st.info("No hay lotes disponibles. Sube un archivo para comenzar.")
    else:
        st.error(f"Error al obtener lotes: Código {res_lotes.status_code}")
        lista_lotes = []
except Exception as e:
    st.error(f"Error de conexión al obtener lotes: {e}")

# 2. Dibujamos los controles
col_busq1, col_busq2, col_busq3 = st.columns([2, 2, 1])
with col_busq1:
    fecha_input = st.date_input("🗓️ Fecha de Producción")
with col_busq2:
    if lista_lotes:
        lote_input = st.selectbox("📦 Código del Sector", options=lista_lotes) 
    else: 
        lote_input = st.text_input("📦 Código del Sector", placeholder="Ej: PICH5ACO") # Fallback de emergencia por si la base de datos está vacía
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
                st.info(f"**Lote:** {datos_lote['produccion']['lote']} | **Producto:** {datos_lote['produccion']['descripcion']} | **Total:** {datos_lote['produccion']['cantidad_kg']:,.0f} Kg")
                
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
