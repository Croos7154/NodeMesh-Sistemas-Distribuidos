import time
import threading
import uuid

from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


#Configuracion del nodo
NODE_ID = "A"
NODE_PORT = 5001

#Tiempo de inicio
inicio_nodo = time.time()

#Usuarios conectados
usuarios = {}

#Mensajes del nodo
mensajes = []

#Control de acceso
lock = threading.Lock()


#Modelo de usuario
class Usuario(BaseModel):
    nombre: str


#Modelo de mensaje
class Mensaje(BaseModel):
    usuario: str
    contenido: str


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
        total_mensajes = len(mensajes)

    return {
        "nodo": NODE_ID,
        "puerto": NODE_PORT,
        "estado": "online",
        "tiempo_activo_segundos": round(tiempo_activo, 2),
        "usuarios_conectados": total_usuarios,
        "mensajes_locales": total_mensajes
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


#Enviar mensaje
@app.post("/mensajes")
def enviar_mensaje(mensaje: Mensaje):

    usuario = mensaje.usuario.strip()
    contenido = mensaje.contenido.strip()

    #Validar usuario
    if not usuario:
        raise HTTPException(
            status_code=400,
            detail="El usuario no puede estar vacio"
        )

    #Validar contenido
    if not contenido:
        raise HTTPException(
            status_code=400,
            detail="El mensaje no puede estar vacio"
        )

    #Comprobar usuario conectado
    with lock:

        if usuario not in usuarios:
            raise HTTPException(
                status_code=404,
                detail="El usuario no esta conectado"
            )

        nuevo_mensaje = {
            "id": str(uuid.uuid4()),
            "usuario": usuario,
            "contenido": contenido,
            "nodo_origen": NODE_ID,
            "fecha": datetime.now(timezone.utc).isoformat()
        }

        mensajes.append(nuevo_mensaje)

    return {
        "mensaje": "Mensaje enviado correctamente",
        "datos": nuevo_mensaje
    }


#Mostrar mensajes
@app.get("/mensajes")
def obtener_mensajes():

    with lock:
        lista_mensajes = mensajes.copy()

    return {
        "nodo": NODE_ID,
        "total": len(lista_mensajes),
        "mensajes": lista_mensajes
    }