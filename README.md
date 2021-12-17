# XWingSimulator

![Demo](docs/animation.gif)

## Información

XWingSimulator es un simple juego multijugador en línea donde un jugador al ingresar recibe una nave X-Wing la cual puede utilizar para moverse por el mundo y ver a otros jugadores
conectados que se encuentran en el rango de visión del mismo.

## Instalación

Se pueden instalar todas las dependencias, tanto del servidor como del cliente, utilizando el archivo requirements.txt: ``pip install -r requirements.txt``. Adicionalmente, existen múltiples parámetros
configurables que se encuentran en las primeras líneas del programa del servidor y del cliente.

## Uso

El programa ``servidor.py`` contiene la implementación del servidor. Este debe estar corriendo para que los clientes, que ejecutan ``cliente.py``, se puedan conectar. Adicionalmente
existe un programa ``testing.py`` para hacer pruebas de conexión de múltiples usuarios al mismo tiempo.

Para manejar el X-Wing se utilizan las teclas clásicas de dirección ``W/A/S/D`` y para cerrar el programa basta con presionar la tecla ``Q``. 

## Información

Este programa fue desarrollado en el contexto del curso de Redes de Computadoras de la Facultad de Ingeniería - UDELAR.

#### Integrantes

  - Guillermo Toyos
  - Federico Vallcorba
  - Santiago Olmedo


