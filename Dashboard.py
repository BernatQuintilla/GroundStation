import time
import tkinter as tk
from Dron import Dron
from tkinter import Canvas
from tkinter import ttk
from tkinter import messagebox
from MapFrame import MapFrameClass
from BodyFrame import BodyFrameClass


def connect ():
    global dron, connectBtn
    # conectamos con el simulador
    connection_string ='tcp:127.0.0.1:5763'
    baud = 115200
    dron.connect(connection_string, baud)

 # una vez conectado cambio en color de boton
    connectBtn['bg'] = 'green'
    connectBtn['fg'] = 'white'
    connectBtn['text'] = 'Conectado'



def arm (button):
    global dron, armBtn
    dron.arm()
    # una vez armado cambio en color de boton
    armBtn['bg'] = 'green'
    armBtn['fg'] = 'white'
    armBtn['text'] = 'Armado'


def takeoff ():
    global dron, takeOffBtn
    global alt_entry
    try:
        # tomamos la altura del cuadro de texto
        alt = float(alt_entry.get())
        # llamo en modo no bloqueante y le indico qué función debe activar al acabar la operación, y qué parámetro debe usar
        dron.takeOff (alt, blocking=False,  callback=informar, params='VOLANDO')
        # mientras despego pongo el boton en amarillo
        takeOffBtn['bg'] = 'yellow'
        takeOffBtn['text'] = 'Despegando....'
    except:
        # en el cuadro de texto no hay ningún numero
        messagebox.showerror("error", "Introducela altura para el despegue")


# esta es la función que se activará cuando acaben las funciones no bloqueantes (despegue y RTL)
def informar (mensaje):
    global takeOffBtn, RTLBtn, connectBtn, armBtn, landBtn
    global dron
    if mensaje == 'VOLANDO':
        # pongo el boton de despegue en verde
        takeOffBtn['bg'] = 'green'
        takeOffBtn['fg'] = 'white'
        takeOffBtn['text'] = 'En el aire'
    if mensaje == "EN CASA":
        # pongo el boton RTL en verde
        RTLBtn['bg'] = 'green'
        RTLBtn['fg'] = 'white'
        RTLBtn['text'] = 'En casa'
        # me desconecto del dron (eso tardará 5 segundos)
        dron.disconnect()
        # devuelvo los botones a la situación inicial


        connectBtn['bg'] = 'dark orange'
        connectBtn['fg'] = 'black'
        connectBtn['text'] = 'Conectar'

        armBtn['bg'] = 'dark orange'
        armBtn['fg'] = 'black'
        armBtn['text'] = 'Armar'

        takeOffBtn['bg'] = 'dark orange'
        takeOffBtn['fg'] = 'black'
        takeOffBtn['text'] = 'Despegar'

        RTLBtn['bg'] = 'dark orange'
        RTLBtn['fg'] = 'black'
        RTLBtn['text'] = 'RTL'

    if mensaje == "EN TIERRA":
        # pongo el boton Aterrizar en verde
        landBtn['bg'] = 'green'
        landBtn['fg'] = 'white'
        landBtn['text'] = 'En tierra'
        # me desconecto del dron (eso tardará 5 segundos)
        dron.disconnect()
        # devuelvo los botones a la situación inicial
        connectBtn['bg'] = 'dark orange'
        connectBtn['fg'] = 'black'
        connectBtn['text'] = 'Conectar'

        armBtn['bg'] = 'dark orange'
        armBtn['fg'] = 'black'
        armBtn['text'] = 'Armar'

        takeOffBtn['bg'] = 'dark orange'
        takeOffBtn['fg'] = 'black'
        takeOffBtn['text'] = 'Despegar'

        landBtn['bg'] = 'dark orange'
        landBtn['fg'] = 'black'
        landBtn['text'] = 'Aterrizar'

def RTL():
    global dron, RTLBtn
    if dron.going:
        dron.stopGo()
    # llamo en modo no bloqueante y le indico qué función debe activar al acabar la operación, y qué parámetro debe usar
    dron.RTL(blocking = False, callback = informar, params= 'EN CASA')
    # mientras retorno pongo el boton en amarillo
    RTLBtn['bg'] = 'yellow'
    RTLBtn['text'] = 'Retornando....'


