import os
import time
import threading
import requests


#Nodos disponibles
NODOS = {
    "A": "http://127.0.0.1:5001",
    "B": "http://127.0.0.1:5002",
    "C": "http://127.0.0.1:5003"
}

#Control del cliente
ejecutando = True

#Mensajes ya mostrados
mensajes_mostrados = set()

#Nodo utilizado actualmente
nodo_actual = None
url_actual = None

#Usuario actual
usuario_actual = None

#Control para cambio de nodo
lock_nodo = threading.Lock()


#Limpiar terminal
def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


#Mostrar nodos disponibles
def mostrar_nodos():

    print("\nNodos disponibles:\n")

    for nodo, url in NODOS.items():

        try:

            respuesta = requests.get(
                f"{url}/health",
                timeout=2
            )

            if respuesta.status_code == 200:
                print(f"Nodo {nodo}: ONLINE")

            else:
                print(f"Nodo {nodo}: OFFLINE")

        except requests.RequestException:
            print(f"Nodo {nodo}: OFFLINE")


#Seleccionar nodo
def seleccionar_nodo():

    while True:

        mostrar_nodos()

        opcion = input("\nSelecciona un nodo [A/B/C]: ").strip().upper()

        if opcion not in NODOS:
            print("Nodo no valido")
            continue

        url = NODOS[opcion]

        try:

            respuesta = requests.get(
                f"{url}/health",
                timeout=2
            )

            if respuesta.status_code == 200:
                return opcion, url

        except requests.RequestException:
            pass

        print(f"El Nodo {opcion} no esta disponible")


#Buscar otro nodo disponible
def buscar_nodo_disponible(nodo_anterior):

    for nodo, url in NODOS.items():

        if nodo == nodo_anterior:
            continue

        try:

            respuesta = requests.get(
                f"{url}/health",
                timeout=2
            )

            if respuesta.status_code == 200:

                return nodo, url

        except requests.RequestException:
            continue

    return None, None

#Cambiar automaticamente de nodo
def cambiar_nodo(nodo_fallido):

    global nodo_actual
    global url_actual
    global usuario_actual

    with lock_nodo:

        #Otro hilo ya cambio el nodo
        if nodo_actual != nodo_fallido:
            return True

        print(f"\nNodo {nodo_fallido} no responde")
        print("Buscando otro nodo disponible...")

        nuevo_nodo, nueva_url = buscar_nodo_disponible(
            nodo_fallido
        )

        if nuevo_nodo is None:

            print("No hay otros nodos disponibles")

            return False

        try:

            respuesta = requests.post(
                f"{nueva_url}/usuarios/conectar",
                json={
                    "nombre": usuario_actual
                },
                timeout=3
            )

            #200 = registrado
            #409 = ya estaba registrado
            if respuesta.status_code not in [200, 409]:

                print(
                    f"No se pudo registrar el usuario en Nodo {nuevo_nodo}"
                )

                return False

            nodo_actual = nuevo_nodo
            url_actual = nueva_url

            print(
                f"Conexion recuperada en Nodo {nuevo_nodo}"
            )

            return True

        except requests.RequestException:

            print(
                f"No se pudo conectar con Nodo {nuevo_nodo}"
            )

            return False

#Conectar usuario
def conectar_usuario(url):

    while True:

        nombre = input("\nNombre de usuario: ").strip()

        if not nombre:
            print("El nombre no puede estar vacio")
            continue

        try:

            respuesta = requests.post(
                f"{url}/usuarios/conectar",
                json={
                    "nombre": nombre
                },
                timeout=3
            )

            if respuesta.status_code == 200:

                datos = respuesta.json()

                print(datos["mensaje"])

                return nombre

            else:

                error = respuesta.json()

                print(
                    "Error:",
                    error.get("detail", "No se pudo conectar")
                )

        except requests.RequestException:
            print("No se pudo establecer conexion con el nodo")


