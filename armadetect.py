
from ultralytics import YOLO
import cv2, time, datetime
import math
import time
import json, rospy
from std_msgs.msg import String

classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
              "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
              "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
              "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
              "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
              "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
              "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
              "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
              "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
              "teddy bear", "hair drier", "toothbrush"
              ]

#mask = cv2.imread("maske.jpg")
kumanda_aralik = 10
# Tracking


prev_frame_time = 0
new_frame_time = 0

#cap = cv2.VideoCapture(0)  # For Webcam
#cap.set(3, 1280)
#cap.set(4, 720)

cap = cv2.VideoCapture(0)
#cap = cv2.VideoCapture("udp://192.168.6.101:8283", cv2.CAP_FFMPEG)
# video kayıt için fourcc ve VideoWriter tanımlama
#cv2_fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#success, img = cap.read()
# print(img.shape)
# cv2.imwrite("ornek_resim.jpg", img)
#size = list(img.shape)
#del size[2]
#size.reverse()
#video = cv2.VideoWriter("kaydedilen_video.mp4", cv2_fourcc, 24, size) #output video name, fourcc, fps, size

tracking = False
kilitlenme = False
kilitlenme_sayisi = 0
csrt = cv2.TrackerCSRT_create()
#csrt = cv2.TrackerGOTURN_create()
#csrt = cv2.TrackerKCF_create()
model = YOLO("yolov8n.pt")
#model = YOLO('keremberke/yolov8m-plane-detection.pt')
def callback_gonder(data):
    global otonommu
    veri = json.loads(data.data)
    if veri["iha_otonom"] == 1:
        otonommu = 1
    else:
        otonommu = 0

def callback_saat(data):
    global sunucu_saati, sunucu_saat, sunucu_dakika, sunucu_saniye, sunucu_milisaniye
    sunucu_saati = json.loads(data.data)
    sunucu_saat=sunucu_saati["saat"]
    sunucu_dakika=sunucu_saati["dakika"]
    sunucu_saniye=sunucu_saati["saniye"]
    sunucu_milisaniye=sunucu_saati["milisaniye"]

