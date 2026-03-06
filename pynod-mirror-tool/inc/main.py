# -*- coding: utf-8 -*-
# This file is part of the PyNOD-Mirror-Tool project,
# the latest version of which can be downloaded at:
# https://github.com/Scorpikor/pynod-mirror-tool

import time
import requests
from requests.adapters import HTTPAdapter, Retry
from inc.log import *
from inc.user_agent import *
from inc.tools import *
from inc.parser import *

#from http import HTTPStatus
from requests.exceptions import HTTPError

def download_av_base_version(version, connect_dict):
    # Download all files for the specified version
    start_ver_time = time.time()
    downloaded_size_version = 0                                       # Network traffic counter for the current version
    downloaded_files_version = 0                                      # Counter of downloaded files for the current version
    os_separator = connect_dict['os_separator']                       # Folder separator specific to the current OS
    connect_user_agent = user_agent(version)                          # Form the User-Agent string
    retries_all = 0                                                   # Counter for total file redownload attempts
    alien_DB_version = 0
    our_DB_version = 0
    mode_one_dir_base = connect_dict['mode_one_dir_base']             # Antivirus database storage mode "mode_one_dir_base"
    
    with requests.Session() as session:                               # Create a session
            retries = Retry(total=connect_dict['mirror_connect_retries'],
                      backoff_factor=0.4,
                      status_forcelist=[ 429, 500, 502, 503, 504 ])
            session.mount('http://', HTTPAdapter(max_retries=retries))
            
            init_environment = connect_dict['init_environment']            # Retrieve variables for this antivirus version
            log(f"[{version}] Updating version: {init_environment['name']}", 1)            
            web_server_root = connect_dict['web_server_root']             # Path to the web server root where we store databases
            
            
            prefix_config = connect_dict['prefix_config']                 # Folder name for storing databases of different versions in the web server root
            add_path = ''                                                 # Additional path
            new_files_list = []                                           # List of files in the new database (needed for cleaning old files)
            files_to_delete = []                                          # List of old database files to delete
            upd_ver_in_storage_path = f"{web_server_root}{os_separator}{init_filepath_fix(os_separator,init_environment['dll'])}"
            our_DB_version, _ = parser_get_DB_version(upd_ver_in_storage_path)
            log(f"[{version}] Current update.ver version in storage: {our_DB_version} {upd_ver_in_storage_path}", 1)
            
            if connect_dict['mode_one_dir_base'] == 1:
                # Mode for storing databases in a single folder is enabled
                log(f"[{version}] Saving databases in a single directory mode", 3)
                save_path = f"{connect_dict['web_server_root']}{os_separator}{init_filepath_fix(os_separator,init_environment['dll']).rsplit(os_separator, 1)[0]}"
            else:
                # Normal database storage mode
                save_path = f"{connect_dict['web_server_root']}{prefix_config}{os_separator}{version}"    # Path to save database files without the update.ver sub-path
            log(f"---- SAVE PATH main [{save_path}]", 5)                      # ----------------------------------------------------------------
            # ===================================
            # Stage 1. Download update.ver to tmp
            # ===================================
            log(f"[{version}] Downloading update.ver file", 2)
            download_text = 'update.ver'
            download_time = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            tmp_updatever_filepath = f"{connect_dict['current_directory']}{os_separator}tmp{os_separator}update.ver"
            log(f"[{version}] Saving update.ver to: {tmp_updatever_filepath}", 1)
            # Dictionary for downloading update.ver
            download_dict = {
                'text': f"{TColor.GREEN}[{download_time}]{TColor.ENDC} [{version}] {download_text}",                                     # Text in the download line
                'colour': 'green',                                                                                                      # Color of the download bar
                'download_url': connect_dict['mirror_server'] + '/'+ init_environment['upd'],                                        # URL to download update.ver for this version
                'file_size': None,
                'save_path': tmp_updatever_filepath,                                                                                    # Path to save update.ver
                'user_agent': connect_user_agent,                                                                                       # User-Agent for server connection
                'server_user': connect_dict['server_user'],                                                                               # Login for server connection
                'server_password': connect_dict['server_password'],                                                                           # Password for server connection
                'server_timeout': connect_dict['server_timeout'],                                                                             # Connection operation timeout
                'mirror_connect_retries': connect_dict['mirror_connect_retries'],                                                             # Number of attempts to download the file
                'mode_one_dir_base': 0                                                                                                  # 0 because we download to tmp
                }
            
            # Expected output:
            # Error, error text, downloaded file size, file save path
            error, error_text, downloaded_size_version_result, path_to_save = tools_download_file(session, download_dict)
            
            if error == None:
                downloaded_size_version += downloaded_size_version_result
                downloaded_files_version += 1   # update.ver is always downloaded
            
                # Parse update.ver and return database version and URL for auth verification 
                alien_DB_version, testfile_url = parser_get_DB_version(download_dict['save_path'])
                
                log("[" + str(version)+ "]" + " Current database version    : " + str(our_DB_version), 1)
                log("[" + str(version)+ "]" + " Database version on mirror: " + str(alien_DB_version), 1)
                
                if alien_DB_version == 0:
                    log("An invalid update.ver was downloaded! Ensure databases for version " + str(version) + " exist on the server.", 4)
                    log("Alternatively, the 'upd' dictionary value in init.py might be incorrect for version " + str(version), 4)
                    log("Cannot continue script execution! Stopping.", 4)
                    sys.exit(0)
                if our_DB_version >= alien_DB_version:
                    log("[" + str(version)+ "]" + " Antivirus version " + str(version) + " does not require database updates from mirror " + str(connect_dict['mirror_server']), 2)
                
                if our_DB_version < alien_DB_version:
                    # ================================
                    log("[" + str(version)+ "]" + " Database update required", 2)
                    
                    files_to_download = parser_update_ver(download_dict['save_path'])
                    num_files_to_download = len(files_to_download)
                    log("[" + str(version)+ "]" + " Number of files in update.ver to download: " + str(num_files_to_download) , 2)                    
                    file_counter = 0

                    if connect_dict['official_servers_update'] == 1 and testfile_url:        # Additional check if updating from official servers
                        # =========================================================
                        # Stage 2.1 Download single file to verify authorization
                        # =========================================================
                        tmp_test_filepath = f"{connect_dict['current_directory']}{os_separator}tmp{os_separator}test.file"                
                        download_dict = {
                        'text': f"{TColor.GREEN}[{download_time}]{TColor.ENDC} [{version}] {testfile_url.split('/')[-1]}",              # Text in the download line
                        'colour': 'red',                                                                                                # Color of the download bar
                        'download_url': f"{connect_dict['mirror_server']}/{testfile_url}",                                          # URL to download for this version
                        'file_size': None,
                        'save_path': tmp_test_filepath,                                                                                 # Path to save
                        'user_agent': connect_user_agent,                                                                               # User-Agent for connection
                        'server_user': connect_dict['server_user'],                                                                             # Login for server connection
                        'server_password': connect_dict['server_password'],                                                                           # Password for server connection
                        'server_timeout': connect_dict['server_timeout'],                                                                             # Connection timeout
                        'mirror_connect_retries': connect_dict['mirror_connect_retries'],                                                             # Number of attempts
                        'mode_one_dir_base': 0                                                                                          # 0 because we download to tmp
                        } 
                        
                        # Expected output:
                        # Error, error text, downloaded file size, file save path
                        error, error_text, downloaded_size_version_result, path_to_save = tools_download_file(session, download_dict)
                    
            if error == None and our_DB_version < alien_DB_version:
                downloaded_size_version += downloaded_size_version_result   # Add test file size to total counter
                downloaded_files_version += 1                                # Test file downloaded successfully
                # ========================================================
                # Stage 2.2 Download database files
                # ========================================================                
                download_dict = {
                    'version': version,
                    'os_separator': os_separator,
                    'path_fix': str(init_environment['fix']),              # Adjust path if updating from a mirror created by the antivirus itself
                    'mirror_server': connect_dict['mirror_server'],              # URL for downloading
                    'save_path': save_path,                                      # Path to save database files
                    'user_agent': connect_user_agent,                            # User-Agent for server connection
                    'server_user': connect_dict['server_user'],                  # Login for server connection
                    'server_password': connect_dict['server_password'],          # Password for server connection
                    'server_timeout': connect_dict['server_timeout'],            # Download operation timeout
                    'mirror_connect_retries' : connect_dict['mirror_connect_retries'],    # Number of retry attempts
                    'max_workers' : connect_dict['max_workers'],                 # Number of download threads
                    'mode_one_dir_base': mode_one_dir_base                       # Change save paths if enabled (=1)
                    }
                
            
                # Expected output:
                # Error, error text, size of downloaded files, count of downloaded files, total retries, list of saved files
                error, error_text, downloaded_size_version_result, downloaded_files_version_result, retries_all, new_files_list = download_files_concurrently(download_dict, files_to_download)
                                        
            if error == None and our_DB_version < alien_DB_version:
                downloaded_size_version += downloaded_size_version_result       # Add file size to counter
                downloaded_files_version += downloaded_files_version_result     # Add file count to counter 
                # Database successfully updated
                if our_DB_version != alien_DB_version:
                    log(f"Successfully updated from version {our_DB_version} to {alien_DB_version}", 2)
                    # Clean update.ver of unnecessary categories
                    categories_to_remove = {r"\[SERVERS\]", r"\[LINKS\]", r"\[HOSTS\]"}
                    update_ver_remove_categories(tmp_updatever_filepath, categories_to_remove)
                    
                    # Clean up old files
                    all_files_in_DB_folder = list_files_and_folders(download_dict['save_path'])
                    files_to_delete = elements_to_delete(new_files_list, all_files_in_DB_folder)
                    delete_files(files_to_delete)
                    remove_empty_folders(download_dict['save_path'])                
                    log(f"Number of old files deleted: {len(files_to_delete)}", 5)                    

                    # ================================
                    # Apply patch for V3 protoscan
                    # ================================
                    if connect_dict['protoscan_v3_patch'] == 1 and version == 'v3':
                            log(f"[{version}] Patching update.ver with PROTOSCAN patch", 1)
                            categories_to_remove = {r'\[.*?PROTOSCAN.*?\]'}    # Remove categories from update.ver
                            update_ver_remove_categories(tmp_updatever_filepath, categories_to_remove)
                            patch_dir = f"{connect_dict['current_directory']}{os_separator}patch{os_separator}protoscanv3"      # Path to folder containing patch files
                            log(f"Path to patch folder: {patch_dir}", 5)
                            # Get patch files in folder
                            file_names = []                            
                            for file_name in os.listdir(patch_dir):
                                if os.path.isfile(os.path.join(patch_dir, file_name)) and file_name.endswith(".nup"):
                                    file_names.append(file_name)
                            log(f"Patch files found: {file_names}", 5)
                            
                            # Copy files to database storage    
                            for file in file_names:                                
                                from_file = f"{patch_dir}{os_separator}{file}"
                                if connect_dict['mode_one_dir_base'] == 1:
                                    # Fix path in mode_one_dir_base
                                    to_file = f"{save_path}{os_separator}{file}"
                                else:
                                    to_file = f"{save_path}{os_separator}patch{os_separator}{file}"
                                log(f"Moving file from {from_file} to {to_file}", 5)
                                move_file(from_file, to_file, mode='copy')
                                    
                            # Add contents of protoscanV3.add to the end of update.ver
                            src_file =f"{patch_dir}{os_separator}protoscanV3.add"
                            dst_file = tmp_updatever_filepath
                            log(f"Appending content of {src_file} to the end of {dst_file}", 5)
                            append_file_to_another(src_file, dst_file)                            
                            
                    # Modify file paths in update.ver for mode_one_dir_base
                    if connect_dict['mode_one_dir_base'] == 1:
                        log(f"[{version}] Modifying update.ver for mode_one_dir_base", 3)
                        modify_update_ver(tmp_updatever_filepath)
                        
                    # Copy update.ver to storage
                    updatever_storage_path = f"{connect_dict['web_server_root']}{os_separator}{init_filepath_fix(os_separator,init_environment['dll'])}"
                    log(f"[{version}] Moving update.ver to storage: {updatever_storage_path}", 1)
                    move_file(tmp_updatever_filepath, updatever_storage_path)
                    
                    
                log(f"[{version}] Path to databases: {save_path}", 3)                                                        
            session.close()
    
    if error != None:
        # Database update error
        log(f"[{version}] Failed to update from version {our_DB_version} to {alien_DB_version}", 4)
        
    end_ver_time = str(convert_seconds(time.time() - start_ver_time))
    # Return
    ret_dict = {
        'error': error,                                             # None = no errors
        'error_text': error_text,                                   # Error text if occurred
        'base_version': alien_DB_version,                           # Database version 
        'downloaded_files_version': downloaded_files_version,       # Count of downloaded files for current version
        'downloaded_size_versionown': downloaded_size_version,      # Size of downloaded files for current version
        'retries_all' : retries_all,                                # Count of redownload attempts
        'full_number_of_files_dir' : len(list_files_and_folders(save_path)),   # Count of files in database folder for current version
        'full_size_dir':  folder_size(save_path),                   # Total size of database files for current version
        'trash_files_deleted': len(files_to_delete),                # Count of old files deleted
        'update_time': end_ver_time,                                # Time spent updating databases for current version
        }
        

    return ret_dict
