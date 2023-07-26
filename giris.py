# -*- coding: UTF-8 -*-

import rospy
from mavros_msgs.msg import State, VFR_HUD, HomePosition
from sensor_msgs.msg import NavSatFix, Imu, BatteryState
from std_msgs.msg import String, Float64
import math
import requests
import json, datetime
home = ""
gonderm = ""
arma_no = ""
takim_numarasi, iha_enlem, iha_boylam, iha_irtifa, iha_relirtifa ,iha_dikilme, iha_yatis, iha_yonelme, iha_otonom, iha_batarya, iha_hiz, iha_kilitlenme, hedef_merkez_X , hedef_merkez_Y, hedef_genislik, hedef_yukseklik, saat, dakika, saniye, milisaniye = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
with open("arma_no.json", "r") as dosya:
    takim_numarasi = json.load(dosya)
takim_numarasi = takim_numarasi["takim_numarasi"]
arma_no=takim_numarasi
def imu_to_euler(x, y, z, w):
    t0 = 2.0 * (w * x + y * z)
    t1 = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(t0, t1)
    t2 = 2.0 * (w * y - z * x)
    t2 = 1.0 if t2 > 1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch = math.asin(t2)
    t3 = 2.0 * (w * z + x * y)
    t4 = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(t3, t4)
    roll = math.degrees(roll)
    pitch = math.degrees(pitch)
    yaw = math.degrees(yaw)
    yaw = (-yaw + 90) % 360
    return roll, -pitch, yaw

def callback_imu(data):
    global iha_dikilme, iha_yatis, iha_yonelme
    roll, pitch, yaw = imu_to_euler(data.orientation.x, data.orientation.y, data.orientation.z, data.orientation.w)
    iha_dikilme = pitch
    iha_yonelme = yaw
    iha_yatis = roll

def callback_state(data):
    global iha_otonom
    mode = data.mode
    if (mode == "MANUAL" or mode == "STABILIZED"):
        iha_otonom = 0
    else:
        iha_otonom = 1

#def callback_altitude(data):
#    global iha_irtifa
#    iha_irtifa = data.data

def callback_gps(data):
    global iha_enlem, iha_boylam, iha_irtifa, saat, dakika, saniye, milisaniye, home
    iha_enlem = data.latitude
    iha_boylam = data.longitude
    iha_irtifa = int(data.altitude)-126
    gps_time = data.header.stamp.to_sec()
    dt = datetime.datetime.fromtimestamp(gps_time)
    saat = dt.hour
    dakika = dt.minute
    saniye = dt.second
    milisaniye = dt.microsecond // 1000  # milisaniye cinsinden

def callback_battery(data):
    global iha_batarya
    voltage = data.voltage
    current = data.current
    iha_batarya = 100*(data.percentage)

def callback_velocity(data):
    global iha_hiz
    iha_hiz = data.groundspeed

def gonder():
    global takim_numarasi, gonderm, arma_no, kadi, sifre
    gonderjson = {
        "takim_numarasi": int(takim_numarasi), #int
        "iha_enlem": float(iha_enlem), #float
        "iha_boylam": float(iha_boylam),#float
        "iha_irtifa": float(iha_irtifa),#int
        "iha_dikilme": int(iha_dikilme),#int
        "iha_yonelme": int(iha_yonelme),#int
        "iha_yatis": int(iha_yatis),#int
        "iha_otonom": int(iha_otonom),#0 1 int
        "iha_hiz": int(iha_hiz),#int
        "iha_batarya": int(iha_batarya),#int
        "iha_kilitlenme": int(iha_kilitlenme),#0 1 int
        "hedef_merkez_X": int(hedef_merkez_X),#int
        "hedef_merkez_Y": int(hedef_merkez_Y),#int
        "hedef_genislik": int(hedef_genislik),#int
        "hedef_yukseklik": int(hedef_yukseklik),#int
        "gps_saati": {
            "saat": int(saat),#int
            "dakika": int(dakika),#int
            "saniye": int(saniye),#int
            "milisaniye": int(milisaniye)#int
        }
    }
    gonderm = json.dumps(gonderjson)

    
def callback_home(data):
    global home, iha_irtifa, iha_relirtifa
    home_enlem = data.geo.latitude
    home_boylam = data.geo.longitude
    home_irtifa = data.geo.altitude
    iha_relirtifa=int(iha_irtifa)-int(home_irtifa)
    home = {
        "home_enlem": home_enlem,
        "home_boylam": home_boylam,
        "home_irtifa": home_irtifa
    }
    home = json.dumps(home)

def callback_tespit(data):
    global iha_kilitlenme, hedef_merkez_X, hedef_merkez_Y, hedef_genislik, hedef_yukseklik
    tespit_veri = json.loads(data.data)
    iha_kilitlenme = tespit_veri["iha_kilitlenme"]
    hedef_merkez_X = tespit_veri["hedef_merkez_X"]
    hedef_merkez_Y = tespit_veri["hedef_merkez_Y"]
    hedef_genislik = tespit_veri["hedef_genislik"]
    hedef_yukseklik = tespit_veri["hedef_yukseklik"]

def publisher():
    global arma_no, gonderm, home
    msg1 = String()
    msg1.data = arma_no
    pub1 = rospy.Publisher('/uav/arma_no', String, queue_size=10)
    pub1.publish(msg1)

    msg2 = String()
    msg2.data = gonderm
    pub2 = rospy.Publisher('/uav/gonder', String, queue_size=10)
    pub2.publish(msg2)

    msg3 = String()
    msg3.data = home
    pub3 = rospy.Publisher('/uav/home', String, queue_size=10)
    pub3.publish(msg3)

def listener():
    rospy.init_node("listener", anonymous=True)
    rospy.Subscriber("/mavros/battery", BatteryState, callback_battery)
    rospy.Subscriber("/mavros/state", State, callback_state)
    rospy.Subscriber("/mavros/global_position/global", NavSatFix, callback_gps)
    rospy.Subscriber("/mavros/imu/data", Imu, callback_imu)
    rospy.Subscriber("/mavros/vfr_hud", VFR_HUD, callback_velocity)
    rospy.Subscriber("/mavros/home_position/home", HomePosition, callback_home)
    rospy.Subscriber("/uav/tespit", String, callback_tespit)
    rate = rospy.Rate(5) # 5 Hz
    while not rospy.is_shutdown():
        gonder()
        publisher()
        rate.sleep()

if __name__ == "__main__":
    listener()