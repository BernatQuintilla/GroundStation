import json
import tkinter as tk
import tkintermapview
from tkinter import Canvas
from tkinter import messagebox
from tkinter import ttk
from tkinter import StringVar
from pymavlink import mavutil
from PIL import Image, ImageTk
from CamaraVideo import *
from ObjectRecognition import *
from CreadorMisiones import *
import json

class MapFrameClass:

    def __init__(self, dron):
        # guardamos el objeto de la clase dron con el que estamos controlando el dron
        self.dron = dron
        self.altura = 0
        self.altura_vuelo = 5

        # atributos necesarios para crear el geofence
        self.vertex_count = 4

        # atributos para establecer el trazado del dron
        self.trace = False
        self.last_position = None  # actualizar trazado

        # Iconos del dron y markers
        self.drone_marker = None
        self.marker = False  # Para activar el marker (en forma de icono de dron)
        self.icon = Image.open("assets/drone.png")
        self.resized_icon = self.icon.resize((50, 50), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.resized_icon)

        self.marker_photo = Image.open("assets/marker_icon.png")
        self.resized_marker_icon = self.marker_photo.resize((20, 20), Image.LANCZOS)
        self.marker_icon = ImageTk.PhotoImage(self.resized_marker_icon)

        # Nombre misión
        self.nombre_mision = "mission"
        self.mission_names = []
        self.mission_var = tk.StringVar()

    def buildFrame(self, fatherFrame):

        self.MapFrame = tk.Frame(fatherFrame)  # create new frame where the map will be allocated

        # creamos el widget para el mapa
        self.map_widget = tkintermapview.TkinterMapView(self.MapFrame, width=1000, height=600, corner_radius=0)
        self.map_widget.grid(row=1, column=0, columnspan=13, padx=5, pady=5)
        # cargamos la imagen del dronlab
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga",
                                            max_zoom=22)
        self.map_widget.set_position(41.276430, 1.988686)  # Coordenadas del Dronelab

        # nivel inicial de zoom y posición inicial
        self.map_widget.set_zoom(20)
        self.initial_lat = 41.276430
        self.initial_lon = 1.988686

        self.MapFrame.rowconfigure(0, weight=1)
        self.MapFrame.rowconfigure(1, weight=10)

        self.MapFrame.columnconfigure(0, weight=1)
        self.MapFrame.columnconfigure(1, weight=1)
        self.MapFrame.columnconfigure(2, weight=1)
        self.MapFrame.columnconfigure(3, weight=1)
        self.MapFrame.columnconfigure(4, weight=1)
        self.MapFrame.columnconfigure(5, weight=1)
        self.MapFrame.columnconfigure(6, weight=1)
        self.MapFrame.columnconfigure(7, weight=1)
        self.MapFrame.columnconfigure(8, weight=1)
        self.MapFrame.columnconfigure(9, weight=1)

        # === FRAME CONTROL ===
        self.control_frame = tk.LabelFrame(self.MapFrame, text="Control")
        self.control_frame.grid(row=0, column=0, columnspan=3, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.control_frame.rowconfigure(0, weight=2)
        self.control_frame.rowconfigure(1, weight=2)
        self.control_frame.columnconfigure(0, weight=2)
        self.control_frame.columnconfigure(1, weight=2)

        self.connectBtn = tk.Button(self.control_frame, text="Conectar", bg="dark orange", fg="black",command=self.connect)
        self.connectBtn.grid(row=0, column=0, columnspan=1, padx=5, pady=3, sticky="nesw")

        self.despegarBtn = tk.Button(self.control_frame, text="Despegar", bg="dark orange", fg="black",command=self.arm_and_takeOff)
        self.despegarBtn.grid(row=0, column=1, columnspan=1, padx=5, pady=3, sticky="nesw")

        self.altura_input = tk.Entry(self.control_frame, width=3)
        self.altura_input.grid(row=0, column=2,columnspan=1, padx=1, pady=3)
        self.altura_input.insert(0, str(self.altura_vuelo))

        self.RTLBtn = tk.Button(self.control_frame, text="RTL", bg="dark orange", fg="black",command=self.RTL)
        self.RTLBtn.grid(row=1, column=0, columnspan=1, padx=5, pady=3, sticky="nesw")

        self.ShowDronBtn = tk.Button(self.control_frame, text="Mostrar dron", bg="black", fg="white", command=self.show_dron)
        self.ShowDronBtn.grid(row=1, column=1, columnspan = 2, padx=5, pady=3, sticky="nesw")

        # === FRAME GESTIÓN DE MISIONES ===
        self.mision_frame = tk.LabelFrame(self.MapFrame, text="Gestión de misiones")
        self.mision_frame.grid(row=0, column=3, columnspan=4, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.mision_frame.rowconfigure(0, weight=1)
        self.mision_frame.rowconfigure(1, weight=1)
        self.mision_frame.columnconfigure(0, weight=1)
        self.mision_frame.columnconfigure(1, weight=1)

        self.CrearMisionBtn = tk.Button(self.mision_frame, text="Crear misión", bg="dark orange", fg="black", command = self.show_mission_map)
        self.CrearMisionBtn.grid(row=0, column=0, padx=5, pady=3, sticky="nesw")

        self.AreaBtn = tk.Button(self.mision_frame, text="Crear área de observación", bg="dark orange", fg="black")
        self.AreaBtn.grid(row=0, column=1, padx=5, pady=3, sticky="nesw")

        self.SelMisionBtn = tk.Button(self.mision_frame, text="Seleccionar misión", bg="dark orange", fg="black", command=self.select_mission)
        self.SelMisionBtn.grid(row=1, column=0, padx=5, pady=3, sticky="nesw")

        #self.mission_dropdown = ttk.Combobox(self.mision_frame, textvariable=self.mission_var, state="readonly")
        #self.mission_dropdown.grid(row=1, column=0, padx=5, pady=3, sticky="nesw")
        #self.update_mission_list()

        self.EjecutarMisionBtn = tk.Button(self.mision_frame, text="Ejecutar misión", bg="black", fg="white", command = self.execute_mission)
        self.EjecutarMisionBtn.grid(row=1, column=1, padx=5, pady=3, sticky="nesw")

        # === FRAME FUNCIONALIDADES ===
        self.func_frame = tk.LabelFrame(self.MapFrame, text="Funcionalidades")
        self.func_frame.grid(row=0, column=7, columnspan=4, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.func_frame.rowconfigure(0, weight=2)
        self.func_frame.rowconfigure(1, weight=2)
        self.func_frame.columnconfigure(0, weight=2)
        self.func_frame.columnconfigure(1, weight=2)

        self.ActivarCamBtn = tk.Button(self.func_frame, text="Activar cámara", bg="dark orange", fg="black", command=self.activar_camara)
        self.ActivarCamBtn.grid(row=0, column=0, columnspan=2, padx=5, pady=3, sticky="nesw")

        self.ObjectRecognBtn = tk.Button(self.func_frame, text="Reconocimiento de Objetos", bg="dark orange", fg="black", command=self.activar_ObjRecognition)
        self.ObjectRecognBtn.grid(row=1, column=0, columnspan=2, padx=5, pady=3, sticky="nesw")

        # === FRAME DATOS TELEMETRÍA ===
        self.tele_frame = tk.LabelFrame(self.MapFrame, text="Datos telemetría")
        self.tele_frame.grid(row=0, column=12, columnspan=1, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.tele_frame.rowconfigure(0, weight=2)
        self.tele_frame.rowconfigure(1, weight=2)
        self.tele_frame.columnconfigure(0, weight=2)

        self.AlturaLabel = tk.Label(
            self.tele_frame,
            text=f"Altura: {self.altura} m",
            bg="light gray",
            fg="black",
            width=12,
        )
        self.AlturaLabel.grid(row=0, column=1, columnspan=2, padx=5, pady=3, sticky="nesw")

        self.TrazadoBtn = tk.Button(self.tele_frame, text="Activar trazado", bg="black", fg="white", command= self.set_trace)
        self.TrazadoBtn.grid(row=1, column=0, columnspan=2, padx=5, pady=3, sticky="nesw")

        return self.MapFrame

    # ======== FUNCIONES CONTROL ========
    def connect(self):
        # conectamos con el simulador
        connection_string = 'tcp:127.0.0.1:5763'
        baud = 115200
        self.dron.connect(connection_string, baud)
        # una vez conectado cambio en color de boton
        self.connectBtn['bg'] = 'green'
        self.connectBtn['fg'] = 'white'
        self.connectBtn['text'] = 'Conectado'
        self.GeoFence()

    def arm_and_takeOff(self):
        self.altura_vuelo = int(self.altura_input.get())
        self.dron.arm()
        self.dron.takeOff(self.altura_vuelo)
        # una vez armado cambio en color de boton
        self.despegarBtn['bg'] = 'green'
        self.despegarBtn['fg'] = 'white'
        self.despegarBtn['text'] = 'Volando'

    def RTL(self):
        if self.dron.going:
            self.dron.stopGo()
        # llamo en modo no bloqueante y le indico qué función debe activar al acabar la operación, y qué parámetro debe usar
        self.dron.RTL(blocking=False, callback=self.informar, params='EN CASA')
        # mientras retorno pongo el boton en amarillo
        self.RTLBtn['bg'] = 'yellow'
        self.RTLBtn['text'] = 'Retornando....'

    def show_dron(self):
        # muestro el dron o dejo de mostrarlo
        self.marker = not self.marker
        if self.marker:
            # si hay que mostrarlo aquí añado el icono del dron
            self.drone_marker = self.map_widget.set_marker(self.initial_lat, self.initial_lon,
                                                           marker_color_outside="blue", marker_color_circle="black",
                                                           text="", text_color="blue",
                                                           icon=self.photo, icon_anchor="center")
            # pido que me envíen datos de telemetría que me permitirán saber dónde está el dron para resituarlo en el mapa
            if not self.dron.sendTelemetryInfo:
                # indico qué función quiero que se ejecute cada vez que llega un nuevo paquete de datos de telemetría
                self.dron.send_telemetry_info(self.process_telemetry_info)
            self.informar('DRON_VISIBLE')
        else:
            # Si hay que quitarlo, lo hago aquí
            if self.drone_marker:
                self.map_widget.delete(self.drone_marker)
                self.drone_marker = None
            if not self.trace:
                self.dron.stop_sending_telemetry_info()
            self.informar('DRON_OCULTO')

    # ===== INFORMAR ======
    def informar(self, mensaje):
        if mensaje == "EN CASA":
            # pongo el boton RTL en verde
            self.RTLBtn['bg'] = 'green'
            self.RTLBtn['fg'] = 'white'

            # me desconecto del dron (eso tardará 5 segundos)
            self.dron.disconnect()
            # devuelvo los botones a la situación inicial

            self.connectBtn['bg'] = 'dark orange'
            self.connectBtn['fg'] = 'black'
            self.connectBtn['text'] = 'Conectar'

            self.despegarBtn['bg'] = 'dark orange'
            self.despegarBtn['fg'] = 'black'
            self.despegarBtn['text'] = 'Armar'

            self.RTLBtn['bg'] = 'dark orange'
            self.RTLBtn['fg'] = 'black'
            self.RTLBtn['text'] = 'RTL'

        if mensaje == "TRAZADO_ON":
            self.TrazadoBtn['bg'] = 'green'
            self.TrazadoBtn['fg'] = 'white'
            self.TrazadoBtn['text'] = 'Ocultar trazado'

        if mensaje == "TRAZADO_OFF":
            self.TrazadoBtn['bg'] = 'black'
            self.TrazadoBtn['fg'] = 'white'
            self.TrazadoBtn['text'] = 'Mostrar trazado'

        if mensaje == "DRON_VISIBLE":
            self.ShowDronBtn['bg'] = 'green'
            self.ShowDronBtn['fg'] = 'white'
            self.ShowDronBtn['text'] = 'Ocultar dron'

        if mensaje == "DRON_OCULTO":
            self.ShowDronBtn['bg'] = 'black'
            self.ShowDronBtn['fg'] = 'white'
            self.ShowDronBtn['text'] = 'Mostrar dron'

    # ===== DATOS DE TELEMETRÍA =====
    # vendremos aquí cada vez que se reciba un paquete de datos de telemetría
    def process_telemetry_info(self, telemetry_info):
        # recupero la posición del dron para redibujar el icono en el mapa
        lat = telemetry_info['lat']
        lon = telemetry_info['lon']
        self.altura = round(telemetry_info['alt'],2)
        self.AlturaLabel.config(text=f"Altura: {self.altura} m")
        if self.trace:
            # dibujamos el ratro
            if self.last_position:
                self.map_widget.set_path([self.last_position, (lat, lon)], width=5)
            self.last_position = (lat, lon)

        if self.marker:

            if self.drone_marker:
                # borro el icono que hay
                self.map_widget.delete(self.drone_marker)
            # coloco el icono en su nueva posición
            self.drone_marker = self.map_widget.set_marker(lat, lon,
                                                           marker_color_outside="blue",
                                                           marker_color_circle="black",
                                                           text="", text_color="blue",
                                                           icon=self.photo, icon_anchor="center")

    # ======= MARCAR TRAZADO DEL DRON =======
    def set_trace(self):
        self.trace = not self.trace

        if self.TrazadoBtn['bg'] == 'black':
            self.informar("TRAZADO_ON")
        elif self.TrazadoBtn['bg'] == 'green':
            self.informar("TRAZADO_OFF")

        if self.trace:
            if not self.dron.sendTelemetryInfo:
                self.dron.send_telemetry_info(self.process_telemetry_info)
        else:
            self.map_widget.delete_all_path()
            self.last_position = []
            if not self.marker:
                self.dron.stop_sending_telemetry_info()

    # ====== GEOFENCE =======
    # aqui venimos cuando tenemos ya definido el geofence y lo queremos enviar al dron
    def GeoFence(self):

        with open("GeoFenceScenario.json", "r") as file:
            scenario_data = json.load(file)

        geofence_waypoints = scenario_data[0]["waypoints"]

        polygon = self.map_widget.set_polygon(
            [(point['lat'], point['lon']) for point in geofence_waypoints],
            fill_color=None,
            outline_color="red",
            border_width=4,
            name="GeoFence_polygon"
        )

        self.dron.setScenario(scenario_data)

    # ====== CREADOR MISIONES ======
    def show_mission_map(self):
        map_window = tk.Toplevel()
        map_window.title("Creador de Misiones")
        map_window.geometry("820x620")

        map_mission_class = MapMission(self.dron, self.altura_vuelo)
        map_frame = map_mission_class.buildFrame(map_window)
        map_frame.pack(fill="both", expand=True)

    def load_mission(self):
        try:
            mission_path = os.path.join("missions", f"{self.nombre_mision}.json")

            with open(mission_path, "r") as mission_file:
                mission = json.load(mission_file)

            if "takeOffAlt" not in mission or "waypoints" not in mission:
                messagebox.showerror("Misión Inválida", "El archivo de misión es inválido.")
                return None

            messagebox.showinfo("Misión Cargada", f'¡La misión "{self.nombre_mision}" se ha cargado correctamente!')
            return mission

        except FileNotFoundError:
            messagebox.showerror("Archivo No Encontrado",f'No se encontró la misión "{self.nombre_mision}.json" en la carpeta "missions".')
        except json.JSONDecodeError:
            messagebox.showerror("Error de JSON", "Hubo un error al leer el archivo de misión.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al cargar la misión: {str(e)}")

        return None

    def execute_mission(self):
        mission = self.load_mission()

        if mission is None:
            return

        self.dron.uploadMission(mission, blocking=True)

        messagebox.showinfo("Inicio Misión", '¡Comienza la misión!')

        self.dron.executeMission(blocking=True)

        messagebox.showinfo("Misión Cumplida", '¡Misión cumplida!')

    def select_mission(self):
        return

    # ====== FUNCIONALIDADES ======
    def activar_camara(self):
        show_camera_video(self.MapFrame)

    def activar_ObjRecognition(self):
        show_camera_recognition(self.MapFrame)






