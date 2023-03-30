import socket
import ssl
import time

HOST="192.168.0.12"
PORT=64321

sslcntxt = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
sslcntxt.load_verify_locations('public.pem')
while True:
    s = socket.socket()
    sslsocketwrapper = sslcntxt.wrap_socket(s, server_hostname=HOST)
    sslsocketwrapper.connect((HOST, PORT))
    data = sslsocketwrapper.recv(1024).decode('utf-8')
    sslsocketwrapper.close()
    print(data)

    humadity, temperature = data.split(',')
    print(humadity)
    print(temperature)
    time.sleep(3)


