import tkinter as tk
from tkinter import filedialog
import face_recognition
from PIL import Image, ImageDraw
import numpy as np
import os
import sys

name = ""
def choisir_fichier():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    chemin_du_fichier = filedialog.askopenfilename(
        title=f"Sélectionnez une image {name}",
        filetypes=[("Images", "*.jpg"), ("Tous les fichiers", "*.*")]
    )

    if chemin_du_fichier:
        # Cette fonction extrait uniquement la fin du chemin
        nom_fichier = os.path.basename(chemin_du_fichier)
        print(f"Image {name} : {nom_fichier}")
        return chemin_du_fichier
    else:
        print("Aucun fichier sélectionné.")

# Appel de la fonction

name="de référence"
ref = choisir_fichier()


image_1 = face_recognition.load_image_file(ref)
encodage_image_1 = face_recognition.face_encodings(image_1)

if not encodage_image_1:
    print("Erreur : Aucun visage n'a été détecté sur l'image de référence.")
    sys.exit()
encodage_visage_im1 = [encodage_image_1[0]]

#Donner un nom au visage
pers = input("Qui est-ce ? ").title()
nom_visage = [pers]

#Image à comparer
name="à comparer"
comp = choisir_fichier()

#Détection et encodage de l'image à comparer
image_2 = face_recognition.load_image_file(comp)
visage_image_2 = face_recognition.face_locations(image_2)
encodage_visage_image_2 = face_recognition.face_encodings(image_2, visage_image_2)

#Conversion de l'image pour la modifié
photo = Image.fromarray(image_2)
draw = ImageDraw.Draw(photo) 

compteur = 0
trouve = False
    
for (haut, droite, bas, gauche), encodage_visage in zip(visage_image_2, encodage_visage_image_2):
    corr = face_recognition.compare_faces(encodage_visage_im1, encodage_visage)
    

    distances_visage = face_recognition.face_distance(encodage_visage_im1, encodage_visage)
    best_ind = np.argmin(distances_visage)

    if corr[best_ind]: 
        compteur += 1
        nom = nom_visage[best_ind]
        draw.rectangle([gauche, haut, droite, bas], outline="red", width=5)
        draw.text((gauche, haut - 10), nom, fill="red")
        trouve = True

if not trouve:
    print("Tu n'es pas sur cette photo ! ")
else:
    print(f"Tu apparais {compteur} fois sur la photo !")
       
photo.show()



