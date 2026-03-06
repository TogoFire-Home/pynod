# -*- coding: utf-8 -*-
# This file is part of the PyNOD-Mirror-Tool project
# The latest version can be downloaded at:
# https://github.com/Scorpikor/pynod-mirror-tool

import re
import platform
import requests
from tqdm import tqdm
import os
import shutil
import sys
import datetime
from inc.log import *
from collections import deque
import threading
import stat

# from http import HTTPStatus
from requests.exceptions import HTTPError
# ==========================
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
# from ping3 import ping, verbose_ping                     # import from ping3

    
def tools_download_file(session, download_dict):
    # ----------------------------------------------------------------------------
    # Downloads a file, returns error, error_text, downloaded_size, path_to_save
    # Error = None - no errors
    # ----------------------------------------------------------------------------                           
    downloaded_size = 0                                         # Downloaded bytes counter 
    error = None                                                # Error status marker
    error_text = ""                                             # Error message text
    mode_one_dir_base = download_dict['mode_one_dir_base']      # If enabled (=1), change file save paths
    mirror_connect_retries = download_dict['mirror_connect_retries']        # Number of retries to download
    log("tools.py:tools_download_file", 5)
    
    # Headers for standard download
    headers = {"User-Agent": download_dict['user_agent'],       # Add user agent to headers
                }
    # Headers to request file size in uncompressed form
    headers_identity = {"User-Agent": download_dict['user_agent'],          # Add user agent to headers
               "Accept-Encoding": "identity"                    # Request files without compression
                }
                
    url = download_dict['download_url']                         # URL for downloading
    bar_color = download_dict['colour'] 
    log("tools.py:tools_download_file: Download URL: " + str(url), 5)
    path_to_save = download_dict['save_path']                   # Path to save file
    # log(f"tools.py:tools_download_file: SAVE PATH: {path_to_save}", 3)  
    server_timeout = download_dict['server_timeout']            # Connection operation timeout
    # Add authorization 
    if download_dict['server_user'] and download_dict['server_password']:
        auth1 = (download_dict['server_user'], download_dict['server_password'])        
    else:
        auth1 = None
                
    # Check if download file size is specified in dictionary
    if download_dict['file_size']:
        total_size = download_dict['file_size']
        log(f"tools.py:tools_download_file: {url} File size taken from update.ver: {total_size}", 5)
        leave = False
    else:
        log(f"tools.py:tools_download_file: File size not specified in input dictionary {url}", 5)
        leave = True    # To make update.ver download visible
    
    # Check for existing file and its size if size is specified
    if os.path.exists(path_to_save) and download_dict['file_size']:
        local_file_size = os.path.getsize(path_to_save)  # Local file size
        if local_file_size == total_size:
            log(str(download_dict['text']) + " " + str(path_to_save) + " File already exists " + str(local_file_size) + " bytes.", 5)
            return error, error_text, 0, path_to_save # Return 0 bytes as we did not download it

            
    # If file does not exist or size differs, perform download
    try:
        response = None
        response = session.get(url, headers=headers, auth=auth1, stream=True, timeout=server_timeout)
        response.raise_for_status()
    
    except requests.exceptions.RequestException as e:
        error = 1
        error_text = f"Connection error: {str(e)}"
        log(f"tools.py:tools_download_file: Server connection error. File {url}", 5)
        log(str(e), 5)
        return error, error_text, downloaded_size, path_to_save
    
    except Exception as e:
        error = 1
        error_text = str(e)
        log(f"tools.py:tools_download_file: Server connection error. File {url}", 5)       
        log(str(e), 5)
        if response and response.status_code == 401:
            error = "401"
            error_text = "401 Authorization error! Check credentials (login/password) in the configuration file!"
            log(f"tools.py:tools_download_file: {error_text} {url}", 5)                
        return error, error_text, downloaded_size, path_to_save

        
    log(f"tools.py:tools_download_file: Request to server - 1: {str(response.request.headers)}", 5)
    log(f"tools.py:tools_download_file: Response from server - 1: {str(response.headers)}", 5)
    
    # Parsing file size
    # We need the uncompressed file size from the server
    total_size = int(response.headers.get('content-length', 0)) 
    encoding = response.headers.get('Content-Encoding', 'identity')
    if encoding != 'identity':               # Must request uncompressed file size from server    
        try:
            response2 = session.get(url, headers=headers_identity, auth=auth1, timeout=server_timeout)
            response2.raise_for_status()
            total_size_identity = int(response2.headers.get('content-length', 0))
            log(f"tools.py:tools_download_file: Request to server - 2: {str(response2.request.headers)}", 5)
            log(f"tools.py:tools_download_file: Response from server - 2: {str(response2.headers)}", 5)
            
        except Exception as e:
            error = 1
            error_text = str(e)
            log(f"tools.py:tools_download_file: Server connection error. File {url}", 5)       
            log(str(e), 5)
            return error, error_text, downloaded_size, path_to_save
                                    
    os.makedirs(os.path.dirname(path_to_save), exist_ok=True)
    with open(path_to_save, "wb") as file, tqdm(
        desc=download_dict['text'],
        total=total_size,
        unit='B',
        unit_scale=True,
        ascii=True,
        colour=bar_color,
        leave=leave,
        unit_divisor=1024,
    ) as bar:
            try:
                for data in response.iter_content(chunk_size=1024):
                    file.write(data)
                    bar.update(len(data))
            except Exception as e:
                error = 1
                error_text = str(e)
                log(str(e), 5)
                return error, error_text, downloaded_size, path_to_save
                
    downloaded_size = os.path.getsize(path_to_save)
            
    if encoding == 'identity':
        # Initial file size specified as uncompressed
        if downloaded_size != total_size:
            error = 1
            error_text = f"Downloaded file size ({downloaded_size} bytes) does not match expected ({total_size} bytes)"
            log(error_text, 3)
        else:
            log(f"Downloaded file size ({downloaded_size} bytes) matches server claim ({total_size} bytes)", 5)
    else:
        # If initial size specified as compressed
        # Check size via second request response2
        encoding2 = response2.headers.get('Content-Encoding', 'identity')
        response2.close()
        
        # Check if we received uncompressed size from server
        if encoding2 == 'identity':
            # Request response2 returned uncompressed file size
            if downloaded_size != total_size_identity:
                # Size does not match expected
                error = 1
                error_text = f"Encoding {encoding}. Downloaded file size ({downloaded_size} bytes) does not match expected ({total_size_identity} bytes)"
                log(error_text, 3)
            else:
                log(f"Encoding {encoding}. Downloaded file size ({downloaded_size} bytes) matches expected ({total_size_identity} bytes)", 5)
        else:            
            log(f"Encoding {encoding}. Server did not provide uncompressed file size, leaving file without check", 3)
        
    response.close()
    return error, error_text, downloaded_size, path_to_save

