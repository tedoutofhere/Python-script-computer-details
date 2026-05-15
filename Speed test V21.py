import os
import platform
import socket
import subprocess
import csv
import time
import urllib.request
from datetime import datetime

def get_computer_name():
    """Gets your computer's name. Like naming a pet, except this pet never responds."""
    name = socket.gethostname()
    print(f"Computer name: {name} (probably named by someone who ran out of creativity)")
    return name

def get_os_info():
    """Discovers your OS. It's like asking "What's your sign?" but for computers."""
    system = platform.system()
    try:
        if system == "Windows":
            info = subprocess.check_output("systeminfo", shell=True, text=True, stderr=subprocess.DEVNULL)
            os_name, os_version = None, None
            for line in info.splitlines():
                if line.strip().startswith("OS Name"):
                    os_name = line.split(":", 1)[1].strip()
                elif line.strip().startswith("OS Version"):
                    os_version = line.split(":", 1)[1].strip()
            if os_name and os_version:
                return f"{os_name} ({os_version})"
            if os_name:
                return os_name
        elif system == "Linux":
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    data = {}
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            data[k] = v.strip().strip('"')
                    return data.get("PRETTY_NAME", f"Linux {platform.release()}")
            return f"Linux {platform.release()}"
        elif system == "Darwin":
            product = subprocess.check_output(["sw_vers", "-productName"], text=True).strip()
            version = subprocess.check_output(["sw_vers", "-productVersion"], text=True).strip()
            return f"{product} {version}"
    except Exception:
        return f"{system} (Unknown Version)"
    return system

