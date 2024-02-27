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
    TYPENAME_7 = 4
    NAME_7     = 5
    TYPENAME_8 = 6
    NAME_8     = 7
    HOUSE      = 8
    VALID      = 9
    LATITUDE   = 10
    LONGITUDE  = 11
    
class PostgrCfg:
    def __init__(self):
        self.host = 'localhost'
        self.dbname = 'fias'
        self.user = 'postgre'
        self.password = 'postgre'
    
    def GetConnection(self, fname) -> str:
        rv = None
        if (not os.path.exists(self.fname)):
            print("ERRR: Can't found config: [{0}]".format(self.fname))
            return rv

        tree = ltree.parse(self.fname)
        root = tree.getroot()

        conn = root.tag.find('connection')
        if (conn == None):
            print("ERRR: Can't found <connection>")
            return rv

        dbname = conn.get('dbname')
        if (dbname == None):
            print("ERRR: Can't found attribute [dbname]")
            return rv

        user = conn.get('user')
        if (user == None):
            print("ERRR: Can't found attribute [user]")
            return rv

        host = conn.get('host')
        if (host == None):
            print("ERRR: Can't found attribute [host]")
            return rv

        host = conn.get('password')
        if (host == None):
            print("ERRR: Can't found attribute [password]")
            return rv
   
queryGetObjByName = '''
SELECT ao.objectid, ao.level, ao.typename, ao.name
FROM addr_obj ao 
WHERE ao.name='{0}' AND ao.isactive=1 AND ao.level >= 4 AND ao.level <= 6
'''

queryGetAddrs = '''
SELECT DISTINCT mh.path, mh.objectid, mh.parentobjid, ao.level, ao7.typename, ao7.name, ao8.typename, ao8.name, h.housenum, h.geocoded, h.latitude, h.longitude
FROM mun_hierarchy mh
     LEFT JOIN addr_obj ao
	 	ON mh.objectid = ao.objectid AND ao.isactive=1
     LEFT JOIN addr_obj ao7
	 	ON mh.objectid = ao7.objectid AND ao7.isactive=1 AND ao7.level=7
     LEFT JOIN addr_obj ao8
	 	ON mh.objectid = ao8.objectid AND ao8.isactive=1 AND ao8.level=8
	 LEFT JOIN houses AS h
		ON mh.objectid = h.objectid AND h.isactive=1
WHERE mh.isactive=1 AND mh.path ~ '*.{0}.*' AND 
		(ao.level > 5 AND ao.level <= 8 OR 
		 ao.level IS NULL AND mh.objectid IN (SELECT objectid FROM houses) AND h.addnum1 IS NULL)
ORDER BY mh.path;
'''

queryGetStreets = '''
SELECT DISTINCT mh.path, mh.objectid, mh.parentobjid, ao.level, ao7.typename, ao7.name, ao8.typename, ao8.name
FROM mun_hierarchy mh
     LEFT JOIN addr_obj ao
	 	ON mh.objectid = ao.objectid AND ao.isactive=1
     LEFT JOIN addr_obj ao7
	 	ON mh.objectid = ao7.objectid AND ao7.isactive=1 AND ao7.level=7
     LEFT JOIN addr_obj ao8
	 	ON mh.objectid = ao8.objectid AND ao8.isactive=1 AND ao8.level=8
WHERE mh.isactive=1 AND mh.path ~ '*.{0}.*' AND ao.level > 5 AND ao.level <= 8 
ORDER BY mh.path;
'''

