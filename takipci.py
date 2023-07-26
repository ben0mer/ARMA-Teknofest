import asyncio
import json, os
from mavsdk import System
from mavsdk.offboard import (Attitude, OffboardError, PositionNedYaw)
import rospy
from std_msgs.msg import String
tahmin = None
def callback_tahminler(data):
    global tahmin
    tahmin = json.loads(data.data)

async def run():
    #uav1
    global tahmin
    drone = System(port=14031)
    await drone.connect(system_address="udp://:14031")

    print("IHA'ya Baglaniliyor...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- IHA'ya Baglanildi!")
            break

    print("Global pozisyon tahmini aliniyor...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global pozisyon -> OK")
            break
        print("-- Motorlar Calisiyor")

    await drone.action.arm()
    print("-- Baslangic Noktasi Ayarlandi")
    await drone.offboard.set_attitude(Attitude(0.0, 0.0, 0.0, 0.0))

    print("-- OFFBOARD Mod Baslatiliyor")
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"OFFBOARD Mod baslatilirken hata: \
              {error._result.result}")
        print("-- Motorlar Durduruluyor")
        await drone.action.disarm()
        return

    print("-- %70 Guc ile yukseliniyor")
    async for position in drone.telemetry.position_velocity_ned():
        print(f"Yukseklik = {-position.position.down_m}")
        if (50 <= -position.position.down_m ):
            break
        else:
            await drone.offboard.set_attitude(Attitude(0.0, 15.0, 0.0, 0.7))
            continue
    print("-- 50 Metreye Ulasildi")

    async for position in drone.telemetry.position_velocity_ned():
        north = position.position.north_m
        east = position.position.east_m
        down = position.position.down_m
        rospy.init_node("listener", anonymous=True)
        rospy.Subscriber("/uav/tahminler", String, callback_tahminler)
        if tahmin == None:
            pass
        else:
            x_h = tahmin["x"]
            y_h = tahmin["y"]
            z_h = -tahmin["z"]
            distance_to_target = ((north - x_h)**2 + (east - y_h)**2 + (down - z_h)**2)**0.5
            print(f"Hedefe uzaklik -> {distance_to_target}")
            await drone.offboard.set_position_ned(PositionNedYaw(x_h, y_h, -z_h, 0.0))
            await asyncio.sleep(0.2)

if __name__ == "__main__":
    asyncio.run(run())