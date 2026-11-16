# Climix

Prototipo Streamlit para explorar temperaturas diarias de Huánuco. Al iniciar, carga automáticamente `datos/climix_nasa_power_huanuco_2015_2025_limpio.csv`; el archivo debe permanecer en esa ruta dentro del proyecto. La app conserva el selector de años, los indicadores, el gráfico interactivo y la comparación de dos periodos.

## Fuente y alcance

La serie proviene de NASA POWER para un punto/celda en Huánuco (-9.9306, -76.2422) y está basada en el reanálisis MERRA-2. No representa todo el departamento ni corresponde a mediciones directas de una estación meteorológica. `T2M_AVG` es el promedio derivado de `T2M_MIN` y `T2M_MAX`.

El lector reconoce las columnas `FECHA`, `T2M_MAX`, `T2M_MIN` y `T2M_AVG`, valida su contenido y normaliza los nombres para las vistas. Si el CSV no está disponible o tiene datos inválidos, la app muestra un error en lugar de cargar datos ficticios.

## Preparar el entorno

En Windows, crea y activa un entorno virtual e instala las dependencias:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Ejecutar

Desde la carpeta del proyecto, con el entorno activado:

```powershell
streamlit run app.py
```
