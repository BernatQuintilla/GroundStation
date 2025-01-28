from PoseDetector import initialize, prepareBody, detectPose
import tkinter as tk
import tkintermapview
from tkinter import Canvas
from tkinter import messagebox
from tkinter import ttk
import cv2
import threading
from PIL import Image, ImageTk



class BodyFrameClass:

    def __init__(self, dron):
        self.dron = dron

        # acciones asociadas a cada una de las poses (si no se detecta ninguna de ellas el dron se parará)
        self.pose_commands = {1: "North",
                              2: "NorthEast",
                              3: "South",
                              4: "East",
                              5: "West",
                              6: "RTL"
                              }

        self.body_control_active = False

    def buildFrame(self, fatherFrame):
        self.BodyFrame = tk.Frame(fatherFrame)

        self.BodyFrame.rowconfigure(0, weight=1)
        self.BodyFrame.rowconfigure(1, weight=30)

        self.BodyFrame.columnconfigure(0, weight=1)


        # ===== BODY CONTROL FRAME =====
        self.mov_frame = tk.LabelFrame(self.BodyFrame, text="Movimiento")
        self.mov_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky=tk.N + tk.S + tk.E + tk.W)

        self.mov_frame.rowconfigure(0, weight=1)
        self.mov_frame.rowconfigure(1, weight=1)
        self.mov_frame.columnconfigure(0, weight=1)


        self.Button6 = tk.Button(self.mov_frame, text="Control por poses", bg="dark orange", fg="black", command=self.start_body_control)
        self.Button6.grid(row=0, column=0, padx=5, pady=3, sticky="nesw")

        self.Button7 = tk.Button(self.mov_frame, text="Detener control por poses", bg="dark orange", fg="black", command=self.stop_body_control)
        self.Button7.grid(row=1, column=0, padx=5, pady=3, sticky="nesw")

        # Cargar imágenes de las poses
        image = Image.open("assets/poses.png").resize((600, 180), Image.LANCZOS)    # Ruta a la imágen
        tk_image = ImageTk.PhotoImage(image)


        # Crear etiquetas para imágenes
        label = tk.Label(self.BodyFrame, image=tk_image)
        label.image = tk_image

        label.grid(row=1, column=0, padx=5, pady=2, sticky="new")


        self.BodyFrame.pack(expand=True, fill="both")

        return self.BodyFrame


    # ======= POSES (BODY CONTROL) =======
    def start_body_control(self):
        self.body_control_active = True
        messagebox.showinfo("Control con poses", "Mueve los brazos para seguir una trayectoria determinada")
        threading.Thread(target=self.capture_and_process_frames, daemon=True).start()

    # En este thread iteramos para capturar el stream de video y detectar poses en cada frame de ese stream
    def capture_and_process_frames(self):
        cap = cv2.VideoCapture(0)
        initialize()

        while self.body_control_active:
            # leemos un frame
            result, computer_frame = cap.read()
            if result:
                computer_frame = cv2.resize(computer_frame, (480, 320))
                # pedimos que nos den los puntos clave
                body_landmarks, frame_with_landmarks = prepareBody(computer_frame)
                frame_with_landmarks = cv2.flip(frame_with_landmarks, 1)
                # si ha encontrado puntos clave
                if len(body_landmarks) > 0:
                    # preguntamos si conrresponden a alguna de las poses
                    mi_pose = detectPose(body_landmarks)
                    if mi_pose is not None:
                        # corresponden a una pose
                        self.dron.changeNavSpeed(float(self.dron.navSpeed))

                        if not self.dron.going:
                            # nos ponemos en modo navegación
                            self.dron.startGo()
                        # miramos en la lista de comandos cuál corresponde a la pose detactada
                        # si no corresponde a ninguna nos dara "Stop"
                        command = self.pose_commands.get(mi_pose, "Stop")
                        if mi_pose == 6:
                            self.dron.RTL(blocking = False)
                        else:
                            self.dron.go(command)
                        # preparamos el texto para etiquetar la imagen con la información de la pose
                        texto = 'Pose '+str(mi_pose) + ': '+command

                    cv2.putText(frame_with_landmarks, texto, (50, 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)


                cv2.imshow("computer", frame_with_landmarks)
                cv2.waitKey(1)



    def stop_body_control(self):
        self.body_control_active = False
