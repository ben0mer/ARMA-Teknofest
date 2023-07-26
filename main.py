# -*- coding: UTF-8 -*-
import asyncio
from tkinter import *
from turtle import home
from async_tkinter_loop import async_handler, async_mainloop
from mavsdk import *
from mavsdk import System
from mavsdk.offboard import (OffboardError, PositionNedYaw)
import requests, random
import subprocess
import time
import webbrowser
import requests, threading
import rospy
from std_msgs.msg import String
import json, os
from mavsdk.offboard import (Attitude, OffboardError, PositionNedYaw)


connected = False
giris_yapildimi = False
girisIslem = None
telemIslem = None
qrIslem = None
rotaIslem = None
kameraIslem = None
qrIslem = None
sunucutelemetri = False
rotatahmini = False
guncelleme= False
sunucutelem = False
sunucutelem_bool = False
sunucusaati_bool = False
arm = False
ototakip = False
dogFight = False
kacis = False
kamera = False
kameraAcik= False
qrAcik = False
drone = System()
lastPacketTime=time.time()-10
gonder = []
sunucuTVeri = None
telemetri_thread = None
sunucutelemetri_thread = None
stop_event = threading.Event()
tespit = 0
poztahmin = None
yonelim = None
kilitlenme_veri = ""
oturum = requests.Session()
async def otonomTakip():
    global kamera, ototakip, dogFight, tespit, poztahmin, yonelim, oturum
    ototakip = True
    dogFight = True
    await drone.offboard.set_attitude(Attitude(0.0, 0.0, 0.0, 0.7))
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"OFFBOARD Mod baslatilirken hata: \
              {error._result.result}")
        return
    while dogFight:
        while ototakip:
            if int(tespit) == 1:
                kamera = True
                ototakip = False
            if poztahmin == None:
                pass
            else:
                x_h = poztahmin["x"]
                y_h = poztahmin["y"]
                z_h = -poztahmin["z"]
                await drone.offboard.set_position_ned(PositionNedYaw(x_h, y_h, -z_h, 0.0))
                await asyncio.sleep(0.2)
        while kamera:
            if yonelim == None or tespit == 0:
                ototakip = True
                kamera = False
            else:
                vertical_x = yonelim["horizontal_x"]
                horizontal_y = yonelim["vertical_y"]
                roll = (vertical_x/64)*30
                pitch = (horizontal_y/36)*15
                yaw = 0
                throttle = 0
                await drone.offboard.set_attitude(Attitude(roll, pitch, yaw, 0.7))
                await asyncio.sleep(0.2)

def callback_kilitlenme(data):
    global kilitlenme_veri
    kilitlenme_veri = json.loads(data.data)
    if not kilitlenme_veri == "":
        print("Kilitlenme bilgisi gonderiliyor")
        url = 'http://'+sunucuIn.get()+'/api/kilitlenme_bilgisi'
        data = kilitlenme_veri
        headers = {'Content-type': 'application/json'}
        response = oturum.post(url, json=json.dumps(data), headers=headers)
        if response.status_code == 200:
            print("Kilitlenme bilgisi gonderildi")
        else:
            print("Kilitlenme bilgisi gonderilemedi")

def callback_gonder(data):
    global gonder, sunucuTVeri
    gonder = json.loads(data.data)
    sunucuTVeri = {
        "takim_numarasi":int(gonder["takim_numarasi"]), #int
        "iha_enlem":float(gonder["iha_enlem"]), #float
        "iha_boylam":float(gonder["iha_boylam"]),#float
        "iha_irtifa":float(gonder["iha_irtifa"]),#int
        "iha_dikilme":int(gonder["iha_dikilme"]),#int
        "iha_yonelme":int(gonder["iha_yonelme"]),#int
        "iha_yatis":int(gonder["iha_yatis"]),#int
        "iha_hiz":int(gonder["iha_hiz"]),#int
        "iha_batarya":int(gonder["iha_batarya"]),#int
        "iha_otonom":int(gonder["iha_otonom"]),#0 1 int
        "iha_kilitlenme":int(gonder["iha_kilitlenme"]),#0 1 int
        "hedef_merkez_X":int(gonder["hedef_merkez_X"]),#int
        "hedef_merkez_Y":int(gonder["hedef_merkez_Y"]),#int
        "hedef_genislik":int(gonder["hedef_genislik"]),#int
        "hedef_yukseklik":int(gonder["hedef_yukseklik"]),#int
        "gps_saati":{
            "saat":int(gonder["gps_saati"]["saat"]),#int
            "dakika":int(gonder["gps_saati"]["dakika"]),#int
            "saniye":int(gonder["gps_saati"]["saniye"]),#int
            "milisaniye":int(gonder["gps_saati"]["milisaniye"])#int
        }
    }
    # sunucuTVeri = {
    #     "takim_numarasi": int(1),
    #     "iha_enlem": float(41.508775),
    #     "iha_boylam": float(36.118335),
    #     "iha_irtifa": int(38),
    #     "iha_dikilme": int(7),
    #     "iha_yonelme": int(210),
    #     "iha_yatis": int(-30),
    #     "iha_hiz": int(28),
    #     "iha_batarya": int(50),
    #     "iha_otonom": int(1),
    #     "iha_kilitlenme": int(1),
    #     "hedef_merkez_X": int(300),
    #     "hedef_merkez_Y": int(230),
    #     "hedef_genislik": int(30),
    #     "hedef_yukseklik": int(43),
    #     "gps_saati": {
    #         "saat": int(11),
    #         "dakika": int(38),
    #         "saniye": int(37),
    #         "milisaniye": int(654)
    #         }
    #     }

