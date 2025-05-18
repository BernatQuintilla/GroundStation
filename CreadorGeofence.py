import tkinter as tk
import tkintermapview
import json
from tkinter import messagebox
from PIL import Image, ImageTk


class GeoFenceCreator:

    def __init__(self):
        # inicializo waypoints
        self.waypoints = []
        # inicializo lineas conectoras de waypoints
        self.lines = []
        # inicializo poligono a dibujar de geofence
        self.polygon = None

    def buildFrame(self, fatherFrame):
        # llamo a la clase y creo frame de ventana
        self.GeofenceCreation = tk.Frame(fatherFrame)

        self.map_widget = tkintermapview.TkinterMapView(self.GeofenceCreation, width=900, height=480, corner_radius=0)
        self.map_widget.grid(row=1, column=0, columnspan=9, padx=5, pady=5)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        self.map_widget.set_position(41.276430, 1.988686)  # coordenadas Dronlab
        self.map_widget.set_zoom(20)

        self.GeofenceCreation.rowconfigure(0, weight=1)
        self.GeofenceCreation.rowconfigure(1, weight=10)
        self.GeofenceCreation.columnconfigure(0, weight=1)
        self.GeofenceCreation.columnconfigure(1, weight=1)
        # introduce vertice cuando al hacer click izquierdo se selecciona la opcion
        self.map_widget.add_right_click_menu_command(
            label="Añadir vértice geofence",
            command=self.add_marker_event,
            pass_coords=True
        )
        # boton para guardar geofence
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
        # funcion para añadir wp en el panel

        # cargo el png del wp
        location_point_img = Image.open("assets/WaypointMarker.png")
        resized_location_point = location_point_img.resize((25, 25), Image.LANCZOS)
        location_point_icon = ImageTk.PhotoImage(resized_location_point)
        # introduzco numero de wp al mostrar en panel
        marker = self.map_widget.set_marker(
            coords[0], coords[1],
            text=f"V {len(self.waypoints) + 1}",
            icon=location_point_icon,
            icon_anchor="center"
        )
        # en el parametro waypoints guardo latitud y longitud del wp
        wp_data = {'lat': coords[0], 'lon': coords[1], 'marker': marker}
        self.waypoints.append(wp_data)

        if len(self.waypoints) > 1:
            prev_wp = self.waypoints[-2]
            current_wp = self.waypoints[-1]
            # creo linea entre wp x, y wp x+1
            line = self.map_widget.set_path(
                [(prev_wp['lat'], prev_wp['lon']), (current_wp['lat'], current_wp['lon'])],
                color="blue",
                width=2
            )
            self.lines.append(line)

        if len(self.waypoints) >= 3:
            # si se han seleccionado 3 wp o mas se actualiza dibujo de geofence
            self.update_geofence_polygon()

    def update_geofence_polygon(self):
        # funcion para crear dibujo de geofence

        if self.polygon:
            self.polygon.delete()

        polygon_coords = [(wp['lat'], wp['lon']) for wp in self.waypoints]
        self.polygon = self.map_widget.set_polygon(
            polygon_coords,
            fill_color=None,
            outline_color="red",
            border_width=4,
            name="geofence"
        )

    def save_geofence(self):
        # funcion para guardar y mostrar geofence

        if len(self.waypoints) < 3:
            messagebox.showerror("Error", "Se necesitan al menos 3 vértices para crear un geofence")
            return None
        # guardar informacion de geofence nueva en formato json
        geofence_data = [{
            "name": "Custom GeoFence",
            "type": "polygon",  # Add this required field
            "waypoints": [
                {"lat": wp['lat'], "lon": wp['lon']}
                for wp in self.waypoints
            ]
        }]
        # este path se sobrescribe cada vez que creamos una nueva geofence
        # a pesar de que al crear nueva geofence el json se sobrescribe, varias geofence nuevas pueden usarse en una misma ejecucion del codigo
        geofence_file = "waypoints geofence/NewGeoFenceScenario.json"

        try:
            # guardamos json con datos para formar geofence y dibujar, se usa en funcion creadorGeoFence de MapInterface (panel principal)
            with open(geofence_file, "w") as f:
                json.dump(geofence_data, f, indent=4)

            messagebox.showinfo("Éxito", "Geofence guardado y actualizado correctamente")
            return geofence_data

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el geofence: {str(e)}")
            return None