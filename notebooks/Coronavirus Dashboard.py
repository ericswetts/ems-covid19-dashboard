#!/usr/bin/env python
# coding: utf-8

# In[101]:


from pandas.io.parsers import read_csv
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np
import json
import requests
import dash_table

#css sheet
external_stylesheet = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# custom_css = requests.get('./stylesheets/style.css').

#for development
from jupyter_dash import JupyterDash


# In[102]:


df_map_raw = pd.read_csv('../grouped.csv', parse_dates = ['date'], index_col = 0)

#Create datalabels for slider
#Get Unique Dates
unique_dates = pd.DataFrame(sorted(df_map_raw['date'].unique())).reset_index()
unique_dates.rename(columns = {'index':'id', 0 : 'date'}, inplace = True)

#Merge map data with unique dates to assign id value (for rendering choropleth map)
df_map = pd.merge(df_map_raw, unique_dates, how = 'left', on = 'date')

# #Extract month and year labels for map axis
df_map['month_year_label'] = pd.DatetimeIndex(df_map['date']).strftime("%b %Y")

# #Extract first day of each month and create corresponding label for slider labels
df_map['day'] = pd.DatetimeIndex(df_map['date']).strftime('%-d')


slider_min = df_map['id'].min()
slider_max = df_map['id'].max()

day_filter = df_map['day'] == '1'
slider_tick_cols  = df_map.loc[day_filter,['id', 'month_year_label']].drop_duplicates()
slider_tick_labels = dict(slider_tick_cols.values)


# In[103]:


#Helper methods for data processing and rendering
def top_15(df, date = '2020-01-22', metric = 'deaths'):
    return df.loc[df_map['date'] == date, ['country', 'deaths']]     .sort_values(metric, ascending = False).head(15)


# In[104]:


#Initialize Dash App
app = JupyterDash(__name__, external_stylesheets=external_stylesheet)


# In[105]:


#Define HTML elements
app.layout = html.Div(
    style = {
        'background-color':'darkslategrey'
    },
    children = [
        html.H3('cool'),
        dcc.Graph(id = 'graph'),
        html.Font(title = 'neato'),
        dcc.Slider(
            id ='date-slider',
            min = slider_min,
            max = slider_max,
            step = 1,
            value = 0,
            marks = slider_tick_labels,
        ), 
        
        #add radio button for morbidity / mortality
        dcc.RadioItems(
            id = 'metric_toggle',
        options=[
            {'label': 'Crude Mortality', 'value': 'deaths'},
            {'label':'Mortality Per 1M','value': 'deaths_per_1m'},
            {'label':'Crude Cases', 'value': 'cases'},
            {'label':'Case Rate per 1M', 'value': 'cases_per_1m'},    
        ],
        style = {'margin: 25px'},
        labelStyle={'display': 'inline-block'},
        value='deaths'
        ),
        
        dash_table.DataTable(
            id='top_15',
            columns=[{"name": i, "id": i} for i in top_15(df_map, '2020-01-01', 'deaths').columns],
            data=top_15(df_map, '2020-01-22', 'deaths').to_dict('records'),
        )
    
])


# In[110]:


#Callback function and Plotly components

@app.callback(
    Output('graph', 'figure'),
    [Input(component_id = 'date-slider', component_property = 'value'),
     Input(component_id = 'metric_toggle', component_property = 'value')]
)
def update_figure(new_date, new_metric):
    
    #helper function for color scale
    def max_range(x,y):
        return (x if x > y else y)
    
    filtered_df = df_map[df_map['id']  == new_date]
    color_scale_min = filtered_df[new_metric].min()
    color_scale_max = max_range(filtered_df[new_metric].max(), 200)
    
    fig = px.choropleth(filtered_df,
              locations = "ISO-3",               
              color = new_metric,
              hover_name = "country",  
              color_continuous_scale = 'Amp',  
              width = 1000, 
              range_color = (color_scale_min, color_scale_max),
              title = "Test"
    )
    fig.update_layout(transition_duration=500)

    return fig

@app.callback(
    Output('top_15', 'data'), 
    Input(component_id = 'date-slider', component_property='value')
)
def update_table(date):
    return top_15(df_map, date, 'deaths').to_dict('records')
    
if __name__ == '__main__':
    app.run_server(debug=False)

# app.run_server(mode='inline')
app.run_server(mode='external', port = 8070)
# app.run_server(mode='jupyterlab')


# In[93]:


app._terminate_server_for_port("localhost", 8060) 


# In[109]:


#Self - Reference materials
# https://dash.plotly.com/dash-core-components/slider
# https://dash.plotly.com/basic-callbacks
# https://www.youtube.com/watch?v=WBiMeRD5yXk
get_ipython().run_line_magic('tb', '')


# In[ ]:


get_ipython().run_line_magic('tb', '')


# In[110]:


def top_15(df, date, metric):
     return df.loc[df_map['date'] == date, ['country', metric]]     .sort_values(metric, ascending = False).head(15)
    
    
    


# In[ ]:


update_table(pd.to_datetime('2020-09-05'))


# In[107]:


date = df_map.loc[1:1, ['date']]


# In[108]:


date.shape


# In[209]:


df_map[(df_map['country'] == 'United Kingdom') & (df_map['date'] == '2020-12-10')]


# In[17]:


df_map.values


# In[196]:


top_15(df_map, '2020-07-24', 'deaths').to_dict('records')


# In[ ]:




