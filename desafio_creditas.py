########################################################################################################################
############################################## CREDITAS PYTHON CHALLENGE ###############################################
########################################################################################################################


import pandas as pd
import numpy as np
import xlsxwriter
from datetime import datetime
from selenium import webdriver


########################################################################################################################
################################################### CREDIT PORTFOLIO ###################################################
########################################################################################################################

case = pd.read_excel('~/Downloads/Case Excel PDD.xlsx', sheet_name = 'LOAN_TAPE')

############################################### EFFECTIVE RATE FUNCTION ################################################

def effective_rate(data, loan_id):

    if loan_id == "all":
        unique_id = data[['LOAN_ID']].drop_duplicates(subset='LOAN_ID', keep='first').reset_index(drop=True)
        unique_id['EFFECTIVE_RATE'] = float(0)

        for i in range(len(unique_id)):

            a = pd.DataFrame({'col1': [max(data[data['LOAN_ID'] == unique_id['LOAN_ID'][i]]['LOAN_AMOUNT'])]})
            b = pd.DataFrame({'col1': -data[data['LOAN_ID'] == unique_id['LOAN_ID'][i]]['FACE_VALUE']})

            unique_id['EFFECTIVE_RATE'][i] = np.irr(a.append(b)['col1']) * 100

        return unique_id

    else:
        test = data[(data['LOAN_ID'] == loan_id)]

        a = pd.DataFrame({'col1': [max(test['LOAN_AMOUNT'])]})
        b = pd.DataFrame({'col1': -test['FACE_VALUE']})

        return np.irr(a.append(b).reset_index(drop=True)['col1']) * 100


effective_rate(case, "f1e6e-b872")

print(effective_rate(case, "all").head(5))

# OUTPUT
#
#    LOAN_ID     EFFECTIVE_RATE
# 0  83510-b872        2.626081
# 1  f1e6e-b872        2.505990
# 2  19bba-b872        2.859519
# 3  ac24c-b872        3.596210
# 4  494fe-b871        2.686172


############################################### DAYS IN ARREARS FUNCTION ###############################################

def days_in_arrears(data, loan_id, data_ref):
    data_ref = pd.to_datetime(data_ref)

    if loan_id == "all":
        unique_id = data[['LOAN_ID']].drop_duplicates(subset='LOAN_ID', keep='first').reset_index(drop=True)
        unique_id['DAYS_IN_ARREARS'] = 0

        for i in range(len(unique_id)):
            min_date = min(data[(data['LOAN_ID'] == unique_id['LOAN_ID'][i])]['DUE_DATE']).date()
            unique_id['DAYS_IN_ARREARS'][i] = (data_ref - pd.to_datetime(min_date)).days

        return unique_id

    else:
        test = data[(data['LOAN_ID'] ==  loan_id)]
        min_date = min(test['DUE_DATE']).date()

        return (data_ref - pd.to_datetime(min_date)).days


print(days_in_arrears(case, "all", '26/02/2019').head(5))

# OUTPUT
#
#    LOAN_ID     DAYS_IN_ARREARS
# 0  83510-b872              365
# 1  f1e6e-b872              365
# 2  19bba-b872              365
# 3  ac24c-b872              363
# 4  494fe-b871              383


############################################### VL OUTSTANDING FUNCTION ################################################

def vl_outstanding(data, loan_id, data_ref):

    if loan_id == "all":
        unique_id = data[['LOAN_ID']].drop_duplicates(subset='LOAN_ID', keep='first').reset_index(drop=True)
        unique_id['VL_OUTSTANDING'] = float(0)

        for i in range(len(unique_id)):
            test = data[(data['LOAN_ID'] == unique_id['LOAN_ID'][i])]

            e_r = effective_rate(data, unique_id['LOAN_ID'][i]) / 100
            a = pd.DataFrame({'col1': [max(test['LOAN_AMOUNT'])]})
            b = pd.DataFrame({'col1': -test[(test['DUE_DATE'] < data_ref)]['FACE_VALUE']})

            unique_id['VL_OUTSTANDING'][i] = round(np.npv(e_r, a.append(b).reset_index(drop=True)['col1']), 2)

        return unique_id

    else:
        test = data[(data['LOAN_ID'] == loan_id)]

        e_r = effective_rate(data, loan_id)/100
        a = pd.DataFrame({'col1': [max(test['LOAN_AMOUNT'])]})
        b = pd.DataFrame({'col1': -test[(test['DUE_DATE'] < data_ref)]['FACE_VALUE']})

        return round((np.npv(e_r, a.append(b).reset_index(drop=True)['col1'])), 2)


vl_outstanding(case, 'f1e6e-b872', '26/02/2019')

print(vl_outstanding(case, 'all', '26/02/2019').head(5))

# OUTPUT
#
#    LOAN_ID     VL_OUTSTANDING
# 0  83510-b872        11041.47
# 1  f1e6e-b872        43934.23
# 2  19bba-b872         9165.56
# 3  ac24c-b872         3635.30
# 4  494fe-b871         8673.62