def get_ip():
    """Finds your IP address. It's like asking a stranger "Where am I?" and they actually tell you."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        print(f"IP Address: {ip} (Now the whole internet knows where you are!)")
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "N/A"

def get_mac():
    """Gets your MAC address - like a fingerprint, but for your network adapter."""
    system = platform.system()
    try:
        if system == "Windows":
            out = subprocess.check_output("getmac /fo csv /nh", shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if line.strip():
                    parts = [p.strip().strip('"') for p in line.split('","') if p]
                    if parts:
                        mac = parts[0].replace("-", ":")
                        if mac and mac != "00:00:00:00:00:00":
                            print(f"MAC Address: {mac} (Your device's secret identity)")
                            return mac
        else:
            try:
                out = subprocess.check_output(["ip", "link", "show"], text=True, stderr=subprocess.DEVNULL)
                for line in out.splitlines():
                    if "link/ether" in line:
                        mac = line.split()[1].strip()
                        if mac and not mac.startswith("00:00:00"):
                            return mac
            except Exception:
                out = subprocess.check_output(["ifconfig"], text=True, stderr=subprocess.DEVNULL)
                for line in out.splitlines():
                    if "ether" in line:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            mac = parts[1]
                            if mac and not mac.startswith("00:00:00"):
                                return mac
    except Exception:
        pass
    return "N/A"


def get_processor():
    """Gets your CPU's name. That chip probably overheating from 47 Chrome tabs."""
    system = platform.system()
    try:
        if system == "Windows":
            out = subprocess.check_output("wmic cpu get Name", shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if line.strip() and "Name" not in line:
                    print(f"Processor: {line.strip()} (The brain doing all the thinking)")
                    return line.strip()
        elif system == "Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "Unknown"


def get_system_time():
    """Gets the current time. That thing you check when wondering how late it is."""
    try:
        now = datetime.now().astimezone()
        return now.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def get_active_ports():
    """Finds all ports your computer is using. Like checking which doors are open, but for the internet."""
    system = platform.system()
    listening = set()
    established = set()

    def _port_only(addr: str) -> str:
        if not addr:
            return ""
        addr = addr.strip()
        if addr.startswith("[") and "]:" in addr:
            return addr.split("]:")[-1]
        if ":" in addr:
            return addr.rsplit(":", 1)[-1]
        return addr

    try:
        if system == "Windows":
            out = subprocess.check_output(["netstat", "-na"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                parts = line.split()
                if not parts or parts[0].upper() != "TCP":
                    continue
                if len(parts) >= 4:
                    local, remote, state = parts[1], parts[2], parts[3].upper()
                    if state == "LISTENING":
                        listening.add(_port_only(local))
                    elif state == "ESTABLISHED":
                        lp, rp = _port_only(local), _port_only(remote)
                        if lp:
                            established.add(lp)
                        if rp:
                            established.add(rp)
        else:
            try:
                out = subprocess.check_output(["ss", "-tnl"], text=True, stderr=subprocess.DEVNULL)
                for line in out.splitlines():
                    if not line or line.strip().startswith("State"):
                        continue
                    parts = line.split()
                    for token in reversed(parts):
                        if ":" in token or "]" in token:
                            listening.add(_port_only(token))
                            break
            except Exception:
                try:
                    out = subprocess.check_output(["netstat", "-tnl"], text=True, stderr=subprocess.DEVNULL)
                    for line in out.splitlines():
                        parts = line.split()
                        if len(parts) >= 4 and parts[0].startswith("tcp"):
                            listening.add(_port_only(parts[3]))
                except Exception:
                    pass

            try:
                out = subprocess.check_output(["ss", "-tn", "state", "established"], text=True, stderr=subprocess.DEVNULL)
                for line in out.splitlines():
                    if not line or line.strip().startswith("State"):
                        continue
                    parts = line.split()
                    addr_tokens = [t for t in parts if (":" in t or (t.startswith("[") and "]" in t))]
                    if len(addr_tokens) >= 2:
                        for tok in addr_tokens[-2:]:
                            established.add(_port_only(tok))
            except Exception:
                try:
                    out = subprocess.check_output(["netstat", "-tn"], text=True, stderr=subprocess.DEVNULL)
                    for line in out.splitlines():
                        parts = line.split()
                        if len(parts) >= 6 and parts[0].startswith("tcp"):
                            established.add(_port_only(parts[3]))
                            established.add(_port_only(parts[4]))
                except Exception:
                    pass
    except Exception:
        pass

    listening = sorted(p for p in listening if p)
    established = sorted(p for p in established if p)
    return listening, established


def test_internet_speed():
    """Tests internet speed. Spoiler: it's probably slower than you think (and your wallet)."""
    file2download = "https://github.com/Mherstik/Automation_Sem2_2025/raw/refs/heads/main/50MB.zip"
    print("Testing internet speed... (This is where your dreams get crushed)")
    starttime = time.time()
    
    try:
        save_path = os.path.join(os.getcwd(), "speed_test_50MB.zip")
        urllib.request.urlretrieve(file2download, save_path)
        endtime = time.time()
        speed = 50 * 8 / (endtime - starttime)
        print(f"Speed: {speed:.2f} Mbps (Not as fast as light, but pretty close!)")
        print(f"File saved to: {save_path}")
        return f"{speed:.2f} Mbps"
    except Exception:
        print("Speed test failed: Your internet is probably slower than a snail on a Sunday")
        return "Speed test failed: Unable to connect"


def write_to_csv(data):
    """Writes system info to CSV. Like a diary, but for your computer's secrets."""
    filename = os.path.join(os.getcwd(), "system_info.csv")
    headers = list(data.keys())
    values = []
    for key in headers:
        v = data[key]
        if isinstance(v, (list, tuple)):
            values.append(";".join(str(x) for x in v))
        else:
            values.append(str(v))

    with open(filename, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(values)
    print(f"Your secrets are now stored in: {filename}")
    return filename


def open_in_excel(filepath):
    """Opens CSV in Excel. Like opening a present, except it's a spreadsheet you'll close immediately."""
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(filepath)
        else:
            subprocess.run(["xdg-open", filepath], check=False)
        print("Excel is loading... prepare yourself for confusion!")
    except Exception:
        pass


def main():
    """The boss function. Like a conductor, but the orchestra collects system info instead of making music."""
    listening, established = get_active_ports()
    data = {
        "Computer Name": get_computer_name(),
        "IP Address": get_ip(),
        "MAC Address": get_mac(),
        "Processor": get_processor(),
        "Operating System": get_os_info(),
        "System Time": get_system_time(),
        "Internet Connection Speed": test_internet_speed(),
        "Listening (TCP)": listening,
        "Established (TCP)": established
    }
    file = write_to_csv(data)
    
    print()
    response = input("Do you want to open the file? (yes/no): ").strip().lower()
    if response in ("yes", "y", "ye"):
        open_in_excel(file)
    else:
        print("File not opened. (Your secret is safe... for now)")


if __name__ == "__main__":
    main()
