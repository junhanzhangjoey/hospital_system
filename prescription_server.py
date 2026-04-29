import socket

from common import (
    HOST,
    PRESCRIPTION_UDP_PORT,
    hash_suffix,
    load_prescriptions,
    recv_udp_json,
    save_prescriptions,
    send_udp_json,
)


def add_prescription(doctor: str, patient_hash: str, treatment: str, frequency: str):
    prescriptions = load_prescriptions()
    prescriptions.append(
        {
            "doctor": doctor,
            "patient_hash": patient_hash,
            "treatment": treatment,
            "frequency": frequency,
        }
    )
    save_prescriptions(prescriptions)
    print(
        f"Successfully saved the prescription details for user with hash suffix: "
        f"{hash_suffix(patient_hash)}."
    )
    return {"status": "ok", "success": True}


def view_prescriptions(patient_hash: str):
    prescriptions = load_prescriptions()
    results = [item for item in prescriptions if item["patient_hash"] == patient_hash]
    if not results or any(item["frequency"] == "None" for item in results):
        print("There are no current prescriptions for this user.")
    else:
        print("A prescription exists for this user.")
    return {"status": "ok", "prescriptions": results}


def main() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST, PRESCRIPTION_UDP_PORT))
        print(
            f"Prescription Server is up and running using UDP on port {PRESCRIPTION_UDP_PORT}."
        )

        while True:
            request, address = recv_udp_json(sock)
            action = request.get("action")
            if action == "add_prescription":
                print(
                    f"Prescription Server has received a request from "
                    f"{request['doctor']} to prescribe the user with hash suffix "
                    f"{hash_suffix(request['patient_hash'])}."
                )
                response = add_prescription(
                    request["doctor"],
                    request["patient_hash"],
                    request["treatment"],
                    request["frequency"],
                )
            elif action == "view_prescriptions":
                print(
                    f"The prescription server has received a request to view the "
                    f"prescription for the user with hash suffix: "
                    f"{hash_suffix(request['patient_hash'])}."
                )
                response = view_prescriptions(request["patient_hash"])
            else:
                response = {"status": "error", "message": "Unknown action."}
            send_udp_json(sock, response, address)


if __name__ == "__main__":
    main()
