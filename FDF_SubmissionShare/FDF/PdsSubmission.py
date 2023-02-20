import requests
import os
import sys
import pandas as pd
import pyodbc
import yaml
import logging
from datetime import datetime as dt
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL



class SQL():

    def __init__(
            self,
            SourceServer,
            SourcePort,
            SourceUser,
            SourcePassword,
            Sourcedatabase,
            SourceSchema,
            sourceOdbcDriver=None,
            useWindowsADSource=False
            ):

        self.SourceServer = SourceServer
        self.SourcePort = SourcePort
        self.SourceUser = SourceUser
        self.SourcePassword = SourcePassword

        self.Sourcedatabase = Sourcedatabase
        self.SourceSchema = SourceSchema

        self.sourceOdbcDriver = sourceOdbcDriver
        self.useWindowsADSource = useWindowsADSource


    def fetch_odbc_drivers(self):
        '''
        Lists all odbc drivers registered on the machine.

        Parameters
        ----------
        None

        Outputs
        ----------
        Prints the ODBC driver names in the console.
        '''
        print("List of ODBC Drivers:")
        dlist = pyodbc.drivers()
        for drvr in dlist:
            print(drvr)


    def createSQLengine(self, username:str, password:str, host:str, port:str,database:str, driver:str, useWindowsAD:bool):
        """
        Creates a SQL engine for database interaciton.

        :param username:        Login Username
        :param password:        Login Password
        :param host:            Database host address.
        :param port:            Datavase port to connect to.
        :param database:        SQL Database name to connect to.
        :param driver:          ODBC driver to be used e.g. ODBC Driver 17 for SQL Server.
        :param useWindowsAD:    True/False - Use active directory to log in.

        :return: SQL Alchemy engine object.
        """
        if useWindowsAD:
            tcon = 'yes'
        else:    
            tcon = 'no'

        connection_url = URL.create(
            "mssql+pyodbc",
            username= username,
            password= password,
            host= host,
            port= port,
            database= database,
            query={
                "driver": driver,
                "trusted_connection": tcon
                }
            )

        return create_engine(connection_url, echo=False, future=True)


    def select_source_data(self, query, returnDF = False):
        
        engine = self.createSQLengine(self.SourceUser,self.SourcePassword,self.SourceServer,self.SourcePort,self.Sourcedatabase, self.sourceOdbcDriver,self.useWindowsADSource)
        
        with engine.connect() as conn:
            if returnDF:
                try:
                    DbDataset = pd.read_sql_query(text(query),conn)
                    logging.info('Dataframe Loaded')
                    print('Dataframe Loaded')
                    return DbDataset
                except Exception as e:
                    # ... PRINT THE ERROR MESSAGE ... #
                    print(e)
                    logging.critical(e)
                    sys.exit()
            else:
                try:
                    DbDataset = conn.execute(text(query))
                    logging.info('Data Loaded')
                    print('Data Loaded')
                    return DbDataset
                except Exception as e:
                    # ... PRINT THE ERROR MESSAGE ... #
                    print(e)   
                    logging.critical(e)
                    sys.exit()


class CreateDataset():
    """
    This class is used to create the csv for submission.

    PosArg1: config
        An instance of the load_config() call.
    
    PosArg2: destinationFolder
        Folder to place the csv's into.

    """
    def __init__(self,config, destinationFolder):
        self.config = config
        self.destinationFolder = destinationFolder

    def getData(self, query, SubmissionType):
        """
        Method to query the SQL database and return a dataframe with the data.
        
        Returns:
            1. The file name for the dataset
            2. A pandas dataframe containing the data
        """
        msg = f'Getting {SubmissionType} data from Data Warehouse'
        print(msg)
        logging.info(msg)
        

        try:
            data = SQL.select_source_data(query, returnDF = True)
            CreatedDate = str(dt.today())[0:19].replace(':','').replace('-','').replace(' ','')
            filename = f'{self.destinationFolder}\{SubmissionType}_{CreatedDate}.csv'
            print(f'Filename: {filename}\n')
            return filename, data

        except Exception as e:
            # ... PRINT THE ERROR MESSAGE ... #
            print(e)
            logging.critical(e)
            sys.exit()

    def generateCSV(self):
        """
        Method that iterates over the 'returns' in the config file and saves a csv containing
        the return data to the specified CSV destination folder.
        
        Returns:
            Dictionary with the return name and the filepath for the saved csv.
        """
        

        outputs = {}
        try:
            for i in config['API']['Returns']:
                query =  config['API']['Returns'][f'{i}']['SqlQuery']   #
                filename, data = self.getData(query,i)
                msg = f'Generating CSV {filename}'
                logging.info(msg)

                data.to_csv(f'{filename}', index = False)
                
                logging.info('CSV Created\n')

                outputs[f'{i}'] = filename

            return outputs

        except Exception as e:
            # ... PRINT THE ERROR MESSAGE ... #
            print(e)
            logging.critical(e)
            sys.exit()

