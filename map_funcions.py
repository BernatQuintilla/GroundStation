from tkinter import messagebox

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