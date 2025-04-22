import paramiko
from ping3 import ping
from wakeonlan import send_magic_packet
import psutil
import time
import socket
import platform
import os
import tempfile
import textwrap
import json

class HostClient:
    def __init__(self, name, ip, mac, ssh_user, ssh_password=None, ssh_key_path=None):
        self.name = name
        self.ip = ip
        self.mac = mac
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.ssh_key_path = ssh_key_path

    def is_online(self):
        return ping(self.ip, timeout=1) is not None

    def shutdown(self):
        if self.ssh_user and (self.ssh_key_path or self.ssh_password):
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                if self.ssh_key_path and os.path.exists(self.ssh_key_path):
                    ssh.connect(self.ip, username=self.ssh_user, key_filename=self.ssh_key_path)
                elif self.ssh_password:
                    ssh.connect(self.ip, username=self.ssh_user, password=self.ssh_password)

                stdin, stdout, stderr = ssh.exec_command('uname')
                os_type = stdout.read().decode().strip().lower()

                if "linux" in os_type or "darwin" in os_type:
                    command = 'sudo /sbin/shutdown -h now'
                elif "msys" in os_type or "mingw" in os_type or "cygwin" in os_type or "nt" in os_type:
                    command = 'shutdown /s /t 0'
                else:
                    stdin, stdout, stderr = ssh.exec_command('ver')
                    ver_output = stdout.read().decode().strip()
                    if "windows" in ver_output.lower():
                        command = 'shutdown /s /t 0'
                    else:
                        command = 'sudo /sbin/shutdown -h now'

                ssh.exec_command(command)
                ssh.close()
                return True
            except Exception as e:
                print(f"Shutdown error: {e}")
                return False
        return False

    def reboot(self):
        if self.ssh_user and (self.ssh_key_path or self.ssh_password):
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                if self.ssh_key_path and os.path.exists(self.ssh_key_path):
                    ssh.connect(self.ip, username=self.ssh_user, key_filename=self.ssh_key_path)
                elif self.ssh_password:
                    ssh.connect(self.ip, username=self.ssh_user, password=self.ssh_password)

                stdin, stdout, stderr = ssh.exec_command('uname')
                os_type = stdout.read().decode().strip().lower()

                if "linux" in os_type or "darwin" in os_type:
                    command = 'sudo /sbin/reboot'
                elif "msys" in os_type or "mingw" in os_type or "cygwin" in os_type or "nt" in os_type:
                    command = 'shutdown /r /t 0'
                else:
                    stdin, stdout, stderr = ssh.exec_command('ver')
                    ver_output = stdout.read().decode().strip()
                    if "windows" in ver_output.lower():
                        command = 'shutdown /r /t 0'
                    else:
                        command = 'sudo /sbin/reboot'

                ssh.exec_command(command)
                ssh.close()
                return True
            except Exception as e:
                print(f"Reboot error: {e}")
                return False
        return False

    def wake(self):
        if self.ssh_user and (self.ssh_key_path or self.ssh_password):
            send_magic_packet(self.mac)
        return "No SSH access available"

    def get_info(self):
        try:
            if self.ip in ['127.0.0.1', 'localhost']:
                uptime_seconds = time.time() - psutil.boot_time()
                uptime_string = time.strftime('%H:%M:%S', time.gmtime(uptime_seconds))
                memory = psutil.virtual_memory()
                cpu = psutil.cpu_percent(interval=1)

                return {
                    'System': f"{platform.system()} {platform.release()}",
                    'Hostname': socket.gethostname(),
                    'Uptime': uptime_string,
                    'Memory': memory.used // (1024 ** 2),
                    'Memory_total': memory.total // (1024 ** 2),
                    'CPU Load': cpu,
                }

            elif self.ssh_user and (self.ssh_key_path or self.ssh_password):
                psutil_script = textwrap.dedent("""
                    import psutil, time, platform, socket, json
                    uptime_seconds = time.time() - psutil.boot_time()
                    uptime_string = time.strftime('%H:%M:%S', time.gmtime(uptime_seconds))
                    memory = psutil.virtual_memory()
                    cpu = psutil.cpu_percent(interval=1)
                    info = {
                        "System": f"{platform.system()} {platform.release()}",
                        "Hostname": socket.gethostname(),
                        "Uptime": uptime_string,
                        "Memory": memory.used // (1024 ** 2),
                        "Memory_total": memory.total // (1024 ** 2),
                        "CPU Load": cpu,
                    }
                    print(json.dumps(info))
                """)

                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                if self.ssh_key_path and os.path.exists(self.ssh_key_path):
                    ssh.connect(self.ip, username=self.ssh_user, key_filename=self.ssh_key_path)
                elif self.ssh_password:
                    ssh.connect(self.ip, username=self.ssh_user, password=self.ssh_password)

                with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as tmp:
                    tmp.write(psutil_script)
                    tmp_path = tmp.name

                remote_path = "/tmp/remote_info.py"
                sftp = ssh.open_sftp()
                sftp.put(tmp_path, remote_path)
                sftp.close()
                os.remove(tmp_path)

                stdin, stdout, stderr = ssh.exec_command(f'python3 {remote_path}')
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()

                ssh.exec_command(f"rm {remote_path}")
                ssh.close()

                if error:
                    return {"error": error}
                return json.loads(output) if output else {"error": "No output received"}

            return {"error": "No SSH access available"}

        except Exception as e:
            return {"error": str(e)}
