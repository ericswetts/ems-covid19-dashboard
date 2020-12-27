#!/usr/bin/env python
# coding: utf-8

# In[1]:


from pandas.io.parsers import read_csv
import plotly.express as px
import plotly.graph_objects as go
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
import random as r

#import data preprocessing function
from process_data import get_chart_ready_df, up_to_date_check, process_raw_data, make_api_call

#Bootstrap frontend framework
import dash_bootstrap_components as dbc

#css sheet
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]
# custom_css = requests.get('./stylesheets/style.css').

#for development
from jupyter_dash import JupyterDash


# In[2]:


try:
    df_map = get_chart_ready_df()
    df_map['Day'] = df_map['Day'].astype(int)
    print('pulled from API call')
    
except:
    df_map = pd.read_csv('../api_data/chart_ready.csv', parse_dates = ['Date'], index_col = 0)

#Last Updated variable
last_updated = df_map['Date'].max().date()

#Date Range for DatePicker
min_date, max_date = df_map['Date'].min().date(), df_map['Date'].max().date()
#Create Labels for Date Slider
#Get Unique Dates
unique_dates = pd.DataFrame(sorted(df_map['Date'].unique())).reset_index()
unique_dates.rename(columns = {'index':'id', 0 : 'Date'}, inplace = True)

#Merge map data with unique dates to assign 'id' value (for rendering choropleth map)
df_map = pd.merge(df_map, unique_dates, how = 'left', on = 'Date')

#Set Slider Range
slider_min = df_map['id'].min()
slider_max = df_map['id'].max()

day_filter = df_map['Day'] == 1
slider_tick_cols  = df_map.loc[day_filter,['id', 'Month and Year']].drop_duplicates()
slider_tick_labels = dict(slider_tick_cols.values)

#add var for all countries
countries = list(df_map.loc[:, 'Country'].unique())

#helper method for rendering top 15 most affected countries for a given date
def top_15(date_id = 0, metric = 'Deaths'):
    return df_map.loc[df_map['id'] == date_id, ['Country', metric]]    .sort_values(metric, ascending = False).head(15)
start_top_15 = top_15()


# Create Each Webpage Component Separately

# In[4]:


open_api_link = html.A('Open Coronavirus API', href = 'https://github.com/ExpDev07/coronavirus-tracker-api')
introduction = html.Div(
                children = [
                    html.P(['Data for this dashboard is provided by Johns Hopkins University, through the ', open_api_link, html.Br(), 'Last Updated = {}'.format(last_updated)]),
                ],
                style = {'background-color':'darkslategrey',
                        'color' : '#ede7c7',
                        'font-size' : '16px', 
                        'font-weight' : 'bold'})


# In[5]:


#Metric Dropdown
metric_dropdown = dbc.Col(
    children = [
    html.Label('Metrics'),   
    dcc.Dropdown(
        id = 'metric_toggle',
        options = [
            # Positive Case Metrics
            {'label':'Cumulative Cases', 'value': 'Cases'},
            {'label':'Cumulative Cases per 1M', 'value': 'Cases per 1M'}, 
            {'label':'Daily Change in Cases (n)', 'value': 'Change in Cases (n)'},
            {'label':'Daily Change in Cases (pct)', 'value': 'Change in Cases (pct)'},

            #Confirmed Death Metrics
            {'label':'Cumulative Deaths', 'value': 'Deaths'},
            {'label':'Cumulative Deaths per 1M', 'value': 'Deaths per 1M'},
            {'label':'Daily Change in Deaths (n)', 'value': 'Change in Deaths (n)'},
            {'label':'Daily Change in Deaths (pct)', 'value': 'Change in Deaths (pct)'}
        ],
    value='Deaths'
    )
    ],
    xs = 12,
    md = 5, 
)

#Country Dropdown
country_dropdown = dbc.Col( 
    children = [
        html.Label('Countries'),
        dcc.Dropdown(
            id = 'country-dropdown',
            options = [{'label': i, 'value' : i} for i in countries],
            multi = True, 
            style = {'font-size': '14px'}, 
            value = ['United States', 'Singapore', 'Brazil', 'France', 'Indonesia']
        )
    ],
    xs = 12,
    md = 5,
)


# In[6]:


date_slider = dbc.Col(
    dcc.Slider(
        id ='date-slider',
        min = slider_min,
        max = slider_max,
        step = 1,
        value = 0,
        marks = slider_tick_labels
    ),
#     style = {'padding' : '20px 200px 30px'},
    width = 12
)


# In[7]:


#Choropleth Map
choropleth_map = dbc.Col(
    dcc.Graph(id = 'map'), 
    width = 12
)

#Line Chart
line_chart = dbc.Col(
    dcc.Graph(id = 'line-chart'), 
    width = 10
)


# In[8]:


#Dash Datatable
top_15_table = dbc.Col([
    html.Label(html.H3("Top 15 Countries for Selected Day & Metric")),
    dash_table.DataTable(
        id='top_15',
        columns = [ {'name' : i , 'id' : i} for i in start_top_15.columns],
        data=start_top_15.to_dict('records'),
        style_as_list_view = True,
        style_table={'height': '450px', 'overflowY': 'auto'},
        fixed_rows={'headers': True},

        style_data = {
            'padding' : '5px',
            'font_size': '12px',
            'text_align': 'left'
        },
        style_header = {
            'backgroundColor': 'white',
            'padding' : '5px',
            'font_size': '14px',
            'text_align': 'left', 
            'font_weight' : 'bold'
        }, 
        style_cell = {
            'whiteSpace': 'normal',
            'height': 'auto',
            'lineHeight': '15px'
        }
        ,style_cell_conditional= [{
            'if': {'column_id': 'Country'},
             'width': '60%'
        }]
    )],
    style = {'height': '400px'}, 
    xs = 12, 
    lg = 2
)


