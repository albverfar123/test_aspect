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

def get_color(valor):
    """Retorna el color RGB més proper segons el valor de pluja."""
    if valor <= 0 or np.isnan(valor):
        return (0, 0, 0, 0) # Transparent o Negre si no hi ha pluja
    
    # Busquem el llindar més proper sense passar-nos (o el primer superior)
    last_color = (0, 0, 0)
    for rgb, llindar in sorted(LLEGENDA_RADAR.items(), key=lambda x: x[1]):
        if valor <= llindar:
            return rgb
        last_color = rgb
    return last_color

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
                # Suposem que la variable es diu 'precip' o 'p' 
                # (Ajusta el nom segons el teu fitxer .nc)
                var_name = [v for v in nc.variables if v not in ['lat', 'lon', 'time']][0]
                dades = nc.variables[var_name][:]
                
                # Si dades té 3 dimensions (temps, lat, lon), agafem la primera de temps
                if len(dades.shape) == 3:
                    dades = dades[0]

                # Creem la imatge buida (RGBA per transparència si cal)
                alt, ample = dades.shape
                img_data = np.zeros((alt, ample, 3), dtype=np.uint8)

                # Omplim els píxels
                # Nota: Això és un loop simple. Per arxius molt grans es podria optimitzar amb vectorització
                for y in range(alt):
                    for x in range(ample):
                        img_data[y, x] = get_color(dades[y, x])

                # Guardem (Invertim l'eix Y si el mapa surt del revés, habitual en NC)
                img = Image.fromarray(img_data)
                img = img.transpose(Image.FLIP_TOP_BOTTOM) 
                img.save(os.path.join(OUTPUT_FOLDER, nom_arxiu))
                
        except Exception as e:
            print(f"Error processant {path}: {e}")

if __name__ == "__main__":
    processar_nc_a_png()
