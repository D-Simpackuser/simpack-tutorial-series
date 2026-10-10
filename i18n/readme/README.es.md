# Tutoriales de dinámica ferroviaria con Simpack

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Español](README.es.md) · [한국어](README.ko.md)

**Interacción vehículo–vía–puente · Cuerpos flexibles · Recuperación de tensiones y fatiga**

Este repositorio reúne siete series de tutoriales sobre flujos de trabajo de dinámica ferroviaria con Simpack, Abaqus, Ansys y fe-safe. Su organización abarca modelos de vehículos, carriles y cimentaciones de vía flexibles, acoplamiento vehículo–vía–puente, recuperación de tensiones y deformaciones y análisis de fatiga de cuerpos flexibles.

El catálogo contiene **194 vídeos**. **193 vídeos** incluyen subtítulos chinos e ingleses en formatos SRT y VTT, con un total de **772 archivos de subtítulos**. El vídeo introductorio `0-课程效果` de la serie 5 no tiene subtítulos asociados.

## Catálogo de series

| Serie | Tema | Vídeos | Archivos |
|---|---|---:|---|
| 1 | [Dinámica acoplada de vehículo ferroviario, carril flexible y losa flotante con Abaqus y Simpack](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/1/README.md) | 18 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-1-v1) |
| 2 | [Análisis de tensiones, deformaciones dinámicas y fatiga de cuerpos flexibles con Ansys/Abaqus, Simpack y fe-safe](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/2/README.md) | 13 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-2-v1) |
| 3 | [Dinámica de vehículo ferroviario y vía flexible con Ansys Workbench Mechanical, APDL y Simpack](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/3/README.md) | 16 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-3-v1) |
| 5 | [Dinámica acoplada vehículo–vía–puente con Abaqus y Simpack](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/5/README.md) | 42 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-5-v1) |
| 6 | [Introducción a la dinámica de vehículos ferroviarios con Simpack](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/6/README.md) | 8 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-6-v1) |
| 7 | [Dinámica vehículo–vía–puente con Ansys y Simpack: modelado Beam–Solid](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/7/README.md) | 46 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-7-v1) |
| 8 | [Dinámica vehículo–vía–puente con Ansys y Simpack: modelado Beam–Beam](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/series/8/README.md) | 51 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-8-v1) |

El título de cada serie abre su índice existente de lecciones. Las páginas de release contienen los vídeos y subtítulos descargables. Se conserva la numeración original; no hay serie 4.

## Por dónde empezar

Para crear el primer modelo de vehículo, se recomienda la **serie 6**. Para vía flexible, elija la **serie 1** con Abaqus o la **serie 3** con Ansys; continúe con las **series 5, 7 u 8** para los modelos vehículo–vía–puente. La **serie 2** se centra en recuperación de tensiones y deformaciones y fatiga. Es una propuesta editorial de aprendizaje, no una secuencia de requisitos previos verificada.

## Guía temática

Los grupos siguientes organizan los títulos proporcionados. No demuestran una validación independiente de modelos, resultados numéricos o combinaciones de versiones de software.

### Serie 1 — Dinámica acoplada de vehículo ferroviario, carril flexible y losa flotante con Abaqus y Simpack

- Modelado del carril flexible y de la losa flotante sobre resortes en Abaqus; generación FBI
- Creación de archivos FTR y configuración de la vía flexible en Simpack
- Modelos de eje montado, bastidor de bogie y vehículo completo; acoplamiento con la losa flotante
- Excitaciones TRE / PSD, animación de cuerpos flexibles y posprocesado de respuestas

### Serie 2 — Análisis de tensiones, deformaciones dinámicas y fatiga de cuerpos flexibles con Ansys/Abaqus, Simpack y fe-safe

- Preparación de interfaces Abaqus / Ansys y generación de cuerpos flexibles FBI
- Configuración de cuerpos flexibles y recuperación de tensiones y deformaciones en Simpack
- Visualización de deformadas, tensiones y deformaciones en Simpack Post
- Exportación a fe-safe, análisis de fatiga y ejemplo de flujo de trabajo integrado

### Serie 3 — Dinámica de vehículo ferroviario y vía flexible con Ansys Workbench Mechanical, APDL y Simpack

- Modelo de carril con elementos viga en SpaceClaim; reducción por subestructuras en Workbench Mechanical
- Procedimientos APDL mediante interfaz gráfica y comandos; gestión de la interfaz FBI
- Conexiones de cimentación FTR y configuración por lotes de elementos de fuerza
- Vehículos simplificados, excitaciones TRE / PSD, animación y parámetros de posprocesado

