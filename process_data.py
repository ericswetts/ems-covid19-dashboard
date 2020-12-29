#!/usr/bin/env python
# coding: utf-8

# In[27]:
import numpy as np
import pandas as pd
import json
from csv import writer
import requests
from datetime import date
# import os


# remove print limit to better explore dataframe data
# NOTE: Many functions related to writing API call data has been removed. Please
# see process_data.ipynb (Jupyter Notebook) format for setter code. For the live
# deployment of this app, all API calls will be made at loadtime.

#helper function to make API call
def make_api_call():
    try:
        response = requests.get('https://coronavirus-tracker-api.herokuapp.com/v2/locations?timelines=1')
        timeline_json = response.json()
        return timeline_json
    
    except Exception as e:
        print('Error making API call: ', e)

#helper function to load previously loaded API data
def use_existing_api_data():
    try:
        timeline_json = json.load(open('../api_data/timeline_json.json'))
        return timeline_json
    except Exception as e:
        print('Error reading existing JSON file: ', e)

#helper function to update api call log
def up_to_date_check():
    today = str(date.today())
    log = pd.read_csv('../api_data/api_call_log.csv')
    last = log.loc[:,'date'].max()
    return last == today

#helper function to load data (cached or via new API call) for webapp
def get_raw_data():
#     raw_data = use_existing_api_data() if up_to_date_check else make_api_call()
        return make_api_call()

# In[4]:


def process_raw_data():

#import ISO3 data for Dash Plotly Choropleth mapping
    iso3 = pd.read_csv("geodata/ISO3.csv",  index_col = 0)
    location_data = get_raw_data()['locations']
    
    #create empty list to compile country-level data
    data_rows = []

    #Extract COVID morbidity and mortality data from COVID JSON
    for loc in location_data:

        #Remove non-countries and countries with missing data
        if loc['country'] in ['MS Zaandam', 'Eritrea', 'Diamond Princess']: continue   

        cases = [{'Date': k, 'Cases' :v} for k,v in loc['timelines']['confirmed']['timeline'].items()]
        deaths = [{'Date': k, 'Deaths' :v} for k,v in loc['timelines']['deaths']['timeline'].items()]

        country_data = pd.merge(
            pd.DataFrame(deaths), 
            pd.DataFrame(cases), 
            left_on = 'Date', 
            right_on = 'Date')

        country_data['Country'] = 'United States' if loc['country'] == 'US' else loc['country']
        country_data['Country Code'] =  loc['country_code']
        country_data['Population'] =  loc['country_population']
        country_data['Province'] =  loc['province']
        country_data['Latitude'], country_data['Longitude'] =  [*loc['coordinates'].values()]
        country_data['Cases per 1M'] = (country_data['Cases'] /  country_data['Population']* 1000000).round(1)
        country_data['Deaths per 1M'] = (country_data['Deaths'] /  country_data['Population']* 1000000).round(1)
        country_data['New Deaths (n)'] = country_data['Deaths'].diff()
#         country_data['Change in Deaths (pct)'] = country_data['Deaths'].pct_change().round(2)
        country_data['New Cases (n)'] = country_data['Cases'].diff()
#         country_data['Change in Cases (pct)'] = country_data['Cases'].pct_change().round(2)
        country_data['Multiple_Territories'] = country_data['Country'].isin(['China', 'Canada', 'United Kingdom', 'France', 'Australia', 'Netherlands', 'Denmark'])
        
        #Date-related Variables
        country_data['Date'] =  pd.to_datetime(country_data['Date'].str.slice(0,10)) # + " " + country_data['Date'].str.slice(11, -1)
        country_data['Month and Year'] = pd.DatetimeIndex(country_data['Date']).strftime("%b %Y")
        # Later joined to dates on first of each month to create data labels
        country_data['Day'] = pd.DatetimeIndex(country_data['Date']).strftime('%-d')
        
        data_rows.append(country_data)

    df_cases = pd.concat(data_rows, axis = 0)
    
    #Merge ISO-3 country codes for cholopleth mapping
    processed_data = pd.merge(df_cases, iso3, left_on = 'Country', right_on = 'Country', how = 'left')
    return processed_data


# In[5]:


# Group by Country and Date, to sum metrics (cases, deaths, etc.)
# for countries with multiple provinces listed. This allows our graphs 
# to render country-level statistics

def get_chart_ready_df():
    df = process_raw_data()

    chart_ready_df = df.groupby(
                        ['Country', 
                        'Population', 
                        'Date', 
                        'ISO-3', 
                        'Multiple_Territories',
                        'Month and Year',
                        'Day']
                    ).agg({
                        'Deaths':'sum',
                        'Deaths per 1M':'sum',
                        'Cases': 'sum',
                        'Cases per 1M' : 'sum',
                        'New Deaths (n)' : 'sum',
                        'New Cases (n)' : 'sum'
#                         'Change in Deaths (pct)' : 'max',
#                         'Change in Cases (pct)' : 'max'
                    }).reset_index()

#     chart_ready_df.to_csv('../api_data/chart_ready.csv')
    return chart_ready_df

