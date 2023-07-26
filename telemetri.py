# -*- coding: UTF-8 -*-
import rospy
from std_msgs.msg import String
import requests
import json
gonderjson=""
kilitlenme_veri= ""
def callback_gonder(data):
    global gonderjson
    gonderjson = json.loads(data.data)

def callback_arma_no(data):
    global arma_no
    arma_no = json.loads(data.data)

def telemetri_gonder():
    global gonderjson
    data = gonderjson
    url = 'http://10.0.0.10:10001/api/telemetri_gonder'
    headers = {'Content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    telemetriler = response.json()
    if response.status_code == 200:
        json_data = json.dumps(telemetriler)
        msg = String()
        msg.data = json_data
        pub = rospy.Publisher('/uav/rakip_telemetriler', String, queue_size=10)
        pub.publish(msg)

def callback_kilitlenme(data):
    global kilitlenme_veri
    kilitlenme_veri = json.loads(data.data)
    if not kilitlenme_veri == "":
        print("Kilitlenme bilgisi gonderiliyor")
        url = 'http://10.0.0.10:10001/api/kilitlenme_bilgisi'
        data = kilitlenme_veri
        headers = {'Content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            print("Kilitlenme bilgisi gonderildi")
        else:
            print("Kilitlenme bilgisi gonderilemedi")
    else:
        pass
def listener():
    rospy.init_node("listener", anonymous=True)
    rospy.Subscriber("/uav/gonder", String, callback_gonder)
    rospy.Subscriber("/uav/arma_no", String, callback_arma_no)
    rospy.Subscriber("/uav/kilitlenme_veri", String, callback_kilitlenme)
    rate = rospy.Rate(2) # 5 Hz
    while not rospy.is_shutdown():
        telemetri_gonder()
        rate.sleep()

if __name__ == "__main__":
    listener()