# NodeMesh - Sistema de Chat Distribuido

![Arquitectura del Sistema Distribuido](diagramas/arquitectura_distribuido.png)

## Proyecto de Sistemas Distribuidos

NodeMesh es la adaptación de un proyecto de chat cliente-servidor desarrollado en Python hacia una arquitectura distribuida.

## Arquitectura del sistema

### ¿Cuántos nodos tendrá el sistema?

El sistema estará compuesto por 3 nodos independientes: Nodo A, Nodo B y Nodo C.

Durante las pruebas locales se utilizarán los siguientes puertos:

- Nodo A: puerto 5001
- Nodo B: puerto 5002
- Nodo C: puerto 5003

Cada nodo ejecutará su propia instancia de FastAPI como un proceso independiente.

### ¿Cómo se van a comunicar?

Los nodos se comunicarán mediante HTTP sobre TCP utilizando una API REST desarrollada con FastAPI.

La información será intercambiada en formato JSON. Los nodos no utilizarán memoria compartida; toda la comunicación entre ellos se realizará mediante la red.

Esto permitirá intercambiar información relacionada con usuarios, salas, mensajes, estado de los nodos y sincronización del sistema.

### ¿Qué pasa si uno falla?

Si uno de los nodos deja de funcionar, los demás nodos continuarán operando.

Los nodos podrán comprobar la disponibilidad de otros nodos mediante endpoints de diagnóstico como:

`GET /health`

Si un cliente pierde la conexión con el nodo que estaba utilizando, podrá conectarse a otro nodo disponible.

Durante el desarrollo del proyecto se implementará replicación y sincronización de información entre los nodos para mejorar la tolerancia a fallos y permitir que un nodo pueda reincorporarse al sistema después de recuperarse.

## Versión de Python

El proyecto utiliza Python 3 como lenguaje principal de desarrollo.

La versión instalada y utilizada para el proyecto se muestra en la siguiente evidencia:

![Versión de Python](capturas/python_version.png)

## Tecnologías utilizadas

El proyecto utiliza las siguientes herramientas y tecnologías:

- Python 3
- FastAPI
- Uvicorn
- Docker Desktop
- GitHub
- Postman
- ngrok
- draw.io

## Estructura del proyecto

La estructura inicial del proyecto es la siguiente:

````text
Proyecto_Sistemas_Distribuidos/
├── capturas/
│   └── python_version.png
├── cliente/
├── diagramas/
│   ├── arquitectura_distribuida.drawio
│   └── arquitectura_distribuida.png
├── nodo/
│   └── Main.py
├── postman/
│   ├── collections/
│   └── environments/
├── pruebas/
├── .gitignore
├── README.md
└── requirements.txt

Cada carpeta tiene una función específica dentro del proyecto:

- `nodo/`: contiene la aplicación FastAPI correspondiente a los nodos del sistema.
- `cliente/`: contendrá el cliente que se comunicará con los nodos.
- `diagramas/`: contiene el diagrama de arquitectura y su archivo editable.
- `capturas/`: contiene evidencias solicitadas durante el desarrollo.
- `postman/`: contiene las colecciones y entornos utilizados para probar la API.
- `pruebas/`: se utilizará para pruebas adicionales del sistema.
- `requirements.txt`: contiene las dependencias de Python necesarias para ejecutar el proyecto.

## Estado actual del desarrollo

Actualmente se encuentra implementado el primer nodo del sistema distribuido.

El Nodo A utiliza FastAPI y se ejecuta localmente en el puerto `5001`.

Hasta el momento se encuentran disponibles los siguientes endpoints:

- `GET /`: muestra información general del nodo.
- `GET /health`: permite comprobar si el nodo se encuentra disponible.
- `GET /estado`: muestra información sobre el estado y tiempo de actividad del nodo.

El Nodo A puede ejecutarse con el siguiente comando:

```bash
uvicorn Main:app --host 0.0.0.0 --port 5001
````

## Entregable 2 - Funcionamiento del Primer Nodo

### Objetivo

Comprobar el funcionamiento del primer nodo del proyecto utilizando una arquitectura cliente-servidor.

En esta etapa se trabajó únicamente con el Nodo A, ejecutado mediante FastAPI en el puerto 5001.

Postman fue utilizado como cliente para realizar peticiones HTTP al servidor y verificar el funcionamiento de los diferentes endpoints implementados.

### Nodo implementado

El primer nodo del sistema corresponde al:

- Nodo A
- Puerto: 5001
- Framework: FastAPI
- Servidor ASGI: Uvicorn

El nodo se ejecuta mediante:

```powershell
python -m uvicorn nodo_a.Main:app --host 0.0.0.0 --port 5001
```

## Entregable 3 - Conversión a Sistema Distribuido

### Objetivo

Convertir el nodo único desarrollado anteriormente en un sistema distribuido con múltiples nodos independientes capaces de comunicarse y sincronizar mensajes mediante red.

### Nodos implementados

Actualmente el sistema utiliza dos nodos independientes:

- Nodo A: puerto 5001
- Nodo B: puerto 5002

Cada nodo ejecuta su propia instancia de FastAPI y mantiene su propia memoria para usuarios y mensajes.

### Ejecución de los nodos

Nodo A:

```powershell
python -m uvicorn nodo_a.Main:app --host 0.0.0.0 --port 5001
```
