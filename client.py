import socket
import sys

from common import HOST, HOSPITAL_TCP_PORT, hash_suffix, recv_tcp_json, send_tcp_json, sha256_hash


PATIENT_HELP = """Please enter the command:
<lookup>
<lookup <doctor>>
<schedule <doctor> <start_time> <illness>>
<cancel>
<view_appointment>
<view_prescription>
<quit>"""

DOCTOR_HELP = """Please enter the command:
<view_appointments>
<prescribe <patient> <frequency>>
<view_prescription <patient>>
<quit>"""


def send_request(sock: socket.socket, file_obj, payload):
    send_tcp_json(sock, payload)
    response = recv_tcp_json(file_obj)
    if response is None:
        raise ConnectionError("Hospital server closed the connection.")
    return response


def print_received_from_hospital(client_port: int):
    print(
        f"The client received the response from the hospital server using TCP "
        f"over port {client_port}."
    )


def authenticate(sock: socket.socket, file_obj, username: str, password: str):#
    username_hash = sha256_hash(username)
    password_hash = sha256_hash(password)
    print(f"{username} sent an authentication request to the hospital server.")
    response = send_request(
        sock,
        file_obj,
        {
            "action": "authenticate",
            "username_hash": username_hash,
            "password_hash": password_hash,
        },
    )
    if response["status"] != "ok":
        print(response["message"])
        return None
    if response["role"] == "doctor":
        print(f"{username} received the authentication result. Authentication successful. You have been granted doctor access.")
    else:
        print(f"{username} received the authentication result. Authentication successful. You have been granted patient access.")
    response["plain_username"] = username
    response["username_hash"] = username_hash
    return response


def print_patient_response(username: str, command: str, response):
    if command == "lookup":
        doctors = response.get("doctors", [])
        print_received_from_hospital(response["client_port"])
        print(f"The following doctors are available:")
        for doctor in doctors:
            print(doctor)
        return
    if command.startswith("lookup "):
        doctor = response.get("doctor")
        slots = response.get("slots", [])
        print_received_from_hospital(response["client_port"])
        if len(slots) == 8:
            print(f"All time blocks are available for {doctor}.")
            return
        if slots:
            print(f"{doctor} is available at times:")
            for slot in slots:
                print(slot)
        else:
            print(f"{doctor} has no time slots available.")
        return
    if command.startswith("schedule "):
        doctor = command.split()[1]
        time_slot = command.split()[2]
        print_received_from_hospital(response["client_port"])
        if response.get("success"):
            print(
                f"An appointment has been successfully scheduled for patient "
                f"{username} with {doctor} at {time_slot}."
            )
        else:
            print(
                f"Unable to schedule an appointment with {doctor} at "
                f"{time_slot}."
            )
        return
    if command == "cancel":
        print_received_from_hospital(response["client_port"])
        if response.get("success"):
            print(
                f"You have successfully cancelled your appointment with "
                f"{response['doctor']} at {response['time']}."
            )
        else:
            print("You have no appointments available to cancel.")
        return
    if command == "view_appointment":
        print_received_from_hospital(response["client_port"])
        if response.get("found"):
            print(
                f"You have an appointment scheduled with {response['doctor']} "
                f"at {response['time']}."
            )
        else:
            print("You do not have an appointment today.")
        return
    if command == "view_prescription":
        prescriptions = response.get("prescriptions", [])
        print_received_from_hospital(response["client_port"])
        if not prescriptions:
            print("You do not have a prescription to look up.")
            return
        item = prescriptions[0]
        if item["frequency"] == "None":
            print(
                f"You were not prescribed any treatment by "
                f"{item['doctor']} following your diagnosis."
            )
        else:
            print(
                f"You have been prescribed {item['treatment']}, to be taken "
                f"{item['frequency']}, by {item['doctor']}."
            )


def print_doctor_response(command: str, response):
    if command == "view_appointments":
        appointments = response.get("appointments", [])
        doctor = response.get("doctor_name", "Doctor")
        print_received_from_hospital(response["client_port"])
        if not appointments:
            print("You do not have any appointments scheduled.")
            return
        print(f"{doctor} is scheduled at times:")
        for item in appointments:
            print(item["time"])
        return
    if command.startswith("prescribe "):
        patient_name = command.split()[1]
        print_received_from_hospital(response["client_port"])
        if response.get("success"):
            print(
                f"You have successfully prescribed {patient_name} with "
                f"{response['treatment']}, to be taken {command.split()[2]}."
            )
        else:
            print(response.get("message", "Prescription failed."))
        return
    if command.startswith("view_prescription "):
        patient_name = command.split()[1]
        prescriptions = response.get("prescriptions", [])
        print_received_from_hospital(response["client_port"])
        if not prescriptions:
            print(f"{patient_name} does not have a prescription.")
            return
        item = prescriptions[0]
        print(
            f"{patient_name} has been prescribed {item['treatment']}, to be "
            f"taken {item['frequency']}, by {item['doctor']}."
        )