def aterrizar():
    global dron, landBtn
    if dron.going:
        dron.stopGo()
    # llamo en modo no bloqueante y le indico qué función debe activar al acabar la operación, y qué parámetro debe usar
    dron.Land(blocking = False, callback = informar, params= 'EN TIERRA')
    # mientras retorno pongo el boton en amarillo
    landBtn['bg'] = 'yellow'
    landBtn['text'] = 'Aterrizando....'

# ====== NAVIGATION FUNCTIONS ======
# Esta función se activa cada vez que cambiamos la velocidad de navegación con el slider
def change_speed (speed):
    global dron
    dron.changeNavSpeed(float(speed))

# función para dirigir el dron en una dirección
def go(direction):
    global dron
    # si empezamos a navegar, le indico al dron
    if not dron.going:
        dron.startGo()
    dron.go(direction)


# abrimos el mapa
def showmap():
    global dron

    map_window = tk.Toplevel()
    map_window.title("Map Display")
    map_window.geometry("820x620")

    map_frame_class = MapFrameClass(dron)
    map_frame = map_frame_class.buildFrame(map_window)
    map_frame.pack(fill="both", expand=True)


def show_body_control():
    global dron
    map_window = tk.Toplevel()
    map_window.title("Control por poses")
    map_window.geometry("630x300")

    body_frame_class = BodyFrameClass(dron)
    body_frame = body_frame_class.buildFrame(map_window)
    body_frame.pack(fill="both", expand=True)


