import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter 
import plotly.express as px
import plotly.graph_objects as go

def mostrar(periodo_seleccionado, API_URL):
    if not periodo_seleccionado:
        return
        
    with st.spinner(f"Consultando datos de {periodo_seleccionado}..."):
        try:
            params = {"periodo": periodo_seleccionado}
            res_resumen = requests.get(f"{API_URL}/resumen-produccion/", params=params)
            
            if res_resumen.status_code == 200:
                datos = res_resumen.json()
                total_kg = datos["total_kg"]
                mes_actual = datos["mes_actual"]
                df_grafico = pd.DataFrame(datos["datos_lotes"])
                
                sector_top = df_grafico.sort_values(by="Cantidad", ascending=False).iloc[0]['Lote'] if not df_grafico.empty else "Sin datos"

                # KPIs
                st.subheader("📌 Indicadores Generales")
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("🗓️ Periodo", mes_actual)
                col2.metric("⚖️ Total Alimento (Kg)", f"{int(total_kg):,}".replace(',', '.'))
                col3.metric("🏭 Sectores", len(datos.get("datos_lotes", [])))
                col4.metric("🥇 Sector Top", sector_top)
                
                total_kg_anterior = datos.get("total_kg_anterior", 0)
                if total_kg_anterior > 0:
                    dif = total_kg - total_kg_anterior
                    var_pct = (dif / total_kg_anterior) * 100
                    col5.metric("📈 Var. vs Mes Ant.", f"{'+' if dif>0 else ''}{int(dif):,}".replace(',', '.') + " Kg", f"{var_pct:.1f}%")
                elif total_kg > 0:
                    col5.metric("📈 Var. vs Mes Ant.", f"+ {int(total_kg):,}".replace(',', '.') + " Kg", "100%")
                else:
                    col5.metric("📈 Var. vs Mes Ant.", "0 Kg", None)

                                # =====================================================
                # ALERTAS AUTOMÁTICAS (Tu código integrado)
                # =====================================================
                # Solo mostramos alertas si realmente hay un mes anterior para comparar
                # en vez de 10 se puede usar desviación estandar
                if total_kg_anterior > 0:
                    if var_pct > 10:
                        st.success(f"🚀 ¡Excelente! La producción aumentó un {var_pct:.1f}% respecto al mes anterior.")
                    elif var_pct < -10:
                        st.error(f"⚠️ Atención: La producción disminuyó un {abs(var_pct):.1f}% respecto al mes anterior.")
                    else:
                        st.info(f"📊 La producción se mantuvo relativamente estable con una variación del {var_pct:.1f}%.")
                
                # Tendencia
                st.markdown("---")
                st.subheader("📈 Evolución Mensual")
                res_tendencia = requests.get(f"{API_URL}/tendencia-mensual/")
                if res_tendencia.status_code == 200 and res_tendencia.json().get("tendencia"):
                    df_mensual = pd.DataFrame(res_tendencia.json().get("tendencia"))
                    df_mensual["Cantidad"] = pd.to_numeric(df_mensual["Cantidad"].astype(str).str.replace(",", "", regex=False), errors="coerce").fillna(0)

                    sns.set_theme(style="white")
                    fig_line, ax_line = plt.subplots(figsize=(16, 5))
                    fig_line.patch.set_alpha(0.0) 
                    ax_line.patch.set_alpha(0.0)
                    plt.rc('axes', edgecolor='#666666', labelcolor='#cccccc')
                    plt.rc('xtick', color='#cccccc')
                    plt.rc('ytick', color='#cccccc')
                    
                    sns.lineplot(data=df_mensual, x="mes", y="Cantidad", marker="o", color="#00d4ff", linewidth=3, markersize=10, ax=ax_line)
                    ax_line.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x/1000000:.2f}M" if x>=1000000 else (f"{x/1000:.0f}K" if x>=1000 else str(int(x)))))
                    
                    for _, row in df_mensual.iterrows():
                        ax_line.annotate(f"{int(row['Cantidad']):,}".replace(",", "."), (row['mes'], row['Cantidad']), ha='center', va='bottom', fontsize=11, fontweight='bold', color="white", xytext=(0, 15), textcoords='offset points')

                    ax_line.set_ylabel("Total Alimento (Kg)", labelpad=15, fontsize=11)
                    ax_line.set_xlabel("") 
                    plt.grid(axis='y', linestyle='--', alpha=0.15, color='#ffffff')
                    sns.despine(left=True, bottom=False) 
                    st.pyplot(fig_line)
                    plt.close(fig_line)
                else:
                    st.info("No hay suficientes datos históricos para mostrar una tendencia.")
                
                # Sectores
                st.markdown("---")
                if not df_grafico.empty:
                    df_grafico["Cantidad"] = pd.to_numeric(df_grafico["Cantidad"], errors="coerce").fillna(0)
                    c1, c2 = st.columns([6, 4]) 
                    
                    with c1:
                        st.subheader("🏭 Distribución por Sector") 
                        df_grafico = df_grafico.sort_values(by="Cantidad", ascending=False)
                        fig, ax = plt.subplots(figsize=(12, 8))
                        fig.patch.set_alpha(0.0) 
                        ax.patch.set_alpha(0.0)
                        sns.barplot(data=df_grafico, x="Cantidad", y="Lote", hue="Lote", palette="magma", legend=False, ax=ax, edgecolor="#cccccc", linewidth=1)
                        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{int(x):,}".replace(",", ".")))
                        for p in ax.patches:
                            if p.get_width() > 0:
                                ax.annotate(f"{int(p.get_width()):,}".replace(",", "."), (p.get_width(), p.get_y() + p.get_height() / 2.), ha='left', va='center', fontsize=10, fontweight='bold', color='white', xytext=(5, 0), textcoords='offset points')
                        ax.set_ylabel("") 
                        ax.set_xlabel("")  
                        plt.grid(axis='x', linestyle='--', alpha=0.15, color='#ffffff')
                        sns.despine(left=True, bottom=True) 
                        ax.set_xticks([]) 
                        st.pyplot(fig)
                        plt.close(fig)

                    with c2:
                        st.subheader("📊 Participación (Top 10)")
                        top10 = df_grafico.head(10).copy()
                        fig_pie = go.Figure(data=[go.Pie(labels=top10["Lote"].tolist(), values=top10["Cantidad"].tolist(), hole=0.5, textinfo='percent+label', hovertemplate="<b>%{label}</b><br>Cantidad: %{value:,.0f} Kg<br>Participación: %{percent}<extra></extra>", marker=dict(colors=px.colors.sequential.Plasma))])
                        fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), showlegend=False, margin=dict(t=30, b=20, l=20, r=20))
                        st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.error("Error al obtener el resumen de producción.")
        except Exception as e:
            st.error(f"Error general: {e}")