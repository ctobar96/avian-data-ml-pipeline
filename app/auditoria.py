import streamlit as st
import pandas as pd
import requests
import re

def orden_natural(lote):
    return [int(texto) if texto.isdigit() else texto.lower() for texto in re.split(r'(\d+)', lote)]

def mostrar(API_URL):
    lista_lotes = []
    try:
        res_lotes = requests.get(f"{API_URL}/listado-lotes/")
        if res_lotes.status_code == 200:
            lista_lotes = sorted(res_lotes.json().get("lotes", []), key=orden_natural)
    except:
        pass

    col_busq1, col_busq2, col_busq3 = st.columns([2, 2, 1])
    with col_busq1:
        fecha_input = st.date_input("🗓️ Fecha de Producción")
    with col_busq2:
        lote_input = st.selectbox("📦 Código del Sector", options=lista_lotes) if lista_lotes else st.text_input("📦 Código del Sector", placeholder="Ej: PICH5A")
    with col_busq3:
        st.markdown("<br>", unsafe_allow_html=True) 
        boton_buscar = st.button("Buscar Registro", type="primary", use_container_width=True)

    if boton_buscar and lote_input:
        with st.spinner("Buscando trazabilidad..."):
            try:
                res_busqueda = requests.get(f"{API_URL}/buscar-lote/", params={"lote": lote_input.strip(), "fecha": str(fecha_input)})
                if res_busqueda.status_code == 200:
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