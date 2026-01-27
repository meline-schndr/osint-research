import os
import sys

import face_recognition
import numpy as np
from PIL import Image, ImageDraw


def chercher_fichier(filename: str):
    if os.name == "nt":
        root = "C:\\Users\\"
    else:
        root = "/home/"

    for folder, subfolder, files in os.walk(root):
        try:
            if filename in files:
                return os.path.join(folder, filename)
        except PermissionError:
            continue
    return None


if __name__ == "__main__":
    # --- PARTIE 1 : RÉFÉRENCE ---
    nom_im1 = input("Nom de l'image de référence (ex: teddy.jpg) : ")
    res = chercher_fichier(nom_im1)

    if res:
        print(f"Trouvé : {res}")
    else:
        print("Nope")
        sys.exit()

    image = face_recognition.load_image_file(res)
    enc_image = face_recognition.face_encodings(image)[0]
    encodage_visage_im1 = [enc_image]

    pers = input("Qui es-tu ? ")
    nom_visage = [pers]

    # --- PARTIE 2 : ANALYSE DU GROUPE ---
    nom_im2 = input("Donnez l'image où trouver le visage : ")
    im2 = chercher_fichier(nom_im2)

    if im2:
        print(f"Trouvé : {im2}")
    else:
        print("Nope")
        sys.exit()

    image2 = face_recognition.load_image_file(im2)
    visage_im2 = face_recognition.face_locations(image2)
    enc_visage_im2 = face_recognition.face_encodings(image2, visage_im2)

    photo = Image.fromarray(image2)
    draw = ImageDraw.Draw(photo)

    compteur = 0
    trouve = False

    for (haut, droite, bas, gauche), encodage_visage in zip(visage_im2, enc_visage_im2):
        corr = face_recognition.compare_faces(encodage_visage_im1, encodage_visage)

        # Calcul de la distance pour trouver l'indice du meilleur match
        distances_visage = face_recognition.face_distance(
            encodage_visage_im1, encodage_visage
        )
        best_ind = np.argmin(distances_visage)

        if corr[best_ind]:
            compteur += 1
            nom = nom_visage[best_ind]
            draw.rectangle([gauche, haut, droite, bas], outline="red", width=5)
            draw.text((gauche, haut - 10), nom, fill="red")
            trouve = True

    # --- BILAN ---
    if not trouve:
        print("Tu n'es pas sur cette photo ! ")
    else:
        print(f"Tu apparais {compteur} fois sur la photo !")

    photo.show()