def callback_yonelim(data):
    global yonelim
    yonelim = json.loads(data.data)

def callback_poztahmin(data):
    global poztahmin
    poztahmin = json.loads(data.data)

def callback_tespit(data):
    global tespit
    tespit = json.loads(data.data)
    tespit = tespit["iha_kilitlenme"]

def start_telemetri():
    global telemetri_thread
    if telemetri_thread is None:
        telemetri_thread = root.after(200, telemetri_guncelle)    

def stop_telemetri():
    global telemetri_thread
    if telemetri_thread is not None:
        root.after_cancel(telemetri_thread)
        telemetri_thread = None

# Thread fonksiyonu
def sunucu_telemetri_thread():
    global gonder, sunucuTVeri
    if sunucutelem_bool:
        data = sunucuTVeri
        url = 'http://'+sunucuIn.get()+'/api/telemetri_gonder'
        headers = {'Content-type': 'application/json'}
        hertz = int(hzIn.get())
        response = oturum.post(url, json=data, headers=headers)
        if response.status_code == 200:
            telemetriler = response.json()
            json_data = json.dumps(telemetriler)
            msg = String()
            msg.data = json_data
            pub = rospy.Publisher('/uav/rakip_telemetriler', String, queue_size=10)
            pub.publish(msg)
        else:
            print(response.status_code)
            print(response.json())
        # Belirli bir süre sonra tekrar thread'i çalıştır
        if sunucutelem_bool:
            root.after(hertz, sunucu_telemetri_thread)

# Telemetri gönderimi başlatma fonksiyonu
def start_sunucutelemetri():
    global sunucutelem_bool
    if not sunucutelem_bool:
        printPxh("Sunucu Telemetri Gonderimi Baslatiliyor...")
        telemTextStr.set("Telemetri Gonderimi\nBaslatildi")
        telemTextObj.config(fg="green")
        sunucutelem_bool = True
        sunucu_telemetri_thread()

# Telemetri gönderimi durdurma fonksiyonu
def stop_sunucutelemetri():
    global sunucutelem_bool
    if sunucutelem_bool:
        printPxh("Telemetri Durduruluyor...")
        telemTextStr.set("Telemetri Gonderimi\nDurduruldu")
        telemTextObj.config(fg="red")
        sunucutelem_bool = False

def sunucu_saati_thread():
    global sunucusaati_bool
    if sunucusaati_bool:
        url = 'http://'+sunucuIn.get()+'/api/sunucusaati'
        headers = {'Content-type': 'application/json'}
        hertz = 200
        response = oturum.get(url, headers=headers)
        if response.status_code == 200:
            saat = response.json()
            json_data = json.dumps(saat)
            msg = String()
            msg.data = json_data
            pub = rospy.Publisher('/uav/sunucu_saati', String, queue_size=10)
            pub.publish(msg)
        else:
            print(response.status_code)
            print(response.json())
        # Belirli bir süre sonra tekrar thread'i çalıştır
        if sunucusaati_bool:
            root.after(hertz, sunucu_saati_thread)

# Telemetri gönderimi başlatma fonksiyonu
def start_sunucusaati():
    global sunucusaati_bool
    if not sunucusaati_bool:
        printPxh("Sunucu Saati Baslatiliyor...")
        sunucusaati_bool = True
        sunucu_saati_thread()

# Telemetri gönderimi durdurma fonksiyonu
def stop_sunucusaati():
    global sunucusaati_bool
    if sunucusaati_bool:
        printPxh("Sunucu Saati Durduruluyor...")
        sunucusaati_bool = False

def qrokuma_gonder():
    printPxh("QR Bilgisi Gonderiliyor")
    url = 'http://'+sunucuIn.get()+'/api/kamikaze_bilgisi'
    qr_veri = {
    "kamikazeBaslangicZamani": {
        "saat": 0,
        "dakika": 0,
        "saniye": 0,
        "milisaniye": 0
    },
    "kamikazeBitisZamani": {
        "saat": 0,
        "dakika": 0,
        "saniye": 0,
        "milisaniye": 0
    },
    "qrMetni": "teknofest2023"
    }
    data = qr_veri
    headers = {'Content-type': 'application/json'}
    response = oturum.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        printPxh("QR bilgisi gonderildi")
    else:
        print("Hata Kodu: ", response.status_code)
        printPxh("QR bilgisi gonderilemedi")

