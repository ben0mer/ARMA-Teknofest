import asyncio

from mavsdk import System
from mavsdk.offboard import (Attitude, OffboardError, PositionNedYaw)
import math

async def run():
    """ Does Offboard control using attitude commands. """

    drone = System(port=14030)
    await drone.connect(system_address="udp://:14030")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Setting initial setpoint")
    await drone.offboard.set_attitude(Attitude(0.0, 0.0, 0.0, 0.0))

    print("-- Starting offboard")
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"Starting offboard mode failed with error code: \
              {error._result.result}")
        print("-- Disarming")
        await drone.action.disarm()
        return

    print("-- Go up at 70% thrust")
    async for position in drone.telemetry.position_velocity_ned():
        print(f"Yukseklik = {-position.position.down_m}")
        if (50 <= -position.position.down_m ):
            break
        else:
            await drone.offboard.set_attitude(Attitude(0.0, 15.0, 0.0, 0.7))
            continue
    print("50 Metreye Ulasildi")
    aci=0
    yaricap=350
    x=yaricap*(math.sin(math.radians(aci)))
    y=yaricap*(math.cos(math.radians(aci)))
    x2=(yaricap+100)*(math.sin(math.radians(aci)))
    y2=(yaricap+100)*(math.cos(math.radians(aci)))
    x3=114*(math.sin(math.radians(aci)))
    y3=114*(math.cos(math.radians(aci)))

    hedefler = [
        (x2, y2, -50.0),
        (x, y, -30.0),
        (x3, y3, -10.0)
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
    # Run the asyncio loop
    asyncio.run(run())