# ================= DASHBOARD INICIAL =================
def crear_ventana():
    global dron
    global  altShowLbl, headingShowLbl,  speedSldr, gradesSldr, speedShowLbl
    global takeOffBtn, connectBtn, armBtn, takeOffBtn, RTLBtn, landBtn
    global alt_entry

    dron = Dron()

    ventana = tk.Tk()
    ventana.title("Ventana con botones y entradas")
    ventana.rowconfigure(0, weight=1)
    ventana.columnconfigure(0, weight=1)
    ventana.columnconfigure(1, weight=1)


    # Configuración del Frame de Control
    controlFrame = tk.LabelFrame(ventana, text="Control")
    controlFrame.grid(row=0, column=0, padx=10, pady=10, sticky=tk.N + tk.S + tk.E + tk.W)

    controlFrame.rowconfigure(0, weight=1)
    controlFrame.rowconfigure(1, weight=1)
    controlFrame.rowconfigure(2, weight=1)
    controlFrame.rowconfigure(3, weight=1)
    controlFrame.rowconfigure(4, weight=1)
    controlFrame.rowconfigure(5, weight=1)
    controlFrame.rowconfigure(6, weight=1)
    controlFrame.rowconfigure(7, weight=1)

    controlFrame.columnconfigure(0, weight=1)


    connectBtn = tk.Button(controlFrame, text="Conectar", bg="dark orange", command = connect)
    connectBtn.grid(row=0, column=0, padx=3, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    # A la función que activamos al clicar en este boton le pasamos el propio boton para
    # que le cambie el color
    armBtn = tk.Button(controlFrame, text="Armar", bg="dark orange",
                       command=lambda: arm(armBtn))
    armBtn.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    takeOffFrame = tk.Frame (controlFrame)
    takeOffFrame.grid(row=2, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
    takeOffFrame.rowconfigure(0, weight=1)
    takeOffFrame.columnconfigure(0, weight=1)
    takeOffFrame.columnconfigure(1, weight=1)

    alt_entry = tk.Entry(takeOffFrame)
    alt_entry.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    takeOffBtn = tk.Button(takeOffFrame, text="Despegar", bg="dark orange", command=takeoff)
    takeOffBtn.grid(row=0, column=1,  padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    RTLBtn = tk.Button(controlFrame, text="RTL", bg="dark orange", command=RTL)
    RTLBtn.grid(row=3, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


# ================= FRAME/BOTONES NAVEGACIÓN =================

    speedSldr = tk.Scale(controlFrame, label="Velocidad (m/s):", resolution=1, from_=0, to=20, tickinterval=5,
                         orient=tk.HORIZONTAL, command=change_speed)
    speedSldr.set(1) # velocidad por defecto de 1 m/s
    speedSldr.grid(row=4, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    navFrame = tk.LabelFrame (controlFrame, text = "Navegación")
    navFrame.grid(row=5, column=0, padx=50, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    # Configuración del Frame de Navegación
    navFrame.rowconfigure(0, weight=1)
    navFrame.rowconfigure(1, weight=1)
    navFrame.rowconfigure(2, weight=1)

    navFrame.columnconfigure(0, weight=1)
    navFrame.columnconfigure(1, weight=1)
    navFrame.columnconfigure(2, weight=1)

    # todos los botones activan la misma función, pero pasándole como parametro
    # la dirección de navegación
    NWBtn = tk.Button(navFrame, text="NW", bg="dark orange",
                        command= lambda: go("NorthWest"))
    NWBtn.grid(row=0, column=0, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    NoBtn = tk.Button(navFrame, text="No", bg="dark orange",
                        command= lambda: go("North"))
    NoBtn.grid(row=0, column=1, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    NEBtn = tk.Button(navFrame, text="NE", bg="dark orange",
                        command= lambda: go("NorthEast"))
    NEBtn.grid(row=0, column=2, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    WeBtn = tk.Button(navFrame, text="We", bg="dark orange",
                        command=lambda: go("West"))
    WeBtn.grid(row=1, column=0, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    StopBtn = tk.Button(navFrame, text="St", bg="dark orange",
                        command=lambda: go("Stop"))
    StopBtn.grid(row=1, column=1, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    EaBtn = tk.Button(navFrame, text="Ea", bg="dark orange",
                        command=lambda: go("East"))
    EaBtn.grid(row=1, column=2, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    SWBtn = tk.Button(navFrame, text="SW", bg="dark orange",
                        command=lambda: go("SouthWest"))
    SWBtn.grid(row=2, column=0, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    SoBtn = tk.Button(navFrame, text="So", bg="dark orange",
                        command=lambda: go("South"))
    SoBtn.grid(row=2, column=1, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    SEBtn = tk.Button(navFrame, text="SE", bg="dark orange",
                        command=lambda: go("SouthEast"))
    SEBtn.grid(row=2, column=2, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)



    MapButton = tk.Button(controlFrame, text="Mostrar mapa", bg="dark orange", command=showmap)
    MapButton.grid(row=6, column=0, padx=5, pady=10, sticky=tk.N + tk.S + tk.E + tk.W)

    PoseButton = tk.Button(controlFrame, text="Control del dron con las poses del cuerpo", bg="dark orange", command=show_body_control)
    PoseButton.grid(row=7, column=0, padx=5, pady=10, sticky=tk.N + tk.S + tk.E + tk.W)

    # ================ FRAME ADICIONAL (AÑADIR FUNCIONALIDADES EXTRA/RETOS) ================

    userFrame = tk.LabelFrame(ventana, text="Funcionalidades extra")
    userFrame.grid(row=0, column=1, padx=10, pady=10, sticky=tk.N + tk.S + tk.E + tk.W)

    # Configuración del Frame de usuario: el usuario puede añadir/quitar filas y columnas como prefiera
    userFrame.rowconfigure(0, weight=1)
    userFrame.rowconfigure(1, weight=1)
    userFrame.rowconfigure(2, weight=1)
    userFrame.rowconfigure(3, weight=1)
    userFrame.rowconfigure(4, weight=1)
    userFrame.rowconfigure(5, weight=1)
    userFrame.rowconfigure(6, weight=1)
    userFrame.rowconfigure(7, weight=1)
    userFrame.rowconfigure(8, weight=1)
    userFrame.rowconfigure(9, weight=1)
    userFrame.rowconfigure(10, weight=1)

    userFrame.columnconfigure(0, weight=1)
    userFrame.columnconfigure(1, weight=1)
    userFrame.columnconfigure(2, weight=1)
    userFrame.columnconfigure(3, weight=1)

    # Estos botones se pueden configurar como se prefiera y añadir cualquier funcionalidad deseada
    landBtn = tk.Button(userFrame, text="Aterrizar", bg="dark orange", command = aterrizar)
    landBtn.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky=tk.N + tk.E + tk.W)

    newButton2 = tk.Button(userFrame, text="Button 2", bg="light grey")
    newButton2.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky=tk.N + tk.E + tk.W)

    newButton3 = tk.Button(userFrame, text="Button 3", bg="light grey")
    newButton3.grid(row=4, column=0, columnspan=4, padx=5, pady=5, sticky=tk.N + tk.E + tk.W)


    return ventana

if __name__ == "__main__":
    ventana = crear_ventana()
    ventana.mainloop()