"""
Author: Annika Duggal
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""
import datetime
# TODO: Import the required modules (Step ii)
import socket
import threading
import sqlite3
import os
import platform
from csv import excel
from zipfile import error

# TODO: Print Python version and OS name (Step iii)
print(platform.python_version())
print(os.name)

# TODO: Create the common_ports dictionary (Step iv)
# python dictionary storing port numbers (int) as key and their service names (string) as value
common_ports = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}

# TODO: Create the NetworkTool parent class (Step v)

class NetworkTool:

    def __init__(self,target: str):
        self.__target = target

    # Q3: What is the benefit of using @property and @target.setter?
    # TODO: Your 2-4 sentence answer here... (Part 2, Q3)
    """ 
    Using @property and @target.setter encapsulates logic for accessing and modifying __target. 
    It allows controlled access to the private data ensuring that __target cannot be set directly.
    THis is because all access goes through methods which contain checks and verification. 
    """

    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value):
        if value == "":
            print("Error: Target cannot be empty")
        else:
            self.__target = value

    def __del__(self):
         print("NetworkTool instance destroyed")

# Q1: How does PortScanner reuse code from NetworkTool?
# TODO: Your 2-4 sentence answer here... (Part 2, Q1)
"""
PortScanner reuses NetworkTool's code through inheritance, allowing it to automatically receive the constructor,
target property, validation setter and destructor. 
PortScanner objects therefore NetworkTool's methods to store and validate the target without explicitly rewriting
the logic within PortScanner. 
"""

# TODO: Create the PortScanner child class that inherits from NetworkTool (Step vi)

class PortScanner(NetworkTool):

    def __init__(self,target):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()

    def scan_port(self, port):
        #     Q4: What would happen without try-except here?
        #     TODO: Your 2-4 sentence answer here... (Part 2, Q4)
        """
        Without the try-except block, any type of socket error will raise an unhandled exception, causing the entire thread to crash.
        Individual threads may also fail without appending the result or closing the socket, potentially leading to resourcing issues.
        'Except' allows us to gracefully handle errors and the finally block ensures the socket will always be closed.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.target,port))
            if (result == 0):
                status = "Open"
            else:
                status = "Closed"
            service_name = common_ports.get(port, "Unknown")
            self.lock.acquire()
            self.scan_results.append((port, status, service_name))
            self.lock.release()
        except socket.error as error:
            print(f"Error scanning port {port}: {error}")
        finally:
            sock.close()

    def get_open_ports(self):
        return [result for result in self.scan_results if result[1] == "Open"]

#     Q2: Why do we use threading instead of scanning one port at a time?
#     TODO: Your 2-4 sentence answer here... (Part 2, Q2)
        """
        since each port scan waits ~1 second for response, scanning a range would mean that time would increase with the number of ports scanned.
        With threading, we can scan ports simultaneously, ensuring that execution time is relatively consistent regardless of range size.
        When scanning a large range, threading is a critical performance enhancement.
        """

    def scan_range(self, start_port, end_port):
        threads = []
        for port in range(start_port, end_port+1):
            thread = threading.Thread(target=self.scan_port, args =(port,))
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()


# TODO: Create save_results(target, results) function (Step vii)

DB_NAME = "scan_history.db"
def save_results(target,results):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            port INTEGER,
            status TEXT,
            service TEXT,
            scan_date TEXT
            )
        """)
        for result in results:
            cursor.execute(
                "INSERT INTO scans (target, port, status, service, scan_date) VALUES (?, ?, ?, ?, ?)",
                (target, result[0], result[1], result[2], str(datetime.datetime.now()))
            )
        conn.commit()
    except sqlite3.Error as error:
        print(f"Database error: {error}")
    finally:
        conn.close()

# TODO: Create load_past_scans() function (Step viii)

def load_past_scans():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scans")
        rows = cursor.fetchall()
        for row in rows:
            print(f"[{row[5]}] {row[1]} : Port {row[2]} ({row[4]}) - {row[3]}")
    except sqlite3.Error:
        print("No past scans found")
    finally:
        conn.close()

# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    # TODO: Get user input with try-except (Step ix)

    target = input("Enter a target IP address. Hit 'Enter' for IP address 127.0.0.1")
    if target == "":
        target = "127.0.0.1"

    try:
        start_port = int(input("Enter starting port (1-1024)"))
        if 1 > start_port or start_port > 1024:
            print("Port must be between 1 and 1024")
    except ValueError:
        print("Invalid input. Please enter a valid integer")

    try:
        end_port = int(input("Enter ending port (1-1024) that is greater than or equal to starting port"))
        if end_port < 1 or end_port > 1024:
            print("Port must be between 1 and 1024")
        if start_port > end_port:
            print(f"End port must be greater than or equal to {start_port}")
    except ValueError:
        print("Invalid input. Please enter a valid integer")

    # TODO: After valid input (Step x)

    scanner = PortScanner(target)
    print(f"\nScanning {target} from port {start_port} to {end_port}...")
    scanner.scan_range(start_port,end_port)

    open = scanner.get_open_ports()
    print(f"\n === Scan Results for {target} ===")
    for port, status, service in open:
        print(f"Port {port}: {status} ({service})")
    print("------------")
    print(f"Total open ports found: {len(open)}")

    save_results(target, scanner.scan_results)

    view_history = input("\nWould you like to see past scan history? (yes/no)")
    if view_history == "yes":
        load_past_scans()

# Q5: New Feature Proposal
# TODO: Your 2-3 sentence description here... (Part 2, Q5)

"""
I would add a filter method that returns open ports matching a specific service name.
This could be implemented as a method called filter_by_service(self, service_name) in PortScanner
It would use list comprehension to filter scan_results by matching the service field against the provided name.
"""

# Diagram: See diagram_101574406.png in the repository root