def kilitlenme_gonder():
    printPxh("Kilitlenme Bilgisi Gonderiliyor")
    url = 'http://'+sunucuIn.get()+'/api/kilitlenme_bilgisi'
    qr_veri = {
        "kilitlenmeBaslangicZamani": {
            "saat":11,
            "dakika": 40,
            "saniye": 51,
            "milisaniye": 478
        },
        "kilitlenmeBitisZamani": {
            "saat": 11,
            "dakika": 41,
            "saniye": 3,
            "milisaniye": 141
        },
        "otonom_kilitlenme": 1
    }
    data = qr_veri
    headers = {'Content-type': 'application/json'}
    response = oturum.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        printPxh("QR bilgisi gonderildi")
    else:
        print("Hata Kodu: ", response.status_code)
        printPxh("QR bilgisi gonderilemedi")

def sunucu_saatial():
    printPxh("Sunucu Saati Aliniyor")
    url = 'http://'+sunucuIn.get()+'/api/sunucusaati'
    response = oturum.get(url)
    qr = response.json()
    if response.status_code == 200:
        print("İstek başarılı! Yanıt içeriği: ")
        print(response.json())
    else:
        print("Hata! İstek başarısız oldu. HTTP durum kodu: ", response.status_code)

def telemetri_guncelle():
    global gonder, telemetri_thread
    data = gonder
    enlem = data["iha_enlem"]
    boylam = data["iha_boylam"]
    irtifa = data["iha_irtifa"]
    dikilme = data["iha_dikilme"]
    yonelme = data["iha_yonelme"]
    yatis = data["iha_yatis"]
    hiz = data["iha_hiz"]
    batarya = data["iha_batarya"]
    otonom = data["iha_otonom"]
    kilitlenme = data["iha_kilitlenme"]
    saat = data["gps_saati"]["saat"]
    dakika = data["gps_saati"]["dakika"]
    saniye = data["gps_saati"]["saniye"]
    milisaniye = data["gps_saati"]["milisaniye"]
    enlemTextStr.set("{}".format(enlem))
    boylamTextStr.set("{}".format(boylam))
    irtifaTextStr.set("{}".format(round(irtifa,4)))
    dikilmeTextStr.set("{}".format(round(dikilme,4)))
    yonelmeTextStr.set("{}".format(round(yonelme,4)))
    yatisTextStr.set("{}".format(round(yatis,4)))
    hizTextStr.set("{}".format(round(hiz,4)))
    bataryaTextStr.set("{}".format(batarya))
    otonomTextStr.set("{}".format(otonom))
    kilitlenmeTextStr.set("{}".format(kilitlenme))
    saatTextStr.set("{}".format(saat))
    dakikaTextStr.set("{}".format(dakika))
    saniyeTextStr.set("{}".format(saniye))
    miliSaniyeTextStr.set("{}".format(milisaniye))
    telemetri_thread = root.after(200, telemetri_guncelle)

def ucak_bilgisi():
    global guncelleme
    if not guncelleme:
        start_telemetri()
        guncelleme = True
    else:
        stop_telemetri()
        guncelleme = False

def hyperLink(url):
    webbrowser.open_new(url)

async def setup():
    global connected
    #await drone.connect(system_address="udp://:"+portIn.get())
    await drone.connect(system_address="tcp://:5760")
    printPxh("-- IHA'YA BAGLANILIYOR...")
    global state
    global lastPacketTime
    global health
    async for state in drone.core.connection_state():
        lastPacketTime=time.time()
        if state.is_connected:
            printPxh(f"-- IHA'YA BAGLANOLDI!")
            connected = True
            break
    asyncio.ensure_future(checkTelem())
    asyncio.ensure_future(print_health(drone))
    printPxh("-- GLOBAL POZISYON TAHMINI BEKLENIYOR...")
    while True:
        await print_health(drone)
        if health.is_global_position_ok and health.is_home_position_ok:
            printPxh("-- GLOBAL POZISYON TAHMINI ALINDI!")
            break
        
async def checkTelem():
    global lastPacketTime 
    while True:
        #printPxh(str(time.time()))
        #printPxh(str(time.time() - lastPacketTime))
        if (time.time() - lastPacketTime) > 1 :
            linkTextObj.config(fg="red")
        else:
            linkTextObj.config(fg="green")
        await asyncio.sleep(3)

async def kacis():
    global kacis
    kacis = True
    await drone.offboard.set_attitude(Attitude(0.0, 0.0, 0.0, 0.7))
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"OFFBOARD Mod baslatilirken hata: \
        {error._result.result}")
        return
    async for position in drone.telemetry.position_velocity_ned():
        north = position.position.north_m
        east = position.position.east_m
        down = position.position.down_m
        if kacis:
            while True:

                n_h = int(random.randint(-500,500))
                e_h = int(random.randint(-500,500))
                d_h = int(random.randint(-70,-30))
                hedef = [n_h, e_h, d_h]
                distance_to_target = ((north - hedef[0])**2 + (east - hedef[1])**2 + (down - hedef[2])**2)**0.5
                if (distance_to_target >= 100):
                    print(f"Hedef -> {hedef}")
                    print(f"Uzaklık -> {distance_to_target}")
                    await drone.offboard.set_position_ned(PositionNedYaw(hedef[0], hedef[1], hedef[2], 0.0))
                    await asyncio.sleep(8)
                    break
                else:
                    continue
        else:
            break

