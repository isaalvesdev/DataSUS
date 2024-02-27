from sqlalchemy import *
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import lifelines
from scipy.stats import norm

DATASUS_PATH = os.path.dirname(os.path.abspath('__file__'))
DB_PATH = os.path.join(DATASUS_PATH, "datasus.db")
os.chdir(DATASUS_PATH)

def import_query(path,**kwards):
    with open(path,'r',**kwards) as file:
        result = file.read()
    return result

def conectando_db():
    return create_engine(f'sqlite:///{DB_PATH}')

query = import_query(os.path.join(DATASUS_PATH,'query2.sql'))
con = conectando_db()

try:
    print("Lendo query...")
    df = pd.read_sql(query,con)
    print("Concluído com sucesso")

except Exception as erro:
    print(f"Erro inesperado:{str(erro)}")


df['ANO_MES'] = pd.to_datetime(df['ANO_CMPT'] + '-' + df['MES_CMPT'] + '-'+ '01')
df['SEXO'] = np.where(df['SEXO'] == '1','M','F')


grouped_cases = df.groupby(['ANO_MES'])['ANO_MES'].count().reset_index(name = 'CASOS')
grouped_cases

ax = grouped_cases.plot('ANO_MES','CASOS',marker='o', linestyle='-')

ax.set_title('Número de Internações por Esquizofrenia e Transtorno Bipolar no Estado de São Paulo (2022 e 2023)')
ax.set_ylabel('Número de Internações')
ax.set_xlabel('Data Competência')
plt.show()


grouped_age = df.groupby(['ANO_MES','SEXO'])['IDADE'].mean().reset_index(name = 'MEDIA_IDADE')
casos_masc = grouped_age[grouped_age['SEXO'] == 'M']
casos_fem = grouped_age[grouped_age['SEXO'] == 'F']
casos_masc
plt.plot(casos_masc['ANO_MES'], casos_masc['MEDIA_IDADE'], marker='o', linestyle='-', label='Masculino')
plt.plot(casos_fem['ANO_MES'], casos_fem['MEDIA_IDADE'], marker='o', linestyle='-', label='Feminino')
plt.xlabel('Data Competência')
plt.ylabel('Idade')
plt.title('Média da Idade dos Internados por Esquizofrenia e Transtorno Bipolar por Sexo no Estado de São Paulo (2022-2023)')
plt.legend()
plt.show()


grouped_diag = df.groupby(['DIAG_PRINC'])['DIAG_PRINC'].count().reset_index(name = 'QUANTI_DIAG')
grouped_diag = grouped_diag.sort_values('QUANTI_DIAG',ascending=True)
grouped_diag

blue_cmap = plt.cm.get_cmap('Blues')
colors = blue_cmap(range(200,50,-10))

plt.barh(grouped_diag['DIAG_PRINC'], grouped_diag['QUANTI_DIAG'],color=colors)

plt.xlabel('Quantidade de internações')
plt.ylabel('CID 10')
plt.title('Número de Internações por CID 10 em Pacientes com Esquizofrenia e Transtorno Bipolar no Estado de São Paulo (2022-2023)')
plt.show()

grouped_perm = df.groupby(['ANO_MES'])['DIAS_PERM'].mean().reset_index(name = 'MEDIA_DIAS')
grouped_perm

plt.plot(grouped_perm['ANO_MES'], grouped_perm['MEDIA_DIAS'], marker='o', linestyle='-')
plt.xlabel('Data Competência')
plt.ylabel('Dias')
plt.title('Média de Dias de Internações por Esquizofrenia e Transtorno Bipolar no Estado de São Paulo (2022-2023).')
plt.show()

grouped_perm_sexo = df.groupby(['ANO_MES','SEXO'])['DIAS_PERM'].mean().reset_index(name = 'MEDIA_DIAS')
grouped_perm_sexo

dias_masc = grouped_perm_sexo[grouped_perm_sexo['SEXO'] == 'M']
dias_fem = grouped_perm_sexo[grouped_perm_sexo['SEXO'] == 'F']


plt.plot(dias_masc['ANO_MES'], dias_masc['MEDIA_DIAS'], marker='o', linestyle='-', label='Masculino')
plt.plot(dias_fem['ANO_MES'], dias_fem['MEDIA_DIAS'], marker='o', linestyle='-', label='Feminino')
plt.xlabel('Data Competência')
plt.ylabel('Dias')
plt.title('Média de Dias de Internações por Esquizofrenia e Transtorno Bipolar por Sexo no Estado de São Paulo (2022-2023).')
plt.legend()
plt.show()

"""
1 - Falha (Mantem)
0 - Censura (Morte)
"""

dados_surv = df[['DIAS_PERM','MORTE']].copy()
dados_surv['DIAS_PERM'] = dados_surv['DIAS_PERM'] + 1
dados_surv['MORTE'] = 1 - dados_surv['MORTE']


