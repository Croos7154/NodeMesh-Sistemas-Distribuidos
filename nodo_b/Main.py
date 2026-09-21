import time
import threading
import uuid
import requests
import os

from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


#Configuracion del nodo
NODE_ID = "B"
NODE_PORT = 5002

#Nodos remotos
PEERS = {
    "A": os.getenv(
        "PEER_A_URL",
        "http://127.0.0.1:5001"
    ),
    "C": os.getenv(
        "PEER_C_URL",
        "http://127.0.0.1:5003"
    )
}

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


#Modelo de mensaje replicado
class MensajeReplicado(BaseModel):
    id: str
    usuario: str
    contenido: str
    nodo_origen: str
    fecha: str

#Crear aplicacion FastAPI
app = FastAPI(
    title="NodeMesh - Nodo B",
    description="Nodo del proyecto de Sistemas Distribuidos",
    version="1.0"
)


#Ruta principal
@app.get("/")
def inicio():
    return {
        "proyecto": "NodeMesh",
        "nodo": NODE_ID,
        "mensaje": "Nodo B funcionando"
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

#Comprobar si un mensaje ya existe
def mensaje_existe(id_mensaje):

    for mensaje in mensajes:

        if mensaje["id"] == id_mensaje:
            return True

    return False

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

    #Replicar mensaje a los otros nodos
    replicados = []
    fallidos = []

    for peer_id, peer_url in PEERS.items():

        try:

            respuesta = requests.post(
                f"{peer_url}/mensajes/replicar",
                json=nuevo_mensaje,
                timeout=3
            )

            if respuesta.status_code == 200:
                replicados.append(peer_id)
            else:
                fallidos.append(peer_id)

        except requests.RequestException:
            fallidos.append(peer_id)

    return {
        "mensaje": "Mensaje enviado correctamente",
        "datos": nuevo_mensaje,
        "replicado": len(fallidos) == 0,
        "replicados": replicados,
        "fallidos": fallidos
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

#Comprobar comunicacion con otros nodos
@app.get("/nodo-remoto")
def nodo_remoto():

    resultados = []

    for peer_id, peer_url in PEERS.items():

        try:

            respuesta = requests.get(
                f"{peer_url}/health",
                timeout=3
            )

            respuesta.raise_for_status()

            resultados.append({
                "nodo": peer_id,
                "estado": "online",
                "respuesta": respuesta.json()
            })

        except requests.RequestException:

            resultados.append({
                "nodo": peer_id,
                "estado": "offline"
            })

    return {
        "nodo_local": NODE_ID,
        "nodos_remotos": resultados
    }

#Recibir mensaje replicado
@app.post("/mensajes/replicar")
def replicar_mensaje(mensaje: MensajeReplicado):

    nuevo_mensaje = {
        "id": mensaje.id,
        "usuario": mensaje.usuario,
        "contenido": mensaje.contenido,
        "nodo_origen": mensaje.nodo_origen,
        "fecha": mensaje.fecha
    }

    with lock:

        #Evitar mensajes duplicados
        if mensaje_existe(mensaje.id):

            return {
                "mensaje": "El mensaje ya existe",
                "nodo": NODE_ID
            }

        mensajes.append(nuevo_mensaje)

    return {
        "mensaje": "Mensaje replicado correctamente",
        "nodo": NODE_ID,
        "datos": nuevo_mensaje
    }