#Mostrar mensajes nuevos
def recibir_mensajes():

    global ejecutando
    global nodo_actual
    global url_actual

    while ejecutando:

        nodo_consultado = nodo_actual
        url_consultada = url_actual

        try:

            respuesta = requests.get(
                f"{url_consultada}/mensajes",
                timeout=3
            )

            if respuesta.status_code == 200:

                datos = respuesta.json()

                for mensaje in datos["mensajes"]:

                    mensaje_id = mensaje["id"]

                    if mensaje_id not in mensajes_mostrados:

                        mensajes_mostrados.add(
                            mensaje_id
                        )

                        print(
                            f"\n[{mensaje['usuario']} | Nodo {mensaje['nodo_origen']}]"
                        )

                        print(
                            mensaje["contenido"]
                        )

                        print(
                            "> ",
                            end="",
                            flush=True
                        )

        except requests.RequestException:

            cambiar_nodo(
                nodo_consultado
            )

        time.sleep(2)


#Mostrar usuarios
def mostrar_usuarios(url):

    try:

        respuesta = requests.get(
            f"{url}/usuarios",
            timeout=3
        )

        if respuesta.status_code == 200:

            datos = respuesta.json()

            print(
                f"\nUsuarios conectados en Nodo {datos['nodo']}:"
            )

            if datos["total"] == 0:

                print("No hay usuarios conectados")

            else:

                for usuario in datos["usuarios"]:
                    print("-", usuario["nombre"])

    except requests.RequestException:
        print("No se pudo consultar usuarios")


#Enviar mensaje
def enviar_mensaje(usuario, contenido):

    global nodo_actual
    global url_actual

    nodo_envio = nodo_actual
    url_envio = url_actual

    try:

        respuesta = requests.post(
            f"{url_envio}/mensajes",
            json={
                "usuario": usuario,
                "contenido": contenido
            },
            timeout=5
        )

        if respuesta.status_code != 200:

            datos = respuesta.json()

            print(
                "Error:",
                datos.get(
                    "detail",
                    "No se pudo enviar el mensaje"
                )
            )

    except requests.RequestException:

        print(
            f"\nSe perdio la conexion con Nodo {nodo_envio}"
        )

        cambio = cambiar_nodo(
            nodo_envio
        )

        if cambio:

            try:

                respuesta = requests.post(
                    f"{url_actual}/mensajes",
                    json={
                        "usuario": usuario,
                        "contenido": contenido
                    },
                    timeout=5
                )

                if respuesta.status_code == 200:

                    print(
                        f"Mensaje enviado mediante Nodo {nodo_actual}"
                    )

                else:

                    print(
                        "No se pudo enviar el mensaje"
                    )

            except requests.RequestException:

                print(
                    "No se pudo recuperar la conexion"
                )


#Desconectar usuario
def desconectar_usuario(url, usuario):

    try:

        requests.delete(
            f"{url}/usuarios/{usuario}",
            timeout=3
        )

    except requests.RequestException:
        pass


#Cliente principal
def main():

    global ejecutando
    global nodo_actual
    global url_actual
    global usuario_actual

    limpiar()

    print("===================================")
    print("            NodeMesh")
    print("      Chat Distribuido")
    print("===================================")

    nodo_actual, url_actual = seleccionar_nodo()

    print(
        f"\nConectado al Nodo {nodo_actual}"
    )

    usuario_actual = conectar_usuario(
        url_actual
    )

    usuario = usuario_actual

    hilo_mensajes = threading.Thread(
        target=recibir_mensajes,
        daemon=True
    )

    hilo_mensajes.start()

    print("\nComandos disponibles:")
    print("/usuarios  Mostrar usuarios")
    print("/ayuda     Mostrar comandos")
    print("/salir     Cerrar cliente")

    print("\nPuedes comenzar a escribir mensajes.\n")

    while ejecutando:

        try:

            contenido = input("> ").strip()

            if not contenido:
                continue

            if contenido == "/salir":

                ejecutando = False

                desconectar_usuario(
                    url_actual,
                    usuario
                )

                print("\nCliente desconectado")

                break

            elif contenido == "/usuarios":

                mostrar_usuarios(url_actual)

            elif contenido == "/ayuda":

                print("\n/usuarios  Mostrar usuarios")
                print("/ayuda     Mostrar comandos")
                print("/salir     Cerrar cliente")

            else:

                enviar_mensaje(
                    usuario,
                    contenido
                )

        except KeyboardInterrupt:

            ejecutando = False

            desconectar_usuario(
                url_actual,
                usuario
            )

            break


if __name__ == "__main__":
    main()