import requests
import json
import time

# --- Configuración ---
API_URLS = {
    'channels': 'https://iptv-org.github.io/api/channels.json',
    'streams': 'https://iptv-org.github.io/api/streams.json',
    'logos': 'https://iptv-org.github.io/api/logos.json'
}
OUTPUT_FILE = 'playlist.m3u8'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'

# --- Funciones de Ayuda ---

def fetch_json(url):
    """Descarga un archivo JSON desde una URL."""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Lanza un error si la petición falla
        return response.json()
    except requests.RequestException as e:
        print(f"Error descargando {url}: {e}")
        return None

def process_data(channels, streams, logos):
    """Procesa los datos JSON y los combina."""
    
    # 1. Crear diccionarios (mapas) para acceso rápido.
    # Esto es mucho más rápido que buscar en las listas una y otra vez.
    
    # Mapa de streams: { channel_id: stream_url }
    # Damos prioridad a los streams que SÍ tienen 'channel' definido
    streams_map = {}
    for stream in streams:
        channel_id = stream.get('channel')
        stream_url = stream.get('url')
        if channel_id and stream_url and channel_id not in streams_map:
            streams_map[channel_id] = stream_url
            
    # Mapa de logos: { channel_id: logo_url }
    logos_map = {}
    for logo in logos:
        channel_id = logo.get('channel')
        logo_url = logo.get('url')
        if channel_id and logo_url and channel_id not in logos_map:
            logos_map[channel_id] = logo_url

    # 2. Construir la lista de canales final
    processed_channels = []
    for channel in channels:
        channel_id = channel.get('id')
        stream_url = streams_map.get(channel_id)
        
        # --- ¡IMPORTANTE! ---
        # Solo incluimos el canal si encontramos un stream para él.
        if not stream_url:
            continue
            
        # Obtener el nombre
        channel_name = channel.get('name', 'Nombre Desconocido')
        
        # Obtener el logo
        logo_url = logos_map.get(channel_id, '') # Logo vacío si no se encuentra
        
        # Obtener la categoría (para 'group-title')
        categories = channel.get('categories', [])
        group_title = categories[0] if categories else 'Sin Categoría'
        
        processed_channels.append({
            'id': channel_id,
            'name': channel_name,
            'logo': logo_url,
            'group': group_title.capitalize(), # Pone la primera letra en mayúscula
            'url': stream_url
        })
        
    return processed_channels

def generate_m3u_file(channels):
    """Genera el contenido del archivo M3U8."""
    
    # Encabezado estándar de un archivo M3U
    m3u_content = ["#EXTM3U"]
    
    # Ordenar canales por nombre para que la lista sea fácil de navegar
    channels.sort(key=lambda x: x['name'])
    
    # Añadir cada canal al archivo
    for channel in channels:
        # Formato: #EXTINF:-1 tvg-id="ID" tvg-logo="URL_LOGO" group-title="GRUPO",NOMBRE_CANAL
        extinf_line = f'#EXTINF:-1 tvg-id="{channel["id"]}" tvg-logo="{channel["logo"]}" group-title="{channel["group"]}",{channel["name"]}'
        
        m3u_content.append(extinf_line)
        m3u_content.append(channel['url']) # La URL del stream en la siguiente línea
        
    # Unir todo con saltos de línea
    return "\n".join(m3u_content)

# --- Ejecución Principal ---

def main():
    print("Iniciando la generación de la lista M3U8...")
    start_time = time.time()
    
    print("Descargando datos de la API...")
    channels_data = fetch_json(API_URLS['channels'])
    streams_data = fetch_json(API_URLS['streams'])
    logos_data = fetch_json(API_URLS['logos'])
    
    if not all([channels_data, streams_data, logos_data]):
        print("Error: No se pudieron descargar todos los archivos de la API. Abortando.")
        return

    print("Datos descargados. Procesando y combinando...")
    processed_channels = process_data(channels_data, streams_data, logos_data)
    
    if not processed_channels:
        print("Error: No se pudo procesar ningún canal con stream válido.")
        return

    print(f"Se procesaron {len(processed_channels)} canales con streams válidos.")
    
    print("Generando archivo M3U8...")
    m3u_content = generate_m3u_file(processed_channels)
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print(f"¡Éxito! Archivo guardado como '{OUTPUT_FILE}'")
    except IOError as e:
        print(f"Error al escribir el archivo: {e}")

    end_time = time.time()
    print(f"Proceso completado en {end_time - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()
