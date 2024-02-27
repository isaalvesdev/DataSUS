import urllib.request
from tqdm import tqdm
import datasus_dbc
import pandas as pd
import os
from tqdm import tqdm
from dbfread import DBF
from sqlalchemy import *
import datetime

DATASUS_PATH = os.path.dirname(os.path.abspath('__file__'))
DB_PATH = os.path.join(DATASUS_PATH, "datasus.db")
os.chdir(DATASUS_PATH)
engine = create_engine(f'sqlite:///{DB_PATH}',echo=True)

def date_range(start,stop,monthly = False):
    dt_start = datetime.datetime.strptime(start,'%Y-%m-%d')
    dt_stop = datetime.datetime.strptime(stop,'%Y-%m-%d')
    dates = []

    while dt_start <= dt_stop:
        dates.append(dt_start.strftime("%Y-%m-%d"))
        dt_start += datetime.timedelta(days=1)


    if monthly:
        return [i for i in dates if i.endswith("01")]

    return dates

#url = f"ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/RD{uf}{ano}{mes}.dbc"
#resp = urllib.request.urlretrieve(url,DBC_PATH)

def get_data_uf_ano_mes(uf,ano,mes):
    url = f"ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/RD{uf}{ano}{mes}.dbc"
    resp = urllib.request.urlretrieve(url,os.path.join(DATASUS_PATH, f"RD{uf}{ano}{mes}.dbc"))

def get_data_uf(uf,datas):

    for i in tqdm(datas):
        ano,mes,dia = i.split("-")
        ano = ano[-2:]
        get_data_uf_ano_mes(uf,ano,mes)

uf = 'SP'
datas = date_range('2022-01-01','2022-12-01',monthly=True)


#Download dos dados do datasus
get_data_uf(uf,datas)

#Converte dbc para dbf
for filename in tqdm(os.listdir()):
    if os.path.isfile(filename) and filename.startswith('RDSP22'):
        print(filename)

        try:
            output_filename = f"{os.path.splitext(filename)[0]}.dbf"
            datasus_dbc.decompress(f"{filename}", output_filename)
            print(f"Arquivo {filename} convertido para {output_filename}")


        except Exception as e:
            print(f"Erro ao conveter {filename}:{str(e)}")

#Importa todos os dbf's e adiciona ao banco de dados datasus.db
for filename in tqdm(os.listdir()):
    if os.path.isfile(filename) and filename.endswith('.dbf'):
        dbf = DBF(filename)
        df = pd.DataFrame(iter(dbf))
        df.to_sql(name='sihsus', con=engine,if_exists='append',index=False)

