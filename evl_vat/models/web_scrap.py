import requests
import urllib.request
import time
from bs4 import BeautifulSoup

url = 'http://web.mta.info/developers/turnstile.html'

url = 'http://www.bangladeshcustoms.gov.bd/users/search_operative_tariff'
response = requests.get(url)

print(response)
#print(response.text)

soup = BeautifulSoup(response.text, "html.parser")

stat_table = soup.findAll('table')

print(len(stat_table))
type(stat_table)
stat_table =stat_table[0]

with open ('hscode.csv', 'w') as file:
    for row in stat_table.findAll('thead'):
        for cell in row.findAll('th'):
            file.write(str(cell.text)+",")


with open ('hscode.csv', 'a+') as file:
    for row in stat_table.findAll('tr'):
        i= 0
        for cell in row.findAll('td'):
            test = cell
            if i==0:
                cell = str(cell.text)
                cell = cell.replace(".", "")
            else:
                cell = cell.text
            if "For Total Tax Incidence" in cell:
                cell = cell.split(" ")[0]
            
            if i == 1:
                cell = cell.replace(",", ";")
            file.write(str(cell)+",")
            i += 1


        for cells in row.findAll('a'):
            link = cells['href']
            response2 = requests.get(link)
            soup2 = BeautifulSoup(response2.text, "html.parser")
            stat_table2 = soup2.findAll('table')
            stat_table2 =stat_table2[0]  
            for row in stat_table2.findAll('tr'): 
                i=0 
                for celll in row.findAll('td'):
                    if i == 2:
                        celll = celll.text.split("%")[0]
                        file.write(str(celll)+",")
                    i+=1
                      
        file.write("\n")
        