def update_ver_remove_categories(filepath, categories_to_remove):
    # Remove categories from update.ver, e.g., [SERVERS], [LINKS], [HOSTS]
    remove_flag = 0
    with open(filepath, "r") as inp, open(filepath + ".out", "w") as out:
        inside_removed_category = False  # Flag if we are inside a section to be removed
        for line in inp:
                stripped_line = line.strip()
                # Check if it starts a new category
                if stripped_line.startswith("[") and stripped_line.endswith("]"):
                    inside_removed_category = any(re.match(pattern, stripped_line) for pattern in categories_to_remove)
                    if inside_removed_category:
                        remove_flag = 1

                # If NOT inside removed category, write line
                if not inside_removed_category:
                    out.write(line)
    shutil.move(filepath + ".out", filepath)
    if remove_flag != 0:
        log(f"File {filepath} was cleaned of categories {categories_to_remove}", 3)
    else:
        log(f"Categories to remove not found in file {filepath} {categories_to_remove}", 3)
        
def script_version(path):
    txt = ""
    filepath = f"{path}version"
    try:
        with open(filepath, 'r') as file:
            txt = file.readline().rstrip('\n')
    except:
        txt = None
    return txt
    
def move_cursor_to(x, y):
    # Function to move cursor to specified position
    print(f"\033[{y};{x}H", end='')

def clear_line():
    # Function to clear line
    print("\033[K", end='')    
        
def pbar_colour(number):
    # Choose progress bar color based on current retry attempt
    colors = [
    'green',
    'yellow',
    'red'
    ]
    if number > 2:
        number = 2
    if number < 0:
        number = 0
    return colors[number]