async def disarm():
    printPxh("-- DISARM EDILIYOR...")
    try:
        await drone.action.disarm()
    except Exception as e:
        printPxh("DISARM EDERKEN HATA OLUSTU: " + str(e))
    
async def arm():
    printPxh("-- ARM EDILIYOR...")
    try:
        await drone.action.arm()
    except Exception as e:
        printPxh("ARM EDERKEN HATA OLUSTU: " + str(e))

async def shutdown():
    printPxh("-- MOTORLAR ZORLA KAPATILIYOR...")
    await drone.action.kill()
    
async def testArm():
    printPxh("-- ARM TESTI YAPILIYOR...")
    printPxh("-- ARM EDILIYOR...")
    try:
        await drone.action.arm()
    except Exception as e:
        printPxh("ARM EDERKEN HATA OLUSTU: " + str(e))   
    await asyncio.sleep(5)
    try:
        printPxh("-- DISARM EDILIYOR...")
        await drone.action.disarm()
    except Exception as e:
        printPxh("DISARM EDERKEN HATA OLUSTU: " + str(e))
    printPxh("-- ARM TESTI TAMAMLANDI")
    
async def takeoff(alt=50):
    printPxh("-- TAKEOFF MOD BASLATILDI!")
    printPxh("-- ARM EDILIYOR...")
    await drone.action.arm()
    printPxh("****** TAKEOFF YAPILIYOR! ******")
    await drone.action.set_takeoff_altitude(int(altIn.get()))
    await drone.action.takeoff()

async def land():
    printPxh("-- LANDING MOD BASLATILDI!")
    await drone.action.land()

async def rtl():
    printPxh("-- RTL MOD BASLATILDI!")
    await drone.action.return_to_launch()

async def mission():
    printPxh("-- MISSION MOD BASLATILDI!")
    await drone.mission.set_return_to_launch_after_mission(True)
    #await drone.mission.upload_mission(mission_items)
    await drone.mission.start_mission()
    printPxh("-- MISSION BASTIRILDI!")
    #await drone.action.return_to_launch()

async def offboardStop():
    global ototakip, kacis, kamera, dogFight
    ototakip = False
    kacis = False
    kamera = False
    dogFight = False
    printPxh("-- OFFBOARD MOD DURDURULDU!")
    await drone.offboard.stop()

def printPxh(msg=""):
    pxhOut.insert(END, msg + '\n')
    print(msg)
    pxhOut.see("end")

async def print_health(drone):
        defColor = portLabelObj.cget("fg")
        async for health in drone.telemetry.health():
            #printPxh(f"Health: {health}")
            if health.is_gyrometer_calibration_ok & health.is_accelerometer_calibration_ok & health.is_magnetometer_calibration_ok :
               ahrsTextObj.config(fg="green") 
               
            if health.is_local_position_ok & health.is_global_position_ok & health.is_home_position_ok :
               posTextObj.config(fg="green") 
        
            if health.is_armable:
               armTextObj.config(fg="green") 
            global lastPacketTime   
            lastPacketTime=time.time()

def kameraackapat():
    global kameraAcik
    if kameraAcik == False:
        printPxh("Kamera Aciliyor...")
        kameraIslem = subprocess.Popen(["/home/arma/.virtualenvs/opencv_dnn_cuda/bin/python", "nesnetespit.py"])
        printPxh("Kamera Acildi")
        kameraAcik = True
    else:
        printPxh("Kamera Kapatiliyor...")
        kameraAcik = False
        kameraIslem = None
        kameraIslem.kill()
        printPxh("Kamera Kapatildi")
        
        
        printPxh("Kamera Kapatilamadi")
        kameraAcik = True

def qr_okuyucu():
    global qrAcik
    if qrAcik == False:
        try:
            printPxh("QR Okuyucu Aciliyor...")
            qrIslem = subprocess.Popen(["/home/arma/.virtualenvs/opencv_dnn_cuda/bin/python", "qrokuyucu.py"])
            printPxh("QR Okuyucu Acildi")
            qrAcik = True
        except:
            printPxh("QR Okuyucu Acilamadi")
            qrAcik = False
    else:
        try:
            printPxh("QR Okuyucu Kapatiliyor...")
            qrIslem.kill()
            printPxh("QR Okuyucu Kapatildi")
            qrAcik = False
            qrIslem = None
        except:
            printPxh("QR Okuyucu Kapatilamadi")
            qrAcik = True

def baglanvekes():
    global connected, giris_yapildimi, girisIslem
    if connected:
        if giris_yapildimi==False:
            
            kullanici_adi = kadiIn.get()
            sifre = sifreIn.get()
            url = "http://"+sunucuIn.get()+"/api/giris"
            bilgiler = {
                "kadi": kullanici_adi, 
                "sifre": sifre
            }
            headers = {"Content-type": "application/json"}
            response = oturum.post(url, data=json.dumps(bilgiler), headers=headers)
            if response.status_code == 200:
                printPxh("Giris başarili!")
                print("Gelen cevap -> "+str(response.status_code))
                takim_numarasi = response.text
                arma_no = {
                    "takim_numarasi": takim_numarasi
                    }
                with open("arma_no.json", "w") as dosya:
                    json.dump(arma_no, dosya)
                girisTextStr.set("Giris Yapildi")
                girisTextObj.config(fg="green")
                time.sleep(1)
                girisIslem = subprocess.Popen(["/bin/python3", "giris.py"])
                giris_yapildimi=True
            else:
                printPxh("Giris yapilamadi!")
                printPxh("Hata kodu: ", response.status_code)
                girisIslem.kill()
                printPxh("Cikis Yapildi")
                girisIslem = None
                girisTextStr.set("Giris Yapilmadi")
                girisTextObj.config(fg="red")
                giris_yapildimi=False
        else:
            printPxh("Zaten giriş yapilmis!")
    else:
        printPxh("Once IHA'ya baglanin!")

