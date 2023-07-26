import cv2
import numpy as np
import math
from math import sqrt
import datetime
import time, requests, json
import json, rospy
from std_msgs.msg import String
#cap = cv2.VideoCapture("deneme.mp4")
#cap = cv2.VideoCapture(0)
cap = cv2.VideoCapture("udp://192.168.6.101:8283", cv2.CAP_FFMPEG)
classesFile = 'model/classes.txt'

a = 0
distance = 0
whT = 320
classNames = []
confThreshold = 0.5
nmsThreshold = 0.3

kumanda_aralık=10
with open(classesFile, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')
#modelConfiguration = 'yolov3_testing.cfg'
#modelWeigts = 'sihax.weights'

#net = cv2.dnn.readNet("sihax.weights", "yolov3_testing.cfg")


#net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
#net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
modelConfiguration = 'model/yolov4-obj.cfg'
modelWeigts = 'model/yolov4-obj_last.weights'
net = cv2.dnn.readNetFromDarknet(modelConfiguration,modelWeigts)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
#tracker = cv2.TrackerGOTURN_create()
tracker = cv2.TrackerCSRT_create()
#tracker = cv2.TrackerKCF_create()


bbox = (0, 0, 0, 0)
otonommu = 1
goturn= False
kilitlenme = False
kilitlenme_saiyisi = 0

camera_height = 1.7
camera_fov = 62.2 * math.pi / 180  # Radyan cinsinden



def findObjects(outputs, img):
    hT, wT, cT = img.shape
    bbox = []
    classIds = []
    confs = []

    for output in outputs:
        for det in output:
            scores = det[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if confidence > confThreshold:
                w, h = int(det[2] * wT), int(det[3] * hT)
                x, y = int((det[0] * wT) - w / 2), int((det[1] * hT) - h / 2)
                bbox.append([x, y, w, h])
                classIds.append(classId)
                confs.append(float(confidence))
    print(len(bbox))
    indices = cv2.dnn.NMSBoxes(bbox, confs, confThreshold, nmsThreshold)
    for i in indices:
        i = i
        box = bbox[i]
        x, y, w, h = box[0], box[1], box[2], box[3]

        #cv2.rectangle(img, (x, y), (x + w, y + h), (25, 50, 255), 2)
        #cv2.putText(img, f'{classNames[classIds[i]].upper()} {int(confs[i] * 100)}%',
        #            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 50, 255), 2)

        return x, y, w, h
def callback_gonder(data):
    global otonommu
    veri = json.loads(data.data)
    if veri["IHA_otonom"] == 1:
        otonommu = 1
    else:
        otonommu = 0
while True:
    rospy.init_node("publisher", anonymous=True)
    rospy.Subscriber("/uav0/gonder", String, callback_gonder)
    success, img = cap.read()
    img = cv2.resize(img, (1280, 720))
    gray_video = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blob = cv2.dnn.blobFromImage(img, 1 / 255, (whT, whT), [0, 0, 0], 1, crop=False)
    net.setInput(blob)
    layerNames = net.getLayerNames()
    outputNames = [layerNames[i - 1] for i in net.getUnconnectedOutLayers()]
    timer = cv2.getTickCount()

    cv2.rectangle(img, (int(img.shape[1] / 4), int(img.shape[0] / 10)),
                  (int(3 * img.shape[1] / 4), int(9 * img.shape[0] / 10)), (61, 217, 255), 3)
    cv2.rectangle(img, (0, 0), (int(img.shape[1]), int(img.shape[0])), (0, 153, 76), 4)
    # cv2.circle(img,(int (img.shape[1]/2),int (img.shape[0]/2)))
    #cv2.putText(img, "AK : Kamera Gorus Alani", (10, int(img.shape[0]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 0),
    #            2, cv2.LINE_AA, False)
    #cv2.putText(img, "Av : Hedef Vurus Alani", (int(img.shape[1] / 4) + 5, int(9 * img.shape[0] / 10) - 10),
    #            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 200), 2, cv2.LINE_AA, False)
    outputs = net.forward(outputNames)
    findObjects(outputs, img)
    returner = findObjects(outputs, img)

    print(returner)
    if returner is not None:
        ok = tracker.init(img, returner)
        start_time = time.time()
        print("Takip Basladi")
        goturn = True

    if goturn:
        ok, bbox = tracker.update(img)
        if ok:
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(img, p1, p2, (25,50,255), 3, 1)
            cv2.line(img, (int(img.shape[1] / 2), int(img.shape[0] / 2)),
                    (int(bbox[0] + bbox[2] / 2), int(bbox[1] + bbox[3] / 2)), (255, 255, 255), 2)
            roi_img = img[bbox[1]:bbox[1] + bbox[3], bbox[0]:bbox[0] + bbox[2]]
            # Gerçek boyut (metre cinsinden)
            gercek_boyut = 1.7
            # Kamera çözünürlüğü
            kamera_cozunurlugu = (1280, 720)
            # Yatay açı (horizontal angle)
            yatay_aci = 62.2 # Raspberry Pi kamera için yatay açı
            # Dikey açı (vertical angle)
            dikey_aci = 48.8 # Raspberry Pi kamera için dikey açı
            # Yatay piksel sayısı
            yatay_piksel = kamera_cozunurlugu[0]
            # Dikey piksel sayısı
            dikey_piksel = kamera_cozunurlugu[1]
            # Nesne genişliği (piksel cinsinden)
            nesne_genisligi = bbox[2]
            # Yatay açının yarısı (radyan cinsinden)
            yatay_aci_yarisi = math.radians(yatay_aci / 2)
            # Kamera odak uzaklığı (milimetre cinsinden)
            odak_uzakligi = 3.04 # Raspberry Pi kamera için odak uzaklığı
            # Nesnenin yatay açısal boyutu (radyan cinsinden)
            nesne_yatay_aci = 2 * math.atan((nesne_genisligi / 2) / yatay_piksel * math.tan(yatay_aci_yarisi))
            # Nesne uzaklığı (metre cinsinden)
            nesne_uzakligi = gercek_boyut / (2 * nesne_genisligi / yatay_piksel * math.tan(yatay_aci_yarisi))
            # Kamera açısal çözünürlüğü (radyan cinsinden)
            kamera_aci_cozunurlugu = (math.radians(yatay_aci), math.radians(dikey_aci))
            # Kamera piksel boyutu (metre cinsinden)
            kamera_piksel_boyutu = (math.tan(kamera_aci_cozunurlugu[0] / 2) * nesne_uzakligi * 2 / yatay_piksel, math.tan(kamera_aci_cozunurlugu[1] / 2) * nesne_uzakligi * 2 / dikey_piksel)
            # Nesne boyutu (metre cinsinden)
            nesne_boyutu_metre = (bbox[2] * kamera_piksel_boyutu[0], bbox[3] * kamera_piksel_boyutu[1])

            sunucu_veri = {
                "IHA_kilitlenme": 1,
                "Hedef_merkez_X": int(bbox[0] + bbox[2] / 2),
                "Hedef_merkez_Y": int(bbox[1] + bbox[3] / 2),
                "Hedef_genislik": bbox[2],
                "Hedef_yukseklik": bbox[3],
            }
            gonder_tespit = json.dumps(sunucu_veri)
            msg1 = String()
            msg1.data = gonder_tespit
            pub1 = rospy.Publisher('/uav0/tespit', String, queue_size=10)
            pub1.publish(msg1)

        #print(math.sqrt(distance))
            cv2.putText(img, "Tahmini Uzaklik" + ('%d' % int(nesne_uzakligi)), (200, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 200),
                    2, cv2.LINE_AA, False)

        # sağ yada sol taraftamı ona bakan bir algoritma yaz
        # üst taraftamı alt taraftamı ona bakan bir algoritma
            horizantal_difference = int(bbox[0] + bbox[2] / 2) - int(img.shape[1] / 2)
            #if horizantal_difference  > 0:
            #    print("right")
            #    cv2.putText(img, "Right:"+ ('%.2f' % float((horizantal_difference)/kumanda_aralık)), (int(img.shape[1] / 4) + 5, int(9 * img.shape[0] / 10) - 150),
            #                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 200), 2, cv2.LINE_AA, False)
            #else:
            #    print("left")
            #    cv2.putText(img, "Left:"+ ('%.2f' % float((horizantal_difference*-1)/kumanda_aralık)), (int(img.shape[1] / 4) + 5, int(9 * img.shape[0] / 10) - 150),
            #                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 200), 2, cv2.LINE_AA, False)
            
            vertical_difference = int(bbox[1] + bbox[3] / 2) - int(img.shape[0] / 2)
            #
            #if vertical_difference > 0:
            #    print("down")
            #    cv2.putText(img, "Down:"+ ('%.2f' % float((vertical_difference)/kumanda_aralık)), (int(img.shape[1] / 4) + 5, int(9 * img.shape[0] / 10) - 100),
            #                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 200), 2, cv2.LINE_AA, False)
            #else:
            #    print("up")
            #    cv2.putText(img, "Up:"+ ('%.2f' % float((vertical_difference*-1)/kumanda_aralık)), (int(img.shape[1] / 4) + 5, int(9 * img.shape[0] / 10) - 100),
            #                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 200), 2, cv2.LINE_AA, False)

            yonelim_veri = {
                "tahmini_uzaklik": nesne_uzakligi,
                "horizontal_x": horizantal_difference/kumanda_aralık,
                "vertical_y": -vertical_difference/kumanda_aralık,
            }
            gonder_yonelim = json.dumps(yonelim_veri)
            msg2 = String()
            msg2.data = gonder_yonelim
            pub2 = rospy.Publisher('/uav0/yonelim', String, queue_size=10)
            pub2.publish(msg2)
            #ICERDE OLUP OLADIGININ KONTROLU
            if int(img.shape[1] / 4)< bbox[0] and int(img.shape[0] / 10) < bbox[1] and bbox[0]+bbox[2] < (3*int(img.shape[1] / 4)) and bbox[1]+bbox[3] < int(9 * img.shape[0] / 10):
                text = "ICERIDE"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 2)[0]
                text_x = int((img.shape[1] - text_size[0]) / 2)
                text_y = int((img.shape[0] - text_size[1]) / 2) + int(9 * img.shape[0] / 20)-50
                cv2.putText(img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 220, 0), 2, cv2.LINE_AA, False)

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
                            url = "http://127.0.0.1:8000/api/kilitlenme_bilgisi"
                            headers = {"Content-type": "application/json"}
                            try:
                                response = requests.post(url, data=json.dumps(kilitlenme_veri), headers=headers)
                                if response.status_code == 200:
                                    print("Kilitlenme Bilgisi Basariyla Gonderildi!")

                                else:
                                    print("Kilitlenme Bilgisi Gönderilemedi!")
                            except requests.exceptions.RequestException as e:
                                print("Kilitlenme Bilgisi Gönderilemedi! Hata: ", e)

                            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                            text_x = int((img.shape[1] - text_size[0]) / 2)
                            text_y = int((img.shape[0] - text_size[1]) / 4)
                            cv2.putText(img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                            kilitlenme = False
                            kilitlenme_suresi = 0
                            kilitlenme_baslangic = 0
                            kilitlenme_saiyisi+=1
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

            print(distance)

            cv2.circle(img, (int(img.shape[1] / 2), int(img.shape[0] / 2)), 3, (0, 0, 0), 2)
            cv2.circle(img, (int(bbox[0] + bbox[2] / 2), int(bbox[1] + bbox[3] / 2)), 3, (0, 0, 255), 2)

        gecen_sure = time.time() - start_time
        if gecen_sure > 3:
            goturn = False
            print("Takip Bitti")
    if not goturn:
        sunucu_veri = {
                "IHA_kilitlenme": 0,
                "Hedef_merkez_X": 0,
                "Hedef_merkez_Y": 0,
                "Hedef_genislik": 0,
                "Hedef_yukseklik": 0,
            }
        gonder_tespit = json.dumps(sunucu_veri)
        msg1 = String()
        msg1.data = gonder_tespit
        pub1 = rospy.Publisher('/uav0/tespit', String, queue_size=10)
        pub1.publish(msg1)
        kilitlenme = False
        kilitlenme_suresi = 0
        kilitlenme_baslangic = 0



    fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer);
    cv2.putText(img, "FPS : " + str(int(fps)), (25,25), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (61,217,255), 2);
    cv2.putText(img, "Kilitlenme Sayisi : " + str(int(kilitlenme_saiyisi)), (25,50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (64,217,255), 2);
    cv2.imshow('Image', img)
    cv2.waitKey(1)
