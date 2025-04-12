# 🦸‍♂️ WOLverine (WOL = Wake-on-LAN + Wolverine 😄)

<div align="center">
  <img src="https://raw.githubusercontent.com/Michdo93/WOLverine/refs/heads/main/static/wolverine.webp" alt="Wolverine Logo" width="300">
</div>

# 🦾 WOLverine – The Power of Resurrection

**WOLverine** (WOL = Wake-on-LAN + Wolverine 😄) is not just a tool for waking up computers remotely, but also a tribute to the legendary mutant known for his incredible healing abilities and his knack for coming back to life no matter what. Just like Wolverine, who can heal and rise again after every defeat, **WOLverine** allows your computer to wake from a deep slumber and resume its duties – without you lifting a finger.

## 📖 The Story Behind WOLverine

In the world of X-Men, Wolverine (a.k.a. Logan) doesn’t just fight the forces of evil, but also races against time, always looking for ways to save the world in the most desperate situations. Just like Wolverine, who regenerates with every battle, **WOLverine** brings the power of **Wake-on-LAN** into the world of technology – a superpower that allows your computer to awaken from the deep sleep and resume action, just when you need it most.

Imagine: you’re the “X-Man” of your network. You’re in the middle of the battle, your server’s screen is dead, it’s in sleep mode, and work is piling up. But no need to worry! Like Wolverine with his indestructible healing factor, you spring into action, and with just one click or command, you wake up the machine from its dark slumber – and it’s ready to go!

## 💪 What Makes WOLverine So Powerful?

**Wake-on-LAN** is like the "healing factor" for your devices. Typically, most devices in your network are asleep to save power. But what if you want to wake them up remotely to get work done? **WOLverine** makes it possible! With this superpower, you can wake up devices from anywhere, without needing physical access to them.

Whether you’re working on a project in your studio or managing a fleet of machines in a data center – **WOLverine** is always ready to help by allowing you to wake up your machines quickly and efficiently, all without having to be there in person.

## ✨ How Does the Magic of WOLverine Work?

The magic behind **WOLverine** lies in **Wake-on-LAN** technology, which allows you to wake up a device with a special "Magic Packet." Essentially, you send a specially formatted network packet (the "Magic Packet") to the target device, and voilà – it wakes up from its slumber. It’s a bit like Wolverine, who rises from the ashes after every battle.

### 🪄 Step-by-Step:

1. **Make the Target Device Available**: Ensure that your device has Wake-on-LAN enabled and is ready to respond to the "Magic Packet" call.

2. **Bring WOLverine into Play**: Use the WOLverine software to send the "Magic Packet" command – and just like that, your device comes back to life!

3. **Enjoy Your Regeneration**: Your computer or server awakens from sleep mode, ready to tackle whatever comes next – just like Wolverine after every battle!

## ❓ Why WOLverine?

In a world full of computer networks where devices often fall into sleep mode, and their heroes (the administrators) are far away, **WOLverine** provides the solution. Why deal with the hassle of waking them up physically when you can remotely call them back to life, whenever you need?

**WOLverine** is not just a name – it’s a philosophy. It’s the power to always be ready to bring your network out of the dark and into action when needed. Just like Wolverine, who comes back after every fight, you’re always prepared to return to the battle.

---

# 🚀 WOLverine – Wake Your Devices Like an X-Man

You are the hero of your network. Get **WOLverine** and wake up your devices remotely – with the power of Wake-on-LAN and the determination of a true X-Man.

---

# 🧰 Features

What does this web application do?

- **Ping**:
    - A ping is used to check whether the computer is `online` or `offline`.
    - If a computer is `offline`, you can wake it up via `WOL`.
    - If a computer is `online`, you can shut it down via `SSH`.
    - Of course, the ping also changes when the device is switched on or off in other ways. The ping is therefore necessary so that the status of the button also changes whether you want to switch a computer on or off.
- **Wake-on-LAN (WOL)**:
    - Could be used to wake up a PC.
    - You need the `MAC` and `IP` addresses from the host.
    - The status of the computer then changes to `online`.
- **Shutdown**:
    - To shut down a PC, you must connect to this computer via `SSH` and shut it down.
    - The status of the computer then changes to `offline`.
- **Shutdown**:
    - To reboot a PC, you must connect to this computer via `SSH` and reboot it.
    - The status of the computer then changes at first to `offline` and later again to `online`.
- **System Monitoring**:
    - Uptime, memory and CPU are monitored (if necessary via `SSH`).
    - In most cases, of course, this monitoring is done via `SSH`, as `SSH` would not be used for this on the localhost.