def rotaolusturucu():
    global connected, giris_yapildimi, rotaIslem, sunucutelemetri, rotatahmini
    if connected:
        if giris_yapildimi:
            if sunucutelemetri:
                if rotatahmini == False:
                    printPxh("Rota Olusturucu Baslatiliyor...")
                    try:
                        rotaIslem = subprocess.Popen(['/bin/python3', 'rotaolusturucu.py'])
                        printPxh("Rota Olusturucu Baslatildi")
                        rotatahmini = True
                    except:
                        printPxh("Rota Olusturucu Baslatilamadi")
                        rotatahmini = False
                else:
                    printPxh("Rota Olusturucu Durduruluyor...")
                    rotaIslem.kill()
                    rotaIslem = None
                    rotatahmini = False
            else:
                printPxh("Once Sunucu ile Telemetri Alisverisini Baslatin!")
        else:
            printPxh("Once Giris Yapin!")
    else:
        printPxh("Once IHA'ya Baglanin!")

def telemetri():
    global connected, giris_yapildimi, telemIslem, sunucutelemetri
    if connected:
        if giris_yapildimi==True:
            if telemIslem == None:
                printPxh("Telemetri Baslatiliyor...")
                telemIslem = subprocess.Popen(['/bin/python3', 'telemetri.py'])
                printPxh("Telemetri Baslatildi")
                telemTextStr.set("Telemetri Gonderimi\nBaslatildi")
                telemTextObj.config(fg="green")
                sunucutelemetri = True
            else:
                printPxh("Telemetri Durduruluyor...")
                telemIslem.kill()
                telemIslem = None
                printPxh("Telemetri Durduruldu")
                telemTextStr.set("Telemetri Gonderimi\nDurduruldu")
                telemTextObj.config(fg="red")
                sunucutelemetri = False
        else:
            printPxh("Once Giris Yapin!")
    else:
        printPxh("Once IHA'ya baglanin!")

def qr():
    global connected, giris_yapildimi, qrIslem
    if connected:
        if giris_yapildimi==True:
            url = "http://"+sunucuIn.get()+"/api/qr_koordinati"
            response = oturum.get(url)
            qr = response.json()
            if response.status_code == 200:
                print("İstek başarılı! Yanıt içeriği: ")
                print(response.json())
                with open("qr.json", "w") as dosya:
                    json.dump(qr, dosya)
            else:
                print("Hata! İstek başarısız oldu. HTTP durum kodu: ", response.status_code)
        else:
            printPxh("Once Giris Yapin!")
    else:
        printPxh("Once IHA'ya baglanin!")


root = Tk()
root.geometry("1280x720")
root.title("ARMA Arayuz v0.1")

#PORT YAZISI
labelPortText=StringVar()
labelPortText.set("Port Girin: ")
portLabelObj=Label(root, textvariable=labelPortText, height=4)
portLabelObj.grid(row=0,column=0,rowspan=1,columnspan=1)

defPort = StringVar(root, value='14030')
portIn = Entry(root, textvariable=defPort)
portIn.grid(row=0,column=1,rowspan=1,columnspan=1)

Button(root, text="Baglan", command=async_handler(setup) , width=20, height=2).grid(row=1,column=1,rowspan=1)

labelSunucuText=StringVar()
labelSunucuText.set("Sunucu IP:")
sunucuLabelObj=Label(root, textvariable=labelSunucuText, height=4)
sunucuLabelObj.grid(row=2,column=2,columnspan=1)

defSunucu = StringVar(root, value='10.0.0.10:10001')
sunucuIn = Entry(root, textvariable=defSunucu)
sunucuIn.grid(row=2,column=3,columnspan=1)

labelHzText=StringVar()
labelHzText.set("Telemetri Hizi (ms):")
hzLabelObj=Label(root, textvariable=labelHzText, height=4)
hzLabelObj.grid(row=3,column=2,columnspan=1)

defHz = StringVar(root, value='200')
hzIn = Entry(root, textvariable=defHz)
hzIn.grid(row=3,column=3,columnspan=1)

# Kullanici Adi YAZISI
labelKadiText=StringVar()
labelKadiText.set("Kullanici Adi: ")
kadiLabelObj=Label(root, textvariable=labelKadiText, height=4)
kadiLabelObj.grid(row=0,column=2,rowspan=1,columnspan=1)

defKadi = StringVar(root, value='arma')
kadiIn = Entry(root, textvariable=defKadi)
kadiIn.grid(row=0,column=3,rowspan=1,columnspan=1)

