import cv2
import pytesseract
import requests
import base64
import numpy as np
from ultralytics import YOLO
from datetime import datetime

# Caminho do Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# URL da API FastAPI
API_URL = "http://127.0.0.1:8000/leituras"

# Carrega o modelo YOLOv8 (pré-treinado)
model = YOLO('yolo_models/yolov8n.pt')

# Inicializa câmera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Erro ao abrir a câmera!")
    exit()

print("✅ Sistema IA iniciado! Pressione 'Q' para sair.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Reduz tamanho para melhor desempenho
    resized = cv2.resize(frame, (640, 480))

    # Detecção YOLO
    results = model(resized)

    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()  # coordenadas [x1, y1, x2, y2]
        classes = result.boxes.cls.cpu().numpy()  # classe detectada
        names = result.names  # nomes das classes

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box)
            label = names[int(classes[i])]

            # Exibir retângulo e rótulo
            cv2.rectangle(resized, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(resized, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Se o objeto for "car", "truck" ou "bus", tentamos extrair a placa
            if label in ["car", "truck", "bus", "motorcycle"]:
                cropped = resized[y1:y2, x1:x2]

                # Converte para tons de cinza e faz OCR
                gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
                text = pytesseract.image_to_string(gray, config='--psm 8').strip()

                if len(text) > 2:  # só envia se tiver algo legível
                    print(f"🪪 Placa detectada: {text} ({label})")

                    # Converte imagem para base64
                    _, buffer = cv2.imencode('.jpg', cropped)
                    imagem_base64 = base64.b64encode(buffer).decode('utf-8')

                    # Envia para API
                    try:
                        resp = requests.post(API_URL, json={
                            "placa": text,
                            "imagem_base64": imagem_base64
                        })
                        if resp.status_code == 200:
                            print("✅ Enviado para API com sucesso!")
                        else:
                            print("⚠️ Erro ao enviar:", resp.text)
                    except Exception as e:
                        print("❌ Falha na comunicação com a API:", e)

    # Mostra na tela
    cv2.imshow("YOLOv8 - Sistema Veicular Inteligente", resized)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("🛑 Encerrando detecção...")
        break

cap.release()
cv2.destroyAllWindows()
