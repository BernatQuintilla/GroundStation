import tkinter as tk
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO

class ObjectRecognition:
    def __init__(self, fatherFrame):
        self.CamaraVideo = tk.Frame(fatherFrame)
        self.CamaraVideo.pack(fill="both", expand=True)

        self.mov_frame = tk.LabelFrame(self.CamaraVideo, text="Video")
        self.mov_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.video_label = tk.Label(self.mov_frame)
        self.video_label.pack(padx=10, pady=10)

        self.cap = cv2.VideoCapture(0)

        self.model = YOLO("models/yolov8n.pt")

        self.update_frame()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            results = self.model(frame)
            annotated_frame = results[0].plot()
            annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(annotated_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.config(image=imgtk)

        self.CamaraVideo.after(10, self.update_frame)

    def release_camera(self):
        self.cap.release()

    def destroy_frame(self):
        self.CamaraVideo.destroy()

def show_camera_recognition(fatherFrame):
    map_window = tk.Toplevel(fatherFrame)
    map_window.title("Camara de Video con Detección de Objetos")
    map_window.geometry("700x500")

    camera_frame = ObjectRecognition(map_window)

    map_window.protocol("WM_DELETE_WINDOW", lambda: close_camera(camera_frame, map_window))

def close_camera(camera_frame, map_window):
    camera_frame.release_camera()
    camera_frame.destroy_frame()
    map_window.destroy()