xmlHeader = '''<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:c="urn:schemas-microsoft-com:office:component:spreadsheet" xmlns:html="http://www.w3.org/TR/REC-html40" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet" xmlns:x2="http://schemas.microsoft.com/office/excel/2003/xml" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <OfficeDocumentSettings xmlns="urn:schemas-microsoft-com:office:office">
    <Colors>
      <Color>
        <Index>3</Index>
        <RGB>#000000</RGB>
      </Color>
      <Color>
        <Index>4</Index>
        <RGB>#0000ee</RGB>
      </Color>
      <Color>
        <Index>5</Index>
        <RGB>#006600</RGB>
      </Color>
      <Color>
        <Index>6</Index>
        <RGB>#333333</RGB>
      </Color>
      <Color>
        <Index>7</Index>
        <RGB>#808080</RGB>
      </Color>
      <Color>
        <Index>8</Index>
        <RGB>#996600</RGB>
      </Color>
      <Color>
        <Index>9</Index>
        <RGB>#c0c0c0</RGB>
      </Color>
      <Color>
        <Index>10</Index>
        <RGB>#cc0000</RGB>
      </Color>
      <Color>
        <Index>11</Index>
        <RGB>#ccffcc</RGB>
      </Color>
      <Color>
        <Index>12</Index>
        <RGB>#dddddd</RGB>
      </Color>
      <Color>
        <Index>13</Index>
        <RGB>#ffcccc</RGB>
      </Color>
      <Color>
        <Index>14</Index>
        <RGB>#ffffcc</RGB>
      </Color>
      <Color>
        <Index>15</Index>
        <RGB>#ffffff</RGB>
      </Color>
    </Colors>
  </OfficeDocumentSettings>
  <ExcelWorkbook xmlns="urn:schemas-microsoft-com:office:excel">
    <WindowHeight>9000</WindowHeight>
    <WindowWidth>13860</WindowWidth>
    <WindowTopX>240</WindowTopX>
    <WindowTopY>75</WindowTopY>
    <ProtectStructure>False</ProtectStructure>
    <ProtectWindows>False</ProtectWindows>
  </ExcelWorkbook>
  <Styles>
    <Style ss:ID="Default" ss:Name="Default" />
    <Style ss:ID="Heading" ss:Name="Heading">
      <Font ss:Bold="1" ss:Color="#000000" ss:Size="24" />
    </Style>
    <Style ss:ID="Text" ss:Name="Text" />
    <Style ss:ID="Note" ss:Name="Note">
      <Borders>
        <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#808080" />
        <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#808080" />
        <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#808080" />
        <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#808080" />
      </Borders>
      <Font ss:Color="#333333" ss:Size="10" />
      <Interior ss:Color="#ffffcc" ss:Pattern="Solid" />
    </Style>
    <Style ss:ID="Footnote" ss:Name="Footnote">
      <Font ss:Color="#808080" ss:Italic="1" ss:Size="10" />
    </Style>
    <Style ss:ID="Hyperlink" ss:Name="Hyperlink">
      <Font ss:Color="#0000ee" ss:Size="10" ss:Underline="Single" />
    </Style>
    <Style ss:ID="Status" ss:Name="Status" />
    <Style ss:ID="Good" ss:Name="Good">
      <Font ss:Color="#006600" ss:Size="10" />
      <Interior ss:Color="#ccffcc" ss:Pattern="Solid" />
    </Style>
    <Style ss:ID="Neutral" ss:Name="Neutral">
      <Font ss:Color="#996600" ss:Size="10" />
      <Interior ss:Color="#ffffcc" ss:Pattern="Solid" />
    </Style>
    <Style ss:ID="Bad" ss:Name="Bad">
      <Font ss:Color="#cc0000" ss:Size="10" />
      <Interior ss:Color="#ffcccc" ss:Pattern="Solid" />
    </Style>
    <Style ss:ID="Warning" ss:Name="Warning">
      <Font ss:Color="#cc0000" ss:Size="10" />
    </Style>
    <Style ss:ID="Error" ss:Name="Error">
      <Font ss:Bold="1" ss:Color="#ffffff" ss:Size="10" />
      <Interior ss:Color="#cc0000" ss:Pattern="Solid" />
    </Style>
    <Style ss:ID="th1" ss:Name="th1">
      <Font ss:Bold="1" ss:Color="#ffffff" ss:Size="10" />
      <Interior ss:Color="#000000" ss:Pattern="Solid" />
    </Style>
    <Style ss:ID="Accent" ss:Name="Accent">
      <Font ss:Bold="1" ss:Color="#000000" ss:Size="10" />
    </Style>
    <Style ss:ID="Result" ss:Name="Result">
      <Font ss:Bold="1" ss:Color="#000000" ss:Italic="1" ss:Size="10" ss:Underline="Single" />
    </Style>
    <Style ss:ID="co1" />
    <Style ss:ID="co2" />
    <Style ss:ID="co3" />
    <Style ss:ID="ta1" />
  </Styles>
  <ss:Worksheet ss:Name="example">
'''
xmlTblHeader = '''
    <Table ss:StyleID="ta1">
      <Column ss:Width="83.3386" />
      <Column ss:Width="181.389" />
      <Column ss:Span="2" ss:Width="64.0063" />
      <Row>
        <Cell ss:StyleID="th1">
          <Data ss:Type="String">Город</Data>
        </Cell>
        <Cell ss:StyleID="th1">
          <Data ss:Type="String">Адрес</Data>
        </Cell>
        <Cell ss:StyleID="th1">
          <Data ss:Type="String">Номер дома</Data>
        </Cell>
        <Cell ss:StyleID="th1">
          <Data ss:Type="String">Широта</Data>
        </Cell>
        <Cell ss:StyleID="th1">
          <Data ss:Type="String">Долгота</Data>
        </Cell>
      </Row>
'''
xmlRow = '''
      <Row>
        <Cell>
          <Data ss:Type="String">{0}</Data>
        </Cell>
        <Cell>
          <Data ss:Type="String">{1}</Data>
        </Cell>
        <Cell>
          <Data ss:Type="Number">{2}</Data>
        </Cell>
        <Cell>
          <Data ss:Type="String">{3}</Data>
        </Cell>
        <Cell>
          <Data ss:Type="String">{4}</Data>
        </Cell>
      </Row>
'''

