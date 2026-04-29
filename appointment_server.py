import socket

from common import (
    APPOINTMENT_UDP_PORT,
    APPOINTMENTS_FILE,
    HOST,
    build_default_slots,
    hash_suffix,
    load_appointments,
    recv_udp_json,
    save_appointments,
    send_udp_json,
)


def ensure_dataset():
    appointments = load_appointments()
    if appointments:
        return appointments
    appointments = {"drsmith": build_default_slots(), "drlee": build_default_slots()}
    save_appointments(appointments)
    return appointments


def available_slots(doctor: str):
    appointments = load_appointments()
    return [slot["time"] for slot in appointments.get(doctor, []) if not slot["patient_hash"]]


def schedule_slot(doctor: str, time_slot: str, patient_hash: str, illness: str):
    appointments = load_appointments()
    for slots in appointments.values():
        for slot in slots:
            if slot["patient_hash"] == patient_hash:
                return {
                    "status": "ok",
                    "success": False,
                    "message": "The patient already has an appointment.",
                }
    for slot in appointments.get(doctor, []):
        if slot["time"] != time_slot:
            continue
        if slot["patient_hash"]:
            return {
                "status": "ok",
                "success": False,
                "message": "The requested appointment time is not available.",
            }
        slot["patient_hash"] = patient_hash
        slot["illness"] = illness
        save_appointments(appointments)
        return {"status": "ok", "success": True, "message": "Appointment scheduled."}
    return {
        "status": "ok",
        "success": False,
        "message": "The requested appointment time is not available.",
    }


def cancel_appointment(patient_hash: str):
    appointments = load_appointments()
    for doctor, slots in appointments.items():
        for slot in slots:
            if slot["patient_hash"] == patient_hash:
                slot["patient_hash"] = ""
                slot["illness"] = ""
                save_appointments(appointments)
                return {
                    "status": "ok",
                    "success": True,
                    "message": "Appointment canceled.",
                    "doctor": doctor,
                    "time": slot["time"],
                }
    return {"status": "ok", "success": False, "message": "No appointment found."}


def view_patient_appointment(patient_hash: str):
    appointments = load_appointments()
    for doctor, slots in appointments.items():
        for slot in slots:
            if slot["patient_hash"] == patient_hash:
                return {
                    "status": "ok",
                    "found": True,
                    "doctor": doctor,
                    "time": slot["time"],
                    "illness": slot["illness"],
                }
    return {"status": "ok", "found": False}


def view_doctor_appointments(doctor: str):
    appointments = load_appointments()
    scheduled = [
        {"time": slot["time"], "patient_hash": slot["patient_hash"], "illness": slot["illness"]}
        for slot in appointments.get(doctor, [])
        if slot["patient_hash"]
    ]
    return {"status": "ok", "appointments": scheduled}


def get_patient_illness(patient_hash: str, doctor: str):
    appointments = load_appointments()
    for slot in appointments.get(doctor, []):
        if slot["patient_hash"] == patient_hash:
            return {
                "status": "ok",
                "found": True,
                "doctor": doctor,
                "illness": slot["illness"],
                "time": slot["time"],
            }
    return {"status": "ok", "found": False}


def complete_appointment(patient_hash: str, doctor: str):
    appointments = load_appointments()
    for slot in appointments.get(doctor, []):
        if slot["patient_hash"] == patient_hash:
            slot["patient_hash"] = ""
            slot["illness"] = ""
            save_appointments(appointments)
            return {"status": "ok", "success": True, "time": slot["time"]}
    return {"status": "ok", "success": False}


