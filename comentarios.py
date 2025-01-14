import os
import praw
import pandas as pd
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

client_id = os.getenv("REDDIT_CLIENT_ID")
client_secret = os.getenv("REDDIT_CLIENT_SECRET")
user_agent = os.getenv("REDDIT_USER_AGENT")

reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent, 
)

print(f"Autenticado como: {reddit.user.me()}")

search_terms = ['Temu']

comments_data = []

for submission in reddit.subreddit('all').search(' '.join(search_terms), limit=10):
    print(f"Buscando en: {submission.title}")
    submission.comments.replace_more(limit=0)  # Evita el truncamiento de comentarios

    # Extraer comentarios
    for comment in submission.comments.list():
        # Usamos BeautifulSoup para asegurarnos de que los comentarios se limpien correctamente (en caso de HTML malformado)
        soup = BeautifulSoup(comment.body, 'html.parser')
        clean_comment = soup.get_text()
        
        # Agregar los datos de cada comentario a la lista
        comments_data.append({
            'Comment': clean_comment
        })

# Crear un DataFrame de Pandas para los comentarios
df = pd.DataFrame(comments_data)

# Guardar los datos en un archivo CSV
df.to_csv('controversial_comments.csv', index=False)

# Mostrar la tabla en formato legible
print(df.head())  # Mostrar las primeras filas