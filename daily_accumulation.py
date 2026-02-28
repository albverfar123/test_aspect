import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.colors as colors
import json
import requests # <--- Nou
import csv      # <--- Nou
# ... resta d'imports que ja tens ...

# --- CONFIGURACIÓ API METEOCAT ---
API_KEY = "5Rq09hMMoQ8JKQ87M9RxL5wM0dIW4HsU27G0WEjo" 
BASE_URL = "https://api.meteo.cat/xema/v1"
CODI_PLUJA = "1300"


OUTPUT_DIR = "dades_radar"
DAILY_DIR = "acumulats_diaris"

def get_stations_daily_data(date_obj):
    """Obté la pluja i coordenades de les estacions per a un dia concret"""
    headers = {"X-Api-Key": API_KEY}
    date_api_str = date_obj.strftime("%Y-%m-%dZ")
    
    print(f"📡 Descarregant dades i coordenades d'estacions per al {date_obj.strftime('%Y-%m-%d')}...")
    
    # 1. Obtenir metadades (incloent coordenades)
    res_est = requests.get(f"{BASE_URL}/estacions/metadades", headers=headers)
    estacions_info = {}
    if res_est.status_code == 200:
        for e in res_est.json():
            estacions_info[e['codi']] = {
                'nom': e['nom'],
                'lat': e['coordenades']['latitud'],
                'lon': e['coordenades']['longitud']
            }

    # 2. Obtenir dades de pluja
    url = f"{BASE_URL}/variables/estadistics/diaris/{CODI_PLUJA}?any={date_obj.year}&mes={date_obj.month:02d}"
    res = requests.get(url, headers=headers)
    
    dades_completes = []
    if res.status_code == 200:
        for estacio in res.json():
            codi = estacio.get('codiEstacio')
            if codi in estacions_info:
                info = estacions_info[codi]
                for val in estacio.get('valors', []):
                    if val['data'] == date_api_str:
                        dades_completes.append({
                            'codi': codi,
                            'nom': info['nom'],
                            'lat': info['lat'],
                            'lon': info['lon'],
                            'data': date_api_str.replace('Z',''),
                            'pluja': float(val['valor'])
                        })
    
    return dades_completes


def calculate_daily():
    # 1. Determinar el dia d'ahir
    ieri_obj = datetime.utcnow() - timedelta(days=1)
    ieri = ieri_obj.strftime("%Y%m%d")
    print(f"📅 Generant acumulat per al dia: {ieri}")

    if not os.path.exists(DAILY_DIR):
        os.makedirs(DAILY_DIR)

    # 2. Filtrar fitxers d'avui (Cerca recursiva en subcarpetes)
    if not os.path.exists(OUTPUT_DIR):
        print(f"❌ La carpeta {OUTPUT_DIR} no existeix.")
        return

    all_files_paths = []
    for root, dirs, filenames in os.walk(OUTPUT_DIR):
        for filename in filenames:
            # Busquem fitxers que comencin amb radar_YYYYMMDD i acabin en .nc
            if filename.startswith(f"radar_{ieri}") and filename.endswith(".nc"):
                full_path = os.path.join(root, filename)
                all_files_paths.append(full_path)
    
    all_files_paths.sort()

    if not all_files_paths:
        print(f"❌ No s'han trobat fitxers per al dia {ieri}")
        # Fem un print per veure què hi ha realment si falla
        for root, dirs, files in os.walk(OUTPUT_DIR):
             print(f"Dins de {root} hi ha: {files}")
        return

    # 3. Carregar i sumar les dades
    # 3. Carregar i sumar les dades
    total_precip = None
    used_files = [] # Aquí guardarem només el nom del fitxer per al log final
    
    FACTOR_TEMPORAL = 0.1 

    for file_path in all_files_paths:
        try:
            with xr.open_dataset(file_path) as ds:
                data = ds['precipitacio'].fillna(0).load()

                if total_precip is None:
                    total_precip = data * FACTOR_TEMPORAL
                    lon, lat = ds['lon'].load(), ds['lat'].load()
                else:
                    total_precip += data * FACTOR_TEMPORAL

                used_files.append(os.path.basename(file_path)) # Guardem només el nom per al TXT

        except Exception as e:
            print(f"⚠️ Error obrint {file_path}: {e}")

    if total_precip is None:
        print("❌ No s'ha pogut processar cap fitxer correctament.")
        return

    # 4. Crear NetCDF diari
    ds_daily = xr.Dataset(
        {"precipitacio_acumulada": (["lat", "lon"], total_precip.values)},
        coords={"lon": lon, "lat": lat},
        attrs={
            "description": f"Acumulat diari {ieri}", 
            "units": "mm", 
            "date": ieri,
            "files_count": len(used_files),
            "resolution_min": 6
        }
    )

    nc_out_path = os.path.join(DAILY_DIR, f"acumulat_{ieri}.nc")
    ds_daily.to_netcdf(nc_out_path)
    print(f"✅ NetCDF diari guardat: {nc_out_path}")

    # 5. TXT fonts (Amb comptador de fitxers per control)
    txt_out_path = os.path.join(DAILY_DIR, f"fonts_acumulat_{ieri}.txt")
    with open(txt_out_path, "w") as f_txt:
        f_txt.write(f"Resum de l'acumulat del dia {ieri}:\n")
        f_txt.write(f"Total fitxers processats: {len(used_files)}\n")
        f_txt.write(f"Resolució temporal: 6 minuts (factor 0.1)\n")
        f_txt.write("-" * 40 + "\n")
        f_txt.write("\n".join(used_files))
    print(f"📄 Llista de fonts guardada a: {txt_out_path}")

    