### Serie 5 — Dinámica acoplada vehículo–vía–puente con Abaqus y Simpack

- Carriles, losas de vía CRTS III, capas de hormigón, losas de base y viga de puente simplemente apoyada
- Materiales, malla, sujeciones, contactos internos y generación de subestructuras
- FBI / FTR, vehículos parametrizados, equilibrio estático y acoplamiento vehículo–vía–puente
- Precarga, solucionador, irregularidades de vía y magnitudes de evaluación dinámica tratadas en los vídeos

### Serie 6 — Introducción a la dinámica de vehículos ferroviarios con Simpack

- Modelado del eje montado y del bastidor de bogie
- Ensamblaje del modelo de vehículo completo
- Archivos TRE y excitación PSD
- Posprocesado y análisis de respuestas

### Serie 7 — Dinámica vehículo–vía–puente con Ansys y Simpack: modelado Beam–Solid

- RAIL-EULER, rail-timo, modelos de puente con elementos sólidos y temas modales
- Archivos FBI del carril y del puente; creación y diagnóstico de archivos FTR
- Vehículos parametrizados, orden de acoplamiento, rigidez y amortiguamiento en zonas de transición
- Precarga, solucionador, excitación, respuestas del puente y del carril, organización de modelos

### Serie 8 — Dinámica vehículo–vía–puente con Ansys y Simpack: modelado Beam–Beam

- RAIL-EULER, rail-timo, modelos de puente BEAM188 y temas modales
- Configuración FBI / FTR, vehículos parametrizados y acoplamiento vehículo–vía–puente
- Creación por lotes de puntos de conexión, uniones, apoyos y sensores
- Precarga, solucionador, excitación, posprocesado y organización de modelos

## Descarga y uso

Entre en la serie elegida y descargue el MP4 junto con su archivo `.zh-CN.srt` o `.en.srt`. Conserve el identificador común del nombre y seleccione el subtítulo en su reproductor de vídeo local. También se ofrece VTT. Un clon del repositorio o el archivo Code → Download ZIP no incluye los vídeos almacenados en Releases.

El acceso a las descargas depende de la visibilidad del repositorio. Mientras sea privado, se necesita una cuenta de GitHub autorizada. Los enlaces de vídeo son para descarga y no garantizan un reproductor de streaming integrado.

## Idiomas

La presentación y la guía temática están disponibles en inglés, chino simplificado, japonés, francés, alemán, italiano, español y coreano. Esta localización afecta a los documentos; no añade pistas de subtítulos ni doblaje. Los idiomas actuales de los subtítulos son chino e inglés. Se conservan los títulos originales chinos para identificar con precisión cada lección.

## Alcance y limitaciones técnicas

Este proyecto es una biblioteca de tutoriales, no un benchmark validado ni una distribución de software. Que aparezca un modelo en un vídeo no significa que se incluyan sus archivos, las licencias del solucionador o los datos de entrada. Antes de adaptar un procedimiento, compruebe versiones, unidades, condiciones de contorno, amortiguamiento, ajustes de reducción y criterios de evaluación. Las explicaciones sobre normas históricas no deben tomarse como requisitos vigentes. Beam–Solid y Beam–Beam identifican dos itinerarios, sin demostrar una superioridad en precisión.

La presencia de subtítulos y la coincidencia de sumas de comprobación no acreditan la precisión de las traducciones ni su sincronización con el audio. Contraste los términos técnicos con el vídeo original y la documentación del software correspondiente.

## Correcciones y contribuciones

Al comunicar una corrección, indique la serie, el identificador estable de la lección, el idioma del subtítulo y, cuando proceda, la marca de tiempo. Mantenga los identificadores originales al mejorar un título o traducción. No suba software comercial, archivos de licencia, cursos de terceros o modelos sin el permiso necesario.

## Fuentes y permisos

El mantenimiento del repositorio, la autoría de los cursos y la propiedad del software son funciones distintas. Consulte la declaración de procedencia para conocer las fuentes y los derechos registrados. No se afirma afiliación ni respaldo oficial de los proveedores. El acceso público no constituye una licencia general para reutilizar o redistribuir los contenidos.

[Fuentes y derechos](https://github.com/D-Simpackuser/simpack-tutorial-series/blob/main/PROVENANCE.md)
