# pynod-mirror-tool - Dockerized
 ![Version](https://img.shields.io/badge/version-20251205-gold)
 [![Python](https://img.shields.io/pypi/pyversions/tensorflow.svg)](https://badge.fury.io/py/tensorflow)
 ![Last commit](https://img.shields.io/github/last-commit/Scorpikor/pynod-mirror-tool/main?cacheSeconds=0)
[![Opened issues](https://img.shields.io/github/issues/Scorpikor/pynod-mirror-tool?color=darkred)](https://github.com/rzc0d3r/ESET-KeyGen/issues?cacheSeconds=0)
[![Closed issues](https://img.shields.io/github/issues-closed/Scorpikor/pynod-mirror-tool?color=darkgreen&cacheSeconds=0)](https://github.com/rzc0d3r/ESET-KeyGen/issues?q=is%3Aissue+is%3Aclosed)
![License](https://img.shields.io/github/license/Scorpikor/pynod-mirror-tool)

**pynod-mirror-tool** is a Python script designed to create a mirror of ESET NOD32 antivirus databases. It supports Windows, Linux, and FreeBSD, and can be run via Docker. It requires Python 3.x and NGINX to serve the databases to antivirus clients.

# Installation:
1) `cd pynod-mirror-tool`
2) `pip3 install -r requirements.txt`
3) Edit the `nod32ms.conf` file according to your needs.
4) Start downloading the databases: `py update.py`
5) To distribute updates to antivirus clients, it is recommended to use NGINX. Configuration files are available in the `nginx-configs` folder (choose the one that matches your NGINX version).

**Quick start with Docker:** `docker compose up -d`

# Windows Dependencies & Troubleshooting:
To set up the necessary environment on Windows, first install Chocolatey:

**Install Chocolatey:**
`Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))`

**Install essential software:**
`choco install python -y`
`choco install nginx -y`
`choco install docker-desktop -y`

**Verify Docker status:**
`Get-Service *docker*`

**WSL 2 & Virtualization setup:**
If you encounter virtualization errors, ensure that your BIOS/UEFI virtualization is enabled. The following commands can be used to manage the Windows subsystem features if required:

*Enable WSL 2:*
`dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart; dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart`

*Disable WSL 2 (Cleanup):*
`dism.exe /online /disable-feature /featurename:Microsoft-Windows-Subsystem-Linux /norestart; dism.exe /online /disable-feature /featurename:VirtualMachinePlatform /norestart`

**Manage WSL distributions:**
`wsl --install`
`wsl --list --verbose`
`wsl --unregister <DistroName>`

**Check system virtualization status:**
`Get-ComputerInfo -Property "HyperV*"`

**ATTENTION!** This script does not search for license keys. Its purpose is to connect to official ESET NOD32 mirror servers (if you have a valid username and password) or unofficial mirrors, download the databases, organize them into folders, and serve them via NGINX to antivirus clients or other mirrors.

---

# 05.12.2025 Update
* Added `log_file_path` parameter to the `[LOG]` section of `nod32ms.conf` to define a custom path and filename for logs.
* Added `mode_one_dir_base` parameter to the `[ESET]` section of `nod32ms.conf`. This mode stores all databases in a single folder with `update.ver`, allowing clients to update directly from a folder without needing a web server.

# 19.06.2025 Update
* Added logging to a text file; corresponding settings added to the `[LOG]` section of `nod32ms.conf`.
* Moved terminal and text log verbosity settings from `log.py` to the `[LOG]` section of `nod32ms.conf`.

# 11.06.2025 Update
* PROTOSCAN patch files for v3 databases replaced with version 1454.

# 10.05.2025 Update
* Added `[PATCH]` section to `nod32ms.conf` with the `protoscan_v3_patch` parameter, which enables the PROTOSCAN patch for v3 databases (includes version 1400.4 files).
* Fixed bugs related to cleaning up old files.
* Changed script behavior on 401 error (Unauthorized). The script now stops trying to download the remaining database files upon authentication failure.
* Fixed minor bugs and, of course, added some new ones :)

# 19.03.2025 Update
* Added `text` parameter to the `[TELEGRAM]` section in the config for custom text or reminders in Telegram notifications.
* Improved the file download algorithm and size verification with compression support.
* `update.ver` is now cleaned of redundant lines that prevent antivirus clients from updating correctly from the script-generated mirror.

# 03.03.2025 Update
* Restored HTML generation.
* Fixed minor glitches.

# 24.04.2025 Update
* Added Windows support.
* Added multi-threaded database downloading.
* Fixed several bugs from the previous version.
* `update.ver` is no longer modified, preventing "path accumulation" when updating from mirrors created by the same script.
* Added report delivery via Telegram.

**Warning!** The `nod32ms.conf` and NGINX configuration files have changed. You must reconfigure them for your server.
* *Note: HTML generation is temporarily disabled.*

# 21.11.2024 Update
* Added a toggle in the configuration file to switch between official ESET servers or mirrors (`official_servers_update` parameter in `nod32ms.conf`). This switches environment variable files (`init.py` for mirror mode and `init_official.py` for official ESET servers).
* In official update mode, the script checks for the server with the lowest latency and updates from it.
* Added generation of a web page for browser viewing, with the option to create a separate table.
* Minor improvements added.

# 24.10.2024 Update
* Added retry functionality for file downloads during connection issues.
* Added a check to determine if a file download is necessary.
* Added cleanup of old files and folders not required by the current database version.
* Improved visual output formatting.
* Added an output verbosity parameter (can be changed in `/inc/log.py` via `log_informativeness`).
* Databases for each version are now stored in separate folders. The folder structure is incompatible with previous versions; please manually clear your storage before updating.

**Script Execution Example:**
![image](https://github.com/user-attachments/assets/48943a3a-95f6-46c1-b265-6b4245360a53)