############################################### CASHFLOW AMOUNT FUNCTION ###############################################

def cashflow_amount(data, loan_id, data_ref):
    data_ref = pd.to_datetime(data_ref)

    if loan_id == "all":
        unique_id = data[['LOAN_ID']].drop_duplicates(subset='LOAN_ID', keep='first').reset_index(drop=True)
        unique_id['CASHFLOW_AMOUNT'] = 0.0

        for i in range(len(unique_id)):

            unique_id['CASHFLOW_AMOUNT'][i] = data[(data['LOAN_ID'] == unique_id['LOAN_ID'][i]) &
                                                   (data['PAYMENT_DATE'] < data_ref)]['AMOUNT_COLLECTED'].sum()
        return unique_id

    else:
        test = data[(data['LOAN_ID'] == loan_id)]

        return test[(test['PAYMENT_DATE'] < data_ref)]['AMOUNT_COLLECTED'].sum()


print(cashflow_amount(case, "all", '26/02/2019').head(5))

# OUTPUT
#
#    LOAN_ID     CASHFLOW_AMOUNT
# 0  16ecc-b871          8614.51
# 1  19bba-b872          8852.94
# 2  241c2-b872          8420.80
# 3  33eb6-b872         24578.55
# 4  3cebe-b871         22807.26



########################################### FINAL DATASET - JAN/18 - DEZ/19 ############################################

import datetime as dt
from pandas.tseries.offsets import MonthEnd


final_case_data = case[(case['DUE_DATE'] >= '01/01/2018') & (case['DUE_DATE'] < '01/01/2020')]

dates = (pd.to_datetime(final_case_data['DUE_DATE']) + MonthEnd(1)).drop_duplicates(keep='first').reset_index(drop=True)

dates = pd.DataFrame({'date': dates})

final_data = pd.DataFrame(columns=['DATA_REF', 'LOAN_ID', 'VL_OUTSTANDING', 'DAYS_IN_ARREARS', 'CASHFLOW_AMOUNT'])

for i in range(len(dates)):

    vl_out = vl_outstanding(case, 'all', dates['date'][i])

    d_arr = days_in_arrears(case, "all", dates['date'][i])

    c_f_amount = cashflow_amount(case, "all", dates['date'][i])

    cp_by_month = pd.DataFrame({'DATA_REF': str(dates['date'][i]),
                                'LOAN_ID': vl_out['LOAN_ID'],
                                'VL_OUTSTANDING': vl_out['VL_OUTSTANDING'],
                                'DAYS_IN_ARREARS': d_arr['DAYS_IN_ARREARS'],
                                'CASHFLOW_AMOUNT': c_f_amount['CASHFLOW_AMOUNT']})

    final_data = final_data.append(cp_by_month)

print(final_data.head(5))

# OUTPUT
#               DATA_REF     LOAN_ID  ...  DAYS_IN_ARREARS CASHFLOW_AMOUNT
# 0  2018-02-28 00:00:00  16ecc-b871  ...               10            0.00
# 1  2018-02-28 00:00:00  19bba-b872  ...                2            0.00
# 2  2018-02-28 00:00:00  241c2-b872  ...                0            0.00
# 3  2018-02-28 00:00:00  33eb6-b872  ...                0            0.00
# 4  2018-02-28 00:00:00  3cebe-b871  ...                5         1040.17



########################################################################################################################
############################################## WEB CRAWLER - INTEREST RATE #############################################
########################################################################################################################


options = webdriver.ChromeOptions()
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)

driver.get('https://www2.bmf.com.br/pages/portal/bmfbovespa/boletim1/TxRef1.asp')

table_text = driver.find_element_by_xpath("""//*[@id="tb_principal1"]""").text

table_text = table_text.replace("""Dias\nCorridos DI x pré\n252(2)(4) 360(1)""",
                                "DIAS_CORRIDOS TAXA_252 TAXA_360").replace(",",".").replace(" ",",").split("\n")

column_names = [line.split(',') for line in table_text].pop(0)

table_text = [line.split(',') for line in table_text[1:len(table_text)]]

final_table = pd.DataFrame(table_text ,columns=column_names)

print(final_table.head(5))

# OUTPUT print(final_table.head(5))
#
#   DIAS_CORRIDOS TAXA_252 TAXA_360
# 0             1     1.90     0.00
# 1             3     1.90     2.73
# 2             7     1.91     1.94
# 3             8     1.91     2.04
# 4             9     1.91     2.12



########################################################################################################################
################################################## POSTGRESQL QUERIES ##################################################
########################################################################################################################

"""
SELECT
    ASSET AS 'asset,
    SUM(COUNT(ASSET)) OVER (ORDER BY DATA) AS 'cum_count'
FROM
    TBL A
WHERE
    ASSET = 'FURI5'
GROUP BY DATA;
"""


###  Infelizmente nunca usei POSTGRESQL, apenas MYSQL. Escrever e executar a primeira consulta foi bem similar ao MYSQL.
###  Porém a segunda, nem sei por onde começar. Peço desculpas.