while True:
    rospy.init_node("publisher", anonymous=True)
    rospy.Subscriber("/uav/gonder", String, callback_gonder)
    rospy.Subscriber("/uav/sunucu_saati", String, callback_saat)
    new_frame_time = time.time()
    success, img = cap.read()
    #img = cv2.resize(img, (1280, 720))
    results = model(img, stream=True)
    time_str = f"{sunucu_saat}:{sunucu_dakika}:{sunucu_saniye}.{sunucu_milisaniye}"
    cv2.putText(img, time_str, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.rectangle(img, (int(img.shape[1] / 4), int(img.shape[0] / 10)),
                  (int(3 * img.shape[1] / 4), int(9 * img.shape[0] / 10)), (61, 217, 255), 3)
    cv2.rectangle(img, (0, 0), (int(img.shape[1]), int(img.shape[0])), (0, 153, 76), 4)
    for r in results:
        boxes = r.boxes
        for box in boxes:
            # Bounding Box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            # cv2.rectangle(img,(x1,y1),(x2,y2),(255,0,255),3)
            w, h = x2 - x1, y2 - y1
            # Confidence
            conf = math.ceil((box.conf[0] * 100)) / 100
            # Class Name
            cls = int(box.cls[0])
            currentClass = classNames[cls]
            if currentClass == "aeroplane" or currentClass == "bird" or currentClass == "kite" and conf > 0.3:
                print("Takip Basladi")
                if w < (int(img.shape[1])*45 / 100) and h < (int(img.shape[0])*45 / 100):
                    tracking = True
                    ok = csrt.init(img, (x1, y1, w, h))
                    start_time = time.time()
                else:
                    tracking = False
                    print("Hedef Cok Buyuk!")
    if tracking:
        ok, bbox = csrt.update(img)
        if ok:
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(img, p1, p2, (0, 0, 255), 2, 1)
            cv2.line(img, (int(img.shape[1] / 2), int(img.shape[0] / 2)),
                    (int(bbox[0] + bbox[2] / 2), int(bbox[1] + bbox[3] / 2)), (255, 255, 255), 2)
            sunucu_veri = {
                "iha_kilitlenme": 1,
                "hedef_merkez_X": int(bbox[0] + bbox[2] / 2),
                "hedef_merkez_Y": int(bbox[1] + bbox[3] / 2),
                "hedef_genislik": bbox[2],
                "hedef_yukseklik": bbox[3],
            }
            gonder_tespit = json.dumps(sunucu_veri)
            msg1 = String()
            msg1.data = gonder_tespit
            pub1 = rospy.Publisher('/uav/tespit', String, queue_size=10)
            pub1.publish(msg1)

            horizantal_difference = int(bbox[0] + bbox[2] / 2) - int(img.shape[1] / 2)
            vertical_difference = int(bbox[1] + bbox[3] / 2) - int(img.shape[0] / 2)
            yonelim_veri = {
                "horizontal_x": horizantal_difference/kumanda_aralik,
                "vertical_y": -vertical_difference/kumanda_aralik,
            }
            gonder_yonelim = json.dumps(yonelim_veri)
            msg2 = String()
            msg2.data = gonder_yonelim
            pub2 = rospy.Publisher('/uav/yonelim', String, queue_size=10)
            pub2.publish(msg2)

            #ICERDE OLUP OLADIGININ KONTROLU
            if int(img.shape[1] / 4)< bbox[0] and int(img.shape[0] / 10) < bbox[1] and bbox[0]+bbox[2] < (3*int(img.shape[1] / 4)) and bbox[1]+bbox[3] < int(9 * img.shape[0] / 10):
                text = "ICERIDE"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 2)[0]
                text_x = int((img.shape[1] - text_size[0]) / 2)
                text_y = int((img.shape[0] - text_size[1]) / 2) + int(9 * img.shape[0] / 20)-50
                cv2.putText(img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 220, 0), 2, cv2.LINE_AA, False)
                #%6'dan büyükse kilitlenme başlıyor

                if bbox[2] > (int(img.shape[1])*6 / 100) or bbox[3] > (int(img.shape[0])*6 / 100):
                    print("Kilitlenme basladi.")
                    utc_time = datetime.datetime.utcnow()
                    ssaat, sdakika, ssaniye = utc_time.hour, utc_time.minute, utc_time.second
                    smilisaaniye = utc_time.microsecond / 1000

                    if kilitlenme:
                        kilitlenme_suresi = time.time() - kilitlenme_baslangic
                        print("Kilitlenme suresi:", kilitlenme_suresi)
                        text = str(round(kilitlenme_suresi, 2))
                        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                        text_x = int((img.shape[1] - text_size[0]) / 2)
                        text_y = int((img.shape[0] - text_size[1]) / 4)-50
                        cv2.putText(img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                        if kilitlenme_suresi > 4:
                            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                            text_x = int((img.shape[1] - text_size[0]) / 2)
                            text_y = int((img.shape[0] - text_size[1]) / 4)
                            cv2.putText(img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                            text = "KILITLENME BASARILI!"
                            utc_time = datetime.datetime.utcnow()
                            fsaat, fdakika, fsaniye = utc_time.hour, utc_time.minute, utc_time.second
                            fmilisaaniye = utc_time.microsecond / 1000
                            kilitlenme_veri = {
                                "kilitlenmeBaslangicZamani": {
                                    "saat": ssaat,
                                    "dakika": sdakika,
                                    "saniye": ssaniye,
                                    "milisaniye": smilisaaniye
                                },
                                "kilitlenmeBitisZamani": {
                                    "saat": fsaat,
                                    "dakika": fdakika,
                                    "saniye": fsaniye,
                                    "milisaniye": fmilisaaniye
                                },
                                "otonom_kilitlenme": otonommu,
                            }
                            gonder_kilitlenme = json.dumps(kilitlenme_veri)
                            msg3 = String()
                            msg3.data = gonder_kilitlenme
                            pub3 = rospy.Publisher('/uav/kilitlenme_veri', String, queue_size=10)
                            pub3.publish(msg3)
                            kilitlenme = False
                            kilitlenme_suresi = 0
                            kilitlenme_baslangic = 0
                            kilitlenme_sayisi+=1

                    if not kilitlenme:
                        kilitlenme = True
                        kilitlenme_suresi = 0
                        kilitlenme_baslangic = time.time()
                else:
                    kilitlenme = False
                    kilitlenme_suresi = 0
                    kilitlenme_baslangic = 0
            else:
                print("dışarda")
                text = "DISARIDA"
                kilitlenme = False
                kilitlenme_suresi = 0
                kilitlenme_baslangic = 0
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 2)[0]
                text_x = int((img.shape[1] - text_size[0]) / 2)
                text_y = int((img.shape[0] - text_size[1]) / 2) + int(9 * img.shape[0] / 20)-50
                cv2.putText(img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 200), 2, cv2.LINE_AA, False)


            cv2.circle(img, (int(img.shape[1] / 2), int(img.shape[0] / 2)), 3, (0, 0, 0), 2)
            cv2.circle(img, (int(bbox[0] + bbox[2] / 2), int(bbox[1] + bbox[3] / 2)), 3, (0, 0, 255), 2)

        gecen_sure = time.time() - start_time
        gecen_sure = time.time() - start_time
        if gecen_sure > 3:
            tracking = False
            print("Takip Bitti")
    if not tracking:
        kilitlenme = False
        kilitlenme_suresi = 0
        kilitlenme_baslangic = 0
        sunucu_veri = {
                "iha_kilitlenme": 0,
                "hedef_merkez_X": 0,
                "hedef_merkez_Y": 0,
                "hedef_genislik": 0,
                "hedef_yukseklik": 0
            }
        gonder_tespit = json.dumps(sunucu_veri)
        msg1 = String()
        msg1.data = gonder_tespit
        pub1 = rospy.Publisher('/uav/tespit', String, queue_size=10)
        pub1.publish(msg1)
        
    #print(x1,y1,w,h)
    # video kayıt
    #video.write(img)
    fps = 1 / (new_frame_time - prev_frame_time)
    prev_frame_time = new_frame_time
    print("fps: ", fps)
    cv2.putText(img, "FPS : " + str(int(fps)), (25,25), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (61,217,255), 2);
    cv2.putText(img, "Kilitlenme Sayisi : " + str(int(kilitlenme_sayisi)), (25,50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (64,217,255), 2);
    cv2.imshow("Image", img)
    # cv2.imshow("ImageRegion", imgRegion)
    cv2.waitKey(1)

video.release()
