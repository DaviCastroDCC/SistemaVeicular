import cv2
import pytesseract
import numpy as np
import requests
import base64

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
API_URL = "http://127.0.0.1:8000/leituras"

def detect_plate(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(blur, 30, 200)

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

    mask = np.zeros(gray.shape, np.uint8)
    new_image = cv2.drawContours(mask, [plate_contour], 0, 255, -1)
    new_image = cv2.bitwise_and(frame, frame, mask=mask)

    (x, y) = np.where(mask == 255)
    (x1, y1) = (np.min(x), np.min(y))
    (x2, y2) = (np.max(x), np.max(y))
    cropped = gray[x1:x2+1, y1:y2+1]

    return new_image, cropped

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
            text = pytesseract.image_to_string(plate, config='--psm 8').strip()
            print("🪪 Placa detectada:", text)

            # Converte imagem da placa para Base64
            _, buffer = cv2.imencode('.jpg', plate)
            imagem_base64 = base64.b64encode(buffer).decode('utf-8')

            # Envia para a API
            try:
                resp = requests.post(API_URL, json={
                    "placa": text,
                    "imagem_base64": imagem_base64
                })
                if resp.status_code == 200:
                    print("✅ Enviado para API com sucesso!")
                else:
                    print("⚠️ Erro ao enviar para API:", resp.text)
            except Exception as e:
                print("❌ Falha ao conectar na API:", e)
        else:
            print("❌ Nenhuma placa detectada.")
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
