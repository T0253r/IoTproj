import paho.mqtt.client as mqtt
from queue import Queue, Empty
import threading
import time

BROKER = "127.0.0.1"
PORT = 1883


response_queue = Queue()
current_temp = { "room1" : 0}

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "server")

def SEND(x):
    return f"room{x}/listen"

def LISTEN(x):
    return f"room{x}/send"

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    if payload.startswith("OK"):
        response_queue.put(payload)
    elif payload.startswith("ping"):
        parts = payload.split()
        if len(parts) == 4:
            _, room, temp, target = parts
            current_temp[room] = (temp, target)

def setupMQQT():
    client.connect(BROKER, PORT)
    client.loop_start()

def subscribe(listen):
    client.subscribe(listen)


def send_to(roomID, temp, timeout=3, retries=3):
    if retries <=0:
        raise TimeoutError("Brak OK")

    for attempt in range(1, retries + 1):
        client.publish(SEND(roomID), f"{temp}")
        try:
            return response_queue.get(timeout=timeout)
        except Empty:
            send_to(roomID, temp, timeout, retries-1)

def ping_loop(roomID):
    topic = SEND(roomID)
    while True:
        client.publish(topic, "ping")
        time.sleep(2)

def start():
    setupMQQT()
    client.on_message = on_message
    subscribe(LISTEN(1))
    threading.Thread(target=ping_loop, args=(1,), daemon=True).start()

"""while True:
    temp = input("Target temp: ")
    print(current_temp["room1"])
    print(send_to(1, temp))"""