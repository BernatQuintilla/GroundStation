import tkinter as tk
from Dron import Dron
from tkinter import messagebox
from MapInterface import MapFrameClass


def showmap():
    global dron
    root_window = tk.Tk()
    root_window.title("Estación de tierra")
    root_window.geometry("820x620")

    map_frame_class = MapFrameClass(dron)
    map_frame = map_frame_class.buildFrame(root_window)
    map_frame.pack(fill="both", expand=True)

    return root_window

if __name__ == "__main__":
    dron = Dron()
    ventana = showmap()
    ventana.mainloop()