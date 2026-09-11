import time
import threading

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


#Configuracion del nodo
NODE_ID = "A"
NODE_PORT = 5001

#Tiempo de inicio
inicio_nodo = time.time()

#Usuarios conectados
usuarios = {}

#Control de acceso a usuarios
lock = threading.Lock()


#Modelo de usuario
class Usuario(BaseModel):
    nombre: str


#Crear aplicacion FastAPI
app = FastAPI(
    title="NodeMesh - Nodo A",
    description="Nodo del proyecto de Sistemas Distribuidos",
    version="1.0"
)


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


#Informacion del nodo
@app.get("/estado")
def estado():
    tiempo_activo = time.time() - inicio_nodo

    with lock:
        total_usuarios = len(usuarios)

    return {
        "nodo": NODE_ID,
        "puerto": NODE_PORT,
        "estado": "online",
        "tiempo_activo_segundos": round(tiempo_activo, 2),
        "usuarios_conectados": total_usuarios
    }


#Conectar usuario
@app.post("/usuarios/conectar")
def conectar_usuario(usuario: Usuario):

    nombre = usuario.nombre.strip()

    #Validar nombre
    if not nombre:
        raise HTTPException(
            status_code=400,
            detail="El nombre no puede estar vacio"
        )

    if len(nombre) > 15:
        raise HTTPException(
            status_code=400,
            detail="El nombre no puede tener mas de 15 caracteres"
        )

    if " " in nombre:
        raise HTTPException(
            status_code=400,
            detail="El nombre no puede contener espacios"
        )

    #Registrar usuario
    with lock:

        if nombre in usuarios:
            raise HTTPException(
                status_code=409,
                detail="El usuario ya esta conectado"
            )

        usuarios[nombre] = {
            "nombre": nombre,
            "nodo": NODE_ID,
            "estado": "conectado"
        }

    return {
        "mensaje": "Usuario conectado correctamente",
        "usuario": nombre,
        "nodo": NODE_ID
    }


#Mostrar usuarios
@app.get("/usuarios")
def obtener_usuarios():

    with lock:
        lista_usuarios = list(usuarios.values())

    return {
        "nodo": NODE_ID,
        "total": len(lista_usuarios),
        "usuarios": lista_usuarios
    }


#Desconectar usuario
@app.delete("/usuarios/{nombre}")
def desconectar_usuario(nombre: str):

    with lock:

        if nombre not in usuarios:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        del usuarios[nombre]

    return {
        "mensaje": "Usuario desconectado correctamente",
        "usuario": nombre,
        "nodo": NODE_ID
    }