def print_patient_request(username: str, command: str):
    if command == "lookup":
        print(f"{username} sent a lookup request to the hospital server.")
    elif command.startswith("lookup "):
        doctor = command.split()[1]
        print(f"Patient {username} sent a lookup request to the hospital server for {doctor}.")
    elif command.startswith("schedule "):
        print(f"{username} sent an appointment schedule request to the hospital server.")
    elif command == "cancel":
        print(f"{username} sent a cancellation request to the Hospital Server.")
    elif command == "view_appointment":
        print(f"{username} sent a request to view their appointment to the Hospital Server.")
    elif command == "view_prescription":
        print(f"{username} sent a request to view their prescription to the Hospital Server.")


def print_doctor_request(username: str, command: str):
    if command == "view_appointments":
        print(
            f"{username} sent a request to view their scheduled appointments to the "
            f"Hospital Server."
        )
    elif command.startswith("prescribe "):
        patient = command.split()[1]
        print(
            f"{username} sent a request to the Hospital Server to prescribe "
            f"{patient} following their diagnosis."
        )
    elif command.startswith("view_prescription "):
        patient = command.split()[1]
        print(
            f"{username} sent a request to view {patient} prescription to the "
            f"Hospital Server."
        )


def parse_patient_command(command: str, state):
    parts = command.split()
    if command == "lookup":
        return {
            "action": "command",
            "role": "patient",
            "command": "lookup",
            "username_hash": state["username_hash"],
        }
    if len(parts) == 2 and parts[0] == "lookup":
        return {
            "action": "command",
            "role": "patient",
            "command": "lookup",
            "doctor": parts[1],
            "username_hash": state["username_hash"],
        }
    if len(parts) >= 4 and parts[0] == "schedule":
        illness = " ".join(parts[3:])
        return {
            "action": "command",
            "role": "patient",
            "command": "schedule",
            "doctor": parts[1],
            "time": parts[2],
            "illness": illness,
            "username_hash": state["username_hash"],
        }
    if command == "cancel":
        return {
            "action": "command",
            "role": "patient",
            "command": "cancel",
            "username_hash": state["username_hash"],
        }
    if command == "view_appointment":
        return {
            "action": "command",
            "role": "patient",
            "command": "view_appointment",
            "username_hash": state["username_hash"],
        }
    if command == "view_prescription":
        return {
            "action": "command",
            "role": "patient",
            "command": "view_prescription",
            "username_hash": state["username_hash"],
        }
    return None


def parse_doctor_command(command: str, state):
    parts = command.split()
    if command == "view_appointments":
        return {
            "action": "command",
            "role": "doctor",
            "command": "view_appointments",
            "username": state["username"],
            "username_hash": state["username_hash"],
        }
    if len(parts) == 3 and parts[0] == "prescribe":
        return {
            "action": "command",
            "role": "doctor",
            "command": "prescribe",
            "username": state["username"],
            "username_hash": state["username_hash"],
            "patient_hash": sha256_hash(parts[1]),
            "frequency": parts[2],
        }
    if len(parts) == 2 and parts[0] == "view_prescription":
        return {
            "action": "command",
            "role": "doctor",
            "command": "view_prescription",
            "username": state["username"],
            "username_hash": state["username_hash"],
            "patient_hash": sha256_hash(parts[1]),
        }
    return None


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python3 client.py <username> <password>")
        raise SystemExit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, HOSPITAL_TCP_PORT))
        with sock.makefile("rb") as file_obj:
            print("The client is up and running.")
            state = authenticate(sock, file_obj, username, password)
            if state is None:#authenication failed
                return
            state["client_port"] = sock.getsockname()[1]

            while True:
                if state["role"] == "patient":
                    print(PATIENT_HELP)
                    command = input("> ").strip()
                    if command == "quit":
                        print("You have successfully been logged out.")
                        print("—Quit Program—")
                        return
                    payload = parse_patient_command(command, state)
                    if payload is None:
                        print("Invalid patient command.")
                        continue
                    print_patient_request(username, command)
                    response = send_request(sock, file_obj, payload)
                    response["client_port"] = state["client_port"]
                    print_patient_response(username, command, response)
                else:
                    print(DOCTOR_HELP)
                    command = input("> ").strip()
                    if command == "quit":
                        print("You have successfully been logged out.")
                        print("—Quit Program—")
                        return
                    payload = parse_doctor_command(command, state)
                    if payload is None:
                        print("Invalid doctor command.")
                        continue
                    print_doctor_request(username, command)
                    response = send_request(sock, file_obj, payload)
                    response["client_port"] = state["client_port"]
                    response["doctor_name"] = username
                    print_doctor_response(command, response)


if __name__ == "__main__":
    main()
