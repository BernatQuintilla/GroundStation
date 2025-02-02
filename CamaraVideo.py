import tkinter as tk
import cv2
from PIL import Image, ImageTk

class CamaraVideo:
    def __init__(self, fatherFrame):
        self.CamaraVideo = tk.Frame(fatherFrame)
        self.CamaraVideo.grid(row=0, column=0, sticky="nsew")

        self.CamaraVideo.rowconfigure(0, weight=1)
        self.CamaraVideo.rowconfigure(1, weight=30)
        self.CamaraVideo.columnconfigure(0, weight=1)

        self.mov_frame = tk.LabelFrame(self.CamaraVideo, text="Video")
        self.mov_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.mov_frame.rowconfigure(0, weight=1)
        self.mov_frame.rowconfigure(1, weight=1)
        self.mov_frame.columnconfigure(0, weight=1)

        self.video_label = tk.Label(self.mov_frame)
        self.video_label.grid(row=1, column=0, padx=10, pady=10)

        self.cap = cv2.VideoCapture(0)
        self.update_frame()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)

            self.video_label.imgtk = imgtk
            self.video_label.config(image=imgtk)

        self.CamaraVideo.after(10, self.update_frame)

    def release_camera(self):
        self.cap.release()

    def destroy_frame(self):
        self.CamaraVideo.destroy()


def show_camera_video(fatherFrame):
    map_window = tk.Toplevel(fatherFrame)
    map_window.title("Camara de Video")
    map_window.geometry("700x500")

    camera_frame = CamaraVideo(map_window)

    map_window.protocol("WM_DELETE_WINDOW", lambda: close_camera(camera_frame, map_window))

def close_camera(camera_frame, map_window):
    camera_frame.release_camera()
    camera_frame.destroy_frame()
    map_window.destroy()