- **REST API**:
    - In addition to using a dashboard, the individual functions can also be operated via a `REST API`. This is what makes WOLverine so powerful.
    - The `REST API` is designed for `basic authentication`.

# 🛠️ Installation

The best and easiest way is to run the existing installation script:

```
sudo .\install.sh
```

## 📦 Clone the repository

At first you have to clone the GitHub Repository:

```
git clone https://github.com/Michdo93/WOLverine.git
```

## 📥 Install the dependencies

You can install the dependencies with

```
cd WOLverine
pip install -r requirements.txt
```

or manually with

```
pip install Flask==3.0.3
pip install ping3==4.0.8
pip install paramiko==2.6.0
pip install wakeonlan==3.1.0
pip install bcrypt==3.1.7
pip install psutil==5.5.1
pip install Flask-SocketIO==5.5.1
pip install eventlet==0.39.1
```

---

# ⚙️ Pre-Configuration (on remote targets)

> [!WARNING]  
> Not all computers are capable of Wake-on-LAN (WOL). You must of course have WOL activated on a remote computer (if supported).

> [!WARNING]  
> Not all computers have it activated so that they can be pinged. Logically, you must have activated that a computer can be pinged.

> [!WARNING]  
> If you want to wake up and shut down a computer, you should have both SSH installed on this computer and the SSH service must also be activated.

## 🔐 sudoers file

In Linux, you must also allow the restart and shutdown in the `/etc/sudoers` file on your target so that this can be carried out without admin rights. You can use the command `sudo visudo` for this. Add the following content to this file:

```
<username>  ALL=(ALL) NOPASSWD: /sbin/shutdown, /sbin/reboot
```

Please replace `<username>` with the username of the user you want to log in with via `ssh`. It is also important that there is a tab between the user name and the commands. The commands are separated from each other with a comma.

---

# 🧾 Configuration (host)

The configuration can be edited in `</path/to/WOLverine>/config.py`. You also have to replace `</path/to/WOLverine>` with the `path` where you stored the application. In the configuration file, you can configure both the login for the web interface with multiple user accounts and multiple hosts including their information for WOL and SSH.

## 🔒 User authentication

I can create several user accounts with passwords for the web interface in the configuration file. I can save the passwords hashed or in plain text.

### 🔓 Password (plain text)

As example a user with its password as plain text could be added like this:

```
USERS = {
    "admin": "password",
}
```

### 🔐 Password (hashed)

As example a user with hashed password could be added like this:

```
USERS = {
    "admin": "$2b$12$dK3Gi9h81vRrgbQxqU6/fux8LTzUbSGyEPIjRnOpqLh3yvPCV/kHK",
}
```

I have added a utility program called `hash_password.py` which can be used to generate hashed passwords. You can use it as follows:

```
python3 hash_password.py
Enter your password: password
Hashed password: $2b$12$dK3Gi9h81vRrgbQxqU6/fux8LTzUbSGyEPIjRnOpqLh3yvPCV/kHK
```
## 🖥️ Host configuration

A minimum configuration includes the name (possibly host name) of the computer, its IP address and its MAC address. This is required to determine whether a device is online or offline. Theoretically, you could now also use the MAC address to switch on a computer via WOL Magic Packet. However, we only want to offer this function to the user if they have also configured an SSH connection, as a computer can only be shut down again via SSH.

For example, a minimal configuration could look like this:

```
HOSTS = [
    {
        'name': 'localhost',
        'ip': '127.0.0.1',
        'mac': '00:11:22:aa:bb:cc',
        'ssh_user': None,
        'ssh_password': None,
        'ssh_key_path': None,
    }
]
```

Please change the `name`, the `ip` and the `mac` with your `name/hostname`, `ip` and `mac` address of your computer.

Additional computers can easily be added here.

### 📡 SSH authentication

The SSH connection makes it possible to shut down the computer. System monitoring is also possible here, which can be used to check the utilization of the computer. Since we have a button that toggles between `Wake Up` and `Shutdown`, Wake-on-LAN, i.e. sending a Magic Packet to start a computer, is also activated after configuring SSH. This button is only active because it must be able to toggle cleanly between `online` and `offline`, otherwise it can never perform the correct action (wake up or shutdown).

However, an SSH connection can be password-based or key-based (private and public key). Accordingly, you can configure either one or the other. I recommend the key-based procedure, as otherwise the user password is saved in plain text in the configuration.

#### 🔑 Password-based

The following is an example of how a password-based SSH connection can be established.

```
HOSTS = [
    {
        'name': 'localhost',
        'ip': '127.0.0.1',
        'mac': '00:11:22:aa:bb:cc',
        'ssh_user': 'ubuntu',
        'ssh_password': 'linux',
    }
]
```

