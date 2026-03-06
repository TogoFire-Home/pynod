# This file is part of the PyNOD-Mirror-Tool project,
# the latest version of which can be downloaded at:
# https://github.com/Scorpikor/pynod-mirror-tool

from inc.log import *
import sys

def init(ver):
   
    if ver == 'v3':
        return {
        'fix': '',
        'upd' : 'update.ver',
        'dll' : 'eset_upd/v3/dll/update.ver',
        'name' : 'ESET NOD32 Ver. 3-4, 6-8'
        }
    
    if ver == 'v5':
        return {
        'fix': '',
        'upd' : 'update.ver',
        'dll' : 'eset_upd/v5/dll/update.ver',
        'name' : 'ESET NOD32 Ver. 5'
        }
        
    if ver == 'v10':
        # Not working
        return {
        'fix': '',
        'upd' : 'eset_upd/v10/dll/update.ver',
        'dll' : 'eset_upd/v10/dll/update.ver',
        'name' : 'ESET NOD32 Ver. 10'
        }
    
    if ver == 'v12':
        return {
        'fix': '/dll',
        'upd' : 'eset_upd/v12/dll/update.ver',
        'dll' : 'eset_upd/v12/dll/update.ver',
        'name' : 'ESET NOD32 Ver. 12'
        }
    
    if ver == 'v14':
        return {
        'fix': '/dll',
        'upd' : 'eset_upd/v14/dll/update.ver',
        'dll' : 'eset_upd/v14/dll/update.ver',
        'name' : 'ESET NOD32 Ver. 14'
        }

    if ver == 'v15':
        return {
        'fix': '/dll',
        'upd' : 'eset_upd/v15/dll/update.ver',
        'dll' : 'eset_upd/v15/dll/update.ver',
        'name' : 'ESET NOD32 Ver. 15'
        }

    if ver == 'v16':
        return {
        'fix': '/dll',
        'upd' : 'eset_upd/v16/dll/update.ver',
        'dll' : 'eset_upd/v16/dll/update.ver',
        'name' : 'ESET NOD32 Ver. 16'
        }

    if ver == 'v18':
        return {
        'fix': '/dll',
        'upd' : 'eset_upd/consumer/windows/full/dll/update.ver',
        'dll' : 'eset_upd/v18/dll/update.ver',
        'name' : 'ESET NOD32 Ver. 17 - 18'
        }
        
    if ver == 'v19':
        return {
        'fix': '/dll',
        'upd' : 'eset_upd/consumer/windows/full/dll/update.ver',
        'dll' : 'eset_upd/v19/dll/update.ver',
        'name' : 'ESET NOD32 Ver. 19'
        }

    if ver == 'ep6':
        return {
        'fix': '/dll',                                     # Additional path, needed when update.ver paths lack directories
        'upd' : 'eset_upd/ep6.6/update.ver',               # Path where ep6 itself requests update.ver from the update server
        'dll' : 'eset_upd/ep6/dll/update.ver',             # Path where update.ver will be located on our mirror
        'name' : 'ESET NOD32 Endpoint Ver. 6'              # Description
        }   
    
    if ver == 'ep8':
        return {
        'fix': '/dll',                                     # Additional path
        'upd' : 'eset_upd/ep8/dll/update.ver',             # Path where ep8 itself requests update.ver from the update server
        'dll' : 'eset_upd/ep8/dll/update.ver',             # Path where update.ver will be located on our mirror
        'name' : 'ESET NOD32 Endpoint Ver. 8'              # Description
        }   

    if ver == 'ep9':
        return {
        'fix': '/dll',                                     # Additional path
        'upd' : 'dll/update.ver',                          # Path where ep9 itself requests update.ver from the update server
        'dll' : 'eset_upd/ep9/dll/update.ver',             # Path where update.ver will be located on our mirror
        'name' : 'ESET NOD32 Endpoint Ver. 9'              # Description
        }    

    if ver == 'ep10':
        return {
        'fix': '/dll',                                     # Additional path
        'upd' : 'dll/update.ver',                          # Path where ep10 itself requests update.ver from the update server
        'dll' : 'eset_upd/ep10/dll/update.ver',            # Path where update.ver will be located on our mirror
        'name' : 'ESET NOD32 Endpoint Ver. 9'              # Description
        }   
    
    if ver == 'ep11':
        return {
        'fix': '/dll',                                     # Additional path
        'upd' : 'dll/update.ver',                          # Path where ep11 itself requests update.ver from the update server
        'dll' : 'eset_upd/ep11/dll/update.ver',            # Path where update.ver will be located on our mirror
        'name' : 'ESET NOD32 Endpoint Ver. 11'             # Description
        }

    if ver == 'ep12':
        return {
        'fix': '/dll',                                    # Additional path
        'upd' : 'dll/update.ver',                         # Path where ep12 itself requests update.ver from the update server
        'dll' : 'eset_upd/ep12/dll/update.ver',           # Path where update.ver will be located on our mirror
        'name' : 'ESET NOD32 Endpoint Ver. 12'            # Description
        }

    else:
        log("Undefined version " + str(ver) + " in init.py", 4)
        sys.exit(1)