xmlTblStreetHeader = '''
    <Table ss:StyleID="ta1">
      <Column ss:Width="83.3386" />
      <Column ss:Width="181.389" />
      <Column ss:Span="2" ss:Width="64.0063" />
      <Row>
        <Cell ss:StyleID="th1">
          <Data ss:Type="String">Город</Data>
        </Cell>
        <Cell ss:StyleID="th1">
          <Data ss:Type="String">Адрес</Data>
        </Cell>
      </Row>
'''
xmlStreetRow = '''
      <Row>
        <Cell>
          <Data ss:Type="String">{0}</Data>
        </Cell>
        <Cell>
          <Data ss:Type="String">{1}</Data>
        </Cell>
      </Row>
'''
xmlTail = '''
    </Table>
    <x:WorksheetOptions />
  </ss:Worksheet>
</Workbook>'''

def loadObjId(conn, objName):
    rv = None
    with conn.cursor() as cursor:
        q = queryGetObjByName.format(objName)
        cursor.execute(q)
        rows = cursor.fetchall()
        
        if (cursor.rowcount > 1):
            print("ERRR: Object counter > 1. Please correct city address! ")
        elif (cursor.rowcount == 0):
            print("ERRR: Can't found object with name [", objName, "]")
        else:
            rv = rows[0][0]
    return rv

def exportAddrs(conn, objName, outFile) -> int:
    rv = 0
    objId = loadObjId(conn, objName)
    with conn.cursor() as cursor:
        q = queryGetAddrs.format(objId)
        cursor.execute(q)
        rows = cursor.fetchall()
        if (cursor.rowcount == 0):
            print("ERRR: Can't found any address in object [", objName, "]")
        else:
            with open(outFile, 'w+', encoding='utf-8') as fd:
                fd.write(xmlHeader)
                fd.write(xmlTblHeader)
                name7 = None
                name8 = None
                currParentId = objId
                prevIsHouse = True
                for row in rows:
                    if (row[EAddrColumn.HOUSE.value] == None):
                        if (prevIsHouse):
                            name7 = None
                            name8 = None
                            prevIsHouse = False
                        if (row[EAddrColumn.NAME_7.value] != None):
                            name7 = "{0} {1}".format(row[EAddrColumn.TYPENAME_7.value], row[EAddrColumn.NAME_7.value]).strip()
                            currParentId = row[EAddrColumn.OID.value]
                        elif (row[EAddrColumn.NAME_8.value] != None):
                            name8 = "{0} {1}".format(row[EAddrColumn.TYPENAME_8.value], row[EAddrColumn.NAME_8.value]).strip()
                            if (currParentId != row[EAddrColumn.PID.value]):
                                name7 = None
                    else:
                        addr = ""
                        if (name7 == None or name7 == ""):
                            addr = name8
                        elif (name8 == None or name8 == ""):
                            addr = name7
                        else:
                            addr = '{0}, {1}'.format(name7, name8)
                        prevIsHouse = True
                        
                        house = row[EAddrColumn.HOUSE.value]
                        xmlRowData = ""
                        if (row[EAddrColumn.VALID.value]):
                            xmlRowData = xmlRow.format(objName, addr, house, row[EAddrColumn.LATITUDE.value], row[EAddrColumn.LONGITUDE.value])
                        else:
                            xmlRowData = xmlRow.format(objName, addr, house, "", "")
                        fd.write(xmlRowData)
                        rv += 1
                fd.write(xmlTail)
    return rv

