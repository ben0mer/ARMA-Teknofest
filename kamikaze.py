import asyncio
from mavsdk import System
from mavsdk.offboard import (Attitude, OffboardError, PositionNedYaw)
import math

async def run():
    #uav1
    global tahmin
    drone = System(port=14030)
    await drone.connect(system_address="udp://:14030")

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

    asyncio.sleep(5)
    await drone.offboard.set_attitude(Attitude(0.0, -30.0, 0.0, 0.4))
    async for position in drone.telemetry.position_velocity_ned():
        north = position.position.north_m
        east = position.position.east_m
        down = -position.position.down_m
        if down <= 30:
            await drone.offboard.set_attitude(Attitude(0.0, 30.0, 0.0, 0.7))
            break
        else:
            continue
    async for position in drone.telemetry.position_velocity_ned():
        north = position.position.north_m
        east = position.position.east_m
        down = -position.position.down_m
        if down >= 50:
            await drone.offboard.set_attitude(Attitude(0.0, 0.0, 0.0, 0.5))
            break
        else:
            continue
    asyncio.sleep(4)
    await drone.offboard.set_attitude(Attitude(30.0, 0.0, 0.0, 0.5))
    asyncio.sleep(4)
    await drone.offboard.set_attitude(Attitude(0.0, 0.0, 0.0, 0.5))
    aci=0
    yaricap=350
    x=yaricap*(math.sin(math.radians(aci)))
    y=yaricap*(math.cos(math.radians(aci)))
    x2=(yaricap+100)*(math.sin(math.radians(aci)))
    y2=(yaricap+100)*(math.cos(math.radians(aci)))
    x3=114*(math.sin(math.radians(aci)))
    y3=114*(math.cos(math.radians(aci)))

    hedefler = [
        (x2, y2, -40.0),
        (x, y, -20.0),
        (x3, y3, -6.0)
    ]        
    for hedef in hedefler:
        print(f"Hedefe gidiliyor: {hedef}")
        async for position in drone.telemetry.position_velocity_ned():
            north = position.position.north_m
            east = position.position.east_m
            down = position.position.down_m
            # Hedef noktaya varıldığını kontrol et
            distance_to_target = ((north - hedef[0])**2 + (east - hedef[1])**2 + (down - hedef[2])**2)**0.5
            print(f"Hedefe Uzaklık --> {distance_to_target}")
            if distance_to_target < 18.0:  # 1 metre hata toleransı
                print("Hedef noktaya varıldı")
                break
            # Hedefe doğru hareket
            await drone.offboard.set_position_ned(PositionNedYaw(hedef[0], hedef[1], hedef[2], 0.0))
            await asyncio.sleep(0.1)

    print("Inis Basliyor")

    print("%5 eğim ile alcaliniyor..")
    async for position in drone.telemetry.position_velocity_ned():
        print(f"Yukseklik = {-position.position.down_m}")
        if ( -position.position.down_m <= 0.3):
            await drone.action.kill()
            break
        else:
            await drone.offboard.set_attitude(Attitude(0.0, -5.0, 0.0, 0.1))
            continue
    try:
        await drone.offboard.stop()
    except OffboardError as error:
        print(f"Stopping offboard mode failed with error code: \
              {error._result.result}")
if __name__ == "__main__":
    asyncio.run(run())