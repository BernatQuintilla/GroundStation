import tkinter as tk
import os
from tkinter import messagebox
import json
import shutil
from geopy.distance import geodesic


class StitchingMission:
    def __init__(self, altura_vuelo, velocidad_vuelo):
        # recibimos altura y velocidad para el plan de vuelo
        self.altura_vuelo = altura_vuelo
        self.velocidad_vuelo = velocidad_vuelo
        # inicializamos wp de mision
        self.waypoints = []
        # inicializamos diccionario para recibir acciones en cada wp
        self.wp_actions = {'photo': [],'angle': [], 'fix': []}
        # grado de solapamiento entre imagenes
        self.solapamiento = None
        self.mission_name = None
        # esta variable recibe I, L, U, O, dependiendo de cuantos lados del DronLab cubre
        self.tipo_mission = None

    def buildFrame(self, fatherFrame):
        # llamamos a la clase y inicializamos ventana
        self.StitchingMission = tk.Frame(fatherFrame)

        self.StitchingMission.rowconfigure(0, weight=1)
        self.StitchingMission.columnconfigure(0, weight=1)

        self.frame = tk.LabelFrame(self.StitchingMission, text="Misión Stitching")
        self.frame.grid(row=0, column=0, columnspan = 2, padx=6, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.frame.rowconfigure(0, weight=2)
        self.frame.rowconfigure(1, weight=2)
        self.frame.rowconfigure(2, weight=2)
        self.frame.rowconfigure(3, weight=2)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)

        self.solapamiento_label = tk.Label(self.frame, text="Grado Solapamiento (0-1):")
        self.solapamiento_label.grid(row=0, column=0, padx=5, pady=3, sticky="w")
        # input donde introducir solapamiento
        self.solapamiento_entry = tk.Entry(self.frame)
        self.solapamiento_entry.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        self.tipo_mission_label = tk.Label(self.frame, text="Tipo de misión (I, L, U, O):")
        self.tipo_mission_label.grid(row=1, column=0, padx=5, pady=3, sticky="w")
        # input donde introducir tipo de mision
        self.tipo_mission_entry = tk.Entry(self.frame)
        self.tipo_mission_entry.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        self.mission_name_label = tk.Label(self.frame, text="Nombre de la misión:")
        self.mission_name_label.grid(row=2, column=0, padx=5, pady=3, sticky="w")
        # input donde introducir nombre de la mision
        self.mission_name_entry = tk.Entry(self.frame)
        self.mission_name_entry.grid(row=2, column=1, padx=5, pady=3, sticky="ew")

        # Boton para guardar mision
        self.save_mission_btn = tk.Button(self.frame, text="Guardar Misión", bg="dark orange", fg="black",
                                          command=self.save_mission)
        self.save_mission_btn.grid(row=3, column=0,columnspan = 2, padx=5, pady=3, sticky="nesw")


        return self.StitchingMission

    def generate_waypoints(self, solapamiento):
        # funcion que dependiendo del solapamiento y tipo de mision genera una mision para el stitching

        # donde almaceno waypoints generados
        waypoints = []

        # creo variables que contienen puntos (lat, lon) de inicio y final de cada lado (esquinas DronLab)
        start_lat, start_lon = 41.2762224, 1.9883487
        end_lat, end_lon = 41.2763895, 1.9890720
        start_lat2, start_lon2 = end_lat, end_lon
        end_lat2, end_lon2 = 41.2765812, 1.9889918
        start_lat3, start_lon3 = end_lat2, end_lon2
        end_lat3, end_lon3 = 41.2764068, 1.9882689
        start_lat4, start_lon4 = end_lat3, end_lon3
        end_lat4, end_lon4 = start_lat, start_lon
        # image_width_meters contiene el numero de metros que la imagen tomada del dron ocupa
        image_width_meters = 20
        start_point = (start_lat, start_lon)
        end_point = (end_lat, end_lon)
        start_point2 = (start_lat2, start_lon2)
        end_point2 = (end_lat2, end_lon2)
        start_point3 = (start_lat3, start_lon3)
        end_point3 = (end_lat3, end_lon3)
        start_point4 = (start_lat4, start_lon4)
        end_point4 = (end_lat4, end_lon4)
        # calculo distancia entre puntos finales e iniciales
        total_distance = geodesic(start_point, end_point).meters
        total_distance2 = geodesic(start_point2, end_point2).meters
        total_distance3 = geodesic(start_point3, end_point3).meters
        total_distance4 = geodesic(start_point4, end_point4).meters
        # step_distance tiene la distancia que ha de tomarse cada imagen teniendo en cuenta cuantos metros visualiza la camara y el grado de solapamiento
        step_distance = image_width_meters * (1 - solapamiento)
        # calculo el numero de wp que se generan para cada lado
        num_waypoints = int(total_distance / step_distance) + 1
        num_waypoints2 = int(total_distance2 / step_distance) + 1
        num_waypoints3 = int(total_distance3 / step_distance) + 1
        num_waypoints4 = int(total_distance4 / step_distance) + 1

        # Primer lado
        for i in range(num_waypoints + 1):
            # numero de wp/numero de wp necesarios en este lado
            fraction = i / num_waypoints
            # calculo punto de wp
            lat = start_lat + fraction * (end_lat - start_lat)
            lon = start_lon + fraction * (end_lon - start_lon)
            # si el wp es el ultimo del lado y el tipo de mision es diferente a I es decir que va a hacer stitching del siguiente lado
            if lat == end_lat and lon == end_lon and self.tipo_mission != "I":
                # para ver funcionamiento de wp_actions que significa cada valor al cual se hace append mirar funcion aqui en MapInterface
                waypoints.append({"lat": lat, "lon": lon})
                # realizas una imagen en el wp
                self.wp_actions['photo'].append(1)
                # no rota dron en wp
                self.wp_actions['angle'].append(-1)
                # se desfija el heading
                self.wp_actions['fix'].append(2)
                waypoints.append({"lat": lat, "lon": lon})
                # se crea otro wp en el mismo sitio que gira para colocarse 45 grados respecto al siguiente lado
                # en punto final de lado si queda un lado se hacen 3 fotografias ya que al pasar al siguiente lado se hace otra imagen en esta posicion
                self.wp_actions['photo'].append(1)
                self.wp_actions['angle'].append(115.55)
                self.wp_actions['fix'].append(0)
            else:
                # si el wp es el inicial del lado
                if lat == start_lat and lon == start_lon:
                    waypoints.append({"lat": lat, "lon": lon})
                    # se hace foto en wp
                    self.wp_actions['photo'].append(1)
                    # gira angulo para estar perpendicular con pared Dronlab
                    self.wp_actions['angle'].append(162.9)
                    # fija el heading para siguientes wp
                    self.wp_actions['fix'].append(1)
                else:
                    # si es wp del medio del lado
                    waypoints.append({"lat": lat, "lon": lon})
                    # se toma una imagen, no se cambia de angulo y no hay cambios respecto al heading
                    self.wp_actions['photo'].append(1)
                    self.wp_actions['angle'].append(-1)
                    self.wp_actions['fix'].append(0)

        # Segundo lado
        # para cada lado el funcionamiento es el mismo, solo cambia la variable num_waypoints, el tipo de mision en las condiciones y el angulo
        if self.tipo_mission != "I":
           for i in range(num_waypoints2 + 1):
               fraction = i / num_waypoints2
               lat = start_lat2 + fraction * (end_lat2 - start_lat2)
               lon = start_lon2 + fraction * (end_lon2 - start_lon2)
               if lat == end_lat2 and lon == end_lon2 and self.tipo_mission != "L":
                   waypoints.append({"lat": lat, "lon": lon})
                   self.wp_actions['photo'].append(1)
                   self.wp_actions['angle'].append(-1)
                   self.wp_actions['fix'].append(2)
                   waypoints.append({"lat": lat, "lon": lon})
                   self.wp_actions['photo'].append(1)
                   self.wp_actions['angle'].append(25.2)
                   self.wp_actions['fix'].append(0)
               else:
                   if lat == start_lat2 and lon == start_lon2:
                       waypoints.append({"lat": lat, "lon": lon})
                       self.wp_actions['photo'].append(1)
                       self.wp_actions['angle'].append(68.2)
                       self.wp_actions['fix'].append(1)
                   else:
                       waypoints.append({"lat": lat, "lon": lon})
                       self.wp_actions['photo'].append(1)
                       self.wp_actions['angle'].append(-1)
                       self.wp_actions['fix'].append(0)

        # Tercer lado
        if self.tipo_mission == "U" or self.tipo_mission == "O":
            for i in range(num_waypoints3 + 1):
                fraction = i / num_waypoints3
                lat = start_lat3 + fraction * (end_lat3 - start_lat3)
                lon = start_lon3 + fraction * (end_lon3 - start_lon3)
                if lat == end_lat3 and lon == end_lon3 and self.tipo_mission == "O":
                    waypoints.append({"lat": lat, "lon": lon})
                    self.wp_actions['photo'].append(1)
                    self.wp_actions['angle'].append(-1)
                    self.wp_actions['fix'].append(2)
                    waypoints.append({"lat": lat, "lon": lon})
                    self.wp_actions['photo'].append(1)
                    self.wp_actions['angle'].append(294.85)
                    self.wp_actions['fix'].append(0)
                else:
                    if lat == start_lat3 and lon == start_lon3:
                        waypoints.append({"lat": lat, "lon": lon})
                        self.wp_actions['photo'].append(1)
                        self.wp_actions['angle'].append(342.2)
                        self.wp_actions['fix'].append(1)
                    else:
                        waypoints.append({"lat": lat, "lon": lon})
                        self.wp_actions['photo'].append(1)
                        self.wp_actions['angle'].append(-1)
                        self.wp_actions['fix'].append(0)

        # Cuarto lado
        if self.tipo_mission == "O":
            for i in range(num_waypoints4 + 1):
                fraction = i / num_waypoints4
                lat = start_lat4 + fraction * (end_lat4 - start_lat4)
                lon = start_lon4 + fraction * (end_lon4 - start_lon4)
                if lat == start_lat4 and lon == start_lon4:
                    waypoints.append({"lat": lat, "lon": lon})
                    self.wp_actions['photo'].append(1)
                    self.wp_actions['angle'].append(247.5)
                    self.wp_actions['fix'].append(1)
                else:
                    if lat == end_lat4 and lon == end_lon4:
                        waypoints.append({"lat": lat, "lon": lon})
                        self.wp_actions['photo'].append(1)
                        self.wp_actions['angle'].append(-1)
                        self.wp_actions['fix'].append(2)
                    else:
                        waypoints.append({"lat": lat, "lon": lon})
                        self.wp_actions['photo'].append(1)
                        self.wp_actions['angle'].append(-1)
                        self.wp_actions['fix'].append(0)
        return waypoints

    def save_mission(self):
        # funcion que guarda la mision creada en generate_waypoints con los parametros seleccionados

        self.solapamiento = self.solapamiento_entry.get().strip()
        if self.mission_name_entry.get().strip() is None or self.mission_name_entry.get().strip() == "":
            messagebox.showerror("Error", "Introduce un nombre de misión.")
            return
        else:
            self.mission_name = self.mission_name_entry.get().strip()
        if self.tipo_mission_entry.get().strip() != "I" and self.tipo_mission_entry.get().strip() != "L" and self.tipo_mission_entry.get().strip() != "U" and self.tipo_mission_entry.get().strip() != "O":
            messagebox.showerror("Error", "Introduce un tipo de misión válido (I, L, U, O).")
            return
        else:
            self.tipo_mission = self.tipo_mission_entry.get().strip()
        try:
            solapamiento = float(self.solapamiento)
            if solapamiento < 0 or solapamiento > 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Introduce un valor válido para el solapamiento (0-1).")
            return

        mission_name = self.mission_name
        # llamo a la funcion generate_waypoints para obtener wp
        self.waypoints = self.generate_waypoints(solapamiento)

        if not mission_name:
            messagebox.showerror("Introduce nombre de la misión", "Por favor, introduce el nombre de la misión.")
            return
        if not self.waypoints:
            messagebox.showerror("No hay Waypoints", "Por favor, añade waypoints antes de guardar la misión.")
            return

        mission_folder = "missions"
        if not os.path.exists(mission_folder):
            os.makedirs(mission_folder)
        # creo el path de la mision con el nombre de mision introducido
        mission_path = os.path.join(mission_folder, f"{mission_name}.json")
        # si path de fotos existe previamente lo elimino y lo vuelvo a crear
        if os.path.exists(mission_path):
            photos_folder = f"photos/{mission_name}"
            if os.path.exists(photos_folder):
                shutil.rmtree(photos_folder)
                print(f"Carpeta '{photos_folder}' eliminada.")
        # creo mision con velocidad y altura introducidas en panel principal y wp guardados
        mission = {
            "speed": self.velocidad_vuelo,
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
        # guardo la mision en formato json en la carpeta de misiones donde se podra seleccionar desde el panel principal en Seleccionar mision
        self.StitchingMission.master.destroy()
        messagebox.showinfo("Misión Guardada",f'¡La misión se ha guardado como "{mission_name}.json" en la carpeta "missions"!')