labelSifreText=StringVar()
labelSifreText.set("Sifre: ")
sifreLabelObj=Label(root, textvariable=labelSifreText, height=4)
sifreLabelObj.grid(row=1,column=2, rowspan=1, columnspan=1)

defSifre = StringVar(root, value='E5vUMyRZmK')
sifreIn = Entry(root, textvariable=defSifre)
sifreIn.grid(row=1,column=3,rowspan=1,columnspan=1)


Button(root, text="Giris", command=baglanvekes, width=20, height=2).grid(row=0,column=4,rowspan=1, columnspan=1)

girisTextStr=StringVar()
girisTextStr.set("Giris Yapilmadi")
girisTextObj=Label(root, textvariable=girisTextStr, height=1)
girisTextObj.grid(row=0,column=5,rowspan=1,columnspan=1)
girisTextObj.config(fg= "red")

Button(root, text="Telemetri Baslat", command=start_sunucutelemetri, width=20, height=2).grid(row=1,column=4,rowspan=1, columnspan=1)
Button(root, text="Telemetri Durdur", command=stop_sunucutelemetri, width=20, height=2).grid(row=2,column=4,rowspan=1, columnspan=1)
Button(root, text="Sunucu Saati Baslat", command=start_sunucusaati, width=20, height=2).grid(row=2,column=5,rowspan=1, columnspan=1)
Button(root, text="Sunucu Saati Durdur", command=stop_sunucusaati, width=20, height=2).grid(row=2,column=6,rowspan=1, columnspan=1)
telemTextStr=StringVar()
telemTextStr.set("Telemetri Gonderimi\nBaslatilmadi")
telemTextObj=Label(root, textvariable=telemTextStr, height=2)
telemTextObj.grid(row=1,column=5,rowspan=1,columnspan=1)
telemTextObj.config(fg= "red")

Button(root, text="QR Verisi\nGET", command=qr, width=15, height=2).grid(row=0,column=6,rowspan=1, columnspan=1)
Button(root, text="Kilitlenme Verisi\nPOST", command=kilitlenme_gonder, width=15, height=2).grid(row=1,column=6,rowspan=1, columnspan=1)
Button(root, text="Kamikaze Verisi\nPOST", command=qrokuma_gonder, width=15, height=2).grid(row=1,column=7,rowspan=1, columnspan=1)
Button(root, text="Sunucu Saati\nGET", command=sunucu_saatial, width=15, height=2).grid(row=0,column=7,rowspan=1, columnspan=1)

## Telemetri Verileri
enlemTextStr=StringVar()
enlemTextStr.set("Enlem")
enlemTextObj=Label(root, textvariable=enlemTextStr, height=1)
enlemTextObj.grid(row=4,column=1,rowspan=1,columnspan=1)
enlemTextObj.config(fg= "red")
enlemTextStr1=StringVar()
enlemTextStr1.set("Enlem")
enlemTextObj1=Label(root, textvariable=enlemTextStr1, height=1)
enlemTextObj1.grid(row=4,column=0,rowspan=1,columnspan=1)
enlemTextObj1.config(fg= "red")

boylamTextStr=StringVar()
boylamTextStr.set("Boylam")
boylamTextObj=Label(root, textvariable=boylamTextStr, height=1)
boylamTextObj.grid(row=5,column=1,rowspan=1,columnspan=1)
boylamTextObj.config(fg= "red")
boylamTextStr1=StringVar()
boylamTextStr1.set("Boylam")
boylamTextObj1=Label(root, textvariable=boylamTextStr1, height=1)
boylamTextObj1.grid(row=5,column=0,rowspan=1,columnspan=1)
boylamTextObj1.config(fg= "red")

irtifaTextStr=StringVar()
irtifaTextStr.set("Irtifa")
irtifaTextObj=Label(root, textvariable=irtifaTextStr, height=1)
irtifaTextObj.grid(row=6,column=1,rowspan=1,columnspan=1)
irtifaTextObj.config(fg= "red")
irtifaTextStr1=StringVar()
irtifaTextStr1.set("Irtifa")
irtifaTextObj1=Label(root, textvariable=irtifaTextStr1, height=1)
irtifaTextObj1.grid(row=6,column=0,rowspan=1,columnspan=1)
irtifaTextObj1.config(fg= "red")

dikilmeTextStr=StringVar()
dikilmeTextStr.set("Dikilme")
dikilmeTextObj=Label(root, textvariable=dikilmeTextStr, height=1)
dikilmeTextObj.grid(row=7,column=1,rowspan=1,columnspan=1)
dikilmeTextObj.config(fg= "red")
dikilmeTextStr1=StringVar()
dikilmeTextStr1.set("Dikilme")
dikilmeTextObj1=Label(root, textvariable=dikilmeTextStr1, height=1)
dikilmeTextObj1.grid(row=7,column=0,rowspan=1,columnspan=1)
dikilmeTextObj1.config(fg= "red")

