import json
import tkinter as tk
import tkintermapview
from tkinter import Canvas
from tkinter import messagebox
from tkinter import ttk
from pymavlink import mavutil
from PIL import Image, ImageTk


class MapFrameClass:

    def __init__(self, dron):
        # guardamos el objeto de la clase dron con el que estamos controlando el dron
        self.dron = dron
        # atributos necesarios para crear el geofence
        self.setting_geofence = False
        self.vertex_count = 0
        self.geofencePoints = []

        # aqui guardaremos los elementos que usemos para dibujar el geofence
        # de manera que podamos recuperarlos para borrarlos
        self.geofenceElements = []

        # atributos para poder establecer WP/ realizar GO TO
        self.destination_WP = None
        self.reach_WP = False


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
        self.MapFrame = tk.Frame(fatherFrame)  # create new frame where the map will be allocated

        # creamos el widget para el mapa
        self.map_widget = tkintermapview.TkinterMapView(self.MapFrame, width=900, height=600, corner_radius=0)
        self.map_widget.grid(row=1, column=0, columnspan=6, padx=5, pady=5)
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


        # ===== FRAME DE GEO FENCE ======
        self.geofence_frame = tk.LabelFrame(self.MapFrame, text="Geo Fence")
        self.geofence_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.geofence_frame.rowconfigure(0, weight=1)
        self.geofence_frame.rowconfigure(1, weight=1)

        self.geofence_frame.columnconfigure(0, weight=1)
        self.geofence_frame.columnconfigure(1, weight=1)

        self.Button1 = tk.Button(self.geofence_frame, text="Crear Geo Fence", bg="dark green", fg="white",
                                 command=self.activate_geofence_mode)
        self.Button1.grid(row=0, column=0, columnspan=2, padx=5, pady=3, sticky="nesw")

        self.Button2 = tk.Button(self.geofence_frame, text="Establecer Geo Fence ", bg="dark green", fg="white",
                                 command=self.GeoFence)
        self.Button2.grid(row=1, column=0, columnspan=2, padx=5, pady=3, sticky="nesw")

        self.count_WP = 0
        self.dron.geofence_markers = []
        self.markers = []


        # ===== FRAME DE NAVEGACIÓN ======
        self.nav_frame = tk.LabelFrame(self.MapFrame, text="Navegación")
        self.nav_frame.grid(row=0, column=3, columnspan=3, padx=10, pady=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.nav_frame.rowconfigure(0, weight=1)
        self.nav_frame.rowconfigure(1, weight=1)

        self.nav_frame.columnconfigure(0, weight=1)
        self.nav_frame.columnconfigure(1, weight=1)

        # tres botones para nuevas funcionalidades

        self.Button3 = tk.Button(self.nav_frame, text="Establecer WP", bg="black", fg="white",  command=self.enable_wp_setting)
        self.Button3.grid(row=0, column=0, padx=5, pady=3, sticky="nesw")

        self.Button4 = tk.Button(self.nav_frame, text="GO TO WP", bg="black", fg="white", command=self.start_goto)
        self.Button4.grid(row=0, column=1, padx=5, pady=3, sticky="nesw")

        self.Button5 = tk.Button(self.nav_frame, text="Mostrar trazado", bg="black", fg="white", command=self.set_trace)
        self.Button5.grid(row=1, column=0, padx=5, pady=3, sticky="nesw")


        # boton para mostrar el icono del dron
        self.Button9 = tk.Button(self.nav_frame, text="Mostrar dron", bg="black", fg="white", command=self.show_dron)
        self.Button9.grid(row=1, column=1, padx=5, pady=3, sticky="nesw")

        return self.MapFrame


    # ====== GEO FENCE ======
    def activate_geofence_mode(self):
        self.setting_geofence = True
        messagebox.showinfo("", "Clic botón derecho para crear los vértices del geo fence.\n Clic 'Establecer Geo Fence' una vez terminado")
        # le indico qué función debe ejecutar cuado se pulse el botón derecho del ratón
        self.map_widget.add_right_click_menu_command(label="Add Marker", command=self.add_marker_event,
                                                     pass_coords=True)

    # aquí venimos cuando se clica el botón derecho del ratóm
    def add_marker_event(self, coords):
        if self.setting_geofence:
            # estamos creando un geofence
            self.vertex_count+=1
            marker_text = f"Vertex {self.vertex_count}"
            # añadimos al mapa un marcador en el punto clicado
            marker = self.map_widget.set_marker(coords[0], coords[1], text=marker_text)
            # guargamos el marcador para poder borrarlo en su momento
            self.geofenceElements.append(marker)
            # añadimos el punto a la lista de puntos de geofence
            self.geofencePoints.append(
                {'lat':coords[0], 'lon':coords[1]})
            # dibujamos una línea entre el último marcador y el penultimo
            if len(self.geofencePoints) > 1:
                last_two_points = [self.geofencePoints[-2], self.geofencePoints[-1]]
                path = self.map_widget.set_path([
                    (point['lat'], point['lon']) for point in last_two_points])
                self.geofenceElements.append(path)
        elif self.reach_WP:
            # estamos marcando el destino del dron
            marker = self.map_widget.set_marker(coords[0], coords[1], text="", icon=self.marker_icon,
                                                icon_anchor="center")
            self.destination_WP = coords
            print(f"Navigate to reach WP: {self.destination_WP}")

    # aqui venimos cuando tenemos ya definido el geofence y lo queremos enviar al dron
    def GeoFence(self):
        # dibujamos el poligono correspondiente al geofence
        polygon = self.map_widget.set_polygon(
                [(point['lat'], point['lon']) for point in self.geofencePoints],
                fill_color=None,
                outline_color="red",
                border_width=12,
                # command=polygon_click,
                name="GeoFence_polygon"
        )

        self.dron.setGEOFence (json.dumps(self.geofencePoints))

        self.setting_geofence = False
        # borramos los marcadores y lineas usados para establecer el geofence
        for element in self.geofenceElements:
            self.map_widget.delete(element)

        # activamos el geofence y le decimos que en caso de llegar al límite se quede allí parado
        parameters = json.dumps([
            {'ID': "FENCE_ENABLE", 'Value': 1},
            {'ID': "FENCE_ACTION", 'Value': 4}
        ])
        self.dron.setParams(parameters)
        messagebox.showinfo("Operación correcta", "El geo fence se ha establecido correctamente!")

    # ======== ESTABLECER WP Y REALIZAR GO TO ========

    def enable_wp_setting(self):
        # activamos o desactivamos la opción de go to
        self.reach_WP = not self.reach_WP
        if self.reach_WP:
            self.Button3.config(text="Desactivar 'establecer WP'")
            messagebox.showinfo("Establecer WP", "Clic derecho en el mapa para seleccionar el WP de destino.")
            # indicamos la función a ejecutar cuando se clica el botón derecho del ratón
            self.map_widget.add_right_click_menu_command(label="Add Marker", command=self.add_marker_event,
                                                         pass_coords=True)

        if not self.reach_WP:
            self.Button3.config(text="Establecer WP")
            self.remove_right_click_menu_command(label="Add Marker")

    def remove_right_click_menu_command(self, label):
        # desactivamos el boton derecho del ratón
        self.map_widget.right_click_menu_commands = [cmd for cmd in self.map_widget.right_click_menu_commands if
                                                     cmd['label'] != label]

    # aquí iremos cuando queramos dirigir el dron al punto marcado
    def start_goto(self):
        if self.destination_WP:
            # mantenemos la altitud que tiene el dron
            alt = self.dron.alt
            self.dron.stopGo()
            self.dron.goto(float(self.destination_WP[0]), float(self.destination_WP[1]), alt, blocking=False)

    # ======= ESTABLECER ICONO DRON (MARKER) =======
    def show_dron(self):
        # muestro el dron o dejo de mostrarlo
        self.marker = not self.marker
        if self.marker:
            # si hay que mostrarlo aquí añado el icono del dron
            self.drone_marker = self.map_widget.set_marker(self.initial_lat, self.initial_lon,
                                                           marker_color_outside="blue", marker_color_circle="black",
                                                           text="", text_color="blue",
                                                           icon=self.photo, icon_anchor="center")
            # pido que me envíen datos de telemetría que me permitirán saber dónde está el dron para resituarlo en el mapa
            if not self.dron.sendTelemetryInfo:
                # indico qué función quiero que se ejecute cada vez que llega un nuevo paquete de datos de telemetría
                self.dron.send_telemetry_info(self.process_telemetry_info)
        else:
            # Si hay que quitarlo, lo hago aquí
            if self.drone_marker:
                self.map_widget.delete(self.drone_marker)
                self.drone_marker = None
            if not self.trace:
                self.dron.stop_sending_telemetry_info()

    # vendremos aquí cada vez que se reciba un paquete de datos de telemetría
    def process_telemetry_info(self, telemetry_info):
        # recupero la posición del dron para redibujar el icono en el mapa
        lat = telemetry_info['lat']
        lon = telemetry_info['lon']

        if self.trace:
            # dibujamos el ratro
            if self.last_position:
                self.map_widget.set_path([self.last_position, (lat, lon)], width=5)
            self.last_position = (lat, lon)

        if self.marker:

            if self.drone_marker:
                # borro el icono que hay
                self.map_widget.delete(self.drone_marker)
            # coloco el icono en su nueva posición
            self.drone_marker = self.map_widget.set_marker(lat, lon,
                                                           marker_color_outside="blue",
                                                           marker_color_circle="black",
                                                           text="", text_color="blue",
                                                           icon=self.photo, icon_anchor="center")

    # ======= MARCAR TRAZADO DEL DRON =======
    def set_trace(self):
        self.trace = not self.trace
        if self.trace:
            if not self.dron.sendTelemetryInfo:
                self.dron.send_telemetry_info(self.process_telemetry_info)
        else:
            self.map_widget.delete_all_path()
            self.last_position = []
            if not self.marker:
                self.dron.stop_sending_telemetry_info()

    def new_function(self):
        pass

