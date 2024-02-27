import requests
from contextlib import closing
import http.client as httplib
from urllib.parse import urlparse

from modules import FiasImport

import psycopg2

from enum import Enum
from datetime import datetime as dt

import argparse
import sys
import os
import shutil
import zipfile


FIAS_UPD_URL = 'https://fias.nalog.ru/WebServices/Public/GetAllDownloadFileInfo'
TMP_SUBDIR = "fias_upd"

LAST_CHANGES_DATE_QUERY = 'SELECT TO_CHAR(cgh.changedate, \'DD.MM.YYYY\') FROM change_history cgh ORDER BY cgh.changedate DESC LIMIT 1'

def loadUpdatesFileListByDate(lastDate, timeout = 2):
    updateList = []
    res = requests.get(FIAS_UPD_URL, timeout = timeout)
    if (res.ok): 
        jsonResp = res.json()
        for desc in jsonResp:
            lastDt = dt.strptime(lastDate, "%d.%m.%Y")
            fileDt = dt.strptime(desc['Date'], "%d.%m.%Y")
            if (fileDt > lastDt):
                updateList.append(desc['GarXMLDeltaURL'])
            else:
                updateList = sorted(updateList)
                del updateList[0]
                break
    else:
        print("INFO: Request status: [{0}]".format(res.status_code))
        
    return sorted(updateList)

def loadLastChangesDate(conn):
    rv = None
    with conn.cursor() as cursor:
        cursor.execute(LAST_CHANGES_DATE_QUERY)
        rows = cursor.fetchall()
        
        if (cursor.rowcount != 1):
            print("ERRR: Can't load last changes!")
        else:
            rv = rows[0][0]
    return rv   

def clrDir(dirpath):
    for filename in os.listdir(dirpath):
        file_path = os.path.join(dirpath, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('ERRR: Failed to delete %s. Reason: %s' % (file_path, e))

def downloadFile(url, fpath):
    with open(fpath, "wb") as f:
        print("INFO: Downloading [", url, "] ...")
        response = requests.get(url, stream=True)
        total_length = response.headers.get('content-length')
    
        if total_length is None: # no content length header
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)) )    
                sys.stdout.flush()
            print("")

def unzipFile(fpath, dirpath, region):
    print("INFO: Unpacking file [", fpath, "] Please wait 1-2 minutes ...")
    zf = zipfile.ZipFile(fpath)
    
    uncompress_size = sum((file.file_size for file in zf.infolist()))
    
    extracted_size = 0
    
    for file in zf.infolist():
        if (file.filename.startswith(region + '/')):
            extracted_size += file.file_size
            print("INFO: Extracting file [{0}] with size: {1} bytes ...".format(file.filename, file.file_size))
            zf.extract(file, dirpath)
    
def applyUpdate(pgCfg, fileUrl, region):

    # Prepare temporary directory
    tmpdir = "{0}/{1}".format(os.environ["TEMP"], TMP_SUBDIR)
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
    else:
        clrDir(tmpdir)

    # Parse filename
    a = urlparse(fileUrl)
    fileName = os.path.basename(a.path)
    filePath = "{0}/{1}".format(tmpdir, fileName)
    
    # Download file to tmp directory and unpack
    downloadFile(fileUrl, filePath)
    
    unzipFile(filePath, tmpdir, region)
    print("INFO: File [", filePath, "] unpacked")
    
    # Import DB updates
    loader = FiasImport.FiasXmlLoader()
    imported = loader.importRegion(pgCfg, tmpdir, region, True)
    print("");
    print("INFO: Imported [{0}] rows from: [{1}]".format(imported, fileUrl))
    print("");

    # Clear temporary directory
    clrDir(tmpdir)
    

def main() -> int:
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", nargs='?', type=str, default="localhost", required=True, help='Database hostname. (default: localhost)')
    parser.add_argument("--user", nargs='?', type=str, default="postgre", required=True, help='Database user. (default: postgres)')
    parser.add_argument("--pwd", nargs='?', type=str, default="postgre", required=True, help='Database password. (default: postgres)')
    parser.add_argument("--dbname", nargs='?', type=str, default="fias", required=True, help='Database name. (default: fias)')
    parser.add_argument("--region", nargs='?', type=str, default="100", required=True, help='Region number for import (default: 100)')
    args = parser.parse_args()
    
    pgCfg = "host={0} user={1} password={2} dbname={3}".format(args.host, args.user, args.pwd, args.dbname)

    try:
        conn = psycopg2.connect(pgCfg)
    except psycopg2.Error as e:
        print(e)
        return -1
    
    lastDate = loadLastChangesDate(conn)
    print("INFO: Date of last changes is {0}".format(lastDate))
    fileUrlList = loadUpdatesFileListByDate(lastDate)
    if (len(fileUrlList) == 0):
        print("INFO: There are no new updates!")
    else:
        for fileUrl in fileUrlList:
            applyUpdate(pgCfg, fileUrl, args.region)

if __name__ == '__main__':
    sys.exit(main())  
