# 🐔 AvianData: Pipeline de Ingeniería de Datos y Predicción de Calidad para la Industria Avícola

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31-FF4B4B.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)


## 📌 Descripción del Proyecto
Este proyecto desarrolla un pipeline de datos de extremo a extremo (ETL) y modelos predictivos para optimizar el rendimiento biológico y clasificar la calidad comercial en la producción de huevos.

## 🏗️ Arquitectura del Sistema
El proyecto está construido bajo una arquitectura de microservicios para separar la lógica de negocio de la interfaz de usuario:
* **Frontend (Streamlit):** Interfaz interactiva para la carga de datos y visualización de KPIs gerenciales.
* **Backend (FastAPI):** Motor de procesamiento de datos, cálculos estadísticos y futura inferencia de modelos predictivos.
* **Análisis (Jupyter):** Exploratory Data Analysis (EDA) para el descubrimiento de patrones y selección de características.

## ⚙️ Tecnologías Utilizadas
* **Manipulación de Datos:** Pandas, Numpy
* **Visualización:** Matplotlib, Seaborn
* **Despliegue y API:** Streamlit, FastAPI, Uvicorn
* **Machine Learning:** (Próximamente: Scikit-Learn, XGBoost)

## 🚀 Instrucciones de Ejecución Local

Para correr este proyecto en tu máquina local, sigue estos pasos:

```bash
# 1. Entra a la carpeta del proyecto
cd tu-repositorio

# 2. Crea el entorno virtual limpio
python3 -m venv env

# 3. Activa el entorno
source env/bin/activate

# 4. Instala las librerías necesarias (si tienes el archivo)
pip install -r requirements.txt

# 5. Abre Visual Studio Code conectado a Linux
code .
```

1. **Clona el repositorio e instala las dependencias:**
   ```bash
   git clone [https://github.com/TU_USUARIO/avian-data-ml-pipeline.git](https://github.com/TU_USUARIO/avian-data-ml-pipeline.git)
   cd avian-data-ml-pipeline
   pip install -r requirements.txt
    ```

2. **Inicia el Servidor de Procesamiento (FastAPI):**  
Abre una terminal y ejecuta:
    ```bash
    uvicorn src.api:app --reload
    ```
    (El servidor estará escuchando en http://127.0.0.1:8000)


3. **Inicia el Dashboard (Streamlit):**  
Abre una segunda terminal y ejecuta:
    ```bash
    streamlit run app/app_alimento.py
    ```




```text
avian-data-ml-pipeline/
│
├── data/                      # 🗄️ Todo lo relacionado con datos (No subir a GitHub)
│   ├── raw/                   # Archivos originales (ej. ALIMENTOENERO2026.xls)
│   └── processed/             # Tablas limpias y cruzadas listas para Machine Learning
│
├── notebooks/                 # 📓 Cuadernos de experimentación y análisis
│   ├── 01_limpieza_datos.ipynb
│   └── 02_eda_produccion.ipynb
│
├── src/                       # 🧠 Backend y Lógica de Negocio (El "Cerebro")
│   ├── api.py                 # Tu servidor de FastAPI
│   └── modelos_ml.py          # (En el futuro) Aquí irá tu código de Random Forest/XGBoost
│
├── app/                       # 💻 Frontend e Interfaz (La "Cara")
│   └── app_alimento.py        # Tu dashboard de Streamlit
│
├── models/                    # 🤖 Modelos ya entrenados (archivos .pkl o .joblib)
│
├── .gitignore                 # 🛡️ Archivo de seguridad clave
├── requirements.txt           # 📦 Lista de librerías y dependencias
└── README.md                  # 📖 La portada de tu portafolio
```

Diagrama ER simple
```text
┌──────────────────────────────────────────────┐
│              produccion_alimento            │
├──────────────────────────────────────────────┤
│ id (PK)                                     │
│ fecha_efectiva                              │
│ lote_destino                                │
│ descripcion                                 │
│ cantidad_kg                                 │
│ UNIQUE(                                     │
│   lote_destino,                             │
│   fecha_efectiva,                           │
│   cantidad_kg                               │
│ )                                           │
└──────────────────────────────────────────────┘
                 ▲
                 │
        Foreign Key (produccion_id)
                 │
        ┌────────┴────────┐
        │                 │

┌────────────────────────────────────┐
│      consumo_insumos_macros        │
├────────────────────────────────────┤
│ id (PK)                            │
│ produccion_id (FK)                 │
│ materia_prima                      │
│ cantidad_consumida                 │
└────────────────────────────────────┘


┌────────────────────────────────────┐
│      consumo_insumos_micros        │
├────────────────────────────────────┤
│ id (PK)                            │
│ produccion_id (FK)                 │
│ materia_prima                      │
│ cantidad_consumida                 │
└────────────────────────────────────┘

Relaciones:
produccion_alimento
    ├── 1:N → consumo_insumos_macros
    └── 1:N → consumo_insumos_micros
```

``` Dockerfile 
# Usamos una versión ligera de Python
FROM python:3.10-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos primero los requerimientos para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código (incluyendo api.py y la carpeta src si la tienes)
COPY . .

# Exponemos el puerto de FastAPI
EXPOSE 8000

# Comando para encender la API
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

```


## 👨‍💻 Autor

**Cristian Tobar Morales**
*Data Scientist | Analytics Engineer*

Especialista en análisis de datos, ingeniería de datos y desarrollo de soluciones basadas en datos. Este proyecto forma parte de mi portafolio técnico y tiene como objetivo demostrar la implementación de un pipeline de datos utilizando herramientas modernas de Data Engineering.

### 🔗 Contacto
* **LinkedIn:** [Cristian Tobar Morales](#)
* **GitHub:** [@ctobar96](https://github.com/ctobar96)

---

## 📄 Licencia

Este proyecto está disponible bajo la **Licencia MIT**.

Nota: Los datos brutos (/data) están ignorados por motivos de confidencialidad comercial.
