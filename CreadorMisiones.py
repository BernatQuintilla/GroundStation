import tkinter as tk
import os
import tkintermapview
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import json
import shutil

class MapMission:

    def __init__(self, altura_vuelo, velocidad_vuelo, boolean_geofence):
        # guardamos parametros de plan de vuelo
        self.speed = velocidad_vuelo
        self.altura_vuelo = altura_vuelo
        # inicializamos wp de geofence para dibujar poligono en interfaz
        self.geofence_waypoints = []
        self.geofence_waypoints1 = []
        # esta variable indica si nueva geofence se ha creado
        self.new_geofence = boolean_geofence

        # waypoints mision
        self.waypoints = []
        # lineas que unen wp
        self.lines = []
        # diccionario de acciones en los wp
        self.wp_actions = {'photo': [],'angle': []}
        # direccion predeterminada
        self.new_direction = "-"

    def buildFrame(self, fatherFrame):
        # declaro la clase y inicializo ventana
        self.MapMission = tk.Frame(fatherFrame)

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

        # creo frame donde introducire input y boton para guardar mision
        self.frame = tk.LabelFrame(self.MapMission, text="Opciones")
        self.frame.grid(row=0, column=0, columnspan = 5, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.frame.rowconfigure(0, weight=2)
        self.frame.rowconfigure(1, weight=2)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.columnconfigure(2, weight=2)

        self.mission_name_label = tk.Label(self.frame, text="Nombre de la misión:")
        self.mission_name_label.grid(row=0, column=0, padx=5, pady=3, sticky="w")
        # input para nombre de la mision
        self.mission_name_entry = tk.Entry(self.frame)
        self.mission_name_entry.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        # boton para guardar misión
        self.save_mission_btn = tk.Button(self.frame, text="Guardar Misión", bg="dark orange", fg="black",
                                          command=self.save_mission)
        self.save_mission_btn.grid(row=0, column=2, padx=5, pady=3, sticky="nesw")

        # frame para mostrar los wp y gestionar sus acciones
        self.wp_frame = tk.LabelFrame(self.MapMission, text="Waypoints")
        self.wp_frame.grid(row=1, column=10, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)
        # listbox permite mostrar los wp que se introducen en una lista infinita
        self.wp_listbox = tk.Listbox(self.wp_frame, height=10, width=30)
        self.wp_listbox.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.wp_scrollbar = tk.Scrollbar(self.wp_frame, orient="vertical", command=self.wp_listbox.yview)
        self.wp_scrollbar.grid(row=0, column=1, sticky="ns")
        self.wp_listbox.config(yscrollcommand=self.wp_scrollbar.set)
        # boton para hacer foto en wp seleccionado en la listbox
        self.edit_wp_button = tk.Button(self.wp_frame, text="Hacer Foto en WP", command=self.photo_waypoint)
        self.edit_wp_button.grid(row=1, column=0, padx=5, pady=2, sticky="ew")
        # boton para cambiar angulo de wp seleccionado en la listbox
        self.delete_wp_button = tk.Button(self.wp_frame, text="Cambiar Ángulo en WP", command=self.change_angle_waypoint)
        self.delete_wp_button.grid(row=2, column=0, padx=5, pady=2, sticky="ew")

        # frame para eliminar mision existente
        self.el_mision = tk.LabelFrame(self.MapMission, text="Eliminar Misión Existente")
        self.el_mision.grid(row=0, column=10, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)
        # input para nombre de mision a eliminar
        self.el_mission_name_entry = tk.Entry(self.el_mision)
        self.el_mission_name_entry.grid(row=0, column=0, padx=5, pady=3, sticky="ew")

        # boton para eliminar misión
        self.el_mission_btn = tk.Button(self.el_mision, text="Eliminar", bg="red", fg="white",
                                          command=self.eliminar_mision)
        self.el_mission_btn.grid(row=0, column=1, padx=5, pady=3, sticky="nesw")

        return self.MapMission

    # ======== GEOFENCE ========
    def MostrarGeoFence(self):
        # funcion que muestra en la interfaz geofence predeterminada y creada si existe

        # obtengo geofence predeterminada
        with open("waypoints geofence/GeoFenceScenario.json", "r") as file:
            scenario_data = json.load(file)

        self.geofence_waypoints = scenario_data[0]["waypoints"]
        # creo el poligono de geofence para mostrar en ventana
        polygon = self.map_widget.set_polygon(
            [(point['lat'], point['lon']) for point in self.geofence_waypoints],
            fill_color=None,
            outline_color="red",
            border_width=4,
            name="GeoFence_polygon"
        )
        # si hay una geofence creada abro el json de la nueva geofence
        if self.new_geofence:
            with open("waypoints geofence/NewGeoFenceScenario.json", "r") as file:
                scenario_data1 = json.load(file)
            self.geofence_waypoints1 = scenario_data1[0]["waypoints"]
            # creo poligono de geofence para mostrar en ventana
            polygon1 = self.map_widget.set_polygon(
                [(point['lat'], point['lon']) for point in self.geofence_waypoints1],
                fill_color=None,
                outline_color="red",
                border_width=4,
                name="NewGeoFence_polygon"
            )

    def dentro_de_geofence(self, lat, lon):
        # esta funcion se usa para comprobar si wp seleccionado se encuentra dentro de geofence

        geofence_polygon = [(point['lat'], point['lon']) for point in self.geofence_waypoints]

        inside = False
        x, y = lat, lon
        n = len(geofence_polygon)
        p1x, p1y = geofence_polygon[0]
        # algoritmo que comprueba que punto este dentro de geofence predeterminada
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
        # si hay una geofence creada se repite el procedimiento
        if self.new_geofence:
            geofence_polygon = [(point['lat'], point['lon']) for point in self.geofence_waypoints1]

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

    # ======== FUNCION MARKER WP ========
    def add_marker_event(self, coords):
        # funcion que permite desde la interfaz añadir wp

        # si wp no esta dentro de geofence (usando dentro_de_geofence)
        if not self.dentro_de_geofence(coords[0], coords[1]):
            messagebox.showwarning("Coordenadas fuera del Geofence", "Selecciona coordenadas dentro del Geofence.")
            return
        # obtengo png de wp
        location_point_img = Image.open("assets/WaypointMarker.png")
        resized_location_point = location_point_img.resize((25, 25), Image.LANCZOS)
        location_point_icon = ImageTk.PhotoImage(resized_location_point)
        # creo el marker para mostrar wp con su numero pertinente
        marker = self.map_widget.set_marker(coords[0], coords[1],
                                            text=f"WP {len(self.waypoints) + 1}",
                                            icon=location_point_icon,
                                            icon_anchor="center")

        wp_data = {'lat': coords[0], 'lon': coords[1], 'marker': marker}
        self.waypoints.append(wp_data)

        self.wp_listbox.insert(tk.END, f"WP {len(self.waypoints)} ")
        # inicializo las acciones del wp a no accion (no foto, no rotacion)
        self.wp_actions['photo'].append(0)
        self.wp_actions['angle'].append(-1)
        # si hay mas de un wp creo linea entre wp x, wp x+1
        if len(self.waypoints) > 1:
            prev_wp = self.waypoints[-2]
            current_wp = self.waypoints[-1]
            line = self.map_widget.set_path(
                [(prev_wp['lat'], prev_wp['lon']), (current_wp['lat'], current_wp['lon'])],
                color="blue",
                width=2
            )
            self.lines.append(line)

    # ======== FUNCIONES ACCIONES EN WP ========
    def photo_waypoint(self):
        # funcion que cambia la accion de foto en wp seleccionado y cambia interfaz de la listbox

        # obtengo el wp seleccionado en la listbox
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
        # si wp tiene foto activada la desactivo y viceversa en variable wp_actions
        if self.wp_actions['photo'][wp_index] == 1:
            self.wp_actions['photo'][wp_index] = 0
        else:
            self.wp_actions['photo'][wp_index] = 1
        # este diccionario contiene angulos y su direccion, necesario para mostrar en interfaz angulo cuando se cambia de accion en la toma de foto
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
        # si wp tiene angulo al que rotar se muestra y sino se usa "-"
        if wp_index < len(self.wp_actions['angle']):
            angle = self.wp_actions['angle'][wp_index]
            direction = direction_angles_reverse[angle]
        else:
            direction = "-"
        # actualizo listbox con acciones de wp seleccionado
        self.wp_listbox.delete(wp_index)
        self.wp_listbox.insert(wp_index,
                               f"WP {wp_index + 1} - Foto: {'Sí' if self.wp_actions['photo'][wp_index] == 1 else 'No'} "
                               f"- Ángulo: ( {direction} )")

    def change_angle_waypoint(self):
        # funcion que cambia accion de angulo en wp seleccionado y cambia interfaz de la listbox

        # obtengo wp seleccionado en la listbox
        selected_wp = self.wp_listbox.curselection()
        if not selected_wp:
            messagebox.showwarning("No WP Seleccionado",
                                   "Por favor, selecciona un waypoint de la lista para cambiar ángulo")
            return

        wp_index = selected_wp[0]

        if 'angle' not in self.wp_actions:
            self.wp_actions['angle'] = []
        # me aseguro de que wp_index sea valido
        while wp_index >= len(self.wp_actions['angle']):
            self.wp_actions['angle'].append(-1)
        # diccionario de direcciones y su angulo pertinente
        direction_angles = {
            "N": 360,
            "NE": 45,
            "E": 90,
            "SE": 135,
            "S": 180,
            "SW": 225,
            "W": 270,
            "NW": 315,
            "Eliminar": -1  # opción para borrar el ángulo
        }
        # muestro una pequeña ventana que pregunta por la direccion que rotara el wp (N, NE, E, SE, S, SW, W, NW)
        self.new_direction = simpledialog.askstring("Selecciona Dirección",
                                               "Ingresa una dirección (N, NE, E, SE, S, SW, W, NW):\n Para eliminar ingresa: Eliminar")

        # si la direccion no aparece en el diccionario y no es "-"
        if self.new_direction not in direction_angles and self.new_direction != "-":
            messagebox.showwarning("Dirección inválida",
                                   "Por favor, ingresa una de las opciones: N, NE, E, SE, S, SW, W, NW")
            return
        # añado a accion de wp en angulo introducido
        self.wp_actions['angle'][wp_index] = direction_angles[self.new_direction]

        if self.new_direction == "Eliminar":
            self.new_direction = "-"
        # actualizo listbox con acciones de foto y angulo del wp seleccionado
        self.wp_listbox.delete(wp_index)
        self.wp_listbox.insert(wp_index,
                               f"WP {wp_index + 1} - Foto: {'Sí' if self.wp_actions['photo'][wp_index] == 1 else 'No'} - Ángulo: ( {self.new_direction} )")
        return

    # ======== FUNCION ELIMINAR MISION ========
    def eliminar_mision(self):
        # funcion para eliminar mision existente seleccionada

        # obtengo nombre de la mision a eliminar
        nombre_mision = self.el_mission_name_entry.get().strip()

        # obtengo paths relacionados con la mision (mision, acciones en wp, fotos)
        mission_path = os.path.join("missions", f"{nombre_mision}.json")
        wp_actions_path = os.path.join("waypoints", f"{nombre_mision}.json")
        photos_path = os.path.join("photos", nombre_mision)

        if not os.path.exists(mission_path):
            messagebox.showerror("Error", f"No existe la misión especificada.")
            return
        # elimino el json de la mision
        if os.path.exists(mission_path):
            os.remove(mission_path)
        # elimino el json de las acciones de la mision
        if os.path.exists(wp_actions_path):
            os.remove(wp_actions_path)
        # elimino la carpeta de las fotos de la mision
        if os.path.exists(photos_path):
            shutil.rmtree(photos_path)

        messagebox.showinfo("Misión Eliminada", f"Misión '{nombre_mision}' eliminada correctamente.")
        # borro texto de la entrada al eliminar mision
        self.el_mission_name_entry.delete(0, tk.END)

    # ===== GUARDAR MISIÓN ======
    def save_mission(self):
        # funcion para guardar mision y acciones de mision en formato json

        mission_name = self.mission_name_entry.get().strip()

        if not mission_name:
            messagebox.showerror("Introduce nombre de la misión", "Por favor, introduce el nombre de la misión.")
            return
        if not self.waypoints:
            messagebox.showerror("No hay Waypoints", "Por favor, añade waypoints antes de guardar la misión.")
            return

        mission_folder = "missions"
        if not os.path.exists(mission_folder):
            os.makedirs(mission_folder)
        # creo path donde guardar json de mision (missions/nombre_de_mision.json
        mission_path = os.path.join(mission_folder, f"{mission_name}.json")
        # hago carpeta donde guardar las imagenes de mision
        if os.path.exists(mission_path):
            photos_folder = f"photos/{mission_name}"
            if os.path.exists(photos_folder):
                shutil.rmtree(photos_folder)
                print(f"Carpeta '{photos_folder}' eliminada.")
        # formo variable diccionario donde guardo mision con la velocidad y altura introducidas en panel principal y wp seleccionados
        mission = {
            "speed": self.speed,
            "takeOffAlt": self.altura_vuelo,
            "waypoints": [{"lat": wp["lat"], "lon": wp["lon"], "alt": self.altura_vuelo} for wp in self.waypoints]
        }
        # creo json de la mision en mission_path
        with open(mission_path, "w") as mission_file:
            json.dump(mission, mission_file, indent=4)

        wp_actions_file = mission_name
        wp_actions_folder = "waypoints"
        # creo path del json para las acciones de los wp
        wp_actions_path = os.path.join(wp_actions_folder, f"{wp_actions_file}.json")
        # guardo en formato json las acciones de los wp de la mision
        with open(wp_actions_path, "w") as file:
            json.dump(self.wp_actions, file, indent=4)
        # cuando los json han sido creados se destruye la ventana (json se seleccionan en select_mission en MapInterface)
        self.MapMission.master.destroy()
        messagebox.showinfo("Misión Guardada",f'¡La misión se ha guardado como "{mission_name}.json" en la carpeta "missions"!')



