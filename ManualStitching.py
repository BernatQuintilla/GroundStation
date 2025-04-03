import numpy as np
import os
import random
import cv2
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox


class ManualImageStitching:
    def __init__(self, mission_name, MapFrame):
        self.path = f"photos/{mission_name}"
        self.images = self.load_images()
        self.gray_images = [self.rgb2gray(img) for img in self.images]
        self.nombre_mision = mission_name
        self.stitch_frame = None
        self.MapFrame = MapFrame

    def load_images(self):
        """Load all images from the mission folder in BGR and convert to RGB"""
        images = []
        for filename in sorted(os.listdir(self.path)):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = cv2.imread(os.path.join(self.path, filename))
                images.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        return images

    def rgb2gray(self, rgb):
        """Convert RGB image to grayscale using OpenCV"""
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    def detect_and_compute(self, image):
        """Detect keypoints and descriptors with SIFT"""
        sift = cv2.SIFT_create(3000)
        return sift.detectAndCompute(image, None)

    def match_features(self, des1, des2):
        """BFMatcher with L2 norm and crossCheck"""
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
        return bf.match(des1, des2)

    def DLT_homography(self, points1, points2):
        """Direct Linear Transform"""
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
        """Finds the inliers between two sets of points using a homography matrix"""
        try:
            transformed = np.dot(H, points1)
            transformed /= transformed[2]
            error = np.sqrt(np.sum((points2 - transformed) ** 2, axis=0))
            return np.where(error < th)[0]
        except:
            return np.empty(0)

    def Ransac_DLT_homography_adaptive_loop(self, points1, points2, th=4, p=0.99):
        """RANSAC implementation with adaptive loop"""
        Ncoords, Npts = points1.shape
        s = 4
        best_inliers = np.empty(1)
        it = 0
        N_trials = 10000  # Initial value

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

    def calculate_corners(self, img, H):
        """Calculate the corners needed for the mosaic based on the image and homography"""
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
        """Image warping with fixed size"""
        x_min, x_max, y_min, y_max = corners
        out_size = (int(x_max - x_min), int(y_max - y_min))
        T = np.array([[1, 0, -x_min], [0, 1, -y_min], [0, 0, 1]])
        warped = cv2.warpPerspective(img, T.dot(H), out_size,
                                     flags=cv2.INTER_LINEAR,
                                     borderMode=cv2.BORDER_REPLICATE)
        return warped

    def stitch_images(self):
        """Stitch multiple images together with improved blending"""
        if len(self.images) < 2:
            return self.images[0] if self.images else None

        # Start with the first image
        current_mosaic = self.images[0].astype(np.float32)
        current_H = np.eye(3)
        weights = np.ones(current_mosaic.shape[:2], dtype=np.float32)

        for i in range(1, len(self.images)):
            print(f"Stitching image {i + 1}/{len(self.images)}")

            # Detect features and match
            kp1, des1 = self.detect_and_compute(self.gray_images[i - 1])
            kp2, des2 = self.detect_and_compute(self.gray_images[i])
            matches = self.match_features(des1, des2)

            # Convert matches to points
            points1, points2 = [], []
            for m in matches:
                points1.append([kp1[m.queryIdx].pt[0], kp1[m.queryIdx].pt[1], 1])
                points2.append([kp2[m.trainIdx].pt[0], kp2[m.trainIdx].pt[1], 1])

            points1 = np.array(points1).T
            points2 = np.array(points2).T

            # Compute homography between current pair
            H, _ = self.Ransac_DLT_homography_adaptive_loop(points1, points2, th=4)
            current_H = H @ current_H

            # Calculate corners for the new mosaic
            corners = self.calculate_corners(self.images[i], current_H)
            x_min, x_max, y_min, y_max = corners
            out_size = (int(x_max - x_min), int(y_max - y_min))

            # Warp the current mosaic and weights
            T = np.array([[1, 0, -x_min], [0, 1, -y_min], [0, 0, 1]])
            mosaic_warped = cv2.warpPerspective(current_mosaic, T.dot(current_H), out_size,
                                                flags=cv2.INTER_LINEAR)
            weights_warped = cv2.warpPerspective(weights, T.dot(current_H), out_size,
                                                 flags=cv2.INTER_LINEAR,
                                                 borderMode=cv2.BORDER_CONSTANT,
                                                 borderValue=0)

            # Warp the new image
            img_warped = cv2.warpPerspective(self.images[i].astype(np.float32),
                                             T.dot(np.eye(3)), out_size,
                                             flags=cv2.INTER_LINEAR)
            img_weights = cv2.warpPerspective(np.ones(self.images[i].shape[:2], dtype=np.float32),
                                              T.dot(np.eye(3)), out_size,
                                              flags=cv2.INTER_LINEAR,
                                              borderMode=cv2.BORDER_CONSTANT,
                                              borderValue=0)

            # Blend using weighted average
            total_weights = weights_warped + img_weights
            total_weights[total_weights == 0] = 1  # Avoid division by zero

            current_mosaic = ((mosaic_warped * weights_warped[..., np.newaxis] +
                               img_warped * img_weights[..., np.newaxis]) /
                              total_weights[..., np.newaxis])

            weights = weights_warped + img_weights
            current_H = np.eye(3)  # Reset for next iteration

        return np.clip(current_mosaic, 0, 255).astype(np.uint8)

    def show_manual_stitched_image(self):
        """EXACT original show_manual_stitched_image function"""
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



