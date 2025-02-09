import json
import tkinter as tk
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

        # === FRAME ===
        self.frame = tk.LabelFrame(self.MapMission, text="Opciones")
        self.frame.grid(row=0, column=0, columnspan = 10, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.frame.rowconfigure(0, weight=2)
        self.frame.rowconfigure(1, weight=2)
        self.frame.columnconfigure(0, weight=2)
        self.frame.columnconfigure(1, weight=2)

        self.ejecutarBtn = tk.Button(self.frame, text="Ejecutar Misión", bg="dark orange", fg="black")
        self.ejecutarBtn.grid(row=0, column=0, columnspan = 5, padx=5, pady=3, sticky="nesw")

        return self.MapMission

    # ====== GEOFENCE =======
    # aqui venimos cuando tenemos ya definido el geofence y lo queremos enviar al dron
    def MostrarGeoFence(self):

        with open("GeoFenceScenario.json", "r") as file:
            scenario_data = json.load(file)

        geofence_waypoints = scenario_data[0]["waypoints"]

        polygon = self.map_widget.set_polygon(
            [(point['lat'], point['lon']) for point in geofence_waypoints],
            fill_color=None,
            outline_color="red",
            border_width=5,
            name="GeoFence_polygon"
        )