def exportStreets(conn, objName, outFile) -> int:
    rv = 0
    objId = loadObjId(conn, objName)
    with conn.cursor() as cursor:
        q = queryGetStreets.format(objId)
        cursor.execute(q)
        rows = cursor.fetchall()
        if (cursor.rowcount == 0):
            print("ERRR: Can't found any address in object [", objName, "]")
        else:
            with open(outFile, 'w+', encoding='utf-8') as fd:
                fd.write(xmlHeader)
                fd.write(xmlTblStreetHeader)
                name7 = None
                name8 = None
                currParentId = objId
                for row in rows:
                    if (row[EAddrColumn.NAME_7.value] != None):
                        name7 = "{0} {1}".format(row[EAddrColumn.TYPENAME_7.value], row[EAddrColumn.NAME_7.value]).strip()
                        currParentId = row[EAddrColumn.OID.value]
                    elif (row[EAddrColumn.NAME_8.value] != None):
                        name8 = "{0} {1}".format(row[EAddrColumn.TYPENAME_8.value], row[EAddrColumn.NAME_8.value]).strip()
                        if (currParentId != row[EAddrColumn.PID.value]):
                            name7 = None
                        addr = ""
                        if (name7 == None or name7 == ""):
                            addr = name8
                        elif (name8 == None or name8 == ""):
                            addr = name7
                        else:
                            addr = '{0}, {1}'.format(name7, name8)

                        xmlStreetRowData = xmlStreetRow.format(objName, addr)
                        fd.write(xmlStreetRowData)
                        rv += 1
                fd.write(xmlTail)
    return rv
    
def main() -> int:
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", nargs='?', type=str, default="localhost", required=True, help='Database hostname. (default: localhost)')
    parser.add_argument("--user", nargs='?', type=str, default="postgre", required=True, help='Database user. (default: postgres)')
    parser.add_argument("--pwd", nargs='?', type=str, default="postgre", required=True, help='Database password. (default: postgres)')
    parser.add_argument("--dbname", nargs='?', type=str, default="fias", required=True, help='Database name. (default: fias)')
    parser.add_argument("--locality", nargs='?', type=str, default="DefaultCity", required=True, help='Locality name. (default: DefaultCity)')
    parser.add_argument("--out", nargs='?', type=str, default="export.xml", required=True, help='Output *.XML file name. (default: export.xml)')
    parser.add_argument('--streets', action='store_true', default=False, help='Export only street names. (default: False)')
    args = parser.parse_args()
    
    pgCfg = "host={0} user={1} password={2} dbname={3}".format(args.host, args.user, args.pwd, args.dbname)
    try:
        conn = psycopg2.connect(pgCfg)
    except psycopg2.Error as e:
        print(e)
        return -1
    exported = 0
    if (args.streets):
        exported = exportStreets(conn, args.locality, args.out)
    else:
        exported = exportAddrs(conn, args.locality, args.out)
    print("INFO: Exported: [{0}] rows.".format(exported))
    return 0

if __name__ == '__main__':
    sys.exit(main())  
