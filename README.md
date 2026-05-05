# AvianData: Pipeline de Ingeniería de Datos y Predicción de Calidad para la Industria Avícola

## Descripción del Proyecto
Este proyecto desarrolla un pipeline de datos de extremo a extremo (ETL) y modelos predictivos para optimizar el rendimiento biológico y clasificar la calidad comercial en la producción de huevos.




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

