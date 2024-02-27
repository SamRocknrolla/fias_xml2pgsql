import xmlschema
import xml.etree.ElementTree as etree
from lxml import etree as ltree
import psycopg2
from enum import Enum

import argparse
import sys
import os

class EAddrColumn(Enum):
    PATH       = 0
    OID        = 1
    PID        = 2
    LEVEL      = 3
    TYPENAME_6 = 4
    NAME_6     = 5
    TYPENAME_7 = 6
    NAME_7     = 7
    TYPENAME_8 = 8
    NAME_8     = 9
    HOUSE      = 10
    VALID      = 11
    LATITUDE   = 12
    LONGITUDE  = 13
    
queryGetLocations = '''
SELECT ao.objectid, ao.typename, ao.name
FROM addr_obj ao 
	LEFT JOIN object_levels ol 
		ON ao.level = ol.level
WHERE ao.isactive=1 AND ao.level >= 5 AND ao.level <= 6
ORDER BY ao.name
'''

queryGetObjNameById = '''
SELECT ao.typename, ao.name
FROM addr_obj ao 
WHERE ao.objectid={0} AND ao.isactive=1 AND ao.level >= 5 AND ao.level <= 6
'''
    
queryGetObjAncestors = '''
SELECT mh.objectid, mh.parentobjid, ao.level, ao.typename, ao.name
FROM mun_hierarchy mh JOIN addr_obj ao ON mh.objectid=ao.objectid AND ao.isactive=1
WHERE path @> '{0}'
ORDER BY ao.level, mh.parentobjid
'''

queryGetAddrs = '''
SELECT DISTINCT mh.path, mh.objectid, mh.parentobjid, ao.level, ao6.typename, ao6.name, ao7.typename, ao7.name, ao8.typename, ao8.name, h.housenum, h.geocoded, h.latitude, h.longitude
FROM mun_hierarchy mh
     LEFT JOIN addr_obj ao
	 	ON mh.objectid = ao.objectid AND ao.isactive=1
     LEFT JOIN addr_obj ao6
	 	ON mh.objectid = ao6.objectid AND ao6.isactive=1 AND ao6.level=6
     LEFT JOIN addr_obj ao7
	 	ON mh.objectid = ao7.objectid AND ao7.isactive=1 AND ao7.level=7
     LEFT JOIN addr_obj ao8
	 	ON mh.objectid = ao8.objectid AND ao8.isactive=1 AND ao8.level=8
	 LEFT JOIN houses AS h
		ON mh.objectid = h.objectid AND h.isactive=1
WHERE mh.isactive=1 AND mh.path ~ '*.{0}.*' AND 
		(ao.level > 5 AND ao.level <= 8 OR 
		 ao.level IS NULL AND mh.objectid IN (SELECT objectid FROM houses) AND h.addnum1 IS NULL 
         {1})
ORDER BY mh.path;
'''
whereGeo = '''AND h.geocoded=True AND h.latitude IS NOT NULL AND h.longitude IS NOT NULL'''

csvTblHeader = '''Населенный пункт;Адрес;Номер дома;Широта;Долгота\n'''
csvRow = '''{0};{1};{2};{3};{4}\n'''
csvTblLocHeader = '''uid;Населенный пункт\n'''
csvLocRow = '''{0};{1}{2}\n'''

def __loadObjName__(cursor, objId):
    rv = None
    q = queryGetObjNameById.format(objId)
    cursor.execute(q)
    if (cursor.rowcount == 0):
        print("ERRR: Can't found any object with UID: [{0}]".format(objId))
    elif (cursor.rowcount > 1):
        print("ERRR: There are a lot of objects with UID: [{0}]. Database data is invalid!".format(objId))
    else:
        rows = cursor.fetchall()
        #rv = "{0} {1}".format(rows[0][0], rows[0][1])
        rv = rows[0][1]
    return rv

