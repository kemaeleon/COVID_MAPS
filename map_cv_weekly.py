#!/home/maria/anaconda3/envs/cdentre/bin/python
import pandas as pd
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
from datetime import timedelta, date
import requests
import zipfile
import io
from pandas import Timestamp


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def go_back(end_date, days):
    for n in range(0,days):
        yield end_date - timedelta(n)

pd.set_option('display.max_columns', 50, 'display.max_rows', 500)

uk = gpd.read_file("Local_Authority_Districts__December_2019__Boundaries_UK_BFC.shp")
pop = pd.read_csv("pop_data.csv")[['CODE', '2020']]
pop['2020']= pop['2020'].str.replace(",","").astype(float)

url="https://coronavirus.data.gov.uk/downloads/csv/coronavirus-cases_latest.csv"
s=requests.get(url).content

virus = pd.read_csv(io.StringIO(s.decode('utf-8'))).drop_duplicates(subset=None, keep='first', inplace=False)
virus = virus.loc[virus['Area type'] == 'Lower tier local authority']
virus = virus.replace(to_replace = "Cornwall and Isles of Scilly", value="Cornwall")
virus_index = pd.pivot_table(virus, index=['Area name'], columns="Specimen date", values = "Daily lab-confirmed cases")  
covid_uk =   uk.merge(virus_index, how='inner', left_on='lad19nm', right_on='Area name')

covid_uk = covid_uk.merge(pop, how='inner', left_on='lad19cd', right_on='CODE')
covid_uk = covid_uk.fillna(0)

start_date = date(2020, 5, 20)
end_date = date.today()-timedelta(2)
sds =  covid_uk.copy(deep=True)
for single_date in daterange(start_date, end_date):
    date = single_date.strftime("%Y-%m-%d")
    sds[date] = 0
    for days in go_back(single_date,7):
        back_day = days.strftime("%Y-%m-%d")
        sds[date] += covid_uk[back_day]
    sds[date]=sds[date]/covid_uk['2020']*100000.0
    print(sds[date].max())
    th = sds[date].max()
#    print(sds)
    ax =  sds.fillna(0).plot(cmap = 'inferno',vmin=0, vmax=25, legend=date,column=date)
    for x,y,label,dt in zip(sds.centroid.x, sds.centroid.y, sds['lad19nm'],sds[date]):
        if dt > 20:
            ax.annotate(label, xy=(x,y), xytext=(1,1), color='white', backgroundcolor='black', textcoords="offset points", size=2) 
    ax.axis("off")
    ax.set_title(date)
    plt.savefig(date + ".png", dpi=1080)