from lifelines import KaplanMeierFitter
kmf = KaplanMeierFitter()
kmf.fit(dados_surv['DIAS_PERM'], event_observed=dados_surv['MORTE'])

kmf.plot_survival_function()
plt.xlabel('Tempo (Dias)')
plt.ylabel('S(t): estimada')
plt.title('Estimador de Kaplan - Meier')
plt.grid()
plt.show()

kmf.plot_cumulative_density()
plt.xlabel('Tempo (Dias)')
plt.ylabel('S(t): estimada acumulada')
plt.title('Estimador de Kaplan - Meier Acumulado')
plt.grid()
plt.show()


t_filtered = dados_surv[dados_surv['MORTE'] == 1]
tj = np.concatenate(([0], np.unique(t_filtered)))
surv = np.array([1] + list(np.unique(kmf.survival_function_['KM_estimate'].values)))
surv = np.sort(surv)[::-1]
k = len(tj) - 1
prod = np.zeros((k, 1))
for j in range(k):
    prod[j] = (tj[j + 1] - tj[j]) * surv[j]

tm = np.sum(prod)
print(f"O valor de tm é: {tm}")


from lifelines.utils import median_survival_times
median_ = kmf.median_survival_time_
median_

median_confidence_interval_ = median_survival_times(kmf.confidence_interval_)
median_confidence_interval_


from lifelines.utils import survival_table_from_events
table = survival_table_from_events(dados_surv['DIAS_PERM'], dados_surv['MORTE'])
print(table.head())

from lifelines import *


kmf = KaplanMeierFitter().fit(dados_surv['DIAS_PERM'], dados_surv['MORTE'], label='KaplanMeierFitter')
wbf = WeibullFitter().fit(dados_surv['DIAS_PERM'], dados_surv['MORTE'], label='WeibullFitter')
exf = ExponentialFitter().fit(dados_surv['DIAS_PERM'], dados_surv['MORTE'], label='ExponentialFitter')
lnf = LogNormalFitter().fit(dados_surv['DIAS_PERM'], dados_surv['MORTE'], label='LogNormalFitter')


kmf.plot_survival_function()
wbf.plot_survival_function()
exf.plot_survival_function()
lnf.plot_survival_function()
plt.xlabel('Tempo')
plt.ylabel('S(t)')
plt.title('Curva de Sobrevivência Estimada pelo Modelo Probabilístico vs Curva de sobrevivência pelo estimada pelo Kaplan-Meier')
plt.grid()
plt.show()


kmf.survival_function_

time = kmf.timeline
st = kmf.survival_function_['KaplanMeierFitter'].values

ste =  np.exp(-time/19.27)
stw =  np.exp(-(time/21.42)**1.65)
stln =  norm.ppf((-np.log(time)+ 2.67)/0.87)

plt.figure(figsize=(15, 5))

plt.subplot(131)
plt.plot(ste, st,'o', label='Kaplan-Meier')
plt.plot([0, 1], [0, 1], 'k--', label='Exponencial')
plt.xlabel('S(t): exponencial')
plt.ylabel('S(t): Kaplan-Meier')
plt.legend()


plt.subplot(132)  # 1 linha, 3 colunas, segundo subplot
plt.plot(stw, st, 'o', label='Kaplan-Meier')
plt.plot([0, 1], [0, 1], 'k--', label='Weibull')
plt.xlabel('S(t): Weibull')
plt.ylabel('S(t): Kaplan-Meier')
plt.legend()


plt.subplot(133)  # 1 linha, 3 colunas, terceiro subplot
plt.plot(stln, st, 'o', label='Kaplan-Meier')
plt.plot([0, 1], [0, 1], 'k--', label='Log-normal')
plt.xlabel('S(t): log-normal')
plt.ylabel('S(t): Kaplan-Meier')
plt.legend()

plt.tight_layout()  # Ajusta o espaçamento entre os subplots
plt.show()

invst = norm.ppf(st)

plt.figure(figsize=(15, 5))
plt.subplot(131)
plt.plot(time, -np.log(st), 'o', label='Kaplan-Meier')
plt.xlabel('tempos')
plt.ylabel('-log(S(t))')
plt.legend()

plt.subplot(132)
plt.plot(np.log(time), np.log(-np.log(st)), 'o', label='Kaplan-Meier')
plt.xlabel('log(tempos)')
plt.ylabel('log(-log(S(t)))')
plt.legend()

plt.subplot(133)
plt.plot(np.log(time), invst, 'o', label='Kaplan-Meier')
plt.xlabel('log(tempos)')
plt.ylabel(r'$\Phi^{-1} (S(t))$')  
plt.legend()

plt.tight_layout() 
plt.show()

wbf.log_likelihood_
exf.log_likelihood_
lnf.log_likelihood_
