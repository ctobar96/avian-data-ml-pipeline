## 3. ESTRATEGIA DE VISUALIZACIÓN (DATA STORYTELLING)
Para asegurar la correcta interpretación por parte de la directiva, el dashboard interactivo desplegará los datos mediante la siguiente suite de componentes visuales de última generación:

```text
+---------------------------------------------------------------------------------+
|                       SUITE DE VISUALIZACIÓN GERENCIAL                          |
+---------------------------------------------------------------------------------+
|                                                                                 |
|  1. MAPA DE CALOR DE CORRELACIONES (Seaborn)                                    |
|     [Matriz divergente que cruza: Alimento, Agua, Edad, Mortalidad y Huevos]    |
|     -> Propósito: Identificar qué variable impacta más a la rentabilidad.       |
|                                                                                 |
|  2. GRÁFICO DE DISPERSIÓN DINÁMICO (Plotly Express)                             |
|     [Eje X: Alimento | Eje Y: Huevos | Tamaño: Edad | Color: Mortalidad]        |
|     -> Propósito: Detectar qué sectores específicos están subproductivos.        |
|                                                                                 |
|  3. DOBLE EJE Y INTERACTIVO (Plotly Graph Objects)                              |
|     [Barras: Toneladas de Alimento | Línea: % de Postura Real]                  |
|     -> Propósito: Evaluar visualmente el Costo de Insumo vs. Retorno Diario.    |
|                                                                                 |
|  4. IMPORTANCIA DE FACTORES (Plotly Bar Horizontal)                             |
|     [Barras ordenadas por peso estadístico del Modelo de Machine Learning]      |
|     -> Propósito: Demostrar científicamente la causa raíz de las variaciones.   |
|                                                                                 |
|  5. EMBUDO DE PROYECCIÓN (Plotly Forecast Funnel)                               |
|     [Línea histórica continua + Línea punteada de predicción con sombra de error]|
|     -> Propósito: Anticipar el volumen de ventas e inventario futuro.          |
|                                                                                 |
+---------------------------------------------------------------------------------+

```