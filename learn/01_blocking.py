import time


def kerja(nama, detik):
    print(f"mulai {nama}")
    time.sleep(detik)
    print(f"selesai {nama}")
    return time.perf_counter()

start_time = time.perf_counter()
kerja("A", 2)
kerja("B", 2)
end_time = time.perf_counter()
print(f"Total waktu: {end_time - start_time}")