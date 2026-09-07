import asyncio
import time


async def kerja(nama, detik):
    print(f"mulai {nama}")
    await asyncio.sleep(detik)
    print(f"selesai {nama}")
    return time.perf_counter()

async def main():
    #versi a
    start_time1 = time.perf_counter()
    await kerja("A", 2)
    await kerja("B", 2)
    end_time1 = time.perf_counter()
    print(f"Total waktu: {end_time1 - start_time1}")    
    #versi b
    start_time2 = time.perf_counter()
    await asyncio.gather(
        kerja("A", 2),
        kerja("B", 2)
    )
    end_time2 = time.perf_counter()
    print(f"Total waktu: {end_time2 - start_time2}")

asyncio.run(main())