class API():
    """
    This class submits the CSV file to the Foundry API using the requests library.
    
    PosArg1: csvFile
        The filename and path of the csv to be submitted.

    PosArg2: submissionType 
        The type of FDS submission. This is used to fetch the appropriate token and thus must match those listed in the Tokens section of the config file.

    PosArg3: config
        An instance of the load_config() call.
    """
    def __init__(self,csvFile,submissionType, config):
        self.csvFile = csvFile
        self.submissionType = submissionType
        self.root_url = config['API']['URL']

    def sendData(self, csvFile):
        try:
            file = os.path.basename(csvFile)
            f = open(f'{csvFile}', 'rb')      # Open file in read binary mode
            
            headers = {
                'Authorization': "Bearer "+config['API']['Returns'][f'{submissionType}']['Token']
                ,'Content-Type': "application/octet-stream"
                
                }
            files = {'file': (f'{file}',f)}   
            content = f.read()

            url = f'{self.root_url}{file}'
            
            msg = f'Posting to {url}\nFile name:{file}'
            print(msg)
            msg = f'Posting to {url}'
            logging.info(msg)
            msg = f'File name:{file}'
            logging.info(msg)

            response = requests.post(f'{url}', data = content, headers = headers)
        
            if response.ok:
                msg = "Upload completed successfully!\n\tResponse:"+str(response)+'\n\tResponse Content:'+response.text
                print(msg)
                logging.info('Upload completed successfully!')
                msg = f"Response: {str(response)}"
                logging.info(msg)
                msg = f"Response Content:{response.text}"
                logging.info(msg)
                outcome = 'SUCCESS'
                return msg, outcome

            else:
                msg = "Something went wrong:"+'\n\tResponse:'+str(response)+'\n\tResponse Content:'+response.text
                print(msg)

                logging.critical("Something went wrong")
                msg = f"Response: '{str(response)}"
                logging.critical(msg)
                msg = f"Response Content: {response.text}"
                logging.critical(msg)

                outcome = 'FAILURE'
                return msg, outcome

        except Exception as e:
            # ... PRINT THE ERROR MESSAGE ... #
            print(e)
            logging.critical(e)
            sys.exit()

def load_config(YAMLfile):
    """
    Loads the information stored in the yaml file.

    Return:
    Dictionary of config variables.
    """
    #dir_root = os.path.dirname(os.path.abspath(YAMLfile))

    with open(YAMLfile, 'r') as yamlfile:
        return yaml.load(yamlfile, Loader=yaml.FullLoader)

        

if __name__ == '__main__':

    # Get configuration data from YAML file
    yamlFile = "C:\\PATH\\TO\\YOUR\\PYTHON\\SERVER\\FDF_SubmissionShare\FDF\config.yaml"
    config = load_config(yamlFile)

    # Configure Logging
    CreatedDate = str(dt.today())[0:11].replace(':','').replace('-','_').replace(' ','')

    logging.basicConfig(
            level=logging.DEBUG,
            filename=f"{config['FileStore']['logFileDestination']}\FDF_Submission_{CreatedDate}.log", 
            filemode='a', # Append to the log file
            encoding='utf-8',
            format='%(asctime)s - (%(name)s) - %(levelname)s: %(message)s',
            datefmt='%d/%m/%Y %H:%M:%S'
            )


    logging.info('\n\t******************* Starting Process *******************')

    # Create an instance of the SQL to query database
    SQL = SQL(
            config['DatabaseInfo']['SourceServer'], 
            config['DatabaseInfo']['SourcePort'], 
            config['DatabaseInfo']['SourceUser'], 
            config['DatabaseInfo']['SourcePassword'], 
            config['DatabaseInfo']['SourceDatabase'], 
            config['DatabaseInfo']['SourceSchema'], 
            sourceOdbcDriver = config['DatabaseInfo']['SourceOdbcDriver'],
            useWindowsADSource= config['DatabaseInfo']['UseWindowsAD']
            )
    
    #SQL.fetch_odbc_drivers() 
    #sys.exit()

    # Fetch data from data warhouse and create csv files in the central store
    files = CreateDataset(config, config['FileStore']['csvDestination']).generateCSV()


    # Send the generated files to the Foundry API
    for i in files:
        submissionType = i
        csvFile = files.get(f'{i}')

        

        msg = '----- Sending File to API -----'
        logging.info(msg)
        print(msg)

        response, outcome = API(csvFile,submissionType, config).sendData(csvFile)

        with open(f"{config['FileStore']['apiResponseDestination']}\{(os.path.basename(csvFile))[:-4]}_ApiResponse{outcome}.txt",'w') as f:
            f.write(response)
        
        msg = '----- API Call End -----\n'
        logging.info(msg)
        print(msg)

    logging.info('\t******************* Finished Process *******************\n')