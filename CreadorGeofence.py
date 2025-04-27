import json
import tkinter as tk
import os
import tkintermapview
from tkinter import Canvas
from tkinter import messagebox, simpledialog
import json
import os
import tkinter as tk
from tkinter import messagebox
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk


class GeoFenceCreator:
    def __init__(self, dron):
        self.dron = dron
        self.altura = 0
        self.geofence_waypoints = []
        self.vertex_count = None
        self.waypoints = []
        self.lines = []  # To store path lines between vertices
        self.polygon = None  # To store the geofence polygon

    def buildFrame(self, fatherFrame):
        self.GeofenceCreation = tk.Frame(fatherFrame)

        self.map_widget = tkintermapview.TkinterMapView(self.GeofenceCreation, width=900, height=480, corner_radius=0)
        self.map_widget.grid(row=1, column=0, columnspan=9, padx=5, pady=5)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        self.map_widget.set_position(41.276430, 1.988686)  # Dronelab coordinates
        self.map_widget.set_zoom(20)

        self.GeofenceCreation.rowconfigure(0, weight=1)
        self.GeofenceCreation.rowconfigure(1, weight=10)
        self.GeofenceCreation.columnconfigure(0, weight=1)
        self.GeofenceCreation.columnconfigure(1, weight=1)

        self.map_widget.add_right_click_menu_command(
            label="Añadir vértice geofence",
            command=self.add_marker_event,
            pass_coords=True
        )

        self.save_geofence_btn = tk.Button(
            self.GeofenceCreation,
            text="Aplicar Geofence",
            bg="dark orange",
            fg="black",
            command=self.save_geofence
        )
        self.save_geofence_btn.grid(row=0, column=0,columnspan=9, padx=5, pady=3, sticky="nesw")

        return self.GeofenceCreation

    def add_marker_event(self, coords):
        location_point_img = Image.open("assets/WaypointMarker.png")
        resized_location_point = location_point_img.resize((25, 25), Image.LANCZOS)
        location_point_icon = ImageTk.PhotoImage(resized_location_point)

        marker = self.map_widget.set_marker(
            coords[0], coords[1],
            text=f"V {len(self.waypoints) + 1}",
            icon=location_point_icon,
            icon_anchor="center"
        )

        wp_data = {'lat': coords[0], 'lon': coords[1], 'marker': marker}
        self.waypoints.append(wp_data)

        if len(self.waypoints) > 1:
            prev_wp = self.waypoints[-2]
            current_wp = self.waypoints[-1]
            line = self.map_widget.set_path(
                [(prev_wp['lat'], prev_wp['lon']), (current_wp['lat'], current_wp['lon'])],
                color="blue",
                width=2
            )
            self.lines.append(line)

        if len(self.waypoints) >= 3:
            self.update_geofence_polygon()

    def update_geofence_polygon(self):
        if self.polygon:
            self.map_widget.delete(self.polygon)

        polygon_coords = [(wp['lat'], wp['lon']) for wp in self.waypoints]
        self.polygon = self.map_widget.set_polygon(
            polygon_coords,
            fill_color=None,
            outline_color="red",
            border_width=4,
            name="geofence"
        )

    def save_geofence(self):
        if len(self.waypoints) < 3:
            messagebox.showerror("Error", "Se necesitan al menos 3 vértices para crear un geofence")
            return None

        geofence_data = [{
            "name": "Custom GeoFence",
            "type": "polygon",  # Add this required field
            "waypoints": [
                {"lat": wp['lat'], "lon": wp['lon']}
                for wp in self.waypoints
            ]
        }]

        geofence_file = "waypoints geofence/NewGeoFenceScenario.json"

        try:
            with open(geofence_file, "w") as f:
                json.dump(geofence_data, f, indent=4)

            messagebox.showinfo("Éxito", "Geofence guardado y actualizado correctamente")
            return geofence_data

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el geofence: {str(e)}")
            return None