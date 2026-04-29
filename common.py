import hashlib
import json
import socket
from pathlib import Path
from typing import Dict, List, Optional, Tuple


BASE_DIR = Path(__file__).resolve().parent
HOST = "127.0.0.1"

AUTH_UDP_PORT = 21107
APPOINTMENT_UDP_PORT = 23107
PRESCRIPTION_UDP_PORT = 22107
HOSPITAL_TCP_PORT = 26107
HOSPITAL_UDP_PORT = 25107

BUFFER_SIZE = 65535

USERS_FILE = BASE_DIR / "users.txt"
HOSPITAL_FILE = BASE_DIR / "hospital.txt"
APPOINTMENTS_FILE = BASE_DIR / "appointments.txt"
PRESCRIPTIONS_FILE = BASE_DIR / "prescriptions.txt"


def sha256_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def hash_suffix(value: str, length: int = 5) -> str:#
    return value[-length:]


def send_udp_message(port: int, payload: Dict) -> Dict:#
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(5)
        sock.sendto(json.dumps(payload).encode("utf-8"), (HOST, port))#the port used by the other server
        data, _ = sock.recvfrom(BUFFER_SIZE)
        return json.loads(data.decode("utf-8"))


def recv_udp_json(sock: socket.socket) -> Tuple[Dict, Tuple[str, int]]:#
    data, address = sock.recvfrom(BUFFER_SIZE)
    return json.loads(data.decode("utf-8")), address


def send_udp_json(sock: socket.socket, payload: Dict, address: Tuple[str, int]) -> None:
    sock.sendto(json.dumps(payload).encode("utf-8"), address)


def send_tcp_json(sock: socket.socket, payload: Dict) -> None:
    sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))


def recv_tcp_json(file_obj) -> Optional[Dict]:#
    line = file_obj.readline()
    if not line:
        return None
    return json.loads(line.decode("utf-8"))


def load_users() -> Dict[str, str]:#return a hashmap of (username_hash,password_hash)
    users: Dict[str, str] = {}
    if not USERS_FILE.exists():
        return users
    for line in USERS_FILE.read_text().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        username_hash, password_hash = stripped.split()
        users[username_hash] = password_hash
    return users


def load_hospital_data() -> Dict[str, Dict]:#
    doctors: Dict[str, str] = {}
    treatments: Dict[str, str] = {}
    section = None
    if not HOSPITAL_FILE.exists():
        return {"doctors": doctors, "treatments": treatments}

    for raw_line in HOSPITAL_FILE.read_text().splitlines():
        line = raw_line.strip() #strip():delete all the space and \n at both end
        if not line:
            continue
        if line == "[Doctors]":
            section = "doctors"
            continue
        if line == "[Treatments]":
            section = "treatments"
            continue
        parts = line.split(maxsplit=1)#only split once at most
        if section == "doctors" and len(parts) == 2:
            doctors[parts[0]] = parts[1]
        elif section == "treatments" and len(parts) == 2:
            treatments[parts[0].lower()] = parts[1]
    return {"doctors": doctors, "treatments": treatments}


def load_appointments() -> Dict[str, List[Dict[str, str]]]:#
    appointments: Dict[str, List[Dict[str, str]]] = {}
    current_doctor: Optional[str] = None

    if not APPOINTMENTS_FILE.exists():
        return appointments

    for raw_line in APPOINTMENTS_FILE.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            current_doctor = None
            continue
        parts = line.split()
        if len(parts) == 1 and ":" not in parts[0]:
            current_doctor = parts[0]
            appointments[current_doctor] = []
            continue
        if current_doctor is None:
            continue
        entry = {"time": parts[0], "patient_hash": "", "illness": ""}
        if len(parts) >= 3:
            entry["patient_hash"] = parts[1]
            entry["illness"] = " ".join(parts[2:])#use a space between words if illness name includes multiple words
        appointments[current_doctor].append(entry)

    return appointments


def save_appointments(appointments: Dict[str, List[Dict[str, str]]]) -> None:
    lines: List[str] = []
    for doctor, slots in appointments.items():
        lines.append(doctor)
        for slot in slots:
            if slot["patient_hash"]:
                lines.append(f'{slot["time"]} {slot["patient_hash"]} {slot["illness"]}')
            else:
                lines.append(slot["time"])
        lines.append("")
    APPOINTMENTS_FILE.write_text("\n".join(lines).rstrip() + "\n")


def load_prescriptions() -> List[Dict[str, str]]:
    prescriptions: List[Dict[str, str]] = []
    if not PRESCRIPTIONS_FILE.exists():
        return prescriptions
    for raw_line in PRESCRIPTIONS_FILE.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=3)
        if len(parts) != 4:
            continue
        prescriptions.append(
            {
                "doctor": parts[0],
                "patient_hash": parts[1],
                "treatment": parts[2],
                "frequency": parts[3],
            }
        )
    return prescriptions


def save_prescriptions(prescriptions: List[Dict[str, str]]) -> None:
    lines = [
        f'{item["doctor"]} {item["patient_hash"]} {item["treatment"]} {item["frequency"]}'
        for item in prescriptions
    ]
    PRESCRIPTIONS_FILE.write_text("\n".join(lines) + ("\n" if lines else ""))


def build_default_slots() -> List[Dict[str, str]]:
    return [
        {"time": f"{hour:02d}:00", "patient_hash": "", "illness": ""}
        for hour in range(9, 17)
    ]
