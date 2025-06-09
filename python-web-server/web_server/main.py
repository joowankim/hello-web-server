from web_server.server import Server


def main():
    server = Server(host="localhost", port=8000)
    server.run()


if __name__ == "__main__":
    main()
