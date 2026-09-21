import os
import time
import threading
from datetime import datetime

import requests

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


#Consola Rich
console = Console()

#Nodos disponibles
NODOS = {
    "A": "http://127.0.0.1:5001",
    "B": "http://127.0.0.1:5002",
    "C": "http://127.0.0.1:5003"
}

#Colores de los nodos
COLORES_NODO = {
    "A": "cyan",
    "B": "magenta",
    "C": "green"
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


#Mostrar banner
def mostrar_banner():
    titulo = Text()
    titulo.append("NodeMesh\n", style="bold cyan")
    titulo.append("Sistema de Chat Distribuido\n", style="bold white")
    titulo.append("FastAPI • Docker • Python", style="dim")

    console.print(
        Panel.fit(
            titulo,
            border_style="cyan",
            padding=(1, 6)
        )
    )


#Consultar estado de un nodo
def consultar_estado_nodo(url):
    try:
        respuesta = requests.get(
            f"{url}/health",
            timeout=2
        )

        if respuesta.status_code == 200:
            return True

    except requests.RequestException:
        pass

    return False


#Mostrar nodos disponibles
def mostrar_nodos():
    tabla = Table(
        title="Estado de la red NodeMesh",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold"
    )

    tabla.add_column("Nodo", justify="center")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Puerto", justify="center")
    tabla.add_column("Actual", justify="center")

    for nodo, url in NODOS.items():
        online = consultar_estado_nodo(url)
        color = COLORES_NODO.get(nodo, "white")
        puerto = url.rsplit(":", 1)[-1]

        if online:
            estado = Text("● ONLINE", style="bold green")
        else:
            estado = Text("● OFFLINE", style="bold red")

        actual = Text("●", style=color) if nodo == nodo_actual else Text("")

        tabla.add_row(
            Text(nodo, style=f"bold {color}"),
            estado,
            puerto,
            actual
        )

    console.print()
    console.print(tabla)


#Mostrar ayuda
def mostrar_ayuda():
    tabla = Table(
        title="Comandos disponibles",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )

    tabla.add_column("Comando", style="bold")
    tabla.add_column("Funcion")

    tabla.add_row("/usuarios", "Mostrar usuarios conectados al nodo actual")
    tabla.add_row("/estado", "Mostrar el estado de los nodos A, B y C")
    tabla.add_row("/clear", "Limpiar la terminal")
    tabla.add_row("/ayuda", "Mostrar los comandos disponibles")
    tabla.add_row("/salir", "Cerrar el cliente")

    console.print()
    console.print(tabla)


#Mostrar aviso de error
def mostrar_error(mensaje):
    console.print(f"[bold red]Error:[/bold red] {escape(str(mensaje))}")


#Mostrar mensaje del sistema
def mostrar_sistema(mensaje, estilo="bright_blue"):
    console.print(
        Panel(
            escape(str(mensaje)),
            title="SISTEMA",
            border_style=estilo,
            expand=False
        )
    )


#Mostrar perdida de conexion
def mostrar_falla_nodo(nodo):
    console.print()
    console.print(
        Panel(
            f"El Nodo {escape(str(nodo))} dejo de responder.\n"
            "Buscando otro nodo disponible...",
            title="CONEXION PERDIDA",
            border_style="red",
            expand=False
        )
    )


#Mostrar recuperacion
def mostrar_recuperacion(nodo_anterior, nuevo_nodo):
    console.print(
        Panel(
            f"Nodo {escape(str(nodo_anterior))}  ->  "
            f"Nodo {escape(str(nuevo_nodo))}",
            title="CONEXION RECUPERADA",
            border_style="green",
            expand=False
        )
    )


#Obtener hora de un mensaje
def obtener_hora(fecha):
    if not fecha:
        return ""

    try:
        fecha_obj = datetime.fromisoformat(
            fecha.replace("Z", "+00:00")
        )

        return fecha_obj.astimezone().strftime("%H:%M")

    except (ValueError, TypeError):
        return ""


#Mostrar mensaje de chat
def mostrar_mensaje_chat(mensaje):
    nodo = str(mensaje.get("nodo_origen", "?"))
    usuario = str(mensaje.get("usuario", "Usuario"))
    contenido = str(mensaje.get("contenido", ""))
    fecha = obtener_hora(mensaje.get("fecha"))

    color = COLORES_NODO.get(nodo, "white")

    encabezado = Text()
    encabezado.append(f"[{nodo}] ", style=f"bold {color}")
    encabezado.append(usuario, style="bold white")

    if fecha:
        encabezado.append(f"    {fecha}", style="dim")

    cuerpo = Text(f"    {contenido}")

    console.print()
    console.print(encabezado)
    console.print(cuerpo)


#Seleccionar nodo
def seleccionar_nodo():
    while True:
        mostrar_nodos()

        opcion = input(
            "\nSelecciona un nodo [A/B/C]: "
        ).strip().upper()

        if opcion not in NODOS:
            mostrar_error("Nodo no valido")
            continue

        url = NODOS[opcion]

        if consultar_estado_nodo(url):
            return opcion, url

        mostrar_error(
            f"El Nodo {opcion} no esta disponible"
        )


#Buscar otro nodo disponible
def buscar_nodo_disponible(nodo_anterior):
    for nodo, url in NODOS.items():
        if nodo == nodo_anterior:
            continue

        if consultar_estado_nodo(url):
            return nodo, url

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

        mostrar_falla_nodo(nodo_fallido)

        nuevo_nodo, nueva_url = buscar_nodo_disponible(
            nodo_fallido
        )

        if nuevo_nodo is None:
            console.print(
                Panel(
                    "No hay otros nodos disponibles",
                    title="SIN NODOS DISPONIBLES",
                    border_style="red",
                    expand=False
                )
            )

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
                mostrar_error(
                    f"No se pudo registrar el usuario en Nodo {nuevo_nodo}"
                )

                return False

            nodo_actual = nuevo_nodo
            url_actual = nueva_url

            mostrar_recuperacion(
                nodo_fallido,
                nuevo_nodo
            )

            return True

        except requests.RequestException:
            mostrar_error(
                f"No se pudo conectar con Nodo {nuevo_nodo}"
            )

            return False


#Conectar usuario
def conectar_usuario(url):
    while True:
        nombre = input(
            "\nNombre de usuario: "
        ).strip()

        if not nombre:
            mostrar_error(
                "El nombre no puede estar vacio"
            )
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

                console.print(
                    f"[bold green]✓[/bold green] "
                    f"{escape(datos['mensaje'])}"
                )

                return nombre

            error = respuesta.json()

            mostrar_error(
                error.get(
                    "detail",
                    "No se pudo conectar"
                )
            )

        except requests.RequestException:
            mostrar_error(
                "No se pudo establecer conexion con el nodo"
            )


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

                        mostrar_mensaje_chat(
                            mensaje
                        )

                        console.print(
                            "> ",
                            end=""
                        )

        except requests.RequestException:

            #Confirmar que el nodo realmente esta caido
            if not consultar_estado_nodo(url_consultada):
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

            tabla = Table(
                title=f"Usuarios conectados - Nodo {datos['nodo']}",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold cyan"
            )

            tabla.add_column("Usuario")
            tabla.add_column(
                "Nodo",
                justify="center"
            )
            tabla.add_column(
                "Estado",
                justify="center"
            )

            if datos["total"] == 0:
                tabla.add_row(
                    "Sin usuarios",
                    "-",
                    "-"
                )

            else:
                for usuario in datos["usuarios"]:
                    nodo = str(
                        usuario.get(
                            "nodo",
                            datos["nodo"]
                        )
                    )

                    color = COLORES_NODO.get(
                        nodo,
                        "white"
                    )

                    tabla.add_row(
                        str(usuario["nombre"]),
                        Text(
                            nodo,
                            style=f"bold {color}"
                        ),
                        Text(
                            str(
                                usuario.get(
                                    "estado",
                                    "conectado"
                                )
                            ),
                            style="green"
                        )
                    )

            console.print()
            console.print(tabla)

    except requests.RequestException:
        mostrar_error(
            "No se pudo consultar usuarios"
        )


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
            timeout=10
        )

        if respuesta.status_code != 200:
            datos = respuesta.json()

            mostrar_error(
                datos.get(
                    "detail",
                    "No se pudo enviar el mensaje"
                )
            )

    except requests.RequestException:

        #Comprobar si el nodo realmente fallo
        if consultar_estado_nodo(url_envio):
            console.print(
                "\n[bold yellow]El nodo sigue activo, "
                "pero la respuesta del mensaje tardo demasiado.[/bold yellow]"
            )
            return

        console.print(
            f"\n[bold yellow]Se perdio la conexion "
            f"con Nodo {escape(str(nodo_envio))}[/bold yellow]"
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
                    timeout=10
                )

                if respuesta.status_code == 200:
                    console.print(
                        f"[bold green]✓[/bold green] "
                        f"Mensaje enviado mediante Nodo "
                        f"{escape(str(nodo_actual))}"
                    )

                else:
                    mostrar_error(
                        "No se pudo enviar el mensaje"
                    )

            except requests.RequestException:
                mostrar_error(
                    "No se pudo enviar el mensaje despues del failover"
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
    mostrar_banner()

    nodo_actual, url_actual = seleccionar_nodo()

    color_nodo = COLORES_NODO.get(
        nodo_actual,
        "white"
    )

    console.print(
        f"\n[bold green]✓[/bold green] "
        f"Conectado al Nodo "
        f"[bold {color_nodo}]"
        f"{nodo_actual}"
        f"[/bold {color_nodo}]"
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

    mostrar_ayuda()

    console.print(
        "\n[dim]Puedes comenzar a escribir mensajes.[/dim]\n"
    )

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

                console.print(
                    "\n[bold cyan]Cliente desconectado[/bold cyan]"
                )

                break

            elif contenido == "/usuarios":
                mostrar_usuarios(
                    url_actual
                )

            elif contenido == "/estado":
                mostrar_nodos()

            elif contenido == "/clear":
                limpiar()
                mostrar_banner()
                mostrar_nodos()

            elif contenido == "/ayuda":
                mostrar_ayuda()

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

            console.print(
                "\n[bold cyan]Cliente desconectado[/bold cyan]"
            )

            break


if __name__ == "__main__":
    main()
