import socket

from common import AUTH_UDP_PORT, HOST, hash_suffix, load_users, recv_udp_json, send_udp_json


def main() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST, AUTH_UDP_PORT))
        print(f"Authentication Server is up and running using UDP on port {AUTH_UDP_PORT}.")

        while True:
            request, address = recv_udp_json(sock)
            if request.get("action") != "authenticate":
                send_udp_json(sock, {"status": "error", "message": "Unknown action."}, address)
                continue

            username_hash = request["username_hash"]
            password_hash = request["password_hash"]
            # Reload the credential file on each request so the server always
            # reflects the latest users.txt content after local edits.
            users = load_users()
            authenticated = users.get(username_hash) == password_hash
            print(
                f"Authentication Server has received an authentication request for a user with hash suffix: "
                f"{hash_suffix(username_hash)}."
            )
            if authenticated:
                print(
                    f"Authentication succeeded for a user with hash suffix: "
                    f"{hash_suffix(username_hash)}."
                )
            else:
                print(
                    f"Authentication failed for a user with hash suffix: "
                    f"{hash_suffix(username_hash)}."
                )
            send_udp_json(sock, {"status": "ok", "authenticated": authenticated}, address)
            print("The Authentication Server has sent the authentication result to the Hospital Server.")


if __name__ == "__main__":
    main()