def download_files_concurrently(download_dict, files_to_download):
    # Parallel file download
    new_files = []                                              # List of new files saved to storage 
    error = None                                                # Overall download status
    error_text = ""                                             # Error text
    stop_downloading = False                                    # Stop download flag
    retries_all = 0                                             # Counter for retry attempts
    os_separator = download_dict['os_separator']
    version = download_dict['version']
    desc = f"[{version}] General progress"                      # Progress indicator message
    mode_one_dir_base = download_dict['mode_one_dir_base']      # If enabled (=1), change file save paths
    path_fix = download_dict['path_fix']                        # Root folder for base files in web root

    # Progress bar
    pbar = tqdm(total=len(files_to_download), desc=desc, colour='cyan', ascii=True, unit="file")

    def prepare_and_download(session, base_url, file_path, file_size, os_separator, version, retry_count):
        # Prepare dictionary for each file download and call tools_download_file
        
        # ---------------------------
        # Fix path when file in update.ver does not start with "/"
        # ---------------------------
        if not file_path.startswith("/"):
            file_path = f"{path_fix}/{file_path}"
        
        file_url = f"{base_url}{file_path}"                     # URL for download
            
        # Form path for saving files
        if mode_one_dir_base == 1:
            # If enabled, crop subfolders so files are saved in one folder
            save_path = f"{download_dict['save_path']}{os_separator}{file_path.split('/')[-1]}"
            log(f"---------: MOD save path : {save_path}  ", 5)
        else:
            # Normal saving mode
            save_path = f"{download_dict['save_path']}{file_path.replace('/', os_separator)}"
        
        download_file_dict = {
            'download_url': file_url,
            'colour': pbar_colour(retry_count),
            'save_path': save_path,
            'user_agent': download_dict['user_agent'],
            'server_user': download_dict['server_user'],
            'server_password': download_dict['server_password'],
            'server_timeout': download_dict['server_timeout'],
            'mirror_connect_retries': download_dict['mirror_connect_retries'],
            'file_size': file_size,
            'text': f"[{version}] [{retry_count}] {file_path.split('/')[-1]}",  # Filename for tqdm
            'mode_one_dir_base': mode_one_dir_base
        }
        return tools_download_file(session, download_file_dict)

    # Maximum attempts
    max_retries = download_dict['mirror_connect_retries']
    max_workers = download_dict['max_workers']
    retry_count = {}                                          # Retry counter for each file
    downloaded_size_version_result = 0                        # Total size of downloaded data
    downloaded_files_version_result = 0                       # Count of successfully downloaded files
    
    # Task queue
    task_queue = deque([(file_path, file_size) for file_path, file_size in files_to_download])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        with requests.Session() as session:
            futures = {}  # Active tasks

            # While there are tasks in queue or active tasks
            while task_queue or futures:
                # Fill task pool
                while task_queue:
                    if not stop_downloading:
                        file_path, file_size = task_queue.popleft()
                        future = executor.submit(
                            prepare_and_download, session, download_dict['mirror_server'], file_path, file_size, os_separator, version, retry_count.get(file_path, 0)
                        )
                        futures[future] = (file_path, file_size)
                    else:
                        break

                # Process completed tasks
                for future in as_completed(futures):
                    file_path, file_size = futures.pop(future)

                    # Execute tools_download_file
                    err, err_text, downloaded_size, path_to_save = future.result()

                    if err is None:  # If file downloaded successfully
                        new_files.append(path_to_save)
                        if downloaded_size != 0:
                            downloaded_size_version_result += downloaded_size
                            downloaded_files_version_result += 1
                    else:
                        if err != "401":
                            # If error, increase retry counter
                            retries_all += 1
                            retry_count[file_path] = retry_count.get(file_path, 0) + 1
                            log(f"tools.prepare_and_download : Download error: {file_path}. Adding to queue for retry.  ", 5)
                            if retry_count[file_path] <= max_retries and not stop_downloading:
                                # Add task to start of queue
                                task_queue.appendleft((file_path, file_size))
                            else:
                                # Limit reached, stop loading
                                log(f"tools.prepare_and_download : Download error: {file_path}. No more retries...", 5)
                                error = 1
                                error_text += f"Error: {file_path.split('/')[-1]} skipped after {max_retries} attempts. {err_text}\n"
                                stop_downloading = True
                                break
                        else:
                            error = err
                            error_text += f"Error: {file_path.split('/')[-1]} {err_text}\n"
                            stop_downloading = True

                    # Update progress bar
                    pbar.update(1)

    pbar.close()
    return error, error_text, downloaded_size_version_result, downloaded_files_version_result, retries_all, new_files
    
