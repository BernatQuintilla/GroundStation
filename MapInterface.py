import json
import time
import tkinter as tk
import tkintermapview
from tkinter import Canvas
from tkinter import messagebox
from tkinter import ttk
from tkinter import StringVar
from tkinter import filedialog
from pymavlink import mavutil
from PIL import Image, ImageTk, ImageGrab
from CamaraVideo import *
from ObjectRecognition import *
from CreadorMisiones import *
import io
import threading
import cv2
import os
from datetime import datetime
import shutil
from dronLink.modules.dron_telemetry import send_telemetry_info
from ultralytics import YOLO


class MapFrameClass:
    # ======== INICIALIZAR CLASE ========
    def __init__(self, dron):
        # guardamos el objeto de la clase dron con el que estamos controlando el dron
        self.dron = dron
        self.altura = 0
        self.altura_vuelo = 5
        self.dron.navSpeed = 0.001
        # atributos necesarios para crear el geofence
        self.vertex_count = 4

        # atributos para establecer el trazado del dron
        self.trace = False
        self.last_position = None  # actualizar trazado

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
        self.marker = False  # Para activar el marker (en forma de icono de dron)
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

        # YOLO model
        self.model = YOLO("models/yolov8n.pt")

    # ======== BUILD FRAME ========
    def buildFrame(self, fatherFrame):

        self.MapFrame = tk.Frame(fatherFrame)  # create new frame where the map will be allocated

        # creamos el widget para el mapa
        self.map_widget = tkintermapview.TkinterMapView(self.MapFrame, width=1000, height=600, corner_radius=0)
        self.map_widget.grid(row=1, column=0, columnspan=15, padx=5, pady=5)
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

        self.MisionLabel = tk.Label(
            self.mision_frame,
            text=f"Misión: no seleccionada",
            bg="light gray",
            fg="black",
            width=20,  # Adjust the width to your needs
        )
        self.MisionLabel.grid(row=0, column=1, columnspan=2, padx=5, pady=3, sticky="nesw")

        #self.AreaBtn = tk.Button(self.mision_frame, text="Crear área de observación", bg="dark orange", fg="black")
        #self.AreaBtn.grid(row=0, column=1, padx=5, pady=3, sticky="nesw")

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

        # === FRAME GALERIA DE IMAGENES ===
        self.galeria_frame = tk.LabelFrame(self.MapFrame, text="Galería de imágenes de misión")
        self.galeria_frame.grid(row=0, column=13, columnspan=1, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.galeria_frame.rowconfigure(0, weight=2)
        self.galeria_frame.rowconfigure(1, weight=2)
        self.galeria_frame.columnconfigure(0, weight=2)

        self.GaleriaBtn = tk.Button(self.galeria_frame, text="Galería de imágenes", bg="dark orange", fg="black", command=self.show_gallery_page)
        self.GaleriaBtn.grid(row=0, column=0, columnspan=2, padx=5, pady=3, sticky="nesw")

        self.GaleriaProcesadaBtn = tk.Button(self.galeria_frame, text="Galería de imágenes procesadas", bg="dark orange", fg="black", command = self.show_gallery_processed_page)
        self.GaleriaProcesadaBtn.grid(row=1, column=0, columnspan=2, padx=5, pady=3, sticky="nesw")

        self.map_frame = self.MapFrame

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
        self.RTL_active = True
        self.informar('DESPEGANDO')
        self.MapFrame.update_idletasks()
        # Ajuste para poder mostrar icono en amarillo y botón
        def takeoff_procedure():
            try:
                self.altura_vuelo = int(self.altura_input.get())
                self.dron.arm()
                self.dron.takeOff(self.altura_vuelo)
            finally:
                self.MapFrame.after(0, lambda: self.informar('VOLANDO'))
        threading.Thread(target=takeoff_procedure, daemon=True).start()

    def RTL(self):
        if self.dron.going:
            self.dron.stopGo()
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

    # ======= MOSTRAR Y MODIFICAR ICONO DEL DRON =======
    def show_dron(self):
        # Muestro el dron o dejo de mostrarlo
        self.marker = not self.marker
        if self.marker:
            self.update_drone_marker(self.initial_lat, self.initial_lon)
            if not self.dron.sendTelemetryInfo:
                self.dron.send_telemetry_info(self.process_telemetry_info)
            self.informar('DRON_VISIBLE')
        else:
            # Si hay que quitarlo, lo hago aquí
            if self.drone_marker:
                self.map_widget.delete(self.drone_marker)
            # if not self.trace:
                #self.dron.stop_sending_telemetry_info()
            self.informar('DRON_OCULTO')

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
        #print(self.dron.heading)
        if self.trace:
            if self.last_position:
                self.map_widget.set_path([self.last_position, (lat, lon)], width=3)
            self.last_position = (lat, lon)

        if self.marker:
            self.update_drone_marker(lat, lon)

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

        parameters = [
            {'ID': "FENCE_ENABLE", 'Value': 1},
            {'ID': "FENCE_ACTION", 'Value': 4}
        ]
        self.dron.setParams(parameters)

    # ====== CREADOR MISIONES ======
    def show_mission_map(self):
        map_window = tk.Toplevel()
        map_window.title("Creador de Misiones")
        map_window.geometry("920x620")

        map_mission_class = MapMission(self.dron, self.altura_vuelo)
        map_frame = map_mission_class.buildFrame(map_window)
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

        if not os.path.exists(mission_folder):
            os.makedirs(mission_folder)
            print(f"Carpeta '{mission_folder}' creada.")

        cap = cv2.VideoCapture(0)

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

        cap.release()
        cv2.destroyAllWindows()

    def aqui(self, index, wp):
        if self.waypoints_actions['photo'][index] == 1:
            self.capture_and_save_photo()
        return

    def execute_mission(self):
        mission = self.load_mission()
        if mission is None:
            return

        mission['speed'] = 1 # Cambio velocidad a 1

        self.dron.uploadMission(mission, blocking=False)

        messagebox.showinfo("Inicio Misión", '¡Comienza la misión!')

        if not self.dron.sendTelemetryInfo:
            self.dron.send_telemetry_info(self.process_telemetry_info)

        self.dron.executeFlightPlan(mission, blocking = False, inWaypoint=self.aqui)

        check_if_landed = lambda: (
            self.informar("FIN MISION")
            if self.altura <= 0.03
            else self.MapFrame.after(1000, check_if_landed)
        )
        self.MapFrame.after(1000, check_if_landed)

        #messagebox.showinfo("Misión Cumplida", '¡Misión cumplida!')

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
        self.gallery_frame.grid(row=0, column=0, columnspan=15, padx=5, pady=5, sticky="nsew")

        self.gallery_frame.rowconfigure(0, weight=0)
        self.gallery_frame.rowconfigure(1, weight=10)

        self.gallery_frame.columnconfigure(0, weight=1)
        self.gallery_frame.columnconfigure(1, weight=10)
        self.gallery_frame.columnconfigure(2, weight=1)

        image_directory = f"photos/{self.nombre_mision}"
        if not os.path.exists(image_directory):
            messagebox.showerror("Error", f"El directorio {image_directory} no existe.")
            return

        images = [f for f in os.listdir(image_directory) if f.endswith(('.png', '.jpg', '.jpeg', '.bmp'))]

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
        self.gallery_processed_frame.grid(row=0, column=0, columnspan=15, padx=5, pady=5, sticky="nsew")
        self.gallery_processed_frame.rowconfigure(0, weight=0)
        self.gallery_processed_frame.rowconfigure(1, weight=10)

        self.gallery_processed_frame.columnconfigure(0, weight=1)
        self.gallery_processed_frame.columnconfigure(1, weight=10)
        self.gallery_processed_frame.columnconfigure(2, weight=1)

        images = [f for f in os.listdir(image_directory) if f.endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        self.current_image_index = 0
        self.img_labels = []

        # Diccionario de clases: (https://stackoverflow.com/questions/77477793/class-ids-and-their-relevant-class-names-for-yolov8-model#:~:text=I%20understand%20there%20are%20approximately,object%20detection%20model%20of%20YOLOv8.)
        class_dict = {0: 'person',1: 'bicycle', 41: 'cup', 46: 'banana', 47: 'apple', 56: 'chair',
                      67: 'cell phone', 73: 'book', 74: 'clock', 76: 'scissors', 77: 'teddy bear'}

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

    # ====== FUNCIONALIDADES ======
    def activar_camara(self):
        show_camera_video(self.MapFrame)

    def activar_ObjRecognition(self):
        show_camera_recognition(self.MapFrame)






