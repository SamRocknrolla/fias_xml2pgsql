echo OFF

:: PostgreSQl host
set HOST="localhost"
:: PostgreSQl user name
set USR="postgres"
:: PostgreSQl user password
set PWD="1"
:: PostgreSQl database name that must be created
set DBNAME="fias"
:: Region name from FIAS 
set REGION="90"
:: Loction in region
set UID="155638689"
:: Yandex API key for developer XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXX
set APIKEY=""
:: Yandex API call limit 
set YA_LIMIT=500

:: Create DB from XSD schema
Call FiasXsd2Sql --host=%HOST% --user=%USR% --pwd=%PWD% --dbname=%DBNAME% --xsd=./xsd/gar_schemas 
IF %ERRORLEVEL% NEQ 0 goto done

:: Import full dump of region number 90
Call FiasXml2Sql --host=%HOST% --user=%USR% --pwd=%PWD% --dbname=%DBNAME% --xml=./xml/gar --region=%REGION%
IF %ERRORLEVEL% NEQ 0 goto done

:: Export all locatons
Call ExportFias2Csv --host=%HOST% --user=%USR% --pwd=%PWD% --dbname=%DBNAME% --loc --cp1251 --out=export/export-locations-%REGION%.csv
IF %ERRORLEVEL% NEQ 0 goto done

:: Update geocodes for the object with UID=155638689 ('Днепрорудное') in region 
Call UpdateFiasGeocodes --host=%HOST% --user=%USR% --pwd=%PWD% --dbname=%DBNAME% --uid=%UID% --apikey=%APIKEY% --limit=%YA_LIMIT%
IF %ERRORLEVEL% NEQ 0 goto done

:: Export all houses for the object with UID=155638689 ('Днепрорудное')
Call ExportFias2Csv --host=%HOST% --user=%USR% --pwd=%PWD% --dbname=%DBNAME% --uid=%UID% --cp1251 --out=export/export-addrs-%UID%.csv
IF %ERRORLEVEL% NEQ 0 goto done

:: Export all houses for the object with UID=155638689 ('Днепрорудное') and geocodes
Call ExportFias2Csv --host=%HOST% --user=%USR% --pwd=%PWD% --dbname=%DBNAME% --uid=%UID% --cp1251 --geo --out=export/export-addrs-%UID%-geo.csv
IF %ERRORLEVEL% NEQ 0 goto done

echo "INFO: Full test finished successfully!"
:done