import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import re

def mostrar(periodo_seleccionado, API_URL):
    if not periodo_seleccionado:
        return

    tipo_ver = st.radio(
        "Filtro de Categoría:",
        options=["Mostrar Ambos", "Solo Macros", "Solo Micros"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("<br>", unsafe_allow_html=True) 

    meses_texto = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, 
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    texto_periodo = str(periodo_seleccionado).lower() 
    match_anio = re.search(r'\d{4}', texto_periodo)
    anio_consulta = int(match_anio.group()) if match_anio else None
    
    mes_consulta = next((num for mes, num in meses_texto.items() if mes in texto_periodo), None)
    
    if anio_consulta and mes_consulta:
        res_mensual = requests.get(f"{API_URL}/consumo-mensual/", params={"anio": anio_consulta, "mes": mes_consulta})
        if res_mensual.status_code == 200:
            datos_mensuales = res_mensual.json()
            if datos_mensuales.get("status") == "success":
                df_macros = pd.DataFrame(datos_mensuales["macros"])
                df_micros = pd.DataFrame(datos_mensuales["micros"])

                if tipo_ver == "Mostrar Ambos":
                    c_graf1, c_graf2 = st.columns(2)
                    with c_graf1: renderizar_grafico(df_macros, "Macros", "viridis")
                    with c_graf2: renderizar_grafico(df_micros, "Micros", "magma")
                elif tipo_ver == "Solo Macros":
                    renderizar_grafico(df_macros, "Macros", "viridis")
                elif tipo_ver == "Solo Micros":
                    renderizar_grafico(df_micros, "Micros", "magma")
            else:
                st.warning("Error procesando insumos.")
        else:
            st.error(f"Error del Backend (Código {res_mensual.status_code}): {res_mensual.text}")

def renderizar_grafico(df, titulo, escala_color):
    st.markdown(f"**{'🌾' if titulo=='Macros' else '🧪'} {titulo} Consumidos (Kg)**")
    if not df.empty:
        fig = px.bar(df, x="Cantidad (Kg)", y="Materia Prima", orientation='h', color="Cantidad (Kg)", color_continuous_scale=escala_color, text_auto='.2s', hover_data=["Número Artículo"])
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No hay registros de {titulo}.")