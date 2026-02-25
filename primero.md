
Analyzed
c:\Users\mpacheco\Desktop\Proyectos\dibujapy
El directorio tiene un virtual environment. Voy a crear el programa. Primero necesito instalar las dependencias necesarias y luego crear el script.

El plan es:

Usar Natural Earth como fuente de datos geográficos (fuente confiable y estándar mundial)
Usar geopandas + matplotlib para dibujar el contorno
Filtrar los estados de Baja California y Baja California Sur
Ran background command
…\dibujapy > .\venv\Scripts\python.exe -m pip install geopandas matplotlib
PS C:\Users\mpacheco\Desktop\Proyectos\dibujapy>        
PS C:\Users\mpacheco\Desktop\Proyectos\dibujapy> ^C     
PS C:\Users\mpacheco\Desktop\Proyectos\dibujapy> cd 'c:\Users\mpacheco\Desktop\Proyectos\dibujapy'
PS C:\Users\mpacheco\Desktop\Proyectos\dibujapy> .\venv\Scripts\python.exe -m pip install geopandas matplotlib  


Collecting geopandas
  Downloading geopandas-1.1.2-py3-none-any.whl.metadata (2.3 kB)
Successfully installed certifi-2026.2.25 contourpy-1.3.upgrade pipapy\venv\Scripts\python.exe -m pip install --u
[notice] To update, run: C:\Users\mpacheco\Desktop\Proye
Exit code 0
Checked command status
Las dependencias se instalaron correctamente. Ahora voy a crear el script de Python:

Created
+214
-0
Ahora voy a ejecutar el programa:

Ran background command
…\dibujapy > .\venv\Scripts\python.exe mapa_baja_california.py
Exit code 0
Checked command status
Está descargando los datos. Esperemos un poco más:

Checked command status
Está descargando los datos. Vamos a esperar a que termine:

Checked command status
El mapa ya se generó. La ventana de matplotlib está abierta mostrando el mapa. Vamos a cerrarla para que el proceso termine:

Checked command status
El programa se ejecutó correctamente. Revisemos la imagen generada:

Analyzed
¡El mapa se generó perfectamente! 🎉

Resultado
El programa se creó y ejecutó exitosamente. Aquí está lo que hace:

Archivo creado: 

mapa_baja_california.py
Fuente de datos: Natural Earth — una fuente pública, gratuita y ampliamente utilizada en cartografía profesional. Se usa el dataset Admin 1 – States, Provinces con resolución 1:10 millones.

Características del mapa:
🗺️ Contorno de la península dibujado en color cyan (#00d4ff)
📍 Dos estados etiquetados: Baja California y Baja California Sur
✂️ Línea divisoria entre ambos estados (línea punteada roja)
🎨 Tema oscuro profesional con cuadrícula sutil
🧭 Indicador de norte (N con flecha)
📐 Ejes con coordenadas (longitud y latitud)
📝 Crédito a la fuente de datos en el subtítulo
💾 Imagen guardada como 

mapa_baja_california.png
 a 200 DPI
Dependencias utilizadas:
geopandas — para cargar y manipular datos geoespaciales
matplotlib — para la visualización
shapely — para unir geometrías (viene con geopandas)
Para volver a ejecutarlo:

bash
.\venv\Scripts\python.exe mapa_baja_california.py
