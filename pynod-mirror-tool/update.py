# -*- coding: utf-8 -*-
# This file is part of the PyNOD-Mirror-Tool project
# the latest version can be downloaded at:
# https://github.com/Scorpikor/pynod-mirror-tool

import os
import time
import platform
import configparser
from inc.main import *
from inc.tools import *
from inc.parser import *
from inc.telegram import *
from inc.log import *
from inc.web import *

if __name__ == "__main__":
    print("\n"*2)
    start_time = time.time()                                            # Script start time
    error_trigger = 0                                                   # Error flag
    error_text = []                                                     # Reasons for errors
    downloaded_size_all = 0                                             # Network traffic counter
    downloaded_files_all = 0                                            # Downloaded files counter
    current_directory = os.path.dirname(os.path.abspath(__file__))      # Path from which update.py is launched

    os_platform, os_separator = os_dir_separator()                      # Determine platform and folder separator
    log(f"Script {script_version(current_directory + os_separator)} started", 1)
    config = configparser.ConfigParser()
    config.read(current_directory + os_separator + 'nod32ms.conf', encoding='utf-8')  # Read configuration file nod32ms.conf
    versions_to_update = parser_config_versions_to_update(current_directory + os_separator + 'nod32ms.conf')  # List of antivirus versions to update
    official_servers_update = int(config.get('CONNECTION', 'official_servers_update'))
    mirror_connect_retries = int(config.get('CONNECTION', 'mirror_connect_retries'))      # Number of attempts to download a file
    max_workers = int(config.get('CONNECTION', 'max_workers'))              # Number of download threads
    mode_one_dir_base = int(config.get('ESET', 'mode_one_dir_base', fallback=0))          # Mode for storing antivirus databases "mode_one_dir_base"
    protoscan_v3_patch = int(config.get('PATCH', 'protoscan_v3_patch'))        # Trigger for applying protoscan_v3_patch
    web_page_data = []                                                  # For generating WEB report page
    
    
    log(f"Using platform {os_platform}", 3)
    log(f"Current directory {current_directory}", 5)
    # Define web_server_root path based on platform (OS)
    if os_platform == 'Linux':
        web_server_root = str(config.get('SCRIPT', 'linux_web_dir'))              # Path to web server root
    elif os_platform == 'Windows':
        web_server_root = str(config.get('SCRIPT', 'windows_web_dir'))
    elif os_platform == 'FreeBSD':
        web_server_root = str(config.get('SCRIPT', 'linux_web_dir'))
    else:
        log("Script started on an undefined platform. Cannot determine variables.", 4)
        log("Terminating script....", 4)
        sys.exit(1)
                                    
    prefix_config = os_separator + config.get('ESET', 'prefix')                # Folder name for different base versions in web root
    server_user = str(config.get('CONNECTION', 'mirror_user'))
    server_password = str(config.get('CONNECTION', 'mirror_password'))
    server_timeout = int(config.get('CONNECTION', 'mirror_timeout'))
    
    # Choose init config according to the server type we are updating from
    if official_servers_update == 1:
        from inc.init_official import *
        log("Update mode from official servers (init_official.py config)", 1)
        oficial_servers = [value for key, value in config.items('OFFICIAL_SERVERS') if key.startswith('mirror')]
        # random
        random_version = random.choice(versions_to_update)
        file_get = init(random_version)['upd']
        random_useragent = user_agent(random_version)
        
        mirror, avg_time = choosing_the_best_server(oficial_servers, random_version, file_get, random_useragent)             # Choosing best official server
        log("Best official server chosen: " + str(mirror) + " " + str(avg_time) + " ms", 2)        
        mirror_server = f"http://{mirror}"
    else:
        from inc.init import *
        log("Update mode from unofficial mirrors (init.py config)", 1)
        mirror_server = str(config.get('CONNECTION', 'mirror'))                 # Mirror server from config
        log(f"Server to update from: {mirror_server}", 2)
        
    log("\n", 1)
    for version in versions_to_update:
        downloaded_size_version = 0                                           # Network traffic counter for current version
        downloaded_files_version = 0                                          # Downloaded files counter for current version
        
        connect_dict = {
        'official_servers_update': official_servers_update,
        'os_separator': os_separator,
        'current_directory': current_directory,
        'mirror_server': mirror_server,
        'mirror_connect_retries': mirror_connect_retries,
        'max_workers': max_workers,
        'server_user': server_user,
        'server_password': server_password,
        'server_timeout': server_timeout,
        'init_environment': init(version),
        'web_server_root': web_server_root,
        'prefix_config': prefix_config,
        'protoscan_v3_patch': protoscan_v3_patch,
        'mode_one_dir_base': mode_one_dir_base,                                     # mode_one_dir_base storage mode
        }
        result_dict = download_av_base_version(version, connect_dict)
        # =================
        # Generating reports
        # =================
        
        # Current date and time
        update_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        
        # update.ver modification date
        try:
            upd_ver_creation_datetime = file_creation_datetime(f"{web_server_root}{os_separator}{init_filepath_fix(os_separator, init(version)['dll'])}") 
        except:
            upd_ver_creation_datetime = None
        
        status_text = ""
        if result_dict['error'] != None:          
            log(f"[{version}] Error downloading version bases", 4)
            log(f"[{version}] Reason: {result_dict['error_text']}", 4)
            error_trigger = 1                                               # Set error trigger
            # Trim long error text
            error_string = result_dict['error_text']
            if len(error_string) > 250:
                try:
                    error_string = error_string.split('Error:')[-1]
                except:
                    error_string = str(error_string[0:250]) + "..."
                    
            error_text.append(f"❌ [{version}] {error_text_fix(error_string)}")      # Write error message
            web_page_data.append([1, str(version), str(error_string), "", "", "", "", "", "", "", ""])
            
        else:
            status_text = ""
            
            status_text += f"✅ [{version}] {result_dict['base_version']:g}\n"+\
                           f"Update : {upd_ver_creation_datetime}\n"+\
                           f"Base size: {sizeof_fmt(result_dict['full_size_dir'])} / {result_dict['full_number_of_files_dir']}f\n"
                        
            if result_dict['retries_all'] != 0:
                status_text += f"           : ⚠️{result_dict['retries_all']} retries\n"
            
            status_text += f"Downloaded  : {sizeof_fmt(result_dict['downloaded_size_versionown'])} / {result_dict['downloaded_files_version']}f\n"
            
            error_text.append(status_text)
            web_page_data.append([0,                                            # error flag
                                str(version),                                   # Antivirus version
                                str(result_dict['base_version']),               # Base version
                                str(result_dict['retries_all']),                # Retries
                                str(result_dict['downloaded_files_version']),   # Files downloaded for current version
                                str(sizeof_fmt(result_dict['downloaded_size_versionown'])),  # Size downloaded for current version
                                str(result_dict['trash_files_deleted']),        # Deleted
                                str(upd_ver_creation_datetime),                 # Bases updated date
                                str(update_date),                               # Last check date
                                str(result_dict['full_number_of_files_dir']),   # files
                                str(sizeof_fmt(result_dict['full_size_dir'])),  # Base size
                                ])
            
        downloaded_files_all += result_dict['downloaded_files_version']
        downloaded_size_all += result_dict['downloaded_size_versionown']
        
        log("-" * 50, 2)
        log(f"Files downloaded for current version : {result_dict['downloaded_files_version']}", 2)
        log(f"Size of downloaded files current version : {sizeof_fmt(result_dict['downloaded_size_versionown'])}", 2)
        log(f"Number of old base files deleted      : {result_dict['trash_files_deleted']}", 2)
        log(f"Total number of retries               : {result_dict['retries_all']}", 2)
        log(f"Time to download bases [{version}]: {result_dict['update_time']}", 2)
        log(f"Number of files in base folder [{version}]: {result_dict['full_number_of_files_dir']}", 2)
        log(f"Size of folder with bases [{version}]: {sizeof_fmt(result_dict['full_size_dir'])}", 2)
        log("-" * 50, 2)
        log("\n" * 3, 1)

        
    end_time = str(convert_seconds(time.time() - start_time))
    full_base_size = (folder_size(web_server_root + prefix_config))
    log("-" * 70, 2)
    log(f"Total files downloaded         : {downloaded_files_all}", 2)
    log(f"Size of all downloaded files: {sizeof_fmt(downloaded_size_all)}", 2)
    log(f"Total size of all bases {web_server_root + prefix_config} : {sizeof_fmt(full_base_size)}", 2)
    log(f"Script execution time: {end_time}", 2)
    log("-" * 70, 2)
    print()
    web_page_data.append([0, "", "", "", "", "", "", "", "", "Total downloaded, files", str(downloaded_files_all)])
    web_page_data.append([0, "", "", "", "", "", "", "", "", "Total downloaded, size", str(sizeof_fmt(result_dict['downloaded_size_versionown']))])
    web_page_data.append([0, "", "", "", "", "", "", "", "", "Full size of all bases", str(sizeof_fmt(full_base_size))])
    web_page_data.append([0, "", "", "", "", "", "", "", "", "Script execution time", str(end_time)])
    
    if config.get('LOG', 'generate_web_page') == "1":
        web_page_generator(web_page_data, config.get('LOG', 'generate_table_only'), init_filepath_fix(os_separator, config.get('LOG', 'html_table_path_file')))
    
    # Form Telegram message
    if str(config.get('TELEGRAM', 'telegram_inform')) == "1":
        info = ""
        token = config.get('TELEGRAM', 'token')
        chat_id = config.get('TELEGRAM', 'chat_id')
        if error_trigger == 0:
            msg_prefix = "✅"
        else:
            msg_prefix = "🆘"
        
        
        try:
            text = config.get('TELEGRAM', 'text').strip()
        except:
            text = ""
        if text != "":
            text += "\n"
            
        for txt in error_text:
            info += f"{txt}\n"
                
        info += '<code>' + '-' * 34 + "\n"
        info += f"Total downloaded: {sizeof_fmt(downloaded_size_all)} / {downloaded_files_all}f\n"
        info += f"Base size       : {sizeof_fmt(full_base_size)}\n"
        info += f"Script ran: {end_time}\n"
        info += "</code>\n"
        
        
        t_msg = f"<code>{msg_prefix} {update_date}\n[Server: {platform.node()}]\n{text}\n{info}</code>"
        log(f"Number of characters in Telegram message : {len(t_msg)}", 3)
        send_msg(t_msg, token, chat_id)
    
    # Close log file
    close_log()