def move_file(source_path, destination_path, mode='move'):
    # Move file
    log(f"tools.py:move_file mode {mode} from {source_path} to {destination_path}", 5)
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    if mode == 'move':
        shutil.move(source_path, destination_path)
        log(f"File moved to {destination_path}", 5)
        
    elif mode == 'copy':
        shutil.copy(source_path, destination_path)        
        log(f"tools.py:move_file File copied to {destination_path}", 5)
        os.chmod(destination_path, 0o644)
        log(f"Rights 644 applied to file {destination_path}", 3)
    else:
        log(f"tools.py:move_file Invalid mode! {mode}", 4)
    
def modify_update_ver(updatever_file_path):
    # Modify 'file' parameter in update.ver
    log("tools.py:modify_update_ver", 5)
    with open(updatever_file_path, 'r') as file:
        lines = file.readlines()
        
    new_lines = []
    for line in lines:
        if line.startswith("file="):
            # Modify directive
            parts = line.split('=', 1)
            parts[1] = parts[1].split('/')[-1]
            modified_line = f"{parts[0]}={parts[1]}"
            new_lines.append(modified_line)
        else:
            new_lines.append(line)
            
    with open(updatever_file_path, 'w') as file:
        file.writelines(new_lines)

def folder_size(folder_path):
    # Return folder size in bytes
    log("tools.py:folder_size", 5)
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for file in filenames:
            file_path = os.path.join(dirpath, file)
            # Verify if it is a file (in case of symlinks)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
    return total_size
    
def sizeof_fmt(num):
    # Translate bytes to readable format
    log("tools.py:sizeof_fmt", 5)
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0
    return "%3.1f %s" % (num, 'TB')
    
def convert_seconds(seconds):
    # Translate seconds to readable format
    log("tools.py:convert_seconds", 5)
    td = datetime.timedelta(seconds=seconds)

    p = str(td).partition('.')
    if p[2]:
        s = ''.join([p[0], p[1], p[2][0:2]]) # Precision to two decimal places for seconds
    else:
        s = p[0]

    p = s.partition(' days,')
    if not p[1]:
        p = s.partition(' day,')
    if p[1]:
        s = ''.join([p[0], 'd', p[2]])

    return s
    
def list_files_and_folders(directory):
    # Return list of files and folders in directory
    log("tools.py:list_files_and_folders", 5)
    file_list = []
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
           file_list.append(os.path.join(dirpath, filename))
    return file_list
    
def elements_to_delete(files_new, files_all):
    # Remove files_new from files_all, leaving only what needs deletion
    log("tools.py:unique_elements", 5)
    return [target for target in files_all if target not in files_new]
    
def delete_files(file_list):
    # Delete files according to list
    log("tools.py:delete_files", 5)
    for file in file_list:
        os.remove(file)
    log("tools.py:delete_files: Old files deleted", 5)
    
def remove_empty_folders(directory):
    # Delete empty folders
    log("tools.py:remove_empty_folders", 5)
    count = 0
    for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
        # If directory is empty (no files or subdirectories)
        if not dirnames and not filenames:
            count += 1 
            log("tools.py:remove_empty_folders: Deleting empty folder: " + str(dirpath), 5)
            os.rmdir(dirpath)
    log("Number of empty folders deleted: " + str(count), 2)

def file_creation_datetime(file_path):
    # Return file creation date
    creation_time = os.path.getmtime(file_path)
    creation_date = datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
    return creation_date

def ping_server(server, attempts=3):
    # Ping server and return average response time
    times = []
    for _ in range(attempts):
        result = ping(server, timeout=1, unit='ms')
        if result is not None and result != 0 and result is not False:
            times.append(result)
            
    log(str(server) + " " + str(times), 5)
    if times:
        avg_time = sum(times) / len(times)
        return server, avg_time
    else:
        return server, None

