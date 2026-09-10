import time
import threading

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

#Configuracion del nodo
NODE_ID = "A"
NODE_PORT = 5001

#Tiempo de inicio del nodo
inicio_nodo = time.time()

#Crear aplicacion FastAPI
app = FastAPI(
    title="NodeMesh - Nodo A",
    description="Nodo del proyecto de Sistemas Distribuidos",
    version="1.0"
)

#Usuarios
usuarios = {}

#Controlar acceso a los datos
lock = threading.Lock()

#Modelo para recibir usuarios
class Usuario(BaseModel):
    nombre: str

#Validar nombre
def validar_nombre(nombre):

    nombre = nombre.strip()

    if nombre == "":
        raise HTTPException(
            status_code=400,
            detail="El nombre no puede estar vacio."
        )

    if len(nombre) > 15:
        raise HTTPException(
            status_code=400,
            detail="Maximo 15 caracteres."
        )

    if " " in nombre:
        raise HTTPException(
            status_code=400,
            detail="El nombre no puede contener espacios."
        )

    return nombre

#Ruta principal
@app.get("/")
def inicio():

    return {
        "proyecto": "NodeMesh",
        "nodo": NODE_ID,
        "mensaje": "Nodo A funcionando"
    }

#Comprobar estado del nodo
@app.get("/health")
def health():

    return {
        "estado": "online",
        "nodo": NODE_ID,
        "puerto": NODE_PORT
    }

#Mostrar informacion del nodo
@app.get("/estado")
def estado():

    tiempo_activo = time.time() - inicio_nodo

    with lock:
        cantidad_usuarios = len(usuarios)

    return {
        "nodo": NODE_ID,
        "puerto": NODE_PORT,
        "estado": "online",
        "tiempo_activo_segundos": round(tiempo_activo, 2),
        "usuarios_conectados": cantidad_usuarios
    }

#Conectar usuario
@app.post("/usuarios/conectar")
def conectar_usuario(datos: Usuario):

    nombre = validar_nombre(datos.nombre)

    with lock:

        #Evitar nombres repetidos
        if nombre in usuarios:
            raise HTTPException(
                status_code=409,
                detail="Nombre ya utilizado."
            )

        #Guardar usuario
        usuarios[nombre] = {
            "nombre": nombre,
            "nodo": NODE_ID,
            "hora_conexion": time.strftime("%H:%M:%S")
        }

    print(nombre + " se conecto al Nodo " + NODE_ID)

    return {
        "ok": True,
        "mensaje": "Bienvenido " + nombre,
        "usuario": nombre,
        "nodo": NODE_ID
    }

#Mostrar usuarios
@app.get("/usuarios")
def mostrar_usuarios():

    with lock:
        lista_usuarios = list(usuarios.values())

    return {
        "cantidad": len(lista_usuarios),
        "usuarios": lista_usuarios
    }

#Desconectar usuario
@app.delete("/usuarios/{nombre}")
def desconectar_usuario(nombre: str):

    nombre = nombre.strip()

    with lock:

        if nombre not in usuarios:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado."
            )

        del usuarios[nombre]

    print(nombre + " se desconecto del Nodo " + NODE_ID)

    return {
        "ok": True,
        "mensaje": nombre + " se desconecto.",
        "nodo": NODE_ID
    }