import tkinter as tk
from Dron import Dron
from MapInterface import MapFrameClass


def showmap():
    # declaro la variable global del dron
    global dron
    root_window = tk.Tk()
    root_window.title("Estación de tierra")
    root_window.geometry("1075x620")
    # inicializo la clase del panel principal y mostramos la interfaz
    map_frame_class = MapFrameClass(dron)
    map_frame = map_frame_class.buildFrame(root_window)
    map_frame.pack(fill="both", expand=True)

    return root_window

if __name__ == "__main__":
    dron = Dron()
    ventana = showmap()
    ventana.mainloop()