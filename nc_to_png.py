import os
import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Configuració de carpetes
INPUT_FOLDER = 'dades_radar'
OUTPUT_FOLDER = 'dades_radar_png'

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Llegenda convertida a colors per Matplotlib
LLEGENDA_RADAR = {
    0.2: (128/255, 0/255, 255/255),
    0.8: (64/255, 0/255, 255/255),
    1.2: (0/255, 0/255, 255/255),
    2.0: (0/255, 255/255, 255/255),
    3.0: (0/255, 255/255, 128/255),
    4.5: (0/255, 255/255, 0/255),
    6.5: (63/255, 255/255, 0/255),
    9.0: (128/255, 255/255, 0/255),
    12.0: (198/255, 255/255, 0/255),
    15.0: (255/255, 255/255, 0/255),
    15.1: (255/255, 171/255, 0/255),
    20.0: (255/255, 129/255, 0/255),
    30.0: (255/255, 87/255, 0/255),
    40.0: (255/255, 45/255, 0/255),
    50.0: (255/255, 0/255, 0/255),
    60.0: (255/255, 0/255, 63/255),
    70.0: (255/255, 0/255, 127/255),
    85.0: (255/255, 0/255, 191/255),
    100.0: (255/255, 0/255, 255/255),
    150.0: (255/255, 255/255, 255/255)
}

def crear_cmap_discret():
    """Crea un colormap personalitzat basat en la teva llegenda"""
    vals = sorted(LLEGENDA_RADAR.keys())
    colors = [LLEGENDA_RADAR[v] for v in vals]
    cmap = mcolors.ListedColormap(colors)
    cmap.set_under(alpha=0) # Transparent per a valors < 0.2
    norm = mcolors.BoundaryNorm([0] + vals + [1000], cmap.N)
    return cmap, norm

def processar_nc_a_png():
    arxius = glob.glob(os.path.join(INPUT_FOLDER, "*.nc"))
    
    if not arxius:
        print(f"No s'han trobat arxius .nc a {INPUT_FOLDER}")
        return

    cmap, norm = crear_cmap_discret()

    for path in arxius:
        nom_arxiu = os.path.basename(path).replace('.nc', '.png')
        print(f"🎨 Generant PNG georeferenciat: {nom_arxiu}...")
        
        try:
            # Utilitzem xarray com el primer codi per mantenir la coherència de coordenades
            with xr.open_dataset(path) as ds:
                # Busquem la variable de dades
                var_name = [v for v in ds.data_vars if v not in ['lat', 'lon', 'time']][0]
                dades = ds[var_name].fillna(0).load()
                lon = ds['lon'].values
                lat = ds['lat'].values

                # --- LÒGICA DE GENERACIÓ IGUAL A L'ACUMULAT ---
                fig = plt.figure(frameon=False)
                # Mantenim la proporció de píxels exacta del NetCDF
                fig.set_size_inches(dades.shape[1]/100, dades.shape[0]/100)
                
                ax = plt.Axes(fig, [0., 0., 1., 1.])
                ax.set_axis_off()
                fig.add_axes(ax)

                # Dibuixem fent servir pcolormesh amb lat/lon (Això corregeix la posició)
                ax.pcolormesh(lon, lat, dades.values, cmap=cmap, norm=norm, shading='auto')

                png_out_path = os.path.join(OUTPUT_FOLDER, nom_arxiu)
                # DPI=100 per mantenir la mida calculada a set_size_inches
                fig.savefig(png_out_path, transparent=True, dpi=100)
                plt.close(fig)
                
                print(f"✅ Finalitzat: {nom_arxiu}")
                
        except Exception as e:
            print(f"❌ Error processant {path}: {e}")

if __name__ == "__main__":
    processar_nc_a_png()
