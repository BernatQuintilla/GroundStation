## Descripción del Proyecto

Este repositorio presenta una estación de tierra, una aplicación de control de drones desarrollada para mejorar la interacción del usuario dentro del entorno DronLab. Construida utilizando el Dron Engineering Ecosystem (DEE) y programada en Python, la aplicación ofrece una plataforma intuitiva y robusta, adecuada tanto para fines educativos como experimentales.

La aplicación integra funcionalidades como monitoreo en tiempo real de telemetría, control manual de vuelo, planificación de misiones y análisis visual de datos, facilitando una experiencia de usuario interactiva e inmersiva. Entre sus características principales destacan la capacidad de diseñar y ejecutar rutas de vuelo complejas, generar imágenes panorámicas mediante la técnica de stitching (unión de imágenes), y realizar control interactivo del dron usando técnicas de reconocimiento de objetos.

## Instrucciones de Instalación

Para ejecutar este proyecto, necesitas instalar algunas dependencias. Estas están listadas en el archivo `requirements.txt` para mayor comodidad.

### Requisitos Previos

- Debes tener **Python 3.8 o superior** instalado en tu sistema. Puedes descargarlo desde [python.org](https://www.python.org/downloads/).
- Se recomienda usar un **entorno virtual** para evitar conflictos con otras bibliotecas de Python que tengas instaladas.
- Para la simulación y el correcto funcionamiento de la aplicación, también se recomienda instalar **Mission Planner**. Puedes descargarlo desde su sitio oficial: [Mission Planner](https://ardupilot.org/planner/docs/mission-planner-installation.html).

### Instalación de Dependencias

Todos los paquetes necesarios están listados en un archivo llamado `requirements.txt`. Para instalarlos, sigue estos pasos:

1. **Clona este repositorio** o descarga el código fuente:

   ```bash
   git clone https://github.com/BernatQuintilla/GroundStation.git
   cd GroundStation

2. **Instala todos los paquetes requeridos**:
   ```bash
   pip install -r requirements.txt

## Explicación del código

En este vídeo se explica la estructura del código y qué hace cada una de las funciones que lo conforman.

[Code Ground Station](https://www.youtube.com/watch?v=2vAB8JKZi_E)

## Video demostrativo

En este vídeo se muestran distintas demostraciones de la aplicación para ilustrar el funcionamiento de sus principales funcionalidades. El vídeo está compuesto por cuatro partes:  

- **Ejecución de una misión en DronLab**, mostrando la operación del dron en el campo de pruebas.  
- **Juego interactivo en entorno simulado**, ejecutando el juego de reconocimiento de objetos en entorno simulado.  
- **Juego interactivo en DronLab**, mostrando la ejecución real del juego en el campo de pruebas.  
- **Misión de stitching**, en la que se muestra la misión de stitching y los resultados obtenidos tras el procesamiento.

[Application Demonstration](https://youtu.be/vOByR9sKV3s)
