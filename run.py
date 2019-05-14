from gmondflux.udp_server import GmondReceiver

if __name__ == "__main__":
    print("starting up...")

    GmondReceiver(":8649").serve_forever()

