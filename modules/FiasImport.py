import re
import sys
import os
import xmlschema
import xml.etree.ElementTree as etree
from lxml import etree as ltree
import psycopg2
from pathlib import Path
from time import time

class FiasXmlLoader:

    def __init__(self):
        self.PG_TABLE_WHITE_LIST = {
              "addhouse_types"
            , "addr_obj_types"
            , "apartment_types"
            , "house_types"
            , "normative_docs_kinds"
            , "normative_docs_types"
            , "object_levels"
            , "operation_types"
            , "param_types"
            , "room_types"
            , "addr_obj"
            , "addr_obj_division"
            , "adm_hierarchy"
            , "apartments"
            , "carplaces"
            , "change_history"
            , "houses"
            , "mun_hierarchy"
            , "normative_docs"
            , "rooms"
            , "steads"
            , "reestr_objects"
            , "param"
            }


        self.PG_RESERVED = { 
             "ALL" 
            ,"ANALYSE"
            ,"ANALYZE"
            ,"AND"
            ,"ANY"
            ,"ASC"
            ,"ASYMMETRIC"
            ,"BOTH"
            ,"CASE"
            ,"CAST"
            ,"CHECK"
            ,"COLLATE"
            ,"COLUMN"
            ,"CONSTRAINT"
            ,"CURRENT_CATALOG"
            ,"CURRENT_DATE"
            ,"CURRENT_ROLE"
            ,"CURRENT_TIME"
            ,"CURRENT_TIMESTAMP"
            ,"CURRENT_USER"
            ,"DEFAULT"
            ,"DEFERRABLE"
            ,"DESC"
            ,"DISTINCT"
            ,"DO"
            ,"ELSE"
            ,"END"
            ,"FALSE"
            ,"FOREIGN"
            ,"IN"
            ,"INITIALLY"
            ,"LATERAL"
            ,"LEADING"
            ,"LOCALTIME"
            ,"LOCALTIMESTAMP"
            ,"NOT"
            ,"NULL"
            ,"ONLY"
            ,"OR"
            ,"PLACING"
            ,"PRIMARY"
            ,"REFERENCES"
            ,"SELECT"
            ,"SESSION_USER"
            ,"SOME"
            ,"SYMMETRIC"
            ,"SYSTEM_USER"
            ,"TABLE"
            ,"THEN"
            ,"TRAILING"
            ,"TRUE"
            ,"UNIQUE"
            ,"USER"
            ,"USING"
            ,"VARIADIC"
            ,"WHEN"
            ,"AUTHORIZATION"
            ,"BINARY"
            ,"COLLATION"
            ,"CONCURRENTLY"
            ,"CROSS"
            ,"CURRENT_SCHEMA"
            ,"FREEZE"
            ,"FULL"
            ,"ILIKE"
            ,"INNER"
            ,"IS"
            ,"JOIN"
            ,"LEFT"
            ,"LIKE"
            ,"NATURAL"
            ,"OUTER"
            ,"RIGHT"
            ,"SIMILAR"
            ,"TABLESAMPLE"
            ,"VERBOSE"
            ,"ISNULL"
            ,"NOTNULL"
            ,"OVERLAPS"
            ,"ARRAY"
            ,"AS"
            ,"CREATE"
            ,"EXCEPT"
            ,"FETCH"
            ,"FROM"
            ,"GRANT"
            ,"GROUP"
            ,"HAVING"
            ,"INTERSECT"
            ,"INTO"
            ,"LIMIT"
            ,"OFFSET"
            ,"ON"
            ,"ORDER"
            ,"RETURNING"
            ,"TO"
            ,"UNION"
            ,"WHERE"
            ,"WINDOW"
            ,"WITH" }

        self.PRINT_STATUS_PERIOD = 3.0

    def __importTable__(self, conn, rootNode, tableName):
        if (rootNode == None):
            return -1
        
        imported = 0
        cursor = conn.cursor()
        last_ts = time()
        children = rootNode.getchildren()
        for child in children:
            q_keys = "INSERT INTO {0} ".format(tableName)
            q_vals = "VALUES "
            for i, key in enumerate(child.attrib):
                column = key.lower()
                val = child.get(key).replace("'", "''")
                div = "(" if (i == 0) else ", "
                column_esc = "\"" if key in self.PG_RESERVED else ""
                q_keys = q_keys + div + column_esc + column + column_esc
                q_vals = q_vals + div + "'" + val + "'"
                
            query = q_keys + ") " + q_vals + ");"
                
            try:    
                cursor.execute(query)
                conn.commit()
            except psycopg2.Error as e:
                print(e)
                print(query)
                return -1
            
            imported += 1
            
            curr_ts = time()
            if (curr_ts - last_ts > self.PRINT_STATUS_PERIOD):
                last_ts = curr_ts
                print("INFO: ... [{0}] of [{1}]".format(imported, len(children)))
                
                
        print("INFO: {0} lines imported into [{1}]".format(imported, tableName))
        return imported

    def __getTableIndex__(self, conn, tableName):
        queryGetTableIndex = 'SELECT indexname FROM pg_indexes WHERE tablename = \'{0}\' LIMIT 1;'
        q = queryGetTableIndex.format(tableName)
        cursor = conn.cursor()
        try:    
            cursor.execute(q)
            conn.commit()
            rows = cursor.fetchall()
        
            if (cursor.rowcount == 0):
                print("ERRR: Can't found index of table [{0}]".format(tableName))
            else:
                rv = rows[0][0].split(".")[-1]
                return rv

        except psycopg2.Error as e:
            print(e)
            return None
        
        

    def __updateTable__(self, conn, rootNode, tableName):
        if (rootNode == None):
            return -1
        
        tableIndex = self.__getTableIndex__(conn, tableName)
        if (tableIndex == None):
            return -1
        
        imported = 0
        cursor = conn.cursor()
        last_ts = time()
        children = rootNode.getchildren()
        for child in children:
            q_keys = 'INSERT INTO {0} '.format(tableName)
            q_vals = 'VALUES '
            q_set  = 'ON CONFLICT({0}) DO UPDATE SET '.format(tableIndex)
            for i, key in enumerate(child.attrib):
                column = key.lower()
                val = child.get(key).replace("'", "''")
                div = "(" if (i == 0) else ", "
                div2 = " " if (i == 0) else ", "
                column_esc = "\"" if key in self.PG_RESERVED else ""
                q_keys = q_keys + div + column_esc + column + column_esc
                q_vals = q_vals + div + "'" + val + "'"
                q_set  = q_set  + div2 + column_esc + column + column_esc + "='" + val + "'"
                
            query = q_keys + ") " + q_vals + ") " + q_set + ";"
                
            try:    
                cursor.execute(query)
                conn.commit()
            except psycopg2.Error as e:
                print(e)
                print(query)
                return -1
            
            imported += 1
            
            curr_ts = time()
            if (curr_ts - last_ts > self.PRINT_STATUS_PERIOD):
                last_ts = curr_ts
                print("INFO: ... [{0}] of [{1}]".format(imported, len(children)))
                
                
        print("INFO: {0} lines imported into [{1}]".format(imported, tableName))
        return imported

    def __importDir__(self, conn, directory, update):
        total = 0
        tables = 0
        for xml in os.listdir(directory):
            
            fpath = directory + "/" + xml
            if (os.path.isdir(fpath)):
                continue
            
            if (not fpath.lower().endswith('.xml')):
                continue
            
            if "_PARAMS_2" in fpath:
                continue
            
            tableName = xml[3:xml.find('_2')].lower()
            if (tableName not in self.PG_TABLE_WHITE_LIST):
                print("info: ignore table: [{0}]".format(tableName))
                continue
            
            tree = ltree.parse(directory + '/' + xml)
            root = tree.getroot()
    
            print("INFO: importing: {1} => {2}".format(tables, xml, tableName))
            
            if (root == None):
                print("ERRR: <root> tag is empty")
                return -1
            if update:
                imported = self.__updateTable__(conn, root, tableName)
            else:
                imported = self.__importTable__(conn, root, tableName)
            if (imported < 0 ):
                print("ERRR: table with name: [{0}] import FAILED!".format(tableName))
                return -1
            else:
                total += imported
                tables += 1
        return total
    
    def __initPgSql__(self, initStr):
        try:
            conn = psycopg2.connect(initStr)
            return conn
        except psycopg2.Error as e:
            print(e)
            return None

    def importCommon(self, pgInitStr, xmlDir):
        with self.__initPgSql__(pgInitStr) as conn:
            if (conn != None):
                return self.__importDir__(conn, xmlDir, False)
        return -1
        
    def importRegion(self, pgInitStr, xmlDir, region, update = False):
        with self.__initPgSql__(pgInitStr) as conn:
            if (conn != None):
                regionXmlPath = "{0}/{1}".format(xmlDir, region)
                if not os.path.exists(regionXmlPath):
                    print("ERRR: Can't found region path[{0}]".format(regionXmlPath))
                else:
                    return self.__importDir__(conn, regionXmlPath, update)
        return -1