# In[9]:


display_slider_date = dbc.Col(
                            html.Label(['Date Selected: ', html.H5(id = 'display-slider-date')]),
                      width = 2)

date_picker = dbc.Col([
    dbc.Row([html.Label('Select a Date')]),
    dbc.Row([
    dcc.DatePickerSingle(
        id='date-picker',
        min_date_allowed=min_date,
        max_date_allowed=max_date,
        initial_visible_month=min_date,
        date = min_date
    )])
])


# In[10]:


page_copy = dbc.Col(
    html.P('This page utilizes the Coronavirus Open API and data from Johns Hopkins University. To explore a variety of time-series data, use the dropdown menus, date picker, and / or date slider below. Enjoy!'),
    width={"size": 10, "offset": 1}, 
    style = {
        'font-size' : '14px'
    }
)


# In[20]:


#Initialize Dash App
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# for app development:
# app = JupyterDash(__name__, external_stylesheets = external_stylesheets)

app.layout = html.Div([
    introduction,
    dbc.Row(page_copy),
    dbc.Container([
        
        dbc.Row([
            choropleth_map, 
            date_slider
        ], 
        style = {'margin' : '20px 0'}),
        dbc.Row([
            country_dropdown, 
            metric_dropdown, 
            display_slider_date,
            dbc.Row([line_chart, top_15_table])
        ],
        style = {'margin' : '20px 0'}),
    ])

])


# In[21]:


#Callback function and Plotly components

@app.callback(
    Output('map', 'figure'),
    [Input(component_id = 'date-slider', component_property = 'value'),
    Input(component_id = 'metric_toggle', component_property = 'value')]
)
def update_map(new_date_id, new_metric):
    
    #helper function for color scale
    def max_range(x,y):
        return (x if x > y else y)
    
    filtered_df = df_map[df_map['id']  == new_date_id]
    color_scale_min = filtered_df[new_metric].min()
    color_scale_max = max_range(filtered_df[new_metric].max(), 200)
    
    fig = px.choropleth(filtered_df,
                locations = "ISO-3",               
                color = new_metric,
                hover_name = "Country",  
                color_continuous_scale = 'Amp',
                range_color = (color_scale_min, color_scale_max),
                title = 'Cumulative COVID-19 {} by Country'.format(new_metric), 
                template = 'plotly_white'
    )
    
    fig.update_geos(projection_type="natural earth")
    fig.update_layout(height=300, margin={"r":10,"t":30,"l":10,"b":30})
    fig.update_layout(transition_duration=500)
    fig.update_layout(title_x=0.3)

    return fig


@app.callback(
Output('line-chart', 'figure'),
    [Input('date-slider', 'value'),
    Input('metric_toggle', 'value'), 
    Input('country-dropdown', 'value')]
)
def update_line_chart(new_date_id, new_metric, new_countries):
    
    line_chart_titles = { 
        'Cases' : "COVID-19 Cumulative Case Count per Country", 
        'Cases per 1M' : 'COVID-19 Cumulative Population - Adjusted Cases (Per 1M)',
        'Change in Cases (n)' : 'COVID-19 Daily Case Count Change (n) per Country',
        'Change in Cases (pct)' : 'COVID-19 Daily Case Change (pct) per Country',
        
        'Deaths': "COVID-19 Cumulative Death Count per Country",
        'Deaths per 1M' : 'COVID-19 Cumulative Population - Adjusted Deaths (Per 1M)',
        'Change in Deaths (n)' : 'COVID-19 Daily Deaths Count Change (n) per Country',
        'Change in Deaths (pct)' : 'COVID-19 Daily Deaths Change (pct) per Country'
    }
    
    line_chart_df = df_map.loc[df_map['Country'].isin(new_countries)]
    fig = px.line(line_chart_df,
        x = 'Date', 
        y = new_metric, 
        title = line_chart_titles[new_metric], 
        color = 'Country',
        text = new_metric, 
        template='gridon', 
        log_y = False,
        labels = dict(
            x = 'Date', 
            y = str(new_metric).title(),
            country = 'Country')
        )

    fig.update_traces(mode='lines')
    fig.update_layout(hovermode='closest')

    return fig


#Data Table callbacks
@app.callback(
    Output('top_15', 'data'), 
    [Input(component_id = 'date-slider', component_property = 'value'),
    Input(component_id = 'metric_toggle', component_property = 'value')]
)
def update_top_15_data(new_date_id, new_metric):
    return df_map.loc[df_map['id'] == new_date_id, ['Country', new_metric]]     .sort_values(new_metric, ascending = False).head(15).to_dict('records')


@app.callback(
    Output('top_15', 'columns'), 
    [Input(component_id = 'date-slider', component_property = 'value'),
    Input(component_id = 'metric_toggle', component_property = 'value')]
)
def update_top_15_headers(new_date, new_metric):
    return [{'name' : i , 'id' : i} for i in ['Country', new_metric]]

#Display Date Selected on Date Slider
@app.callback(
    Output('display-slider-date', 'children'),
    Input('date-slider', 'value'),
)
def show_selected_date(date_id):
     return pd.to_datetime(unique_dates.loc[date_id, ['Date']]).dt.date
    

    


# In[ ]:


#For Development
# app.run_server(mode = 'external', port = 8190)

if __name__ == '__main__':
    app.run_server(debug=True)
#     %tb


# In[ ]:


#Check themes during development
#import plotly
# plotly.io.templates