yonelmeTextStr=StringVar()
yonelmeTextStr.set("Yonelme")
yonelmeTextObj=Label(root, textvariable=yonelmeTextStr, height=1)
yonelmeTextObj.grid(row=8,column=1,rowspan=1,columnspan=1)
yonelmeTextObj.config(fg= "red")
yonelmeTextStr1=StringVar()
yonelmeTextStr1.set("Yonelme")
yonelmeTextObj1=Label(root, textvariable=yonelmeTextStr1, height=1)
yonelmeTextObj1.grid(row=8,column=0,rowspan=1,columnspan=1)
yonelmeTextObj1.config(fg= "red")

yatisTextStr=StringVar()
yatisTextStr.set("Yatis")
yatisTextObj=Label(root, textvariable=yatisTextStr, height=1)
yatisTextObj.grid(row=9,column=1,rowspan=1,columnspan=1)
yatisTextObj.config(fg= "red")
yatisTextStr1=StringVar()
yatisTextStr1.set("Yatis")
yatisTextObj1=Label(root, textvariable=yatisTextStr1, height=1)
yatisTextObj1.grid(row=9,column=0,rowspan=1,columnspan=1)
yatisTextObj1.config(fg= "red")

hizTextStr=StringVar()
hizTextStr.set("Hiz")
hizTextObj=Label(root, textvariable=hizTextStr, height=1)
hizTextObj.grid(row=10,column=1,rowspan=1,columnspan=1)
hizTextObj.config(fg= "red")
hizTextStr1=StringVar()
hizTextStr1.set("Hiz")
hizTextObj1=Label(root, textvariable=hizTextStr1, height=1)
hizTextObj1.grid(row=10,column=0,rowspan=1,columnspan=1)
hizTextObj1.config(fg= "red")

bataryaTextStr=StringVar()
bataryaTextStr.set("Batarya")
bataryaTextObj=Label(root, textvariable=bataryaTextStr, height=1)
bataryaTextObj.grid(row=11,column=1,rowspan=1,columnspan=1)
bataryaTextObj.config(fg= "red")
bataryaTextStr1=StringVar()
bataryaTextStr1.set("Batarya")
bataryaTextObj1=Label(root, textvariable=bataryaTextStr1, height=1)
bataryaTextObj1.grid(row=11,column=0,rowspan=1,columnspan=1)
bataryaTextObj1.config(fg= "red")

otonomTextStr=StringVar()
otonomTextStr.set("Otonom")
otonomTextObj=Label(root, textvariable=otonomTextStr, height=1)
otonomTextObj.grid(row=12,column=1,rowspan=1,columnspan=1)
otonomTextObj.config(fg= "red")
otonomTextStr1=StringVar()
otonomTextStr1.set("Otonom")
otonomTextObj1=Label(root, textvariable=otonomTextStr1, height=1)
otonomTextObj1.grid(row=12,column=0,rowspan=1,columnspan=1)
otonomTextObj1.config(fg= "red")

kilitlenmeTextStr=StringVar()
kilitlenmeTextStr.set("Kilitlenme")
kilitlenmeTextObj=Label(root, textvariable=kilitlenmeTextStr, height=1)
kilitlenmeTextObj.grid(row=13,column=1,rowspan=1,columnspan=1)
kilitlenmeTextObj.config(fg= "red")
kilitlenmeTextStr1=StringVar()
kilitlenmeTextStr1.set("Kilitlenme")
kilitlenmeTextObj1=Label(root, textvariable=kilitlenmeTextStr1, height=1)
kilitlenmeTextObj1.grid(row=13,column=0,rowspan=1,columnspan=1)
kilitlenmeTextObj1.config(fg= "red")

saatTextStr=StringVar()
saatTextStr.set("Saat")
saatTextObj=Label(root, textvariable=saatTextStr, height=1)
saatTextObj.grid(row=14,column=1,rowspan=1,columnspan=1)
saatTextObj.config(fg= "red")
saatTextStr1=StringVar()
saatTextStr1.set("Saat")
saatTextObj1=Label(root, textvariable=saatTextStr1, height=1)
saatTextObj1.grid(row=14,column=0,rowspan=1,columnspan=1)
saatTextObj1.config(fg= "red")

dakikaTextStr=StringVar()
dakikaTextStr.set("Dakika")
dakikaTextObj=Label(root, textvariable=dakikaTextStr, height=1)
dakikaTextObj.grid(row=15,column=1,rowspan=1,columnspan=1)
dakikaTextObj.config(fg= "red")
dakikaTextStr1=StringVar()
dakikaTextStr1.set("Dakika")
dakikaTextObj1=Label(root, textvariable=dakikaTextStr1, height=1)
dakikaTextObj1.grid(row=15,column=0,rowspan=1,columnspan=1)
dakikaTextObj1.config(fg= "red")

saniyeTextStr=StringVar()
saniyeTextStr.set("Saniye")
saniyeTextObj=Label(root, textvariable=saniyeTextStr, height=1)
saniyeTextObj.grid(row=16,column=1,rowspan=1,columnspan=1)
saniyeTextObj.config(fg= "red")
saniyeTextStr1=StringVar()
saniyeTextStr1.set("Saniye")
saniyeTextObj1=Label(root, textvariable=saniyeTextStr1, height=1)
saniyeTextObj1.grid(row=16,column=0,rowspan=1,columnspan=1)
saniyeTextObj1.config(fg= "red")