Please change the `name`, the `ip` and the `mac` with your `name/hostname`, `ip` and `mac` address of your computer. You should also change the user name (`ssu_user`) and password (`ssh_password`) for SSH.

#### 🗝️ Key-based (recommended)

The following is an example of how a key-based SSH connection can be established.

```
HOSTS = [
    {
        'name': 'localhost',
        'ip': '127.0.0.1',
        'mac': '00:11:22:aa:bb:cc',
        'ssh_user': 'ubuntu',
        'ssh_key_path': '/home/ubuntu/.ssh/id_rsa',
    }
]
```

##### 🛠️ Generate SSH key (if not already available):

On the host computer you may need to do the following:

```
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
```

Stores keys under `~/.ssh/id_rsa` (private) and `~/.ssh/id_rsa.pub` (public). You can set a password (passphrase) or simply press `Enter`.

##### 📤 Copy public key to host (if not already done):

In order for your host to send the public key to the target, you must execute the following command from your host:

```
ssh-copy-id -i ~/.ssh/id_rsa.pub <target_user>@<target_ip>
```

Please replace `<target_user>` and `<target_ip>` with the `username` and `ip address` of your target computer.

If you have created a passphrase, you may have to enter this password once. Otherwise, you will need to establish an SSH connection from the host to the target, which may also require you to enter a password.

##### 🧪 Testing key-based authentication

You can test the key-based authentication by entering:

```
ssh -i ~/.ssh/id_rsa <target_user>@<target_ip>
```

Please replace `<target_user>` and `<target_ip>` with the `username` and `ip address` of your target computer.

If everything works, you should now establish an SSH connection without a password.

---

# ⚙️ Execution and Deployment

## ▶️ Execute the Web App

In itself, the following command is enough:

```
python3 app.py
```

It is better to use a `system service`. I would also recommend using `nginx` and a reverse proxy.

## 🧱 System service

### 📝 Create the systemd service file

Create a new file, e.g. wolverine.service, in the /etc/systemd/system/ directory:

```
sudo nano /etc/systemd/system/wolverine.service
```

### 📄 Content of the service file

The file should look something like this:

```
[Unit]
Description=WOLverine Web Application
After=network.target

[Service]
User=<username>
Group=<username>
WorkingDirectory=</path/to/WOLverine>
ExecStart=/usr/bin/python3 </path/to/WOLverine>/app.py
Restart=always
Environment="FLASK_ENV=production"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

Please replace `<username>` with the `username` of your account. You also have to replace `</path/to/WOLverine>` with the `path` where you stored the application.

### 🔄 Reload the service file and start the service

After you have created the service file, you must inform systemd about it and start the service:

```
sudo systemctl daemon-reload
sudo systemctl start wolverine.service
sudo systemctl enable wolverine.service
```

---

# 📡 REST API Overview

## 🔍 GET Endpoints

| Endpoint                                | Description                                                                 |
|----------------------------------------|-----------------------------------------------------------------------------|
| `/rest/computer`                       | Returns a list of all configured computers.                                |
| `/rest/computer/<name>`                | Returns detailed information for a specific computer by name.              |
| `/rest/computer/<name>/ip`             | Returns the IP address of the specified computer.                          |
| `/rest/computer/<name>/mac`            | Returns the MAC address of the specified computer.                         |
| `/rest/computer/<name>/status`         | Returns the current status of the computer (`online` or `offline`).        |
| `/rest/computer/<name>/systeminfo`     | Returns system information of the computer (e.g. from `get_info`).         |

## ⚙️ POST Endpoints

| Endpoint                                | Description                                                  |
|----------------------------------------|--------------------------------------------------------------|
| `/rest/computer/<name>/wake`           | Sends a Wake-on-LAN signal to power on the computer.         |
| `/rest/computer/<name>/reboot`         | Reboots the specified computer (if online).                  |
| `/rest/computer/<name>/shutdown`       | Shuts down the specified computer (if online).               |

---

## 🧪 Testing the REST API

Use a tool like **Postman** or **cURL** to test the endpoints.  
Make sure to use **Basic Authentication** with a valid `username` and `password` from your `config.py`.

### ✅ Example GET request with cURL

```bash
curl -u username:password http://localhost:5000/rest/computer
```

### 🔁 Example POST request with cURL

```bash
curl -u username:password -X POST http://localhost:5000/rest/computer/<name>/reboot
```

Replace `<name>` with the actual computer name (e.g. `pc01`, `media-server`, etc.).

---

# 🤝 Contributing

Contributions are welcome! Please submit a pull request or open an issue to suggest improvements.

---

# 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 

---

🦸‍♂️ **Enjoy using WOLverine!** 🚀