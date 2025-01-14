from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import requests
import pandas as pd
import logging
import uvicorn


# Configuración del logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

# Lista global para almacenar comentarios extraídos de múltiples videos
all_comments = []

# Función para configurar los encabezados de las solicitudes
def set_headers(videoid):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
        'referer': f'https://www.tiktok.com/@x/video/{videoid}',
    }
    return headers

# Función para extraer respuestas de un comentario
def extract_replies(videoid, comment_id, headers, cursor):
    try:
        response = requests.get(
            f"https://www.tiktok.com/api/comment/list/reply/?aweme_id={videoid}&comment_id={comment_id}&count=20&cursor={cursor}",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error al extraer respuestas: {e}")
        return {"comments": []}

# Función principal para extraer comentarios de un video de TikTok
def tiktok_extract_comments(video_url):
    global all_comments

    # Obtener el ID del video
    if "vm.tiktok.com" in video_url or "vt.tiktok.com" in video_url:
        video_url = requests.head(video_url, allow_redirects=True).url
    videoid = video_url.split("/")[5].split("?", 1)[0]

    cursor = 0
    headers = set_headers(videoid)
    total_comments = 0

    while True:
        try:
            # Realizar solicitud a la API de TikTok
            response = requests.get(
                f"https://www.tiktok.com/api/comment/list/?aid=1988&aweme_id={videoid}&count=20&cursor={cursor}",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            comments = data.get("comments")
            if not comments:
                logging.info(f"No hay más comentarios para extraer del video {videoid}.")
                break

            # Procesar comentarios
            for comment in comments:
                parent_comment = comment.get('text', '')
                all_comments.append(parent_comment)  # Guardar solo el texto del comentario
                total_comments += 1

                # Extraer respuestas si existen
                reply_count = comment.get('reply_comment_total', 0)
                if reply_count > 0:
                    comment_id = comment["cid"]
                    replies = extract_replies(videoid, comment_id, headers, cursor)
                    for reply in replies.get("comments", []):
                        reply_text = reply.get('text', '')
                        all_comments.append(reply_text)  # Guardar solo el texto de la respuesta
                        total_comments += 1

            cursor += len(comments)

        except Exception as e:
            logging.error(f"Error durante la extracción del video {videoid}: {e}")
            break

    logging.info(f"Extracción completada para el video {videoid}. Total de comentarios: {total_comments}.")
    return total_comments

# Rutas de la API
@app.post("/extract")
async def extract_comments(video_url: str):
    """
    Ruta para extraer comentarios de un video de TikTok y guardarlos temporalmente.
    """
    if not video_url:
        raise HTTPException(status_code=400, detail="Se requiere una URL de video.")
    
    total_comments = tiktok_extract_comments(video_url)
    return {"message": f"Comentarios extraídos del video. Total: {total_comments}"}

@app.get("/comments")
async def get_comments():
    """
    Ruta para obtener un archivo CSV con todos los comentarios acumulados.
    """
    if not all_comments:
        raise HTTPException(status_code=404, detail="No hay comentarios extraídos hasta ahora.")

    # Crear un DataFrame y guardar solo los comentarios en un archivo CSV
    output_file = "comentarios_acumulados.csv"
    df = pd.DataFrame(all_comments, columns=["comentario"])
    df.to_csv(output_file, index=False)

    logging.info(f"Archivo CSV generado: {output_file}")
    return FileResponse(output_file, media_type="text/csv", filename="comentarios_acumulados.csv")

@app.get("/")
async def redirect_to_docs():
    """
    Redirige a la documentación interactiva de la API.
    """
    return RedirectResponse("/docs")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
