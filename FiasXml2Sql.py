
from modules import FiasImport

import argparse

from time import time
import sys
import os

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", nargs='?', type=str, default="localhost", required=True, help='Database hostname. (default: localhost)')
    parser.add_argument("--user", nargs='?', type=str, default="postgre", required=True, help='Database user. (default: postgres)')
    parser.add_argument("--pwd", nargs='?', type=str, default="postgre", required=True, help='Database password. (default: postgres)')
    parser.add_argument("--dbname", nargs='?', type=str, default="fias", required=True, help='Database name. (default: fias)')
    parser.add_argument("--xml", nargs='?', type=str, default="xml/gar", required=True, help='Path to XML directory with database dump (default: xml/gar)')
    parser.add_argument("--region", nargs='?', type=str, default="100", required=True, help='Region number for import (default: 100)')
    args = parser.parse_args()
    
    pgCfg = "host={0} user={1} password={2} dbname={3}".format(args.host, args.user, args.pwd, args.dbname)
    
    regionXmlPath = "{0}/{1}".format(args.xml, args.region)
    if not os.path.exists(regionXmlPath):
        print("ERRR: Can't found region directory [{0}]".format(regionXmlPath))
        return -1
    
    loader = FiasImport.FiasXmlLoader()
    
    start_ts = time()
    cmnRows = loader.importCommon(pgCfg, args.xml)
    if (cmnRows < 0):
        return -1
    regRows = loader.importRegion(pgCfg, args.xml, args.region)
    if (regRows < 0):
        return -1
    print("INFO: Imported: Total: [{0}] records ({1} seconds)".format(cmnRows + regRows, int(time() - start_ts)))
    
    return 0

if __name__ == '__main__':
    sys.exit(main())  