def request_ping_server(server, random_version, file_get, random_useragent, timeout=2, attempts=1):
    # Alternative method to check official server status
    times = []
    server_url = f'http://{server}/{file_get}'
    headers = {"User-Agent": random_useragent}
    
    for _ in range(attempts):
        response = None
        start = time.time()
        try:                
            response = requests.get(server_url, headers=headers, timeout=timeout)
            response.raise_for_status()       
            latency = (time.time() - start) * 1000
                
        except requests.RequestException as e:            
            if response is not None and response.status_code in (200, 401, 403):
                latency = (time.time() - start) * 1000
            else:                
                log(f'{server} Error: {e.__class__.__name__} | {e}', 5)
                return server, None
                           
        times.append(latency)
    if times:
        log(f'try {server} {times}', 5)
        avg_time = sum(times) / len(times)
        return server, avg_time
    else:
        return server, None

def choosing_the_best_server(oficial_servers, random_version, file_get, random_useragent, mode='pong'):
    # Choose best official server for update
    log("Choosing best official server for updates...", 1)
    
    results = []
    if mode == 'ping':        
        log("tools.py:choosing_the_best_server: mode = ping3", 5)
        pinger = ping_server
    else:
        log("tools.py:choosing_the_best_server: mode = request", 5)
        log(f'Identifying as antivirus {random_version} for check', 5)
        pinger = partial(request_ping_server, random_version=random_version, file_get=file_get, random_useragent=random_useragent)        
        
    with ThreadPoolExecutor(max_workers=len(oficial_servers)) as executor:
        future_to_server = {executor.submit(pinger, server): server for server in oficial_servers}
        for future in as_completed(future_to_server):
            server = future_to_server[future]
            try:
                server, avg_time = future.result()
                if avg_time is not None:
                    results.append((server, avg_time))
            except Exception as exc:
                print(f"tools.py:choosing_the_best_server: {server} raised exception: {exc}")
                sys.exit(1)
                
    # Choose server
    if len(results) == 0:
        log("tools.py:choosing_the_best_server: No live servers for update", 4)
        log("tools.py:choosing_the_best_server: Script terminating", 4)
        sys.exit(1)
    elif len(results) == 1:
        server, avg_time = results[0]
        log("tools.py:choosing_the_best_server: Only one live server " + str(server) + " " + str(avg_time), 5)
        return server, avg_time
    else:
        best_server = None
        best_time = 10000
        for server, avg_time in results:
            if avg_time is not None:
                if avg_time < best_time:
                    best_server = server
                    best_time = avg_time
        
        return best_server, best_time
        
def os_dir_separator():
    os_platform = platform.system()
    if os_platform == "Linux":
        log("tools.py:os_dir_separator: Using Linux platform", 5)
        return os_platform, "/"
    elif os_platform == "Windows":
        log("tools.py:os_dir_separator: Using Windows platform", 5)
        return os_platform, "\\"
    elif os_platform == "FreeBSD":
        log("tools.py:os_dir_separator: Using FreeBSD platform", 5)
        return os_platform, "/"
    else:
        log("tools.py:choosing_the_best_server: Platform script is running on was not tested!", 4)
        log("tools.py:choosing_the_best_server: If you have a strong need to run it on your platform, contact the script author.", 4)
        log("tools.py:choosing_the_best_server: Script terminating", 4)
        sys.exit(1)
        
def init_filepath_fix(os_separator, filepath):
    # Fix path according to OS
    return filepath.replace('/', os_separator)
    
def error_text_fix(text):
    # Remove potentially dangerous characters that might prevent telegram message sending
    text = text.translate(str.maketrans({"<": "", ">": "", "'": "", '"': ""}))
    return text
    
def append_file_to_another(src, dst):
    # Read from 'src' and append to the end of 'dst'
    try:
        with open(src, 'rb') as file1, open(dst, 'ab') as file2:
            # Read from first file and write to end of second
            file2.write(file1.read())
        log(f"Contents of '{src}' added to end of '{dst}'", 5)
    except Exception as e:
        log(f"tools.py:append_file_to_another: Error during copy: {e}", 4)
