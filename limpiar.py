import csv
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    return webdriver.Chrome(options=options)


def clean_text(text):
    """
    Normaliza y limpia un texto: elimina caracteres especiales, 
    convierte a minúsculas y elimina espacios extras.
    """
    text = text.lower()
    text = re.sub(r"[^a-záéíóúüñ0-9\s]", "", text)  # Mantiene letras, números y espacios
    text = re.sub(r"\s+", " ", text).strip()  # Elimina espacios extra
    return text


def extract_comments(driver, video_url, max_comments=10):
    driver.get(video_url)
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    comments_data = []
    last_height = driver.execute_script("return document.documentElement.scrollHeight")

    while len(comments_data) < max_comments:
        print(f"🔄 Scroll para cargar más comentarios... ({len(comments_data)}/{max_comments})")

        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(2)

        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            print("✅ Fin de los comentarios cargados.")
            break
        last_height = new_height

        comments_elements = driver.find_elements(By.ID, "content-text")

        for i in range(len(comments_elements)):
            if len(comments_data) >= max_comments:
                break

            comment_text = comments_elements[i].text.strip()

            # Normalizar texto del comentario
            normalized_comment = clean_text(comment_text)

            comments_data.append(normalized_comment)

    return comments_data


def main():
    search_query = input("Introduce el término de búsqueda para YouTube: ").strip()
    max_results = 5  # Número de videos a analizar
    max_comments = 10  # Número de comentarios por video
    all_comments = []

    driver = setup_driver()

    try:
        # Buscar videos en YouTube con el término de búsqueda
        print(f"🔍 Buscando videos con el término: {search_query}")
        driver.get("https://www.youtube.com/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "search_query")))

        search_box = driver.find_element(By.NAME, "search_query")
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)

        # Esperar a que se carguen los resultados de búsqueda
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "video-title")))
        video_elements = driver.find_elements(By.ID, "video-title")[:max_results]

        video_urls = [video.get_attribute("href") for video in video_elements]
        print(f"📝 Videos encontrados: {video_urls}")

        # Extraer comentarios de cada video encontrado
        for url in video_urls:
            print(f"📥 Extrayendo hasta {max_comments} comentarios de: {url}")
            comments = extract_comments(driver, url, max_comments)
            all_comments.extend(comments)
            print(f"✅ Total comentarios extraídos de {url}: {len(comments)}")

    finally:
        driver.quit()

    # CREACIÓN Y GUARDADO DE DATASET
    output_file = "limpo.csv"
    with open(output_file, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["comment"])  # Cabecera
        for comment in all_comments:
            writer.writerow([comment])

    print(f"🎉 Extracción completada. Todos los comentarios guardados en {output_file}")


if __name__ == "__main__":
    main()
