import socket
import threading

from common import (
    APPOINTMENT_UDP_PORT,
    AUTH_UDP_PORT,
    HOST,
    HOSPITAL_TCP_PORT,
    HOSPITAL_UDP_PORT,
    PRESCRIPTION_UDP_PORT,
    hash_suffix,
    load_hospital_data,
    recv_tcp_json,
    send_tcp_json,
    send_udp_message,
)


def authenticate_user(username_hash: str, password_hash: str):#make request to auth server
    print("Hospital Server has sent an authentication request to the Authentication Server.")
    auth_response = send_udp_message(
        AUTH_UDP_PORT,
        {
            "action": "authenticate",
            "username_hash": username_hash,
            "password_hash": password_hash,
        },
    )
    print(
        f"Hospital server has received the response from the authentication server "
        f"using UDP over port {HOSPITAL_UDP_PORT}."
    )
    if not auth_response.get("authenticated"):
        return {"status": "error", "message": "The credentials are incorrect. Please try again."}

    print(
        f"User with a hash suffix {hash_suffix(username_hash)} has been granted "
        f"access to the system. Determining the access of the user."
    )

    hospital_data = load_hospital_data()
    role = "doctor" if username_hash in hospital_data["doctors"].values() else "patient"
    username = None
    if role == "doctor":
        for doctor_name, doctor_hash in hospital_data["doctors"].items():
            if doctor_hash == username_hash:
                username = doctor_name
                break
        print(f"User with hash {hash_suffix(username_hash)} will be granted doctor access.")
    else:
        print(f"User with hash {hash_suffix(username_hash)} will be granted patient access.")

    return {
        "status": "ok",
        "role": role,
        "username_hash": username_hash,
        "username": username,
    }


def handle_patient_command(request):
    action = request["command"]
    patient_hash = request["username_hash"]

    if action == "lookup":
        if "doctor" not in request:
            print(
                f"Hospital Server received a lookup request from a user with hash suffix "
                f"{hash_suffix(patient_hash)} over port {HOSPITAL_TCP_PORT}."
            )
            print("Hospital Server sent the doctor lookup request to the Appointment server.")
            response = send_udp_message(APPOINTMENT_UDP_PORT, {"action": "lookup_doctors"})
            print(
                f"Hospital Server has received the response from Appointment Server "
                f"using UDP over port {HOSPITAL_UDP_PORT}."
            )
            print("Hospital Server has sent the doctor lookup to the client.")
            return {"status": "ok", "doctors": response.get("doctors", [])}
        print(
            f"Hospital Server has received a lookup request from a user with hash suffix "
            f"{hash_suffix(patient_hash)} to lookup {request['doctor']} availability using "
            f"TCP over port {HOSPITAL_TCP_PORT}."
        )
        print("Hospital Server sent the doctor lookup request to the Appointment server.")
        response = send_udp_message(
            APPOINTMENT_UDP_PORT,
            {"action": "lookup_availability", "doctor": request["doctor"]},
        )
        print(
            f"Hospital Server has received the response from Appointment Server using UDP "
            f"over port {HOSPITAL_UDP_PORT}."
        )
        print("The Hospital Server has sent the response to the client.")
        return {"status": "ok", "doctor": request["doctor"], "slots": response.get("slots", [])}

    if action == "schedule":
        print(
            f"Hospital Server has received a schedule request from a user with hash suffix: "
            f"{hash_suffix(patient_hash)} to book an appointment using TCP over port "
            f"{HOSPITAL_TCP_PORT}."
        )
        print("Hospital Server has sent the schedule request to the appointment server.")
        response = send_udp_message(
            APPOINTMENT_UDP_PORT,
            {
                "action": "schedule",
                "doctor": request["doctor"],
                "time": request["time"],
                "patient_hash": patient_hash,
                "illness": request["illness"],
            },
        )
        print(
            f"Hospital Server has received the response from Appointment Server using UDP "
            f"over {HOSPITAL_UDP_PORT}."
        )
        print("The hospital server has sent the response to the client.")
        return response

    if action == "cancel":
        print(
            f"Hospital Server has received a cancel request from user with hash suffix: "
            f"{hash_suffix(patient_hash)} to cancel their appointment using TCP over port "
            f"{HOSPITAL_TCP_PORT}."
        )
        print("The hospital server has sent the cancel request to the appointment server.")
        response = send_udp_message(
            APPOINTMENT_UDP_PORT,
            {"action": "cancel", "patient_hash": patient_hash},
        )
        print(
            f"Hospital Server has received the response from Appointment Server using UDP "
            f"over port {HOSPITAL_UDP_PORT}."
        )
        print("The hospital server has sent the response to the client.")
        return response

    if action == "view_appointment":
        print(
            f"Hospital server has received a view appointment request from a user with hash "
            f"suffix {hash_suffix(patient_hash)} to view their appointment details using TCP "
            f"over port {HOSPITAL_TCP_PORT}."
        )
        print("Hospital Server has sent the view appointments request to the Appointment Server.")
        response = send_udp_message(
            APPOINTMENT_UDP_PORT,
            {"action": "view_patient_appointment", "patient_hash": patient_hash},
        )
        print(
            f"Hospital Server has received the response from the appointment server using UDP "
            f"over port {HOSPITAL_UDP_PORT}."
        )
        print("The hospital server has sent the response to the client.")
        return response

    if action == "view_prescription":
        print(
            f"Hospital Server has received a prescription request from a patient with hash "
            f"suffix {hash_suffix(patient_hash)} to view their prescription details using TCP "
            f"over port {HOSPITAL_TCP_PORT}."
        )
        print("Hospital Server has sent the prescription request to the Prescription Server.")
        response = send_udp_message(
            PRESCRIPTION_UDP_PORT,
            {"action": "view_prescriptions", "patient_hash": patient_hash},
        )
        print(
            f"Hospital server has received the response from the prescription server using "
            f"UDP over port {HOSPITAL_UDP_PORT}."
        )
        print("The hospital server has sent the response to the client.")
        return response

    return {"status": "error", "message": f"Unsupported patient command: {action}"}