# --- NOU: PUNT 5.5 DESCARREGA I GUARDA ESTACIONS (CSV i GeoJSON) ---
    try:
        estacions_data = get_stations_daily_data(ieri_obj)
        if estacions_data:
            # 1. Guardar CSV
            csv_path = os.path.join(DAILY_DIR, f"estacions_{ieri}.csv")
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Codi', 'Nom', 'Data', 'Precipitacio_mm'])
                for d in estacions_data:
                    writer.writerow([d['codi'], d['nom'], d['data'], d['pluja']])
            print(f"📊 CSV d'estacions guardat: {csv_path}")

            # 2. Guardar GeoJSON
            geojson_path = os.path.join(DAILY_DIR, f"estacions_{ieri}.json")
            save_stations_geojson(estacions_data, geojson_path)
            print(f"📍 GeoJSON d'estacions guardat: {geojson_path}")
            
        else:
            print("⚠️ No s'han trobat dades d'estacions per a aquest dia.")
    except Exception as e:
        print(f"❌ Error processant dades d'estacions: {e}")

    
    # 6. GENERAR PNG
    generate_daily_png(total_precip, lon, lat, ieri)

    # 7. BORRAR RADARS (Neteja de la carpeta de treball)
    print(f"🗑️ Iniciant neteja de dades temporals a {OUTPUT_DIR}...")
    deleted_count = 0
    for f in used_files:
        file_to_delete = os.path.join(OUTPUT_DIR, f)
        try:
            os.remove(file_to_delete)
            deleted_count += 1
        except Exception as e:
            print(f"  ⚠️ No s'ha pogut esborrar {f}: {e}")

    print(f"✨ Neteja completada. S'han eliminat {deleted_count} fitxers.")


def generate_daily_png(data, lon, lat, date_str):
    fig = plt.figure(frameon=False)
    # Mantenim l'aspecte segons la mida de la matriu de dades
    fig.set_size_inches(data.shape[1]/100, data.shape[0]/100)

    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)

    # El rang de colors per a un dia sencer sol ser millor fins a 100-200mm
    norm = colors.LogNorm(vmin=0.1, vmax=200)
    cmap = plt.get_cmap('turbo').copy()
    cmap.set_under(alpha=0) # Transparent per a zones sense pluja significativa

    ax.pcolormesh(lon.values, lat.values, data.values,
                  cmap=cmap, norm=norm, shading='auto')

    png_out_path = os.path.join(DAILY_DIR, f"acumulat_{date_str}.png")
    fig.savefig(png_out_path, transparent=True, dpi=100)
    plt.close(fig)
    print(f"🎨 PNG logarítmic guardat: {png_out_path}")

    # Actualitzar bounds.json per si hi ha hagut canvis en la graella
    bounds_data = {
        "lat_min": float(lat.min()),
        "lat_max": float(lat.max()),
        "lon_min": float(lon.min()),
        "lon_max": float(lon.max())
    }

    with open("bounds.json", "w") as f:
        json.dump(bounds_data, f)
    print(f"📍 Coordenades guardades a bounds.json")

def save_stations_geojson(dades, path):
    """Genera un fitxer GeoJSON a partir de les dades de les estacions"""
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    for d in dades:
        # Filtre opcional: només estacions que hagin marcat pluja (>0)
        # Si vols totes, treu el "if d['pluja'] > 0:"
        if d['pluja'] >= 0.1:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [d['lon'], d['lat']]
                },
                "properties": {
                    "codi": d['codi'],
                    "nom": d['nom'],
                    "pluja": d['pluja'],
                    "data": d['data']
                }
            }
            geojson["features"].append(feature)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False)

if __name__ == "__main__":
    calculate_daily()










