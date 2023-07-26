import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar
cap = cv2.VideoCapture(0)

while True:
    _, frame = cap.read()
    decodedObjects = pyzbar.decode(frame)

    # Kare içinde QR kodunu çerçeveleme
    if len(decodedObjects) > 0:
        # İlk QR kodunu çerçevele
        rect = decodedObjects[0].rect
        cv2.rectangle(frame, (rect.left, rect.top), (rect.left + rect.width, rect.top + rect.height), (0, 0, 255), thickness=2)

    for obj in decodedObjects:
        print("QR kodu tespit edildi!")
        decoded_text = obj.data.decode('utf-8') # byte dizisini string'e dönüştürme
        print("Metin: ", decoded_text)
        cv2.putText(frame, decoded_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        #tahminler = json.dumps(tahminler)
        #msg = String()
        #msg.data = tahminler
        #pub = rospy.Publisher('/uav/poztahmin', String, queue_size=10)
        #pub.publish(msg)
    cv2.imshow("QR kodu okuyucu", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()