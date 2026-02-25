# 🗺️ DibujaPy — Generador de Mapas de Baja California

Programa en Python para generar mapas de la **Península de Baja California** usando datos de [Natural Earth](https://www.naturalearthdata.com/).

![Mapa de ejemplo](mapa_ejemplo.png)

## ✨ Características

- **Datos automáticos**: descarga y cachea datos de Natural Earth (1:10m)
- **Paletas de colores**: 4 esquemas incluidos (clásico, nocturno, topográfico, blanco/negro) — personalizables vía JSON
- **Zonas de interés**: marca puntos geográficos con círculos de color e IDs, leyendo datos desde archivos JSON
- **Múltiples datasets** (en `dibuja.py`): estados, ciudades, países y carreteras en capas seleccionables
- **Área configurable**: define latitud y longitud del mapa
- **Exportación PNG** a 200 DPI

## 📁 Estructura del proyecto

```
dibujapy/
├── mapa.py                  # Mapa con soporte de zonas personalizadas
├── dibuja.py                # Mapa con 4 datasets de Natural Earth
├── mapa_baja_california.py  # Versión básica (contorno + paletas)
├── requirements.txt         # Dependencias
├── datos/
│   ├── paletas.json         # Paletas de colores personalizables
│   ├── zonas.json           # Zonas de interés (puntos geográficos)
│   └── capas_zonas.json     # Registro de archivos de zonas
└── .gitignore
```

## 🚀 Instalación

```bash
# Clonar el repositorio
git clone https://github.com/TU_USUARIO/dibujapy.git
cd dibujapy

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🎮 Uso

### Mapa con zonas personalizadas
```bash
python mapa.py
```
Permite:
1. Elegir paleta de colores
2. Activar archivos de zonas (puntos de interés)
3. Configurar el área del mapa
4. Solo muestra zonas dentro del área visible

### Mapa con múltiples datasets
```bash
python dibuja.py
```
Permite combinar capas:
- Estados/Provincias (contornos)
- Ciudades/Localidades (puntos)
- Países (fronteras)
- Carreteras principales

### Mapa básico
```bash
python mapa_baja_california.py
```

## 🎨 Paletas disponibles

| # | Paleta | Descripción |
|---|--------|-------------|
| 1 | Clásico | Fondo blanco, contornos azul marino |
| 2 | Nocturno | Fondo oscuro, acentos cyan |
| 3 | Topográfico | Verde/tierra, estilo geográfico |
| 4 | Blanco y Negro | Ideal para impresión |

Agrega tus propias paletas editando `datos/paletas.json`.

## 📌 Zonas personalizadas

Crea archivos JSON en `datos/` con esta estructura:

```json
{
    "nombre": "Mis zonas",
    "zonas": [
        {
            "id": 1,
            "nombre": "Bahía Almejas",
            "latitud": 24.47,
            "longitud": -111.8,
            "figura": "circulo",
            "color": "rojo"
        }
    ]
}
```

Luego regístralo en `datos/capas_zonas.json`:
```json
{
    "archivos": [
        {"archivo": "mi_archivo.json", "descripcion": "Mis zonas"}
    ]
}
```

**Colores soportados** (en español): rojo, azul, verde, amarillo, naranja, morado, rosa, negro, blanco, gris, café, cyan, magenta, turquesa, dorado, plateado — o códigos hex (#ff0000).

## 📊 Fuente de datos

[Natural Earth](https://www.naturalearthdata.com/) — datos geográficos públicos y gratuitos, resolución 1:10m.

Los archivos ZIP se descargan automáticamente en la primera ejecución y se guardan en `datos/` para uso futuro.

## 📋 Requisitos

- Python 3.8+
- geopandas
- matplotlib
- shapely
- numpy

## 📄 Licencia

Uso libre. Los datos de Natural Earth son de dominio público.