def handle_doctor_command(request):
    action = request["command"]
    doctor = request["username"]
    hospital_data = load_hospital_data()

    if action == "view_appointments":
        print(
            f"Hospital Server has received a view appointments request from {doctor} to view "
            f"their schedule details using TCP over port {HOSPITAL_TCP_PORT}."
        )
        print("The hospital server has sent the view appointments request to the Appointment Server.")
        response = send_udp_message(
            APPOINTMENT_UDP_PORT,
            {"action": "view_doctor_appointments", "doctor": doctor},
        )
        print(
            f"Hospital server has received the response from the Appointment Server using UDP "
            f"over port {HOSPITAL_UDP_PORT}."
        )
        print("The hospital server has sent the response to the client.")
        return response

    if action == "prescribe":
        print(
            f"Hospital Server has received a prescription request from {doctor} for a user "
            f"with hash suffix {hash_suffix(request['patient_hash'])} using TCP over port "
            f"{HOSPITAL_TCP_PORT}."
        )
        print(
            f"Hospital Server has sent a request to fetch patients with hash suffix "
            f"{hash_suffix(request['patient_hash'])} illness information to the Appointment Server."
        )
        illness_response = send_udp_message(
            APPOINTMENT_UDP_PORT,
            {
                "action": "get_patient_illness",
                "patient_hash": request["patient_hash"],
                "doctor": doctor,
            },
        )
        print(
            f"Hospital Server has received the illness response from the Appointment server "
            f"using UDP over port {HOSPITAL_UDP_PORT}."
        )
        if not illness_response.get("found"):
            return {
                "status": "ok",
                "success": False,
                "message": "The patient does not have an appointment on record.",
            }
        treatment = hospital_data["treatments"].get(illness_response["illness"].lower())
        if not treatment:
            return {
                "status": "ok",
                "success": False,
                "message": f'No treatment found for illness "{illness_response["illness"]}".',
            }
        print(f"Acquiring treatment for {illness_response['illness']} from the database.")
        print(
            f"Hospital server has sent the prescription request to the prescription server "
            f"to prescribe {treatment}."
        )
        result = send_udp_message(
            PRESCRIPTION_UDP_PORT,
            {
                "action": "add_prescription",
                "doctor": doctor,
                "patient_hash": request["patient_hash"],
                "treatment": treatment,
                "frequency": request["frequency"],
            },
        )
        print(
            f"Hospital server has received the response from the prescription server using "
            f"UDP over port {HOSPITAL_UDP_PORT}."
        )
        if result.get("success"):
            print("Hospital Server has sent a request to clear the completed appointment.")
            completion_result = send_udp_message(
                APPOINTMENT_UDP_PORT,
                {
                    "action": "complete_appointment",
                    "doctor": doctor,
                    "patient_hash": request["patient_hash"],
                },
            )
            print(
                f"Hospital Server has received the appointment completion response from "
                f"Appointment Server using UDP over port {HOSPITAL_UDP_PORT}."
            )
            result["appointment_cleared"] = completion_result.get("success", False)
        print("The hospital server has sent the response to the client.")
        result["treatment"] = treatment
        return result

    if action == "view_prescription":
        print(
            f"Hospital Server has received a prescription request from {doctor} to view a "
            f"patient with hash suffix {hash_suffix(request['patient_hash'])} prescription "
            f"details using TCP over port {HOSPITAL_TCP_PORT}."
        )
        print("Hospital Server has sent the prescription request to the Prescription Server.")
        response = send_udp_message(
            PRESCRIPTION_UDP_PORT,
            {"action": "view_prescriptions", "patient_hash": request["patient_hash"]},
        )
        print(
            f"Hospital server has received the response from the prescription server using "
            f"UDP over port {HOSPITAL_UDP_PORT}."
        )
        print("The hospital server has sent the response to the client.")
        return response

    return {"status": "error", "message": f"Unsupported doctor command: {action}"}


def handle_client(connection: socket.socket, address):
    with connection:
        with connection.makefile("rb") as file_obj:
            while True:
                request = recv_tcp_json(file_obj)
                if request is None:
                    break
                action = request.get("action")

                if action == "authenticate":
                    print(
                        f"Hospital Server received an authentication request from a user with hash "
                        f"suffix {hash_suffix(request['username_hash'])}."
                    )
                    response = authenticate_user(request["username_hash"], request["password_hash"])
                elif action == "command":
                    role = request["role"]
                    if role == "patient":
                        response = handle_patient_command(request)
                    else:
                        response = handle_doctor_command(request)
                else:
                    response = {"status": "error", "message": "Unknown action."}

                send_tcp_json(connection, response)
                if action == "authenticate" and response["status"] == "ok":
                    print(
                        f"Hospital Server has sent the response from Authentication Server to the "
                        f"client using TCP over port {HOSPITAL_TCP_PORT}."
                    )


def main() -> None:
    # A dedicated UDP port is kept to match the project topology and logging expectations.
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((HOST, HOSPITAL_UDP_PORT))
    udp_sock.close()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)# you can reuse the port
        server.bind((HOST, HOSPITAL_TCP_PORT))
        server.listen()
        print(f"Hospital Server is up and running using UDP on port {HOSPITAL_UDP_PORT}.")

        while True:
            connection, address = server.accept()
            thread = threading.Thread(target=handle_client, args=(connection, address), daemon=True)
            thread.start()


if __name__ == "__main__":
    main()
