from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from fastapi.responses import Response
import psycopg2
import base64
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="API - Sistema Veicular")

# Configuração do banco
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "user": "postgres",
    "password": "admin123",  # altere se necessário
    "database": "sistema_veicular"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# Modelo de dados
class Leitura(BaseModel):
    placa: str
    imagem_base64: str | None = None  # imagem opcional

@app.post("/leituras")
def registrar_leitura(leitura: Leitura):
    conn = get_connection()
    cur = conn.cursor()

    imagem_bytes = None
    if leitura.imagem_base64:
        imagem_bytes = base64.b64decode(leitura.imagem_base64)

    cur.execute(
        "INSERT INTO leituras (placa, imagem) VALUES (%s, %s)",
        (leitura.placa, imagem_bytes)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "ok", "placa": leitura.placa, "data": datetime.now()}

@app.get("/leituras")
def listar_leituras():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, placa, data_hora FROM leituras ORDER BY data_hora DESC")
    dados = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": d[0], "placa": d[1], "data_hora": d[2]} for d in dados]

# 🔹 Rota para retornar a imagem armazenada no banco
@app.get("/imagem/{id}")
def get_imagem(id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT imagem FROM leituras WHERE id = %s", (id,))
    imagem = cur.fetchone()
    cur.close()
    conn.close()

    if imagem and imagem[0]:
        return Response(content=bytes(imagem[0]), media_type="image/jpeg")
    else:
        raise HTTPException(status_code=404, detail="Imagem não encontrada")

# 🔹 Monta o dashboard web na raiz do servidor
app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")
