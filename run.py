from gmondflux.udp_server import GmondReceiver

if __name__ == "__main__":
    print("starting up...")

    r = GmondReceiver(":8649")
    r.serve_forever()
