import cv2
import pytesseract
import numpy as np
import requests  # 🔹 novo: envia dados para a API

# Caminho do executável do Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# URL da API local (ajuste se rodar em outro PC/servidor)
API_URL = "http://127.0.0.1:8000/leituras"

# Função para processar e detectar a placa
def detect_plate(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(blur, 30, 200)

    # Encontra contornos na imagem
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    plate_contour = None

    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * peri, True)
        if len(approx) == 4:
            plate_contour = approx
            break

    if plate_contour is None:
        return frame, None

    # Cria máscara da região da placa
    mask = np.zeros(gray.shape, np.uint8)
    new_image = cv2.drawContours(mask, [plate_contour], 0, 255, -1)
    new_image = cv2.bitwise_and(frame, frame, mask=mask)

    # Recorta a área da placa
    (x, y) = np.where(mask == 255)
    (x1, y1) = (np.min(x), np.min(y))
    (x2, y2) = (np.max(x), np.max(y))
    cropped = gray[x1:x2+1, y1:y2+1]

    return new_image, cropped

# Inicia a câmera
cap = cv2.VideoCapture(0)

print("✅ Sistema iniciado! Pressione 'S' para tentar ler a placa, 'Q' para sair.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Camera - Sistema Veicular", frame)
    key = cv2.waitKey(1)

    if key == ord('s'):
        processed_frame, plate = detect_plate(frame)
        if plate is not None:
            # 🔹 pré-processa pra OCR mais limpo
            plate_gray = cv2.bilateralFilter(plate, 11, 17, 17)
            _, plate_thresh = cv2.threshold(plate_gray, 150, 255, cv2.THRESH_BINARY)
            config = "--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            text = pytesseract.image_to_string(plate_thresh, config=config).strip()

            if text:
                print("🪪 Placa detectada:", text)
                cv2.imshow("Placa Detectada", plate_thresh)

                # 🔹 envia para a API FastAPI
                try:
                    response = requests.post(API_URL, json={"placa": text})
                    if response.status_code == 200:
                        print("📡 Placa registrada no servidor com sucesso!")
                    else:
                        print("⚠️ Erro ao registrar placa:", response.text)
                except Exception as e:
                    print("❌ Falha ao conectar com a API:", e)
            else:
                print("❌ Nenhum texto legível detectado.")
        else:
            print("❌ Nenhuma placa detectada. Tente ajustar o ângulo/iluminação.")

    if key == ord('q'):
        print("🛑 Encerrando...")
        break

cap.release()
cv2.destroyAllWindows()
