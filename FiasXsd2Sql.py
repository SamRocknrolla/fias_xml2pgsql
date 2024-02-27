import xmlschema
import xml.etree.ElementTree as etree
from lxml import etree as ltree

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT 

import argparse
import sys
import os

create_db_query = '''CREATE DATABASE {} WITH OWNER=postgres ENCODING='UTF8' LC_COLLATE='Russian_Russia.1251' LC_CTYPE='Russian_Russia.1251' LOCALE_PROVIDER='libc' TABLESPACE=pg_default CONNECTION LIMIT = -1 IS_TEMPLATE = False;'''
ext_queries = [ 'CREATE EXTENSION ltree;' ]

add_queries = [ 'ALTER TABLE addr_obj ALTER COLUMN level TYPE integer USING level::integer;'
              , 'ALTER TABLE IF EXISTS houses ADD COLUMN IF NOT EXISTS geocoded boolean;'
              , 'ALTER TABLE IF EXISTS houses ADD COLUMN IF NOT EXISTS latitude real;'
              , 'ALTER TABLE IF EXISTS houses ADD COLUMN IF NOT EXISTS longitude real;'
              ]
idx_queries = [ 'CREATE UNIQUE INDEX "mun_hierarchy.path" ON "mun_hierarchy" USING btree ("path" "ltree_ops");'
              , 'CREATE UNIQUE INDEX "adm_hierarchy.path" ON "adm_hierarchy" USING btree ("path" "ltree_ops");'
              , 'CREATE UNIQUE INDEX "addhouse_types.id" ON "addhouse_types"("id");'
              , 'CREATE UNIQUE INDEX "addr_obj.id" ON "addr_obj"("id");'
              , 'CREATE UNIQUE INDEX "addr_obj_division.id" ON "addr_obj_division"("id");'
              , 'CREATE UNIQUE INDEX "addr_obj_types.id" ON "addr_obj_types"("id");'
              , 'CREATE UNIQUE INDEX "adm_hierarchy.id" ON "adm_hierarchy"("id");'
              , 'CREATE UNIQUE INDEX "apartments.id" ON "apartments"("id");'
              , 'CREATE UNIQUE INDEX "apartment_types.id" ON "apartment_types"("id");'
              , 'CREATE UNIQUE INDEX "carplaces.id" ON "carplaces"("id");'
              , 'CREATE UNIQUE INDEX "change_history.changeid" ON "change_history"("changeid");'
              , 'CREATE UNIQUE INDEX "houses.id" ON "houses"("id");'
              , 'CREATE UNIQUE INDEX "house_types.id" ON "house_types"("id");'
              , 'CREATE UNIQUE INDEX "mun_hierarchy.id" ON "mun_hierarchy"("id");'
              , 'CREATE UNIQUE INDEX "normative_docs.id" ON "normative_docs"("id");'
              , 'CREATE UNIQUE INDEX "normative_docs_kinds.id" ON "normative_docs_kinds"("id");'
              , 'CREATE UNIQUE INDEX "normative_docs_types.id" ON "normative_docs_types"("id");'
              , 'CREATE UNIQUE INDEX "object_levels.level" ON "object_levels"("level");'
              , 'CREATE UNIQUE INDEX "operation_types.id" ON "operation_types"("id");'
              , 'CREATE UNIQUE INDEX "param.id" ON "param"("id");'
              , 'CREATE UNIQUE INDEX "param_types.id" ON "param_types"("id");'
              , 'CREATE UNIQUE INDEX "reestr_objects.objectguid" ON "reestr_objects"("objectguid");'
              , 'CREATE UNIQUE INDEX "rooms.id" ON "rooms"("id");'
              , 'CREATE UNIQUE INDEX "room_types.id" ON "room_types"("id");'
              , 'CREATE UNIQUE INDEX "steads.id" ON "steads"("id");'
              ]

def findRootElementNode(root, i):
    elementNode = None;
    for child in root.getchildren():
        if (child.tag.find('element') > 0):
            elementNode = child;
    return elementNode;

def findElementNode(root, i):
    elementNode = None;
    for child in root.getchildren():
        if (child.tag.find('element') > 0):
            i = i + 1
        if (i == 2):
            elementNode = child;
            return elementNode;
        else:
            elementNode = findElementNode(child, i);
    return elementNode;

def findNode(root, nodeName):
    elementNode = None;
    if (root != None):

        for child in root.getchildren():
            if (child.tag.find(nodeName) > 0):
                elementNode = child;
                return elementNode;
            else:
                elementNode = findNode(child, nodeName);
    return elementNode;

def getIntegerType(restriction):
    if (restriction != None):
        totalDigitsNode = findNode(restriction, 'totalDigits')
        enumerationNode = findNode(restriction, 'enumeration')
        if (totalDigitsNode != None):
            intSize = int(totalDigitsNode.get('value'))
            if (intSize > 9):
                return 'bigint'
            else:
                return 'integer'
        elif (enumerationNode != None):
            return 'smallint'
        else:
            return 'bigint'
    else:
        return 'bigint'

