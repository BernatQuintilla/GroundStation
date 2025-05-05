import numpy as np
import os
import random
import cv2
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox


class ManualImageStitching:
    def __init__(self, mission_name, MapFrame):
        # guardo el path de la carpeta de imagenes de la mision seleccionada
        self.path = f"photos/{mission_name}"
        # cargo las imagenes llamando a load_images
        self.images = self.load_images()
        # guardo imagenes en escala de grises
        self.gray_images = [self.rgb2gray(img) for img in self.images]
        self.nombre_mision = mission_name
        self.stitch_frame = None
        self.MapFrame = MapFrame

    # ======== CARGA Y TRATAMIENTO INICIAL IMAGENES ========
    def load_images(self):
        # funcion que devuelve las imagenes del path

        images = []
        for filename in sorted(os.listdir(self.path)):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = cv2.imread(os.path.join(self.path, filename))
                images.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        return images

    def rgb2gray(self, rgb):
        #funcion que convierte imagen rgb a escala de grises

        return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # ======== ENCONTRAR KEYPOINTS Y CORRESPONDENCIAS ENTRE ELLOS ========
    def detect_and_compute(self, image):
        # funcion que utiliza el algoritmo SIFT para detectar puntos clave y calcular sus descriptores en una imagen

        sift = cv2.SIFT_create(3000)
        return sift.detectAndCompute(image, None)

    def match_features(self, des1, des2):
        # funcion que utiliza un comparador de fuerza bruta para encontrar correspondencias entre descriptores de dos imágenes

        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
        return bf.match(des1, des2)

    # ======== CREACION DE LA MATRIZ DE HOMOGRAFIA ========
    def DLT_homography(self, points1, points2):
        # funcion que implementa el algoritmo DLT (Direct Linear Transform) para calcular una matriz
        # de homografía (H) que relaciona dos conjuntos de puntos correspondientes en imágenes diferentes

        A = []
        for i in range(points1.shape[1]):
            x, y, _ = points1[:, i]
            u, v, _ = points2[:, i]
            A.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
            A.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
        A = np.array(A)
        _, _, V = np.linalg.svd(A)
        H = V[-1].reshape(3, 3)
        return H / H[2, 2]

    def find_homography_inliers(self, H, points1, points2, th):
        # funcion que evalúa la calidad de una homografía (H) al medir cómo de bien transforma los puntos
        # de una imagen (points1) a sus correspondientes puntos en otra imagen (points2). Luego, filtra
        # los "inliers" (puntos que cumplen con un umbral de error th)

        try:
            transformed = np.dot(H, points1)
            transformed /= transformed[2]
            error = np.sqrt(np.sum((points2 - transformed) ** 2, axis=0))
            return np.where(error < th)[0]
        except:
            return np.empty(0)

    def Ransac_DLT_homography_adaptive_loop(self, points1, points2, th=4, p=0.99):
        #  implementa el algoritmo RANSAC de forma adaptativa para estimar una matriz
        #  de homografía (H) robusta, incluso en presencia de outliers

        Ncoords, Npts = points1.shape
        s = 4
        best_inliers = np.empty(1)
        it = 0
        N_trials = 10000

        while it < N_trials:
            indices = random.sample(range(Npts), s)
            H = self.DLT_homography(points1[:, indices], points2[:, indices])
            inliers = self.find_homography_inliers(H, points1, points2, th)

            w = len(inliers) / Npts
            N_trials = min(N_trials, int(np.ceil(np.log(1 - p) / np.log(1 - w ** s))))

            if len(inliers) > len(best_inliers):
                best_inliers = inliers
            it += 1

        H = self.DLT_homography(points1[:, best_inliers], points2[:, best_inliers])
        return H, best_inliers

    # ======== IMPLEMENTACION TRANSFORMACION DDE HOMOGRAFIA ========
    def calculate_corners(self, img, H):
        # funcion que calcula las nuevas esquinas de una imagen despues de aplicar
        # una transformación de homografía (H)

        h, w = img.shape[:2]
        corners = np.array([
            [0, 0, 1],
            [w, 0, 1],
            [w, h, 1],
            [0, h, 1]
        ]).T

        transformed_corners = np.dot(H, corners)
        transformed_corners /= transformed_corners[2]

        x_min = min(transformed_corners[0].min(), 0)
        x_max = max(transformed_corners[0].max(), w)
        y_min = min(transformed_corners[1].min(), 0)
        y_max = max(transformed_corners[1].max(), h)

        return [x_min, x_max, y_min, y_max]

    def apply_H_fixed_image_size(self, img, H, corners):
        # funcion que aplica una transformación de homografía (H) a una imagen (img) mientras ajusta el
        # tamaño de salida para que toda la imagen transformada sea visible, evitando recortes

        x_min, x_max, y_min, y_max = corners
        out_size = (int(x_max - x_min), int(y_max - y_min))
        T = np.array([[1, 0, -x_min], [0, 1, -y_min], [0, 0, 1]])
        warped = cv2.warpPerspective(img, T.dot(H), out_size,
                                     flags=cv2.INTER_LINEAR,
                                     borderMode=cv2.BORDER_REPLICATE)
        return warped

    # ======== REALIZACION DEL STITCHING ========
    def stitch_images(self):

        if len(self.images) < 2:
            return self.images[0] if self.images else None

        # inicialización del mosaico con la primera imagen
        current_mosaic = self.images[0].astype(np.float32)
        current_H = np.eye(3)  # Matriz de homografía inicial (identidad)
        weights = np.ones(current_mosaic.shape[:2], dtype=np.float32)  # Mapa de pesos inicial

        for i in range(1, len(self.images)):
            print(f"Stitching image {i + 1}/{len(self.images)}")

            # --------------------------------------------------
            # 1. DETECCIÓN DE CARACTERÍSTICAS Y MATCHING
            # --------------------------------------------------

            # detectar puntos clave y descriptores en ambas imágenes
            kp1, des1 = self.detect_and_compute(self.gray_images[i - 1])  # Imagen anterior
            kp2, des2 = self.detect_and_compute(self.gray_images[i])  # Imagen actual

            # encontrar correspondencias entre descriptores
            matches = self.match_features(des1, des2)

            # preparar puntos para la homografía (en coordenadas homogéneas)
            points1, points2 = [], []
            for m in matches:
                points1.append([kp1[m.queryIdx].pt[0], kp1[m.queryIdx].pt[1], 1])
                points2.append([kp2[m.trainIdx].pt[0], kp2[m.trainIdx].pt[1], 1])

            points1 = np.array(points1).T  # Convertir a formato 3xN
            points2 = np.array(points2).T

            # --------------------------------------------------
            # 2. ESTIMACIÓN DE HOMOGRAFÍA CON RANSAC
            # --------------------------------------------------

            # calcular homografía robusta usando RANSAC
            H, _ = self.Ransac_DLT_homography_adaptive_loop(points1, points2, th=4)

            # actualizar homografía acumulada (composición de transformaciones)
            current_H = H @ current_H

            # --------------------------------------------------
            # 3. CALCULAR NUEVO ESPACIO DE MOSAICO
            # --------------------------------------------------

            # determinar esquinas transformadas para calcular tamaño de salida
            corners = self.calculate_corners(self.images[i], current_H)
            x_min, x_max, y_min, y_max = corners
            out_size = (int(x_max - x_min), int(y_max - y_min))  # nuevas dimensiones

            # matriz de traslación para evitar recortes
            T = np.array([
                [1, 0, -x_min],
                [0, 1, -y_min],
                [0, 0, 1]
            ])

            # --------------------------------------------------
            # 4. TRANSFORMACIÓN DE IMÁGENES
            # --------------------------------------------------

            # aplicar transformación al mosaico actual
            mosaic_warped = cv2.warpPerspective(
                current_mosaic,
                T.dot(current_H),  # homografía ajustada
                out_size,
                flags=cv2.INTER_LINEAR  # interpolación para calidad
            )

            # transformar los pesos del mosaico actual
            weights_warped = cv2.warpPerspective(
                weights,
                T.dot(current_H),
                out_size,
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,  # rellenar con 0 fuera de bordes
                borderValue=0
            )

            # transformar la nueva imagen al espacio del mosaico
            img_warped = cv2.warpPerspective(
                self.images[i].astype(np.float32),
                T.dot(np.eye(3)),  # solo aplicación de traslación
                out_size,
                flags=cv2.INTER_LINEAR
            )

            # crear mapa de pesos para la nueva imagen
            img_weights = cv2.warpPerspective(
                np.ones(self.images[i].shape[:2], dtype=np.float32),
                T.dot(np.eye(3)),
                out_size,
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0  # 0 fuera de la imagen
            )

            # --------------------------------------------------
            # 5. FUSIÓN PONDERADA DE IMÁGENES
            # --------------------------------------------------

            # calcular pesos totales
            total_weights = weights_warped + img_weights
            total_weights[total_weights == 0] = 1

            current_mosaic = (
                    (mosaic_warped * weights_warped[..., np.newaxis] +
                     img_warped * img_weights[..., np.newaxis]) /
                    total_weights[..., np.newaxis]
            )

            # actualizar pesos acumulados
            weights = weights_warped + img_weights

            # reiniciar homografia para la siguiente iteración
            current_H = np.eye(3)

        # --------------------------------------------------
        # 6. POST-PROCESAMIENTO FINAL
        # --------------------------------------------------

        # asegurar valores de píxel validos y convertir a formato uint8
        return np.clip(current_mosaic, 0, 255).astype(np.uint8)

    # ======== MUESTRA DE STITCHING EN PANEL PRINCIPAL ========
    def show_manual_stitched_image(self):
        # funcion que muestra la imagen resultante del stitching en el panel principal sobreponiendose
        # a esta interfaz. El procedimiento es el miso que para las galerias y el stitching de OpenCV.

        if self.nombre_mision == "":
            messagebox.showerror("Selecciona Misión", "Selecciona una misión.")
            return

        if not os.path.exists(self.path):
            messagebox.showerror("Misión sin imágenes", "La misión seleccionada no tiene imágenes.")
            return

        if len(self.images) < 2:
            messagebox.showerror("Error", "Se necesitan al menos dos imágenes para hacer el stitching.")
            return

        try:
            stitched = self.stitch_images()
            stitched_pil = Image.fromarray(stitched)
            stitched_pil = stitched_pil.resize((800, 600), Image.Resampling.LANCZOS)
            stitched_photo = ImageTk.PhotoImage(stitched_pil)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo hacer el stitching de las imágenes. Error: {str(e)}")
            return

        if self.stitch_frame:
            self.stitch_frame.destroy()

        self.stitch_frame = tk.Frame(self.MapFrame)
        self.stitch_frame.grid(row=0, column=0, columnspan=16, padx=5, pady=5, sticky="nsew")

        self.stitch_frame.rowconfigure(0, weight=0)
        self.stitch_frame.rowconfigure(1, weight=10)
        self.stitch_frame.columnconfigure(0, weight=1)
        self.stitch_frame.columnconfigure(1, weight=10)
        self.stitch_frame.columnconfigure(2, weight=1)

        img_label = tk.Label(self.stitch_frame, image=stitched_photo)
        img_label.image = stitched_photo
        img_label.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        back_button = tk.Button(self.stitch_frame, text="Volver", bg="dark orange", fg="black",
                                command=self.stitch_frame.grid_forget)
        back_button.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")



