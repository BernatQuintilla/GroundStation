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
from geopy.distance import geodesic


class StitchingMission:
    def __init__(self, dron, altura_vuelo):
        self.dron = dron
        self.altura = 0
        self.altura_vuelo = altura_vuelo

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
        self.angles = []
        self.wp_actions = {'photo': [],'angle': []}
        self.solapamiento = None
        self.mission_name = None
        self.tipo_mission = None

    def buildFrame(self, fatherFrame):

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

        self.solapamiento_entry = tk.Entry(self.frame)
        self.solapamiento_entry.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        self.tipo_mission_label = tk.Label(self.frame, text="Tipo de misión (I, L, U, O):")
        self.tipo_mission_label.grid(row=1, column=0, padx=5, pady=3, sticky="w")

        self.tipo_mission_entry = tk.Entry(self.frame)
        self.tipo_mission_entry.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        self.mission_name_label = tk.Label(self.frame, text="Nombre de la misión:")
        self.mission_name_label.grid(row=2, column=0, padx=5, pady=3, sticky="w")

        self.mission_name_entry = tk.Entry(self.frame)
        self.mission_name_entry.grid(row=2, column=1, padx=5, pady=3, sticky="ew")

        # Botón para guardar misión
        self.save_mission_btn = tk.Button(self.frame, text="Guardar Misión", bg="dark orange", fg="black",
                                          command=self.save_mission)
        self.save_mission_btn.grid(row=3, column=0,columnspan = 2, padx=5, pady=3, sticky="nesw")


        return self.StitchingMission

    def generate_waypoints(self, solapamiento):
        waypoints = []

        start_lat, start_lon = 41.2762224, 1.9883487
        end_lat, end_lon = 41.2763895, 1.9890720
        start_lat2, start_lon2 = end_lat, end_lon
        end_lat2, end_lon2 = 41.2765812, 1.9889918
        start_lat3, start_lon3 = end_lat2, end_lon2
        end_lat3, end_lon3 = 41.2764068, 1.9882689
        start_lat4, start_lon4 = end_lat3, end_lon3
        end_lat4, end_lon4 = start_lat, start_lon

        image_width_meters = 20
        start_point = (start_lat, start_lon)
        end_point = (end_lat, end_lon)
        start_point2 = (start_lat2, start_lon2)
        end_point2 = (end_lat2, end_lon2)
        start_point3 = (start_lat3, start_lon3)
        end_point3 = (end_lat3, end_lon3)
        start_point4 = (start_lat4, start_lon4)
        end_point4 = (end_lat4, end_lon4)

        total_distance = geodesic(start_point, end_point).meters
        total_distance2 = geodesic(start_point2, end_point2).meters
        total_distance3 = geodesic(start_point3, end_point3).meters
        total_distance4 = geodesic(start_point4, end_point4).meters

        step_distance = image_width_meters * (1 - solapamiento)

        num_waypoints = int(total_distance / step_distance) + 1
        num_waypoints2 = int(total_distance2 / step_distance) + 1
        num_waypoints3 = int(total_distance3 / step_distance) + 1
        num_waypoints4 = int(total_distance4 / step_distance) + 1

        # Primer lado
        for i in range(num_waypoints + 1):
            fraction = i / num_waypoints
            lat = start_lat + fraction * (end_lat - start_lat)
            lon = start_lon + fraction * (end_lon - start_lon)
            waypoints.append({"lat": lat, "lon": lon})
            self.wp_actions['photo'].append(1)
            self.wp_actions['angle'].append(162.9)
        # Segundo lado
        if self.tipo_mission != "I":
            for i in range(num_waypoints2 + 1):
                fraction = i / num_waypoints2
                lat = start_lat2 + fraction * (end_lat2 - start_lat2)
                lon = start_lon2 + fraction * (end_lon2 - start_lon2)
                waypoints.append({"lat": lat, "lon": lon})
                self.wp_actions['photo'].append(1)
                self.wp_actions['angle'].append(68.2)
        # Tercer lado
        if self.tipo_mission == "U" or self.tipo_mission == "O":
            for i in range(num_waypoints3 + 1):
                fraction = i / num_waypoints3
                lat = start_lat3 + fraction * (end_lat3 - start_lat3)
                lon = start_lon3 + fraction * (end_lon3 - start_lon3)
                waypoints.append({"lat": lat, "lon": lon})
                self.wp_actions['photo'].append(1)
                self.wp_actions['angle'].append(342.2)
        # Cuarto lado
        if self.tipo_mission == "O":
            for i in range(num_waypoints4 + 1):
                fraction = i / num_waypoints4
                lat = start_lat4 + fraction * (end_lat4 - start_lat4)
                lon = start_lon4 + fraction * (end_lon4 - start_lon4)
                waypoints.append({"lat": lat, "lon": lon})
                self.wp_actions['photo'].append(1)
                self.wp_actions['angle'].append(247.5)

        return waypoints

    def save_mission(self):
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

        mission_path = os.path.join(mission_folder, f"{mission_name}.json")

        if os.path.exists(mission_path):
            photos_folder = f"photos/{mission_name}"
            if os.path.exists(photos_folder):
                shutil.rmtree(photos_folder)
                print(f"Carpeta '{photos_folder}' eliminada.")

        mission = {
            "speed": 7,
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

        self.StitchingMission.master.destroy()
        messagebox.showinfo("Misión Guardada",f'¡La misión se ha guardado como "{mission_name}.json" en la carpeta "missions"!')