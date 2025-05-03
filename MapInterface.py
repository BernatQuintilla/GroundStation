from tkinter import filedialog
from StitchingMission import *
from CreadorMisiones import *
from ManualStitching import *
from CreadorGeofence import *
import threading
import os
from datetime import datetime
from ultralytics import YOLO
import cv2


class MapFrameClass:
    # ======== INICIALIZAR CLASE ========
    def __init__(self, dron):
        # guardamos el objeto de la clase dron con el que estamos controlando el dron
        self.dron = dron
        self.altura = 0
        self.heading = 0
        self.altura_vuelo = 5
        self.dron.navSpeed = 1
        # atributos necesarios para crear el geofence
        self.vertex_count = 4
        self.flag_new_geofence = False
        self.isconnected = False
        # Cargamos los tres iconos
        self.RTL_active = False
        self.icon_red = Image.open("assets/RedArrow.png")
        self.resized_icon_red = self.icon_red.resize((30, 30), Image.LANCZOS)
        self.photo_red = ImageTk.PhotoImage(self.resized_icon_red)

        self.icon_yellow = Image.open("assets/YellowArrow.png")
        self.resized_icon_yellow = self.icon_yellow.resize((30, 30), Image.LANCZOS)
        self.photo_yellow = ImageTk.PhotoImage(self.resized_icon_yellow)

        self.icon_green = Image.open("assets/GreenArrow.png")
        self.resized_icon_green = self.icon_green.resize((30, 30), Image.LANCZOS)
        self.photo_green = ImageTk.PhotoImage(self.resized_icon_green)

        # Iconos del dron y markers
        self.drone_marker = None
        self.icon = Image.open("assets/drone.png")
        self.resized_icon = self.icon.resize((50, 50), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.resized_icon)

        self.marker_photo = Image.open("assets/marker_icon.png")
        self.resized_marker_icon = self.marker_photo.resize((20, 20), Image.LANCZOS)
        self.marker_icon = ImageTk.PhotoImage(self.resized_marker_icon)

        # Nombre misión
        self.nombre_mision = ""
        self.mission_names = []
        self.mission_var = tk.StringVar()
        self.waypoints_actions = None

        self.map_frame = None
        self.gallery_frame = None
        self.gallery_processed_frame = None
        self.stitch_frame = None

        # YOLO model
        self.model = YOLO("models/yolov8n.pt")

        # Reconocimiento Objetos
        self.video_label = None
        self.detected_objects = []

        # Variables para cambiar producción y simulación (simulación en predeterminado)
        self.tipo_conexión = "simulación"
        self.camara_input = 0
        self.connection_string = 'tcp:127.0.0.1:5763'
        self.baud = 115200

        # Abrimos cámara
        self.cap = None

    # ======== BUILD FRAME ========
    def buildFrame(self, fatherFrame):

        self.MapFrame = tk.Frame(fatherFrame)  # create new frame where the map will be allocated

        # creamos el widget para el mapa
        self.map_widget = tkintermapview.TkinterMapView(self.MapFrame, width=850, height=600, corner_radius=0)
        self.map_widget.grid(row=1, column=0, columnspan=10, rowspan=3, padx=5, pady=5)
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
        self.MapFrame.rowconfigure(2, weight=10)
        self.MapFrame.rowconfigure(3, weight=10)

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
        self.MapFrame.columnconfigure(10, weight=1)
        self.MapFrame.columnconfigure(11, weight=1)
        self.MapFrame.columnconfigure(12, weight=1)
        self.MapFrame.columnconfigure(13, weight=1)

        # === FRAME CONTROL ===
        self.control_frame = tk.LabelFrame(self.MapFrame, text="Control")
        self.control_frame.grid(row=0, column=0, columnspan=3, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.control_frame.rowconfigure(0, weight=2)
        self.control_frame.rowconfigure(1, weight=2)
        self.control_frame.columnconfigure(0, weight=2)
        self.control_frame.columnconfigure(1, weight=2)
        self.control_frame.columnconfigure(2, weight=2)

        self.connectBtn = tk.Button(self.control_frame, text="Conectar", bg="dark orange", fg="black",command=self.connect)
        self.connectBtn.grid(row=0, column=0, columnspan=1, padx=5, pady=3, sticky="nesw")

        self.despegarBtn = tk.Button(self.control_frame, text="Despegar", bg="dark orange", fg="black",command=self.arm_and_takeOff)
        self.despegarBtn.grid(row=1, column=0, columnspan=1, padx=5, pady=3, sticky="nesw")

        self.RTLBtn = tk.Button(self.control_frame, text="RTL", bg="dark orange", fg="black",command=self.RTL)
        self.RTLBtn.grid(row=1, column=2, columnspan=1, padx=5, pady=3, sticky="nesw")

        self.LandBtn = tk.Button(self.control_frame, text="Aterrizar", bg="dark orange", fg="black", command=self.dron.Land)
        self.LandBtn.grid(row=1, column=1, columnspan=1, padx=5, pady=3, sticky="nesw")

        self.CambiarConexionBtn = tk.Button(self.control_frame, text="Cambiar a producción", bg="black", fg="white", command=self.change_connection)
        self.CambiarConexionBtn.grid(row=0, column=1, columnspan = 2, padx=5, pady=3, sticky="nesw")

        # === FRAME DATOS TELEMETRÍA ===
        self.tele_frame = tk.LabelFrame(self.MapFrame, text="Datos telemetría")
        self.tele_frame.grid(row=0, column=3, columnspan=1, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

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
        self.AlturaLabel.grid(row=0, column=0, columnspan=1, padx=5, pady=3, sticky="nesw")

        self.HeadingLabel = tk.Label(
            self.tele_frame,
            text=f"Heading: {self.heading} º",
            bg="light gray",
            fg="black",
            width=12,
        )
        self.HeadingLabel.grid(row=1, column=0, columnspan=1, padx=5, pady=3, sticky="nesw")

        # === FRAME GESTIÓN DE MISIONES ===
        self.mision_frame = tk.LabelFrame(self.MapFrame, text="Gestión de misiones")
        self.mision_frame.grid(row=0, column=4, columnspan=5, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.mision_frame.rowconfigure(0, weight=1)
        self.mision_frame.rowconfigure(1, weight=1)
        self.mision_frame.columnconfigure(0, weight=1)
        self.mision_frame.columnconfigure(1, weight=1)

        self.CrearMisionBtn = tk.Button(self.mision_frame, text="Crear misión", bg="dark orange", fg="black", command = self.show_mission_map)
        self.CrearMisionBtn.grid(row=0, column=0, padx=5, pady=3, sticky="nesw")

        self.MisionLabel = tk.Label(
            self.mision_frame,
            text=f"Misión: no seleccionada",
            bg="light gray",
            fg="black",
            width=20,  # Adjust the width to your needs
        )
        self.MisionLabel.grid(row=0, column=1, columnspan=2, padx=5, pady=3, sticky="nesw")

        self.SelMisionBtn = tk.Button(self.mision_frame, text="Seleccionar misión", bg="dark orange", fg="black", command=self.select_mission)
        self.SelMisionBtn.grid(row=1, column=0, padx=5, pady=3, sticky="nesw")

        self.EjecutarMisionBtn = tk.Button(self.mision_frame, text="Ejecutar misión", bg="black", fg="white", command = self.execute_mission)
        self.EjecutarMisionBtn.grid(row=1, column=1, padx=5, pady=3, sticky="nesw")

        # === FRAME DETECCION DE OBJETOS ===
        self.func_frame = tk.LabelFrame(self.MapFrame, text="Detección de objetos")
        self.func_frame.grid(row=0, column=9, columnspan=3, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.func_frame.rowconfigure(0, weight=2)
        self.func_frame.rowconfigure(1, weight=2)
        self.func_frame.columnconfigure(0, weight=2)
        self.func_frame.columnconfigure(1, weight=2)

        self.ActivarCamBtn = tk.Button(self.func_frame, text="Iniciar juego", bg="dark orange", fg="black", command=self.iniciar_juego)
        self.ActivarCamBtn.grid(row=0, column=0, columnspan=2, padx=5, pady=3, sticky="nesw")

        self.ObjectRecognBtn = tk.Button(self.func_frame, text="Galería imágenes procesadas", bg="dark orange", fg="black", command=self.show_gallery_processed_page)
        self.ObjectRecognBtn.grid(row=1, column=0, columnspan=2, padx=5, pady=3, sticky="nesw")

        # === FRAME IMAGE STITCHING ===
        self.galeria_frame = tk.LabelFrame(self.MapFrame, text="Image Stitching")
        self.galeria_frame.grid(row=0, column=12, columnspan=4, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.galeria_frame.rowconfigure(0, weight=1)
        self.galeria_frame.rowconfigure(1, weight=1)
        self.galeria_frame.columnconfigure(0, weight=2)
        self.galeria_frame.columnconfigure(1, weight=2)

        self.GaleriaBtn = tk.Button(self.galeria_frame, text="Galería imágenes", bg="dark orange", fg="black", command=self.show_gallery_page)
        self.GaleriaBtn.grid(row=0, column=0, columnspan=1, padx=5, pady=3, sticky="nesw")

        self.CrearMisionStBtn = tk.Button(self.galeria_frame, text="Crear misión stitching", bg="dark orange", fg="black", command=self.show_mission_stitching)
        self.CrearMisionStBtn.grid(row=0, column=1, columnspan=1, padx=5, pady=3, sticky="nesw")

        self.StOpenCVBtn = tk.Button(self.galeria_frame, text="Stitching OpenCV", bg="dark orange", fg="black", command= self.show_stitched_image)
        self.StOpenCVBtn.grid(row=1, column=0, columnspan=1, padx=5, pady=3, sticky="nesw")

        self.StSIFTBtn = tk.Button(self.galeria_frame, text="Stitching SIFT", bg="dark orange", fg="black", command= self.show_manual_stitched_image)
        self.StSIFTBtn.grid(row=1, column=1, columnspan=1, padx=5, pady=3, sticky="nesw")

        # FRAME PARÁMETROS
        self.param_frame = tk.LabelFrame(self.MapFrame, text="Editor Parámetros")
        self.param_frame.grid(row=1, column=11, columnspan=4, rowspan=2, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)
        self.param_frame.rowconfigure(0, weight=2)
        self.param_frame.rowconfigure(1, weight=2)
        self.param_frame.rowconfigure(2, weight=2)
        self.param_frame.rowconfigure(3, weight=2)
        self.param_frame.rowconfigure(4, weight=2)
        self.param_frame.rowconfigure(5, weight=2)
        self.param_frame.rowconfigure(6, weight=2)
        self.param_frame.columnconfigure(0, weight=2)
        self.param_frame.columnconfigure(1, weight=2)

        self.info_label = tk.Label(self.param_frame, text="Los parámetros seleccionados se utilizarán en los planes de vuelo y acciones de control", fg="black",wraplength=240)
        self.info_label.grid(row=0, column=0, columnspan=4, padx=5, pady=3, sticky="w")

        self.alt_label = tk.Label(self.param_frame, text="Editar Altura (m):", fg="black")
        self.alt_label.grid(row=1, column=0, columnspan=4, padx=5, pady=3, sticky="w")
        self.altura_entry = tk.Entry(self.param_frame)
        self.altura_entry.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.altura_entry.insert(0, str(self.altura_vuelo))
        self.altBtn = tk.Button(self.param_frame, text="Aplicar", bg="dark orange", fg="black", command=self.aplicar_altura)
        self.altBtn.grid(row=2, column=1, columnspan=2, padx=5, pady=3, sticky="nesw")

        self.vel_label = tk.Label(self.param_frame, text="Editar Velocidad (m/s):", fg="black")
        self.vel_label.grid(row=3, column=0, columnspan=4, padx=5, pady=3, sticky="w")
        self.velBtn = tk.Button(self.param_frame, text="Aplicar", bg="dark orange", fg="black", command=self.aplicar_velocidad)
        self.velBtn.grid(row=4, column=1, columnspan=2, padx=5, pady=3, sticky="nesw")
        self.vel_entry = tk.Entry(self.param_frame)
        self.vel_entry.grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.vel_entry.insert(0, str(self.dron.navSpeed))

        self.geo_label = tk.Label(self.param_frame, text="Editar Geofence:", fg="black")
        self.geo_label.grid(row=5, column=0, columnspan=4, padx=5, pady=3, sticky="w")
        self.CrearGeoBtn = tk.Button(self.param_frame, text="Crear Geofence", bg="dark orange", fg="black", command=self.creadorGeoFence)
        self.CrearGeoBtn.grid(row=6, column=0, columnspan = 4, padx=5, pady=3, sticky="nesw")

        # === FRAME VIDEO ===
        self.camaravideo_frame = tk.LabelFrame(self.MapFrame, text="Cámara dron")
        self.camaravideo_frame.grid(row=3, column=11, columnspan=4, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.camaravideo_frame.config(width=2, height=100)
        self.camaravideo_frame.grid_propagate(False)

        self.camaravideo_frame.rowconfigure(0, weight=1)
        self.camaravideo_frame.columnconfigure(0, weight=1)
        self.camaravideo_frame.columnconfigure(1, weight=1)

        self.video_label = tk.Label(self.camaravideo_frame)
        self.video_label.grid(row=0, column=0, columnspan=1, padx=5, pady=5, sticky="nsew")
        self.show_video()
        self.GuardarFrameBtn = tk.Button(self.camaravideo_frame, text="Guardar Frame", bg="dark orange", fg="black", command=self.capture_and_save_photo)
        self.GuardarFrameBtn.grid(row=1, column=0, columnspan = 4, padx=5, pady=3, sticky="nesw")
        self.map_frame = self.MapFrame

        return self.MapFrame

    # ======== FUNCIONES CONTROL ========
    def connect(self):
        # conectamos con el simulador
        self.dron.connect(self.connection_string, self.baud)
        # una vez conectado cambio en color de boton
        self.connectBtn['bg'] = 'green'
        self.connectBtn['fg'] = 'white'
        self.connectBtn['text'] = 'Conectado'
        self.GeoFence()
        self.show_dron()
        self.cap = cv2.VideoCapture(self.camara_input)
        self.dron.unfixHeading()
        self.isconnected = True

    def arm_and_takeOff(self):
        self.informar('DESPEGANDO')
        self.dron.setFlightMode('GUIDED')
        self.MapFrame.update_idletasks()
        # Ajuste para poder mostrar icono en amarillo y botón
        def takeoff_procedure():
            try:
                self.dron.arm()
                self.dron.takeOff(self.altura_vuelo)
            finally:
                self.MapFrame.after(0, lambda: self.informar('VOLANDO'))
        threading.Thread(target=takeoff_procedure, daemon=True).start()

    def RTL(self):
        self.RTL_active = True

        # llamo en modo no bloqueante y le indico qué función debe activar al acabar la operación, y qué parámetro debe usar
        self.dron.RTL(blocking=False, callback=self.informar, params='EN CASA')
        # mientras retorno pongo el boton en amarillo
        self.RTLBtn['bg'] = 'yellow'
        self.RTLBtn['text'] = 'Retornando....'

    # ===== INFORMAR ======
    def informar(self, mensaje):
        if mensaje == "EN CASA" or mensaje == "FIN MISION":
            # pongo el boton RTL en verde
            self.RTLBtn['bg'] = 'green'
            self.RTLBtn['fg'] = 'white'
            self.RTL_active = False
            self.dron.send_telemetry_info(self.process_telemetry_info)
            # me desconecto del dron (eso tardará 5 segundos)
            self.dron.disconnect()
            # devuelvo los botones a la situación inicial

            self.connectBtn['bg'] = 'dark orange'
            self.connectBtn['fg'] = 'black'
            self.connectBtn['text'] = 'Conectar'

            self.despegarBtn['bg'] = 'dark orange'
            self.despegarBtn['fg'] = 'black'
            self.despegarBtn['text'] = 'Despegar'

            self.RTLBtn['bg'] = 'dark orange'
            self.RTLBtn['fg'] = 'black'
            self.RTLBtn['text'] = 'RTL'
        if mensaje == "DESPEGANDO":
            self.RTL_active = True
            self.despegarBtn['bg'] = 'yellow'
            self.despegarBtn['fg'] = 'black'
            self.despegarBtn['text'] = 'Despegando...'
        if mensaje == "VOLANDO":
            self.RTL_active = False
            self.despegarBtn['bg'] = 'green'
            self.despegarBtn['fg'] = 'white'
            self.despegarBtn['text'] = 'Volando'
        if mensaje == "PRODUCCIÓN":
            self.CambiarConexionBtn['text'] = 'Cambiar a simulación'
        if mensaje == "SIMULACIÓN":
            self.CambiarConexionBtn['text'] = 'Cambiar a producción'

    # ======= MOSTRAR Y MODIFICAR ICONO DEL DRON =======
    def show_dron(self):
        self.update_drone_marker(self.initial_lat, self.initial_lon)
        if not self.dron.sendTelemetryInfo:
            self.dron.send_telemetry_info(self.process_telemetry_info)

    def rotate_icon(self, icon, angle):
        if icon == self.photo_red:
            pil_image = self.resized_icon_red
        elif icon == self.photo_yellow:
            pil_image = self.resized_icon_yellow
        elif icon == self.photo_green:
            pil_image = self.resized_icon_green
        else:
            pil_image = self.resized_icon
        rotated_image = pil_image.rotate(-angle, resample=Image.BICUBIC, expand=True)
        rotated_icon = ImageTk.PhotoImage(rotated_image)
        return rotated_icon

    def update_drone_marker(self, lat, lon):
        if self.RTL_active:
            icon_to_use = self.photo_yellow
        elif self.altura <= 0.03:
            icon_to_use = self.photo_red
        else:
            icon_to_use = self.photo_green

        heading = self.dron.heading
        rotated_icon = self.rotate_icon(icon_to_use, heading)

        if self.drone_marker:
            self.map_widget.delete(self.drone_marker)

        self.drone_marker = self.map_widget.set_marker(
            lat, lon,
            marker_color_outside="blue",
            marker_color_circle="black",
            text="",
            text_color="blue",
            icon=rotated_icon,
            icon_anchor="center"
        )

    # ===== DATOS DE TELEMETRÍA =====
    def process_telemetry_info(self, telemetry_info):
        lat = telemetry_info['lat']
        lon = telemetry_info['lon']
        self.altura = round(telemetry_info['alt'], 2)
        self.AlturaLabel.config(text=f"Altura: {self.altura} m")
        self.heading = int(round(telemetry_info['heading']))
        self.HeadingLabel.config(text=f"Heading: {self.heading} º")
        self.update_drone_marker(lat, lon)

    # ====== GEOFENCE =======
    def GeoFence(self):
        with open("waypoints geofence/GeoFenceScenario.json", "r") as file:
            scenario_data = json.load(file)

        geofence_waypoints = scenario_data[0]["waypoints"]

        self.map_widget.set_polygon(
            [(point['lat'], point['lon']) for point in geofence_waypoints],
            fill_color=None,
            outline_color="red",
            border_width=4,
            name="GeoFence_polygon"
        )

        self.dron.setScenario(scenario_data)

        parameters = [
            {'ID': "FENCE_ENABLE", 'Value': 1},
            {'ID': "FENCE_ACTION", 'Value': 4}
        ]
        self.dron.setParams(parameters)

    def creadorGeoFence(self):
        if self.isconnected == False:
            messagebox.showerror("Error", f"Establece conexión para crear la Geofence.")
            return
        map_window = tk.Toplevel()
        map_window.title("Creador de Misiones")
        map_window.geometry("720x480")

        map_geofence_class = GeoFenceCreator(self.dron)
        map_frame = map_geofence_class.buildFrame(map_window)
        map_frame.pack(fill="both", expand=True)

        map_geofence_class.save_geofence_btn.config(
            command=lambda: self.handle_new_geofence(map_geofence_class.save_geofence(), map_window)
        )

    def handle_new_geofence(self, geofence_data, window):
        if geofence_data:
            self.dron.setScenario(geofence_data)
            parameters = [
                {'ID': "FENCE_ENABLE", 'Value': 1},
                {'ID': "FENCE_ACTION", 'Value': 4}
            ]
            self.dron.setParams(parameters)

            self.update_geofence_display(geofence_data[0]["waypoints"])
            window.destroy()
        self.flag_new_geofence = True

    def update_geofence_display(self, waypoints):
        for item in self.map_widget.canvas.find_withtag("geofence"):
            self.map_widget.canvas.delete(item)

        self.map_widget.set_polygon(
            [(point['lat'], point['lon']) for point in waypoints],
            fill_color=None,
            outline_color="red",
            border_width=4,
            name="geofence"  # Remove the tag parameter
        )

    # ====== CAMBIAR PRODUCCIÓN SIMULACIÓN ======
    def change_connection(self):
        if self.tipo_conexión == "simulación":

            #self.tipo_conexión = "producción"
            #self.camara_input = 1
            #self.connection_string = 'COM3'
            #self.baud = 57600
            #self.informar('PRODUCCIÓN')

            conn_window = tk.Toplevel()
            conn_window.title("Configuración de Simulación")
            conn_window.geometry("300x120")

            tk.Label(conn_window, text="Introduce el puerto de conexión:").pack(pady=10)

            conn_entry = tk.Entry(conn_window, width=40)
            conn_entry.pack(pady=5)

            def apply_connection():
                new_connection = conn_entry.get()
                if new_connection:
                    self.connection_string = new_connection
                    self.tipo_conexión = "producción"
                    self.camara_input = 1
                    self.baud = 57600
                    self.informar('PRODUCCIÓN')
                    conn_window.destroy()

            tk.Button(conn_window, text="Aceptar", command=apply_connection).pack(pady=10)

        elif self.tipo_conexión == "producción":

            self.tipo_conexión = "simulación"
            self.camara_input = 0
            self.connection_string = 'tcp:127.0.0.1:5763'
            self.baud = 115200
            self.informar('SIMULACIÓN')

    # ====== CREADOR MISIONES ======
    def show_mission_map(self):
        map_window = tk.Toplevel()
        map_window.title("Creador de Misiones")
        map_window.geometry("920x620")

        map_mission_class = MapMission(self.dron, self.altura_vuelo, self.dron.navSpeed, self.flag_new_geofence)
        map_frame = map_mission_class.buildFrame(map_window)
        map_frame.pack(fill="both", expand=True)

    # ====== CREADOR MISIONES STITCHING ======
    def show_mission_stitching(self):
        map_window = tk.Toplevel()
        map_window.title("Creador de Misiones")
        map_window.geometry("300x150")

        map_mission_stiching = StitchingMission(self.dron, self.altura_vuelo, self.dron.navSpeed)
        map_frame = map_mission_stiching.buildFrame(map_window)
        map_frame.pack(fill="both", expand=True)

    # ====== SELECCIONAR MISION ======
    def select_mission(self):
        mission_path = filedialog.askopenfilename(
            title="Seleccionar Misión",
            initialdir=os.path.join(os.getcwd(), "missions"),
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )

        if mission_path:
            self.nombre_mision = os.path.splitext(os.path.basename(mission_path))[0]
            #messagebox.showinfo("Misión Seleccionada", f'La misión "{self.nombre_mision}" ha sido seleccionada.')
        self.load_visual_mission_waypoints(mission_path)
        self.MisionLabel.config(text=f"Misión: {self.nombre_mision}")

    def load_visual_mission_waypoints(self, mission_path):
        try:
            with open(mission_path, "r") as file:
                mission_data = json.load(file)

            waypoints = mission_data.get("waypoints", [])
            self.map_widget.delete_all_marker()
            self.map_widget.delete_all_path()

            wp_positions = []

            location_point_img = Image.open("assets/WaypointMarker.png")
            resized_location_point = location_point_img.resize((25, 25), Image.LANCZOS)
            location_point_icon = ImageTk.PhotoImage(resized_location_point)

            self.wp_icon = location_point_icon

            for i, wp in enumerate(waypoints, start=1):
                lat, lon = wp["lat"], wp["lon"]
                self.map_widget.set_marker(lat, lon,
                                           text=f"WP {i}",
                                           icon=self.wp_icon,
                                           icon_anchor="center")
                wp_positions.append((lat, lon))

            if len(wp_positions) > 1:
                self.map_widget.set_path(wp_positions, width=3, color="blue")

            print(f"Misión '{self.nombre_mision}' cargada con éxito!")

        except FileNotFoundError:
            print(f"Error: No se encontró el archivo '{mission_path}'.")
        except json.JSONDecodeError:
            print(f"Error: Formato JSON inválido en '{mission_path}'.")

    # ====== EJECUTAR MISION ======
    def load_mission(self):
        if self.nombre_mision == "":
            messagebox.showerror("Selecciona Misión", "Selecciona una misión.")
            return None
        try:
            mission_path = os.path.join("missions", f"{self.nombre_mision}.json")
            actions_waypoints_path = os.path.join("waypoints", f"{self.nombre_mision}.json")
            with open(mission_path, "r") as mission_file:
                mission = json.load(mission_file)
            with open(actions_waypoints_path, "r") as file:
                self.waypoints_actions = json.load(file)

            if "takeOffAlt" not in mission or "waypoints" not in mission:
                messagebox.showerror("Misión Inválida", "El archivo de misión es inválido.")
                return None

            #messagebox.showinfo("Misión Cargada", f'¡La misión "{self.nombre_mision}" se ha cargado correctamente!')
            return mission

        except FileNotFoundError:
            messagebox.showerror("Archivo No Encontrado",f'No se encontró la misión "{self.nombre_mision}.json" en la carpeta "missions".')
        except json.JSONDecodeError:
            messagebox.showerror("Error de JSON", "Hubo un error al leer el archivo de misión.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al cargar la misión: {str(e)}")

        return None

    def capture_and_save_photo(self):
        mission_folder = f"photos/{self.nombre_mision}"
        if self.cap == None:
            messagebox.showerror("Error", f"Inicia la conexión para poder capurar el frame.")
        if not self.nombre_mision:
            messagebox.showerror("Error", f"No hay una misión seleccionada donde guardar el frame.")
            return

        if not os.path.exists(mission_folder):
            os.makedirs(mission_folder)
            print(f"Carpeta '{mission_folder}' creada.")

        cap = self.cap

        if not cap.isOpened():
            print("Error: No se ha podido acceder a la cámara.")
            return

        ret, frame = cap.read()

        if ret:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{mission_folder}/photo_{timestamp}.jpg"

            cv2.imwrite(filename, frame)
            print(f"Foto guardada como {filename}.")

        else:
            print("Error: Fallo en capturar la foto.")

    def aqui(self, index, wp):
        if self.waypoints_actions['angle'][index] != -1:
            self.dron.changeHeading(self.waypoints_actions['angle'][index])
        if self.waypoints_actions['photo'][index] == 1:
            self.capture_and_save_photo()

        fix_actions = self.waypoints_actions.get('fix', []) # Fix solo se usa en misiones de stitching, este if hace que no de error en misiones normales
        if index < len(fix_actions):
            if fix_actions[index] == 1:
                self.dron.fixHeading()
            elif fix_actions[index] == 2:
                self.dron.unfixHeading()
        return

    def execute_mission(self):
        mission = self.load_mission()
        if mission is None:
            return

        self.dron.uploadMission(mission, blocking=False)
        messagebox.showinfo("Inicio Misión", '¡Comienza la misión!')

        if not self.dron.sendTelemetryInfo:
            self.dron.send_telemetry_info(self.process_telemetry_info)

        self.dron.executeFlightPlan(mission, blocking = False, inWaypoint=self.aqui)
        def check_if_landed():
            if self.altura <= 0.03:
                self.informar("FIN MISION")
            else: self.MapFrame.after(1000, check_if_landed)
        self.MapFrame.after(12000, check_if_landed) # Primer check después de 12 segundos

        #messagebox.showinfo("Misión Cumplida", '¡Misión cumplida!')

    # ====== IMAGE STITCHING OPENCV =======
    def show_stitched_image(self):
        if self.nombre_mision == "":
            messagebox.showerror("Selecciona Misión", "Selecciona una misión.")
            return None

        image_directory = f"photos/{self.nombre_mision}"
        if not os.path.exists(image_directory):
            messagebox.showerror("Misión sin imágenes", "La misión seleccionada no tiene imágenes.")
            return None

        image_directory = f"photos/{self.nombre_mision}"
        if not os.path.exists(image_directory):
            messagebox.showerror("Error", f"El directorio {image_directory} no existe.")
            return

        images = [cv2.imread(os.path.join(image_directory, f)) for f in os.listdir(image_directory)
                  if f.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.JPG'))]

        images = [img for img in images if img is not None]

        if len(images) < 2:
            messagebox.showerror("Error", "Se necesitan al menos dos imágenes para hacer el stitching.")
            return

        stitcher = cv2.Stitcher.create()
        status, stitched = stitcher.stitch(images)

        if status != cv2.Stitcher_OK:
            messagebox.showerror("Error", "No se pudo hacer el stitching de las imágenes.")
            return

        stitched = cv2.cvtColor(stitched, cv2.COLOR_BGR2RGB)  # Convert from BGR to RGB
        stitched_pil = Image.fromarray(stitched)
        stitched_pil = stitched_pil.resize((800, 600), Image.Resampling.LANCZOS)
        stitched_photo = ImageTk.PhotoImage(stitched_pil)


        if self.map_frame:
            self.map_frame.grid_forget()

        self.stitch_frame = tk.Frame(self.MapFrame)
        self.stitch_frame.grid(row=0, column=0, columnspan=16, padx=5, pady=5, sticky="nsew")

        self.stitch_frame.rowconfigure(0, weight=0)
        self.stitch_frame.rowconfigure(1, weight=10)
        self.stitch_frame.columnconfigure(0, weight=1)
        self.stitch_frame.columnconfigure(1, weight=10)
        self.stitch_frame.columnconfigure(2, weight=1)

        img_label = tk.Label(self.stitch_frame, image=stitched_photo)
        img_label.image = stitched_photo
        img_label.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        back_button = tk.Button(self.stitch_frame, text="Volver", bg="dark orange", fg="black",
                                command=self.show_main_page)
        back_button.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")

    # ====== IMAGE STITCHING MANUAL =======
    def show_manual_stitched_image(self):
        stitchingmanual = ManualImageStitching(self.nombre_mision, self.MapFrame)
        stitchingmanual.show_manual_stitched_image()
        return

    # ====== GALERIA MISION ======
    def show_gallery_page(self):
        if self.nombre_mision == "":
            messagebox.showerror("Selecciona Misión", "Selecciona una misión.")
            return None

        image_directory = f"photos/{self.nombre_mision}"
        if not os.path.exists(image_directory):
            messagebox.showerror("Misión sin imágenes", "La misión seleccionada no tiene imágenes.")
            return None

        if self.map_frame:
            self.map_frame.grid_forget()

        self.gallery_frame = tk.Frame(self.MapFrame)
        self.gallery_frame.grid(row=0, column=0, columnspan=16, padx=5, pady=5, sticky="nsew")

        self.gallery_frame.rowconfigure(0, weight=0)
        self.gallery_frame.rowconfigure(1, weight=10)

        self.gallery_frame.columnconfigure(0, weight=1)
        self.gallery_frame.columnconfigure(1, weight=10)
        self.gallery_frame.columnconfigure(2, weight=1)

        image_directory = f"photos/{self.nombre_mision}"
        if not os.path.exists(image_directory):
            messagebox.showerror("Error", f"El directorio {image_directory} no existe.")
            return

        images = [f for f in os.listdir(image_directory) if f.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.JPG'))]

        self.current_image_index = 0
        self.img_labels = []

        def display_image(index):
            for label in self.img_labels:
                label.destroy()

            image_name = images[index]
            image_path = os.path.join(image_directory, image_name)
            img = Image.open(image_path)
            img = img.resize((800, 600), Image.Resampling.LANCZOS)
            img_photo = ImageTk.PhotoImage(img)

            img_label = tk.Label(self.gallery_frame, image=img_photo)
            img_label.image = img_photo
            img_label.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

            self.img_labels.append(img_label)

        display_image(self.current_image_index)

        def next_image():
            if self.current_image_index < len(images) - 1:
                self.current_image_index += 1
                display_image(self.current_image_index)

        def prev_image():
            if self.current_image_index > 0:
                self.current_image_index -= 1
                display_image(self.current_image_index)

        left_button = tk.Button(self.gallery_frame, text="<", bg="dark orange", fg="black", command=prev_image)
        left_button.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        right_button = tk.Button(self.gallery_frame, text=">", bg="dark orange", fg="black", command=next_image)
        right_button.grid(row=0, column=2, padx=20, pady=10, sticky="nsew")

        back_button = tk.Button(self.gallery_frame, text="Volver", bg="dark orange", fg="black",
                                command=self.show_main_page)
        back_button.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")

    # ====== GALERIA MISION PROCESADA ======
    def show_gallery_processed_page(self):
        if self.nombre_mision == "":
            messagebox.showerror("Selecciona Misión", "Selecciona una misión.")
            return None

        image_directory = f"photos/{self.nombre_mision}"
        if not os.path.exists(image_directory):
            messagebox.showerror("Misión sin imágenes", "La misión seleccionada no tiene imágenes.")
            return None

        if self.map_frame:
            self.map_frame.grid_forget()

        self.gallery_processed_frame = tk.Frame(self.MapFrame)
        self.gallery_processed_frame.grid(row=0, column=0, columnspan=16, padx=5, pady=5, sticky="nsew")
        self.gallery_processed_frame.rowconfigure(0, weight=0)
        self.gallery_processed_frame.rowconfigure(1, weight=10)

        self.gallery_processed_frame.columnconfigure(0, weight=1)
        self.gallery_processed_frame.columnconfigure(1, weight=10)
        self.gallery_processed_frame.columnconfigure(2, weight=1)

        images = [f for f in os.listdir(image_directory) if f.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.JPG'))]
        self.current_image_index = 0
        self.img_labels = []

        # Diccionario de clases: (https://stackoverflow.com/questions/77477793/class-ids-and-their-relevant-class-names-for-yolov8-model#:~:text=I%20understand%20there%20are%20approximately,object%20detection%20model%20of%20YOLOv8.)
        class_dict = {0: 'person',1: 'bicycle', 51: 'carrot', 46: 'banana', 38: 'tennis racket', 74: 'clock'}

        self.selected_class = tk.IntVar()
        self.selected_class.set(0)

        class_names = list(class_dict.values())
        self.selected_name = tk.StringVar()

        class_menu = tk.OptionMenu(self.gallery_processed_frame, self.selected_name, *class_names,
                                   command=lambda x: on_class_select(x))

        class_menu.grid(row=0, column=3, padx=5, pady=5)

        def on_class_select(selected_name):
            selected_key = [key for key, value in class_dict.items() if value == selected_name][0]
            self.selected_class.set(selected_key)
            display_image(self.current_image_index)


        def display_image(index):
            for label in self.img_labels:
                label.destroy()

            image_name = images[index]
            image_path = os.path.join(image_directory, image_name)

            selected_class = [self.selected_class.get()]
            self.model.classes = selected_class

            results = self.model.predict(source=image_path, save=False, classes=selected_class)

            processed_img = results[0].plot()
            processed_img = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)

            img_pil = Image.fromarray(processed_img)
            img_pil = img_pil.resize((800, 600), Image.Resampling.LANCZOS)
            img_photo = ImageTk.PhotoImage(img_pil)

            img_label = tk.Label(self.gallery_processed_frame, image=img_photo)
            img_label.image = img_photo
            img_label.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

            self.img_labels.append(img_label)

        display_image(self.current_image_index)

        def next_image():
            if self.current_image_index < len(images) - 1:
                self.current_image_index += 1
                display_image(self.current_image_index)

        def prev_image():
            if self.current_image_index > 0:
                self.current_image_index -= 1
                display_image(self.current_image_index)

        left_button = tk.Button(self.gallery_processed_frame, text="<", bg="dark orange", fg="black",
                                command=prev_image)
        left_button.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        right_button = tk.Button(self.gallery_processed_frame, text=">", bg="dark orange", fg="black",
                                 command=next_image)
        right_button.grid(row=0, column=2, padx=20, pady=10, sticky="nsew")

        back_button = tk.Button(self.gallery_processed_frame, text="Volver", bg="dark orange", fg="black",
                                command=self.show_main_page)
        back_button.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")

    def show_main_page(self):
        if self.gallery_frame:
            self.gallery_frame.grid_forget()
        if self.gallery_processed_frame:
            self.gallery_processed_frame.grid_forget()
        if self.stitch_frame:
            self.stitch_frame.grid_forget()

    # ======== INICIAR JUEGO ========
    def iniciar_juego(self):
        self.stop_show_video()

        self.arm_and_takeOff()
        self.cam_window = tk.Toplevel(self.MapFrame)
        self.cam_window.title("Detección de Objetos")
        self.cam_window.geometry("700x500")

        self.video_frame = tk.Frame(self.cam_window)
        self.video_frame.pack(fill="both", expand=True)

        self.game_video_label = tk.Label(self.video_frame)
        self.game_video_label.pack(padx=10, pady=10)

        self.update_frame()

        self.cam_window.protocol("WM_DELETE_WINDOW", self.close_game_window)

    def update_frame(self):
        ret, frame = self.cap.read()
        porcentaje_recon = 0.3 # Solo se reconocen objetos en recuadro central que ocupa 30% del frame
        if ret:
            h, w = frame.shape[:2]
            center_x, center_y = w // 2, h // 2
            box_w, box_h = int(w * porcentaje_recon), int(h * porcentaje_recon)
            x1, y1 = center_x - box_w // 2, center_y - box_h // 2
            x2, y2 = center_x + box_w // 2, center_y + box_h // 2

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            roi = frame[y1:y2, x1:x2].copy()

            results = self.model.predict(source=roi, save=False, classes=[51, 11, 38, 46, 74])

            if len(results[0].boxes) > 0:
                for box in results[0].boxes:
                    box_coords = box.xyxy[0].clone().cpu().numpy()

                    box_coords[0] += x1
                    box_coords[1] += y1
                    box_coords[2] += x1
                    box_coords[3] += y1

                    cv2.rectangle(frame,
                                  (int(box_coords[0]), int(box_coords[1])),
                                  (int(box_coords[2]), int(box_coords[3])),
                                  (255, 0, 0), 2)

                    label = f"{self.model.names[int(box.cls[0])]} {box.conf[0]:.2f}"
                    cv2.putText(frame, label,
                                (int(box_coords[0]), int(box_coords[1]) - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.game_video_label.imgtk = imgtk
            self.game_video_label.config(image=imgtk)

            self.detected_objects = [int(box.cls[0]) for box in results[0].boxes] if len(results[0].boxes) > 0 else []

            if 51 in self.detected_objects:  # Zanahoria
                self.MapFrame.update_idletasks()
                self.dron.go("North")
            if 11 in self.detected_objects:  # Stop sign
                self.MapFrame.update_idletasks()
                self.RTL()
                self.close_game_window()
            if 38 in self.detected_objects:  # Raqueta
                self.MapFrame.update_idletasks()
                self.dron.go("South")
            if 46 in self.detected_objects:  # Plátano
                self.MapFrame.update_idletasks()
                self.dron.go("West")
            if 74 in self.detected_objects:  # Reloj
                self.MapFrame.update_idletasks()
                self.dron.go("East")

        if self.cap:
            self.video_label.after(10, self.update_frame)

    # ======== VIDEO CAMARA =======
    def show_video(self):
        if self.cap is None:
            self.video_label.after(30, self.show_video)
            return
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (228, 171))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self._video_job = self.video_label.after(30, self.show_video)

    def stop_show_video(self):
        if hasattr(self, '_video_job'):
            self.video_label.after_cancel(self._video_job)
            self._video_job = None

    def close_game_window(self):
        self.cam_window.destroy()
        self.show_video()

    # ====== PARAMETROS ======
    def aplicar_altura(self):
        try:
            nueva_altura = int(self.altura_entry.get())
            if nueva_altura <= 0:
                raise ValueError("La altura debe ser mayor que 0")

            self.altura_vuelo = nueva_altura

        except ValueError as e:
            messagebox.showerror("Error", f"Dato inválido: {str(e)}")
            self.altura_entry.delete(0, tk.END)
            self.altura_entry.insert(0, str(self.altura_vuelo))

    def aplicar_velocidad(self):
        try:
            nueva_velocidad = float(self.vel_entry.get())
            if nueva_velocidad <= 0:
                raise ValueError("La velocidad debe ser mayor que 0")

            self.dron.navSpeed = nueva_velocidad

        except ValueError as e:
            messagebox.showerror("Error", f"Dato inválido: {str(e)}")
            self.vel_entry.delete(0, tk.END)
            self.vel_entry.insert(0, f"{self.dron.navSpeed:.1f}")






