# -*- coding: utf-8 -*-
# This file is part of the PyNOD-Mirror-Tool project,
# the latest version of which can be downloaded at:
# https://github.com/Scorpikor/pynod-mirror-tool

import configparser
import time
import os
import re
from inc.class_tools import *

if os.name == "nt":
    try:
        # Trying to connect colorama for correct color display in the terminal for Windows OS
        import colorama
        colorama.init(convert=True, autoreset=True)
    except ImportError:
        print("Colorama library not found")

    

def log(text, log_level):
    # Function to distribute message output
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    
    levels = {
        1: (TColor.GREEN, 1),   # info
        2: (TColor.CYAN, 2),    # info2
        3: (TColor.MAGENTA, 3), # warning
        4: (TColor.RED, 0),     # error (always displayed)
        5: (TColor.GRAY, 5),    # debug1
    }
    
    color, min_level = levels.get(log_level, (TColor.YELLOW, 0))
    
    # Writing to file
    if generate_log_file == 1:
        if log_level <= log_informativeness or log_level == 4:
            log_file.writelines(f"{timestamp} {text}\n")
            
    # Displaying to console
    if log_level == 4 or log_informativeness >= min_level:
        print(f"{color}[{timestamp}]{TColor.ENDC} {text}")    

            
def trim_log_file_tail(path, max_bytes=1024*1024):
    # Function to trim the log file if its size exceeds max_bytes
    if not os.path.exists(path):
        return

    size = os.path.getsize(path)
    if size <= max_bytes:
        log(f"Log file trimming not needed. File size {size} <= {max_bytes}", 5)
        return  # Trimming not needed
        
    log(f"Trimming log file....", 3)
    with open(path, "rb") as f:
        f.seek(-max_bytes, os.SEEK_END)  # Seek back from the end
        data = f.read()

        # Find the first full line
        first_newline = data.find(b'\n')
        if first_newline != -1:
            data = data[first_newline + 1:]

    # Overwrite the file with only this part
    with open(path, "wb") as f:
        f.write(data)

def path_is_valid_for_os(path: str) -> bool:
    # Validation function to filter out incorrect strings in the file name from the config
    if os.name == "posix":  # Linux / macOS
        # Windows-style path looks like C:\ or D:\, check for this
        if re.match(r"^[A-Za-z]:\\", path):
            return False
        # Backslashes for Linux are suspicious
        if "\\" in path:
            return False
        return True

    elif os.name == "nt":  # Windows
        invalid_chars = r'<>:"|?*'
        return not any(ch in path for ch in invalid_chars)

    return True

        
def close_log():
    if generate_log_file == 1:
        trim_log_file_tail(log_file_path, max_bytes=log_file_size*1024)
        log_file.writelines("\n"*5)
        log_file.close()


# Log file initialization        
script_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config = configparser.ConfigParser()
config.read(f"{script_root_dir}{os.sep}nod32ms.conf", encoding='utf-8')        # Read configuration file nod32ms.conf

generate_log_file = int(config.get('LOG', 'generate_log_file'))
log_informativeness = int(config.get('LOG', 'log_informativeness'))
log_file_size = int(config.get('LOG', 'log_file_size'))
default_log_file_path = f"{script_root_dir}{os.sep}pynod-mirror-tool.log"     # Default log location in script folder
log_file_path = str(config.get('LOG', 'log_file_path', fallback=default_log_file_path))
    
if generate_log_file == 1:
    # Log file path validity checks
    if log_file_path == "":
        log_file_path = default_log_file_path
            
    if not path_is_valid_for_os(log_file_path):
        # Invalid log path, writing to script folder
        text_msg = f"WARNING! Log file path format is invalid for this OS: {log_file_path}"
        print(f"{TColor.RED}{'-'*len(text_msg)}\n{text_msg}")
        print(f"Logging to {default_log_file_path}\n{'-'*len(text_msg)}{TColor.ENDC}")
        log_file_path = default_log_file_path

    if not os.path.isabs(log_file_path):
        # Path in config is not absolute, log will be written relative to script path    
        log_file_path = f"{script_root_dir}{os.sep}{log_file_path}"        

    try:
        # Create directories in path if they don't exist
        target_path = os.path.dirname(log_file_path)
        if target_path and not os.path.exists(target_path):
            os.makedirs(target_path, exist_ok=True)
            
        log_file = open(log_file_path, "a", encoding='utf-8')        
    except Exception as e:
        # If there's an error creating the log file using the config path,
        # try to write to the script directory
        text_msg = f"Error creating log file from config path:"
        print(f"{TColor.RED}{'-'*len(text_msg)}\n{text_msg}\n{e}\n{'-'*len(text_msg)}\n{TColor.ENDC}")
        log_file_path = default_log_file_path
        
        try:            
            log_file = open(log_file_path, "a", encoding='utf-8')
            
        except Exception as f:
            # Seems we cannot write a log file, trying to work without it
            text_msg = f"Cannot write log file, trying to work without it:"
            print(f"{TColor.RED}{'-'*len(text_msg)}\n{text_msg}\n{f}\n{'-'*len(text_msg)}\n{TColor.ENDC}")
            generate_log_file = 0
            
    if generate_log_file != 0:
        
        text_msg = f"Writing log file to {log_file_path}"
        
        print(f"{TColor.GREEN}{'-'*len(text_msg)}\n{text_msg}\n{'-'*len(text_msg)}\n{TColor.ENDC}")
        
        # Trim log file
        trim_log_file_tail(log_file_path, max_bytes=log_file_size*1024)
        log_file.write(f"\n{'='*40} NEW SESSION {'='*40} \n")
