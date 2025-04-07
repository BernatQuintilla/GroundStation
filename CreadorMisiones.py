import json
import tkinter as tk
import os
import tkintermapview
from tkinter import Canvas
from tkinter import messagebox, simpledialog
from tkinter import ttk
from pymavlink import mavutil
from PIL import Image, ImageTk
from CamaraVideo import *
from ObjectRecognition import *
import json
import shutil

class MapMission:

    def __init__(self, dron, altura_vuelo):
        # guardamos el objeto de la clase dron con el que estamos controlando el dron
        self.dron = dron
        self.altura = 0
        self.speed = 1 # Velocidad predeterminada
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
        self.wp_actions = {'photo': [],'angle': []}
        self.selected_wp = None
        self.new_direction = "-"


    def buildFrame(self, fatherFrame):

        self.MapMission = tk.Frame(fatherFrame)  # create new frame where the map will be allocated

        # creamos el widget para el mapa
        self.map_widget = tkintermapview.TkinterMapView(self.MapMission, width=820, height=600, corner_radius=0)
        self.map_widget.grid(row=1, column=0, columnspan = 9, padx=5, pady=5)
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
        self.frame.grid(row=0, column=0, columnspan = 5, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

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

        # === Lista de Waypoints ===
        self.wp_frame = tk.LabelFrame(self.MapMission, text="Waypoints")
        self.wp_frame.grid(row=1, column=10, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.wp_listbox = tk.Listbox(self.wp_frame, height=10, width=30)
        self.wp_listbox.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.wp_scrollbar = tk.Scrollbar(self.wp_frame, orient="vertical", command=self.wp_listbox.yview)
        self.wp_scrollbar.grid(row=0, column=1, sticky="ns")
        self.wp_listbox.config(yscrollcommand=self.wp_scrollbar.set)

        self.edit_wp_button = tk.Button(self.wp_frame, text="Hacer Foto en WP", command=self.photo_waypoint)
        self.edit_wp_button.grid(row=1, column=0, padx=5, pady=2, sticky="ew")

        self.delete_wp_button = tk.Button(self.wp_frame, text="Cambiar Ángulo en WP", command=self.change_angle_waypoint)
        self.delete_wp_button.grid(row=2, column=0, padx=5, pady=2, sticky="ew")

        # === Input Velocidad ===
        self.vel = tk.LabelFrame(self.MapMission, text="Velocidad Misión")
        self.vel.grid(row=0, column=6, columnspan=4, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.vel.rowconfigure(0, weight=2)
        self.vel.columnconfigure(0, weight=1)
        self.vel.columnconfigure(1, weight=1)

        self.speed_label = tk.Label(self.vel, text="Velocidad (m/s):")
        self.speed_label.grid(row=0, column=2, padx=5, pady=3, sticky="w")

        self.speed_entry = tk.Entry(self.vel)
        self.speed_entry.insert(0, str(self.speed))
        self.speed_entry.grid(row=0, column=3, padx=5, pady=3, sticky="ew")

        # === Eliminar Misión ===
        self.el_mision = tk.LabelFrame(self.MapMission, text="Eliminar Misión Existente")
        self.el_mision.grid(row=0, column=10, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.el_mission_name_entry = tk.Entry(self.el_mision)
        self.el_mission_name_entry.grid(row=0, column=0, padx=5, pady=3, sticky="ew")

        # Botón para eliminar misión
        self.el_mission_btn = tk.Button(self.el_mision, text="Eliminar", bg="red", fg="white",
                                          command=self.eliminar_mision)
        self.el_mission_btn.grid(row=0, column=1, padx=5, pady=3, sticky="nesw")

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
            messagebox.showwarning("Coordenadas fuera del Geofence", "Selecciona coordenadas dentro del Geofence.")
            return

        location_point_img = Image.open("assets/WaypointMarker.png")
        resized_location_point = location_point_img.resize((25, 25), Image.LANCZOS)
        location_point_icon = ImageTk.PhotoImage(resized_location_point)

        marker = self.map_widget.set_marker(coords[0], coords[1],
                                            text=f"WP {len(self.waypoints) + 1}",
                                            icon=location_point_icon,
                                            icon_anchor="center")

        wp_data = {'lat': coords[0], 'lon': coords[1], 'marker': marker}
        self.waypoints.append(wp_data)

        self.wp_listbox.insert(tk.END, f"WP {len(self.waypoints)} ")

        self.wp_actions['photo'].append(0)
        self.wp_actions['angle'].append(-1)

        if len(self.waypoints) > 1:
            prev_wp = self.waypoints[-2]
            current_wp = self.waypoints[-1]
            line = self.map_widget.set_path(
                [(prev_wp['lat'], prev_wp['lon']), (current_wp['lat'], current_wp['lon'])],
                color="blue",
                width=2
            )
            self.lines.append(line)

    # ===== FUNCIONES MISION WP ======
    def photo_waypoint(self):

        selected_wp = self.wp_listbox.curselection()
        if not selected_wp:
            messagebox.showwarning("No WP Seleccionado",
                                   "Por favor, selecciona un waypoint de la lista para tomar una foto.")
            return

        wp_index = selected_wp[0]

        if 'photo' not in self.wp_actions:
            self.wp_actions['photo'] = []

        if wp_index >= len(self.wp_actions['photo']):
            self.wp_actions['photo'].append(0)

        if self.wp_actions['photo'][wp_index] == 1:
            self.wp_actions['photo'][wp_index] = 0
        else:
            self.wp_actions['photo'][wp_index] = 1

        direction_angles_reverse = {
            360: "N",
            45: "NE",
            90: "E",
            135: "SE",
            180: "S",
            225: "SW",
            270: "W",
            315: "NW",
            -1: "-"
        }
        if wp_index < len(self.wp_actions['angle']):
            angle = self.wp_actions['angle'][wp_index]
            direction = direction_angles_reverse[angle]
        else:
            direction = "-"

        self.wp_listbox.delete(wp_index)
        self.wp_listbox.insert(wp_index,
                               f"WP {wp_index + 1} - Foto: {'Sí' if self.wp_actions['photo'][wp_index] == 1 else 'No'} "
                               f"- Ángulo: ( {direction} )")

    def change_angle_waypoint(self):
        selected_wp = self.wp_listbox.curselection()
        if not selected_wp:
            messagebox.showwarning("No WP Seleccionado",
                                   "Por favor, selecciona un waypoint de la lista para cambiar ángulo")
            return

        wp_index = selected_wp[0]

        if 'angle' not in self.wp_actions:
            self.wp_actions['angle'] = []

        while wp_index >= len(self.wp_actions['angle']):
            self.wp_actions['angle'].append(-1)

        direction_angles = {
            "N": 360,
            "NE": 45,
            "E": 90,
            "SE": 135,
            "S": 180,
            "SW": 225,
            "W": 270,
            "NW": 315,
            "Eliminar": -1  # Opción para borrar el ángulo
        }
        self.new_direction = simpledialog.askstring("Selecciona Dirección",
                                               "Ingresa una dirección (N, NE, E, SE, S, SW, W, NW):\n Para eliminar ingresa: Eliminar")

        if self.new_direction not in direction_angles and self.new_direction != "-":
            messagebox.showwarning("Dirección inválida",
                                   "Por favor, ingresa una de las opciones: N, NE, E, SE, S, SW, W, NW")
            return

        self.wp_actions['angle'][wp_index] = direction_angles[self.new_direction]

        if self.new_direction == "Eliminar":
            self.new_direction = "-"
        self.wp_listbox.delete(wp_index)
        self.wp_listbox.insert(wp_index,
                               f"WP {wp_index + 1} - Foto: {'Sí' if self.wp_actions['photo'][wp_index] == 1 else 'No'} - Ángulo: ( {self.new_direction} )")
        return

    # ===== ELIMINAR MISIÓN =====
    def eliminar_mision(self):

        nombre_mision = self.el_mission_name_entry.get().strip()

        mission_path = os.path.join("missions", f"{nombre_mision}.json")
        wp_actions_path = os.path.join("waypoints", f"{nombre_mision}.json")
        photos_path = os.path.join("photos", nombre_mision)
        if not os.path.exists(mission_path):
            messagebox.showerror("Error", f"No existe la misión especificada.")
            return

        if os.path.exists(mission_path):
            os.remove(mission_path)

        if os.path.exists(wp_actions_path):
            os.remove(wp_actions_path)

        if os.path.exists(photos_path):
            shutil.rmtree(photos_path)

        messagebox.showinfo("Misión Eliminada", f"Misión '{nombre_mision}' eliminada correctamente.")

        self.el_mission_name_entry.delete(0, tk.END)  # Borra el texto de la entrada

    # ===== GUARDAR MISIÓN ======
    def save_mission(self):
        mission_name = self.mission_name_entry.get().strip()

        if not mission_name:
            messagebox.showerror("Introduce nombre de la misión", "Por favor, introduce el nombre de la misión.")
            return
        if not self.waypoints:
            messagebox.showerror("No hay Waypoints", "Por favor, añade waypoints antes de guardar la misión.")
            return
        try:
            self.speed = float(self.speed_entry.get())
        except ValueError:
            messagebox.showerror("Velocidad inválida", "Por favor, introduce un número válido para la velocidad.")
            return

        mission_folder = "missions"
        if not os.path.exists(mission_folder):
            os.makedirs(mission_folder)

        mission_path = os.path.join(mission_folder, f"{mission_name}.json")

        if os.path.exists(mission_path):
            photos_folder = f"photos/{mission_name}"
            if os.path.exists(photos_folder):
                shutil.rmtree(photos_folder)
                print(f"Carpeta '{photos_folder}' eliminada.")

        mission = {
            "speed": self.speed,
            "takeOffAlt": self.altura_vuelo,
            "waypoints": [{"lat": wp["lat"], "lon": wp["lon"], "alt": self.altura_vuelo} for wp in self.waypoints]
        }

        with open(mission_path, "w") as mission_file:
            json.dump(mission, mission_file, indent=4)

        wp_actions_file = mission_name
        wp_actions_folder = "waypoints"
        wp_actions_path = os.path.join(wp_actions_folder, f"{wp_actions_file}.json")
        with open(wp_actions_path, "w") as file:
            json.dump(self.wp_actions, file, indent=4)

        self.MapMission.master.destroy()
        messagebox.showinfo("Misión Guardada",f'¡La misión se ha guardado como "{mission_name}.json" en la carpeta "missions"!')



