import os
import glob
import numpy as np
from netCDF4 import Dataset
from PIL import Image

# Configuració de carpetes
INPUT_FOLDER = 'dades_radar'
OUTPUT_FOLDER = 'dades_radar_png'

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# La teva llegenda (RGB: Valor de pluja)
LLEGENDA_RADAR = {
    (128, 0, 255): 0.2,   (64, 0, 255): 0.8,   (0, 0, 255): 1.2,
    (0, 255, 255): 2.0,   (0, 255, 128): 3.0,   (0, 255, 0): 4.5,
    (63, 255, 0): 6.5,    (128, 255, 0): 9.0,   (198, 255, 0): 12.0,
    (255, 255, 0): 15.0,  (255, 171, 0): 15.1,  (255, 129, 0): 20.0,
    (255, 87, 0): 30.0,   (255, 45, 0): 40.0,   (255, 0, 0): 50.0,
    (255, 0, 63): 60.0,   (255, 0, 127): 70.0,  (255, 0, 191): 85.0,
    (255, 0, 255): 100.0, (255, 255, 255): 150.0
}

def processar_nc_a_png():
    arxius = glob.glob(os.path.join(INPUT_FOLDER, "*.nc"))
    
    if not arxius:
        print(f"No s'han trobat arxius .nc a {INPUT_FOLDER}")
        return

    for path in arxius:
        nom_arxiu = os.path.basename(path).replace('.nc', '.png')
        print(f"Processant: {nom_arxiu}...")
        
        try:
            with Dataset(path, 'r') as nc:
                # Busquem la variable de dades (que no sigui lat, lon o time)
                var_name = [v for v in nc.variables if v not in ['lat', 'lon', 'time']][0]
                dades = nc.variables[var_name][:]
                
                if len(dades.shape) == 3:
                    dades = dades[0]

                # Convertim a array de numpy normal si és un masked_array
                dades = np.ma.filled(dades, fill_value=0)

                # Creem una matriu RGBA (4 canals: Vermell, Verd, Blau, Alfa)
                # Inicialment tot a zero (transparent)
                alt, ample = dades.shape
                img_data = np.zeros((alt, ample, 4), dtype=np.uint8)

                # --- VECTORITZACIÓ ---
                # En lloc de fer bucles per píxel, iterem només sobre els colors de la llegenda
                for rgb, valor_exacte in LLEGENDA_RADAR.items():
                    # Creem una màscara de tots els píxels que coincideixen amb el valor
                    # Fem servir un marge petit (tol) per si hi ha errors de precisió float
                    mask = np.isclose(dades, valor_exacte, atol=0.01)
                    
                    # Pintem els píxels que compleixen la condició
                    img_data[mask] = [rgb[0], rgb[1], rgb[2], 255] # 255 és opac

                # Invertim l'eix vertical si és necessari per a la correcta georeferenciació
                img = Image.fromarray(img_data, 'RGBA')
                img = img.transpose(Image.FLIP_TOP_BOTTOM) 
                
                img.save(os.path.join(OUTPUT_FOLDER, nom_arxiu))
                print(f"  Finalitzat: {nom_arxiu}")
                
        except Exception as e:
            print(f"  Error processant {path}: {e}")

if __name__ == "__main__":
    processar_nc_a_png()