def getStringType(restriction):
    if (restriction != None) :
        lengthNode = findNode(restriction, 'length')
        maxLengthNode = findNode(restriction, 'maxLength')
        if (lengthNode != None):
            length = lengthNode.get('value')
            return 'varchar('+ length + ')'
        elif (maxLengthNode != None):
            length = maxLengthNode.get('value')
            return 'varchar('+ length + ')'
        else:
            return 'text'
    else:
        return 'text'

def getType(simpleTypeNode, typeName):
    restriction = None;
    if typeName == '':
        if (simpleTypeNode != None):
            restriction = findNode(simpleTypeNode, 'restriction')
            typeName = restriction.get('base')
        else:
            return None

    if (typeName == 'xs:integer' or typeName == 'xs:int'):
        type = getIntegerType(restriction)
    elif (typeName == 'xs:long'):
        type = 'bigint'
    elif (typeName == 'xs:byte'):
        type = 'smallint'
    elif (typeName == 'xs:string'):
        type = getStringType(restriction)
    elif (typeName == 'xs:date'):
        type = 'timestamp'
    elif (typeName == 'xs:boolean'):
        type = 'boolean'

    return type

def queryAddColumns(complexTypeNode, tableName):
    queries = []
    reservedWords = ['desc']
    for child in complexTypeNode:
        if (child.tag.find('attribute') > 0):
            columnName = child.get('name').lower() 
            if (reservedWords.count(columnName)):
                columnName = '\"' + columnName + '\"'
            use = child.get('use')
            typeName = child.get('type')
            if (typeName == None):
                simpleTypeNode = findNode(child, 'simpleType')
                # There are no type of column in xsd PARAMS
                if (simpleTypeNode == None):
                    if (columnName == 'objectid'):
                        type = 'bigint'
                    elif (columnName == 'path'):
                        type = 'ltree'
                else:
                    type = getType(simpleTypeNode, '')
            else:
                type = getType(None, typeName)
                
            if (type == None):
                print("ERRR: invalid Type in [" + tableName + "]")
            else:
                query = 'ALTER TABLE ' + tableName + ' ADD COLUMN IF NOT EXISTS ' + columnName + ' ' \
                        + type + ';'
                queries.append(query)
    return queries

def createDb(pgCfg, dbname) -> bool:
    try:
        conn = psycopg2.connect(pgCfg)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(sql.SQL(create_db_query).format(sql.Identifier(dbname)))
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        print(e)
        return False
    
    return True

def createTablesFromXSD(conn, directory) -> int:
    tables = 0
    if (not os.path.exists(directory) or not os.path.isdir(directory)):
        print("ERRR: Can't open directory [{0}]".format(directory))
        return -1
    
    # Add extentions
    with conn.cursor() as cursor:
        for query in ext_queries:
            cursor.execute(query)
    conn.commit()

    for xsd in os.listdir(directory):
        if (os.path.isdir(directory + "/" + xsd)):
            continue
        tree = ltree.parse(directory + '/' + xsd)
        root = tree.getroot()
        
        elementNode = findElementNode(root, 0)

        tableName = xsd[3:xsd.find('_2')].lower()
        
        print("INFO: Import file: [{0}] => [{1}]".format(xsd, tableName))
        tables += 1

        queryCreateTable = 'CREATE TABLE IF NOT EXISTS {0}();'.format(tableName)
        complexTypeNode = findNode(elementNode, 'complexType')
        queries = queryAddColumns(complexTypeNode, tableName)

        with conn.cursor() as cursor:
            cursor.execute(queryCreateTable)

	        # Create table in accordance with XSD schema
            for query in queries:
                cursor.execute(query)
        conn.commit()
    print("INFO: Imported {0} tables".format(tables))
    # Add additional columns for geocoding
    with conn.cursor() as cursor:
        for query in add_queries:
            cursor.execute(query)
        conn.commit()
        print("INFO: Apply {0} schema fixes".format(len(add_queries)))
        for query in idx_queries:
            cursor.execute(query)
        conn.commit()
        print("INFO: Create {0} indexes".format(len(idx_queries)))
    
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", nargs='?', type=str, default="localhost", required=True, help='Database hostname. (default: localhost)')
    parser.add_argument("--user", nargs='?', type=str, default="postgre", required=True, help='Database user. (default: postgres)')
    parser.add_argument("--pwd", nargs='?', type=str, default="postgre", required=True, help='Database password. (default: postgres)')
    parser.add_argument("--dbname", nargs='?', type=str, default="fias", required=True, help='Database name. (default: fias)')
    parser.add_argument("--xsd", nargs='?', type=str, default="xsd/gar_schemas", required=True, help='Path to XSD directory with database schema (default xsd/gar_schemas)')
    args = parser.parse_args()
    
    pgCfg = "host={0} user={1} password={2} dbname=postgres".format(args.host, args.user, args.pwd)
    if (createDb(pgCfg, args.dbname) == False):
        return -1

    pgCfg = "host={0} user={1} password={2} dbname={3}".format(args.host, args.user, args.pwd, args.dbname)
    try:
        with psycopg2.connect(pgCfg) as conn:
            return createTablesFromXSD(conn, args.xsd)
    except psycopg2.Error as e:
        print(e)
        return -1
    

if __name__ == '__main__':
    sys.exit(main())  