miliSaniyeTextStr=StringVar()
miliSaniyeTextStr.set("MiliSaniye")
miliSaniyeTextObj=Label(root, textvariable=miliSaniyeTextStr, height=1)
miliSaniyeTextObj.grid(row=17,column=1,rowspan=1,columnspan=1)
miliSaniyeTextObj.config(fg= "red")
miliSaniyeTextStr1=StringVar()
miliSaniyeTextStr1.set("MiliSaniye")
miliSaniyeTextObj1=Label(root, textvariable=miliSaniyeTextStr1, height=1)
miliSaniyeTextObj1.grid(row=17,column=0,rowspan=1,columnspan=1)
miliSaniyeTextObj1.config(fg= "red")

Button(root, text="Verileri Guncelle", command=ucak_bilgisi, width=15, height=2).grid(row=1,column=0,rowspan=1, columnspan=1)


posTextStr=StringVar()
posTextStr.set("NAV")
posTextObj=Label(root, textvariable=posTextStr, height=1)
posTextObj.grid(row=2,column=0,rowspan=1,columnspan=1)
posTextObj.config(fg= "red")

ahrsTextStr=StringVar()
ahrsTextStr.set("AHRS")
ahrsTextObj=Label(root, textvariable=ahrsTextStr, height=1)
ahrsTextObj.grid(row=2,column=1,rowspan=1,columnspan=1)
ahrsTextObj.config(fg= "red")


linkTextStr=StringVar()
linkTextStr.set("LINK")
linkTextObj=Label(root, textvariable=linkTextStr, height=1)
linkTextObj.grid(row=3,column=0,rowspan=1,columnspan=1)
linkTextObj.config(fg= "red")

armTextStr=StringVar()
armTextStr.set("HAZIR")
armTextObj=Label(root, textvariable=armTextStr, height=1)
armTextObj.grid(row=3,column=1,rowspan=1,columnspan=1)
armTextObj.config(fg= "red")


defAlt = StringVar(root, value='30')
altIn = Entry(root, textvariable=defAlt, width=15)
altIn.grid(row=6,column=2,rowspan=1,columnspan=1)

Button(root, text="TAKEOFF", command=async_handler(takeoff),width=15, height=2).grid(row=7,column=2,rowspan=1,columnspan=1)
Button(root, text="LAND\n(Suanki Pozisyona)", command=async_handler(land),width=15, height=2).grid(row=8,column=2,rowspan=1, columnspan=1)
Button(root, text="ARM", command=async_handler(arm),width=15, height=2).grid(row=7,column=3,rowspan=1,columnspan=1)
Button(root, text="DISARM", command=async_handler(disarm),width=15, height=2).grid(row=8,column=3,rowspan=1, columnspan=1)
Button(root, text="TEST ARM", command=async_handler(testArm),width=15, height=2).grid(row=9,column=2,rowspan=1,columnspan=1)
Button(root, text="DISARMA\nZORLA", command=async_handler(shutdown),width=15, height=2).grid(row=9,column=3,rowspan=1, columnspan=1)
Button(root, text="OTONOM TAKIP", command=async_handler(otonomTakip),width=15, height=2).grid(row=10,column=2,rowspan=1,columnspan=1)
Button(root, text="RTL", command=async_handler(rtl),width=15, height=2).grid(row=10,column=3,rowspan=1, columnspan=1)
Button(root, text="MISSION", command=async_handler(mission),width=15, height=2).grid(row=11,column=2,rowspan=1,columnspan=1)
Button(root, text="OFFBOARD\nSTOP", command=async_handler(offboardStop),width=15, height=2).grid(row=11,column=3,rowspan=1, columnspan=1)
Button(root, text="ROTA\nOLUSTURUCU", command=async_handler(rotaolusturucu),width=15, height=2).grid(row=12,column=2,rowspan=1, columnspan=1)
Button(root, text="KACIS", command=async_handler(kacis),width=15, height=2).grid(row=12,column=3,rowspan=1, columnspan=1)
Button(root, text="Takip Kamerasi\nAc/Kapat", command=kameraackapat, width=15, height=2).grid(row=13,column=2,rowspan=1, columnspan=1)
Button(root, text="QR Kamerasi\nAc/Kapat", command=qr_okuyucu, width=15, height=2).grid(row=13,column=3,rowspan=1, columnspan=1)
pxhOut = Text(
    root,
    height=20,
    width=70
)
pxhOut.grid(row=3,column=4,rowspan=8 ,columnspan=8)
pxhOut.insert(END,"Drone state will be shown here..."+ '\n')
# pxhOut.config(state=DISABLED)


linkFooter = StringVar()
linkFooter.set("ARMA UAV")


rospy.init_node("telemetri_subscriber")
rospy.Subscriber("/uav/gonder", String, callback_gonder)
rospy.Subscriber("/uav/yonelim", String, callback_yonelim)
rospy.Subscriber("/uav/tespit", String, callback_tespit)
rospy.Subscriber("/uav/poztahmin", String, callback_poztahmin)
rospy.Subscriber("/uav/kilitlenme_veri", String, callback_kilitlenme)
async_mainloop(root)
