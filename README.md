# NodeMesh - Sistema de Chat Distribuido

## Proyecto de Sistemas Distribuidos

NodeMesh es la adaptación de un proyecto de chat cliente-servidor desarrollado en Python hacia una arquitectura distribuida.

## Arquitectura propuesta

El sistema estará compuesto por tres nodos independientes:

- Nodo A: puerto 5001
- Nodo B: puerto 5002
- Nodo C: puerto 5003

Cada nodo ejecutará una instancia independiente de FastAPI.

## Comunicación

Los nodos se comunicarán mediante HTTP sobre TCP utilizando una API REST desarrollada con FastAPI.

La información se intercambiará en formato JSON.

Los nodos no utilizarán memoria compartida; toda la comunicación entre ellos se realizará mediante red.

## Tolerancia a fallos

Si uno de los nodos deja de funcionar, los demás nodos continuarán operando.

Los nodos podrán verificar la disponibilidad de otros nodos mediante endpoints como:

GET /health

Los clientes podrán conectarse a otro nodo disponible si el nodo que estaban utilizando deja de funcionar.

## Stack tecnológico

- Python 3
- FastAPI
- Uvicorn
- Docker Desktop
- GitHub
- Postman
- ngrok
- draw.io

## Estructura inicial

Proyecto_Sistemas_Distribuidos/
- cliente/
- diagramas/
- nodo/
- postman/
- pruebas/
- requirements.txt
- README.md