def main() -> None:
    ensure_dataset()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST, APPOINTMENT_UDP_PORT))
        print(
            f"Appointment Server is up and running using UDP on port {APPOINTMENT_UDP_PORT}."
        )

        while True:
            request, address = recv_udp_json(sock)
            action = request.get("action")

            if action == "lookup_doctors":
                print("The Appointment Server has received a doctor availability request.")
                appointments = load_appointments()
                send_udp_json(sock, {"status": "ok", "doctors": list(appointments)}, address)
                print("The Appointment Server has sent the lookup result to the Hospital Server.")
            elif action == "lookup_availability":
                doctor = request["doctor"]
                slots = available_slots(doctor)

                print("The Appointment Server has received a doctor availability request.")

                if len(slots) == 8:
                    print(f"All time blocks are available for {doctor}.")
                elif len(slots) == 0:
                    print(f"{doctor} has no time slots available.")
                else:
                    print(f"{doctor} has some time slots available.")
                
                send_udp_json(
                    sock,
                    {"status": "ok", "doctor": request["doctor"], "slots": available_slots(request["doctor"])},
                    address,
                )

                print("The Appointment Server has sent the lookup result to the Hospital Server.")

            elif action == "schedule":
                print(
                    f"Appointment scheduling request received (time: {request['time']}, "
                    f"doctor: {request['doctor']}, patient hash suffix: "
                    f"{hash_suffix(request['patient_hash'])}, illness: {request['illness']})."
                )
                schedule_result = schedule_slot(
                    request["doctor"],
                    request["time"],
                    request["patient_hash"],
                    request["illness"],
                )
                if schedule_result["success"]:
                    print(
                        f"Appointment has been scheduled successfully for user "
                        f"{hash_suffix(request['patient_hash'])} with {request['doctor']}."
                    )
                else:
                    print("The requested appointment time is not available.")
                send_udp_json(
                    sock,
                    schedule_result,
                    address,
                )
                print("The Appointment Server has sent the schedule result to the Hospital Server.")

            elif action == "cancel":
                print(
                    f"Appointment Server has received a cancel appointment command for "
                    f"the user with hash suffix: {hash_suffix(request['patient_hash'])}."
                )
                cancel_result = cancel_appointment(request["patient_hash"])
                if cancel_result["success"]:
                    print("Successfully cancelled appointment.")
                else:
                    print("Error: Failed to find appointment.")
                send_udp_json(sock, cancel_result, address)
            elif action == "view_patient_appointment":
                print(
                    f"Appointment Server has received a view appointment command for "
                    f"the user with hash suffix {hash_suffix(request['patient_hash'])}."
                )
                patient_appointment_result = view_patient_appointment(request["patient_hash"])
                if patient_appointment_result["found"]:
                    print(
                        f"Returning details regarding the appointment for the user "
                        f"with hash suffix {hash_suffix(request['patient_hash'])}."
                    )
                else:
                    print(
                        f"The user with hash suffix {hash_suffix(request['patient_hash'])} "
                        f"has no appointment in the system."
                    )
                send_udp_json(sock, patient_appointment_result, address)

            elif action == "view_doctor_appointments":
                print(
                    f"Appointment Server has received a request to view appointments "
                    f"scheduled for {request['doctor']}."
                )
                doctor_appointments_result = view_doctor_appointments(request["doctor"])
                if doctor_appointments_result["appointments"]:
                    print(f"Returning the scheduled appointments for {request['doctor']}.")
                else:
                    print(f"No appointments have been made for {request['doctor']}.")
                send_udp_json(sock, doctor_appointments_result, address)
            elif action == "get_patient_illness":
                print(
                    f"Appointment Server has received a request from Hospital Server "
                    f"regarding information about a user with hash suffix "
                    f"{hash_suffix(request['patient_hash'])} from {request.get('doctor', 'a doctor')}."
                )
                patient_illness_result = get_patient_illness(
                    request["patient_hash"],
                    request.get("doctor", ""),
                )
                if patient_illness_result["found"]:
                    print("Sending back the requested information to the Hospital server.")
                    print(
                        f"Located appointment details for the user with hash suffix "
                        f"{hash_suffix(request['patient_hash'])}."
                    )
                send_udp_json(sock, patient_illness_result, address)
            elif action == "complete_appointment":
                print(
                    f"Appointment Server has received a request to complete the appointment for "
                    f"user with hash suffix {hash_suffix(request['patient_hash'])} with "
                    f"{request['doctor']}."
                )
                complete_result = complete_appointment(
                    request["patient_hash"],
                    request["doctor"],
                )
                if complete_result["success"]:
                    print("The appointment has been cleared after prescription issuance.")
                else:
                    print("The appointment could not be cleared because no matching slot was found.")
                send_udp_json(sock, complete_result, address)
            else:
                send_udp_json(sock, {"status": "error", "message": "Unknown action."}, address)


if __name__ == "__main__":
    main()
