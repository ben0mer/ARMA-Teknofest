import json
from pyproj import Proj
import math
import rospy
from std_msgs.msg import String
# UTM projeksiyonu oluştur
utm = Proj(proj='utm', zone=37, south=True, ellps='WGS84', preserve_units=False)
lat_home, lon_home, alt_home = [0 ,0 ,0]
home = ""
kendi_takim = ""
veri = None

# Global verileri local verilere dönüştüren fonksiyon (home verilerine göre)
def global_to_local(lat_target, lon_target, alt_target):
    global lat_home, lon_home, alt_home
    # Home global verilerini UTM projeksiyonuna dönüştür
    x_home, y_home = utm(lon_home, lat_home) # x: east_m, y: north_m
    z_home = -alt_home # z: down_m
    # Target global verilerini UTM projeksiyonuna dönüştür
    x_target, y_target = utm(lon_target, lat_target) # x: east_m, y: north_m
    z_target = -alt_target # z: down_m
    # Local verileri home verilerine göre hesapla
    x_local = x_target - x_home
    y_local = y_target - y_home
    z_local = z_target - z_home
    # Local verileri döndür
    return x_local, y_local, z_local



def veri_guncelle(veri):
    konumlar = veri['konumBilgileri'] # konum bilgilerini bir liste içinde tut
    rakip = [] # rakip listesini boş olarak oluştur
    rakip_local = [] # local verileri tutacak boş bir liste oluştur
    kendi_takim_bilgisi = None
    kendi_local_bilgisi = []
    for konum in konumlar: # konumlar listesini döngüye al
        if konum["takim_numarasi"] == int(kendi_takim): # eğer takım numarası kendi takım numarasına eşitse
            kendi_takim_bilgisi = konum # o elemanı kendi_takim_bilgisi değişkenine ata
            x_local, y_local, z_local = global_to_local(konum["iha_enlem"], konum["iha_boylam"], konum["iha_irtifa"])
            kendi_local_bilgisi = {"x": x_local, "y": y_local, "z": z_local}
        else: # değilse
            rakip.append(konum) # o elemanı rakip listesine ekle
            # her rakibin enlem, boylam ve irtifa bilgilerini global_to_local() fonksiyonuna ver
            x_local, y_local, z_local = global_to_local(konum["iha_enlem"], konum["iha_boylam"], konum["iha_irtifa"])
            # fonksiyondan dönen değerleri bir sözlük olarak local_veriler listesine ekle
            rakip_local.append({"x": x_local, "y": y_local, "z": z_local})
    return rakip, rakip_local, kendi_takim_bilgisi, kendi_local_bilgisi # rakip listesini, kendi takım bilgisini ve local_veriler listesini döndür


def rakip_uzaklik(rakipler_local,kendi_local_bilgisi):
    uzakliklar= []
    x_our = kendi_local_bilgisi["x"]
    y_our = kendi_local_bilgisi["y"]
    z_our = kendi_local_bilgisi["z"]
    for i in rakipler_local:
        x_target = i["x"]
        y_target = i["y"]
        z_target = i["z"]
        d = math.sqrt((x_target - x_our) ** 2 + (y_target - y_our) ** 2 + (z_target - z_our) ** 2)
        uzakliklar.append(d)
    en_yakin_mesafe = min(uzakliklar)
    en_yakin_indeks = uzakliklar.index(en_yakin_mesafe)
    return uzakliklar, en_yakin_mesafe, en_yakin_indeks


def tahmin(hedef,hedef_local):
    # uçağın x, y ve z koordinatlarını metre cinsinden değişkenlere ata
    x=hedef_local["x"]
    y=hedef_local["y"]
    z=hedef_local["z"]
    roll = hedef["iha_yatis"]
    pitch = hedef["iha_dikilme"]
    yaw = hedef["iha_yonelme"]
    hiz=18

    a = hiz * math.cos(math.radians(abs(roll)))
    aci = 90 - (yaw + roll)
    b = a*math.cos(math.radians(pitch))
    zt = b*math.sin(math.radians(pitch))
    yeni_z = round(z + zt,6)
    alfa = 180-(90+pitch)
    a_fark = zt/(math.tan(math.radians(alfa)))
    yeni_a = a - a_fark
    yeni_x = yeni_a*math.sin(math.radians(aci))
    yeni_y = yeni_a*math.cos(math.radians(aci))
    yeni_x = round(x + yeni_x, 6)
    yeni_y = round(y + yeni_y, 6)

    return yeni_y, yeni_x, yeni_z

def callback_home(data):
    global home, lat_home, lon_home, alt_home
    home = json.loads(data.data)
    lat_home = home["home_enlem"]
    lon_home = home["home_boylam"]
    alt_home = home["home_irtifa"]

def callback_arma_no(data):
    global kendi_takim
    kendi_takim = json.loads(data.data)

def callback_rakip_telemetri(data):
    global veri
    veri = json.loads(data.data)
    

def listener():
    global kendi_takim
    rospy.init_node("listener", anonymous=True)
    rospy.Subscriber("/uav/home", String, callback_home)
    rospy.Subscriber("/uav/rakip_telemetriler", String, callback_rakip_telemetri)
    rospy.Subscriber("/uav/arma_no", String, callback_arma_no)
    rate = rospy.Rate(5) # 5 Hz
    while not rospy.is_shutdown():
        global veri
        if veri == None:
            pass
        else:
            rakipler, rakipler_local, ben, ben_local = veri_guncelle(veri)
            uzakliklar, en_yakin_mesafe, en_yakin_indeks = rakip_uzaklik(rakipler_local, ben_local)
            hedef = rakipler[en_yakin_indeks]
            hedef_local = rakipler_local[en_yakin_indeks]
            x_tahmin, y_tahmin, z_tahmin = tahmin(hedef, hedef_local)
            tahminler = {"x": x_tahmin,
                        "y": y_tahmin,
                        "z": z_tahmin,
                        "uzaklik": uzakliklar[en_yakin_indeks]}
            tahminler = json.dumps(tahminler)
            msg = String()
            msg.data = tahminler
            pub = rospy.Publisher('/uav/poztahmin', String, queue_size=10)
            pub.publish(msg)
        rate.sleep()
if __name__ == "__main__":
    print("Rota Olusturucu Baslatiliyor..")
    listener()