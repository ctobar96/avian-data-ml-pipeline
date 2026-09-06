import streamlit as st
import pandas as pd
import requests
import seaborn as sns
import matplotlib.pyplot as plt
import re

def mostrar(periodo_seleccionado, API_URL):
    if not periodo_seleccionado:
        return

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

                # Despliegue directo en la misma pestaña dividiendo en 2 columnas
                c_graf1, c_graf2 = st.columns(2)
                with c_graf1: 
                    renderizar_grafico(df_macros, "Macros", "viridis")
                with c_graf2: 
                    renderizar_grafico(df_micros, "Micros", "magma")
            else:
                st.warning("Error procesando insumos.")
        else:
            st.error(f"Error del Backend (Código {res_mensual.status_code}): {res_mensual.text}")

def renderizar_grafico(df, titulo, paleta):
    st.markdown(f"**{'🌾' if titulo=='Macros' else '🧪'} {titulo} Consumidos (Kg)**")
    if not df.empty:
        # Ordenar de mayor a menor para mantener la legibilidad
        df = df.sort_values(by="Cantidad (Kg)", ascending=False)
        
        # Crear la figura y los ejes para matplotlib/seaborn
        fig, ax = plt.subplots(figsize=(6, 4))
        
        sns.barplot(
            data=df, 
            x="Cantidad (Kg)", 
            y="Materia Prima", 
            hue="Materia Prima", 
            palette=paleta, 
            legend=False,
            ax=ax
        )
        
        # Limpieza visual del gráfico
        ax.set_ylabel("")
        ax.set_xlabel("Cantidad (Kg)")
        sns.despine()
        
        # Agregar los valores numéricos al final de cada barra
        for p in ax.patches:
            width = p.get_width()
            if width > 0:
                ax.text(width + (width * 0.02), 
                        p.get_y() + p.get_height() / 2, 
                        f'{width:.1f}', 
                        ha='left', va='center', fontsize=9)
                    
        # Renderizar en Streamlit
        st.pyplot(fig)
    else:
        st.info(f"No hay registros de {titulo}.")