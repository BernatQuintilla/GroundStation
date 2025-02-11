import json
import tkinter as tk
import os
import tkintermapview
from tkinter import Canvas
from tkinter import messagebox
from tkinter import ttk
from pymavlink import mavutil
from PIL import Image, ImageTk
from CamaraVideo import *
from ObjectRecognition import *
import json

class MapMission:

    def __init__(self, dron, altura_vuelo):
        # guardamos el objeto de la clase dron con el que estamos controlando el dron
        self.dron = dron
        self.altura = 0
        self.altura_vuelo = altura_vuelo
        self.geofence_waypoints = []

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

        # Waypoints misión
        self.waypoints = []
        self.lines = []

    def buildFrame(self, fatherFrame):

        self.MapMission = tk.Frame(fatherFrame)  # create new frame where the map will be allocated

        # creamos el widget para el mapa
        self.map_widget = tkintermapview.TkinterMapView(self.MapMission, width=820, height=620, corner_radius=0)
        self.map_widget.grid(row=1, column=0, columnspan = 10, padx=5, pady=5)
        # cargamos la imagen del dronlab
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga",
                                            max_zoom=22)
        self.map_widget.set_position(41.276430, 1.988686)  # Coordenadas del Dronelab

        # nivel inicial de zoom y posición inicial
        self.map_widget.set_zoom(20)
        self.initial_lat = 41.276430
        self.initial_lon = 1.988686

        self.MapMission.rowconfigure(0, weight=1)
        self.MapMission.rowconfigure(1, weight=10)

        self.MapMission.columnconfigure(0, weight=1)
        self.MapMission.columnconfigure(1, weight=1)

        self.MostrarGeoFence()

        self.map_widget.add_right_click_menu_command(label="Añadir Waypoint", command=self.add_marker_event, pass_coords=True)

        # === FRAME ===
        self.frame = tk.LabelFrame(self.MapMission, text="Opciones")
        self.frame.grid(row=0, column=0, columnspan = 10, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.frame.rowconfigure(0, weight=2)
        self.frame.rowconfigure(1, weight=2)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.columnconfigure(2, weight=2)

        self.mission_name_label = tk.Label(self.frame, text="Nombre de la misión:")
        self.mission_name_label.grid(row=0, column=0, padx=5, pady=3, sticky="w")

        self.mission_name_entry = tk.Entry(self.frame)
        self.mission_name_entry.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        # Botón para guardar misión
        self.save_mission_btn = tk.Button(self.frame, text="Guardar Misión", bg="dark orange", fg="black",
                                          command=self.save_mission)
        self.save_mission_btn.grid(row=0, column=2, padx=5, pady=3, sticky="nesw")

        return self.MapMission

    # ====== GEOFENCE =======
    # aqui venimos cuando tenemos ya definido el geofence y lo queremos enviar al dron
    def MostrarGeoFence(self):

        with open("GeoFenceScenario.json", "r") as file:
            scenario_data = json.load(file)

        self.geofence_waypoints = scenario_data[0]["waypoints"]

        polygon = self.map_widget.set_polygon(
            [(point['lat'], point['lon']) for point in self.geofence_waypoints],
            fill_color=None,
            outline_color="red",
            border_width=4,
            name="GeoFence_polygon"
        )
    # Usamos para comprobar si wp dentro de geofence
    def dentro_de_geofence(self, lat, lon):
        geofence_polygon = [(point['lat'], point['lon']) for point in self.geofence_waypoints]

        inside = False
        x, y = lat, lon
        n = len(geofence_polygon)
        p1x, p1y = geofence_polygon[0]

        for i in range(n + 1):
            p2x, p2y = geofence_polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        else:
                            xinters = p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside

            p1x, p1y = p2x, p2y

        return inside

    # ===== FUNCIONES MISIÓN ======
    def add_marker_event(self, coords):

        if not self.dentro_de_geofence(coords[0], coords[1]):
            messagebox.showwarning("Coordenadas fuera del Geofence","Selecciona coordenadas dentro del Geofence.")
            return

        location_point_img = Image.open("assets/WaypointMarker.png")
        resized_location_point = location_point_img.resize((25, 25), Image.LANCZOS)
        location_point_icon = ImageTk.PhotoImage(resized_location_point)

        marker = self.map_widget.set_marker(coords[0], coords[1],
                                            text=f"WP {len(self.waypoints) + 1}",
                                            icon=location_point_icon,
                                            icon_anchor="center")

        self.waypoints.append({'lat': coords[0], 'lon': coords[1], 'marker': marker})

        if len(self.waypoints) > 1:
            last_wp = self.waypoints[-2]
            current_wp = self.waypoints[-1]

            self.map_widget.set_path(
                [(last_wp['lat'], last_wp['lon']), (current_wp['lat'], current_wp['lon'])],
                color="blue",
                width=2
            )

    def save_mission(self):
        mission_name = self.mission_name_entry.get().strip()

        if not mission_name:
            mission_name = "mission"

        if not self.waypoints:
            messagebox.showerror("No hay Waypoints", "Por favor, añade waypoints antes de guardar la misión.")
            return

        mission_folder = "missions"
        if not os.path.exists(mission_folder):
            os.makedirs(mission_folder)

        mission_path = os.path.join(mission_folder, f"{mission_name}.json")

        mission = {
            "takeOffAlt": self.altura_vuelo,
            "waypoints": [{"lat": wp["lat"], "lon": wp["lon"], "alt": self.altura_vuelo} for wp in self.waypoints]
        }

        with open(mission_path, "w") as mission_file:
            json.dump(mission, mission_file, indent=4)

        messagebox.showinfo("Misión Guardada",f'¡La misión se ha guardado como "{mission_name}.json" en la carpeta "Missions"!')