def exportAddrs(conn, objId, outFile, geo, cp1251) -> int:
    rv = 0
    if (objId == None or objId == '0'):
        return rv
    with conn.cursor() as cursor:
        # Load Object name by Object UID
        objName = __loadObjName__(cursor, objId)
        if (objName == None):
            return rv
        q = queryGetAddrs.format(objId, (whereGeo if (geo == True) else ""))
        cursor.execute(q)
        rows = cursor.fetchall()
        if (cursor.rowcount == 0):
            print("ERRR: Can't found any address in object [{0}]".format(objId))
        else:
            with open(outFile, 'w+', encoding=('cp1251' if (cp1251 == True) else 'utf-8')) as fd:
                fd.write(csvTblHeader)
                name = [None, None, None]
                currParentId = objId
                prevIsHouse = True
                for row in rows:
                    if (row[EAddrColumn.HOUSE.value] == None):
                        if (prevIsHouse):
                            names = [None, None, None]
                            prevIsHouse = False
                        if (row[EAddrColumn.NAME_6.value] != None):
                            currParentId = row[EAddrColumn.OID.value]
                            if (currParentId != row[EAddrColumn.PID.value]):
                                names = [None, None, None]
                            names[0] = "{0} {1}".format(row[EAddrColumn.TYPENAME_6.value], row[EAddrColumn.NAME_6.value]).strip()
                        elif (row[EAddrColumn.NAME_7.value] != None):
                            currParentId = row[EAddrColumn.OID.value]
                            if (currParentId != row[EAddrColumn.PID.value]):
                                names = [None, None, None]
                            names[1] = "{0} {1}".format(row[EAddrColumn.TYPENAME_7.value], row[EAddrColumn.NAME_7.value]).strip()
                        elif (row[EAddrColumn.NAME_8.value] != None):
                            currParentId = row[EAddrColumn.OID.value]
                            if (currParentId != row[EAddrColumn.PID.value]):
                                names = [None, None, None]
                            names[2] = "{0} {1}".format(row[EAddrColumn.TYPENAME_8.value], row[EAddrColumn.NAME_8.value]).strip()
                    else:
                        addr = ""
                        firstName = True
                        for name in names:
                            if (name != None):
                                if (firstName == True):
                                    firstName = False
                                    addr = name    
                                else:
                                    addr = addr + "," + name
                        prevIsHouse = True
                        
                        house = row[EAddrColumn.HOUSE.value]
                        csvRowData = ""
                        if (row[EAddrColumn.VALID.value]):
                            csvRowData = csvRow.format(objName, addr, house, row[EAddrColumn.LATITUDE.value], row[EAddrColumn.LONGITUDE.value])
                        else:
                            csvRowData = csvRow.format(objName, addr, house, "", "")
                        fd.write(csvRowData)
                        rv += 1
    return rv

def exportLocations(conn, outFile, cp1251) -> int:
    rv = 0
    with conn.cursor() as cursor:
        cursor.execute(queryGetLocations)
        rows = cursor.fetchall()
        if (cursor.rowcount == 0):
            print("ERRR: Can't found any locations!")
        else:
            with open(outFile, 'w+', encoding=('cp1251' if (cp1251 == True) else 'utf-8')) as fd:
                fd.write(csvTblLocHeader)
                for row in rows:
                    csvLocRowData = csvLocRow.format(row[0], row[1], row[2])
                    fd.write(csvLocRowData)
                    rv += 1
    return rv
    
def main() -> int:
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", nargs='?', type=str, default="localhost", required=True, help='Database hostname. (default: localhost)')
    parser.add_argument("--user", nargs='?', type=str, default="postgre", required=True, help='Database user. (default: postgres)')
    parser.add_argument("--pwd", nargs='?', type=str, default="postgre", required=True, help='Database password. (default: postgres)')
    parser.add_argument("--dbname", nargs='?', type=str, default="fias", required=True, help='Database name. (default: fias)')
    parser.add_argument("--out", nargs='?', type=str, default="export.xml", required=True, help='Output *.XML file name. (default: export.xml)')
    parser.add_argument('--loc', action='store_true', default=False, help='Export all locations. (default: False)')
    parser.add_argument('--cp1251', action='store_true', default=False, help='Set codepage for export file as CP1251')
    parser.add_argument("--uid", nargs='?', type=str, default="0", help='objece UID. (default: 0)')
    parser.add_argument('--geo', action='store_true', default=False, help='Export only geocoded objects. (default: False)')
    args = parser.parse_args()
    
    pgCfg = "host={0} user={1} password={2} dbname={3}".format(args.host, args.user, args.pwd, args.dbname)
    try:
        conn = psycopg2.connect(pgCfg)
    except psycopg2.Error as e:
        print(e)
        return -1
    exported = 0
    if (args.loc and args.uid != '0'):
        print('ERRR: Unsupported combination of input arguments. Please use only one argument: [--loc] or [--uid=XXXXXXXX]')
        return -1    
    if (args.loc == False and args.uid == '0'):
        print('ERRR: Please set [--loc] or [--uid=XXXXXXXX]')
        return -1    
    
    if (args.loc):
        exported = exportLocations(conn, args.out, args.cp1251)
    else :
        exported = exportAddrs(conn, args.uid, args.out, args.geo, args.cp1251)
        
    print("INFO: Exported: [{0}] rows.".format(exported))
    return 0

if __name__ == '__main__':
    sys.exit(main())  
