from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import psycopg2

app = FastAPI(title="API - Sistema Veicular")

# Configurações do banco
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "user": "postgres",
    "password": "admin123",  # sua senha aqui
    "database": "sistema_veicular"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# Modelo de dados
class Leitura(BaseModel):
    placa: str

@app.post("/leituras")
def registrar_leitura(leitura: Leitura):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO leituras (placa) VALUES (%s)", (leitura.placa,))
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
