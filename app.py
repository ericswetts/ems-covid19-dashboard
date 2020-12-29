#!/usr/bin/env python
# coding: utf-8

# In[347]:


from pandas.io.parsers import read_csv
import plotly.express as px
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
# import json
# import requests
import dash_table


#import data preprocessing function
from process_data import get_chart_ready_df, up_to_date_check, process_raw_data, make_api_call

#Bootstrap frontend framework
import dash_bootstrap_components as dbc

#css sheet
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]

#for development
# from jupyter_dash import JupyterDash
# import random as r


# In[348]:


try:
    df_map = get_chart_ready_df()
    df_map['Day'] = df_map['Day'].astype(int)
    print('pulled from API call')
    
except Exception as e:
    # df_map = pd.read_csv('../api_data/chart_ready.csv', parse_dates = ['Date'], index_col = 0)
    print('oof. new problems')
    print(e)

#Last Updated variable
last_updated = df_map['Date'].max().date().strftime("%B %d, %Y")

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


# ### Create Each Webpage Component Separately

# In[349]:


#Variables for Fast Facts Card
fast_facts_filter = (df_map['Date'] == df_map['Date'].max())
latest_data = df_map.loc[fast_facts_filter, ['Country', "Deaths", 'Cases', 'New Cases (n)', 'New Deaths (n)','Date']]    .sort_values('Country', axis = 0)

pandemic_length = df_map['Date'].unique().size
active_countries = latest_data.loc[latest_data['New Cases (n)'] > 100, 'Country'].size
total_deaths = latest_data['Deaths'].sum()
total_cases = latest_data['Cases'].sum()


# In[350]:


fast_fact_card = dbc.Col(
            dbc.ListGroup(
                dbc.ListGroupItem(children = [
                    dbc.ListGroupItemHeading(dcc.Markdown('''# Fast Facts''')),
                    html.Hr(),
                    dbc.ListGroupItemText(f"Global Cases : {total_cases}"),
                    dbc.ListGroupItemText(f"Global Deaths : {total_deaths}"),
                    dbc.ListGroupItemText(f"Days Since First Reported Case : {pandemic_length}"),
                    dbc.ListGroupItemText(f"Countries reporting > 100 cases / Day : {active_countries}")
                ], 
                style = {'color': '#2f4f4f', 'backgroundColor' : '#ede7c6' }
            ),
            flush = True),
        
        style = {
            'border': 'none', 
            'fontSize' : '14px',
            'backgroundColor' : '#ede7c6',
            'paddingTop' : '20px' },
        width = 3, 
)


# In[351]:


#Metric Dropdown
metric_dropdown = dbc.Col(
    children = [
    html.Label('Metrics', style = {"fontSize" : '14px'}),   
    dcc.Dropdown(
        id = 'metric_toggle',
        options = [
            # Confirmed Case Metrics
            {'label':'Cumulative Cases', 'value': 'Cases'},
            {'label':'Cumulative Cases per 1M', 'value': 'Cases per 1M'}, 
            {'label':'Daily Cases (n)', 'value': 'New Cases (n)'},

            #Confirmed Death Metrics
            {'label':'Cumulative Deaths', 'value': 'Deaths'},
            {'label':'Cumulative Deaths per 1M', 'value': 'Deaths per 1M'},
            {'label':'Daily Deaths (n)', 'value': 'New Deaths (n)'},
        ],
    value='Deaths',
    optionHeight = 25
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
            style = {'fontSize': '14px'}, 
            value = ['United States', 'Singapore', 'Brazil', 'France', 'Indonesia'], 
            optionHeight = 25
        )
    ],
    xs = 12,
    md = 5,
)


# In[352]:


#Date Slider for Choropleth Map and DataTable
date_slider = dbc.Col(
    children = [
        html.Label('Select a Date'),
        dcc.Slider(
            id ='date-slider',
            min = slider_min,
            max = slider_max,
            step = 1,
            value = 0,
            marks = slider_tick_labels
        )
    ],
    width = 12
)


# In[353]:


#Choropleth Map
choropleth_map = dbc.Col(
    dcc.Graph(id = 'map'), 
    width = 9, 
    style={'position':'relative', 'zIndex':'1'}
)

#Line Chart
line_chart = dbc.Col(
    dcc.Graph(id = 'line-chart'), 
    width = 8, 
    style={'position':'relative', 'zIndex':'1'}
)


# In[354]:


#Dash Datatable
top_15_table = dbc.Col([
    html.Label(id = 'top-15-title', style = {'fontSize': '18px'}),
    dash_table.DataTable(
        id='top_15',
        columns = [ {'name' : i , 'id' : i} for i in start_top_15.columns],
        data=start_top_15.to_dict('records'),
        style_as_list_view = True,
        style_table={'height': '320px', 'overflowY': 'hidden'},
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
    style = {'height': '400px', 'zIndex' : 0, 'border' : '1px solid black'}, 
    width = 4
)


# In[355]:


#Displays the Current Date Slider Value
display_slider_date = dbc.Col(
                            html.Label(['Date Selected: ', html.H5(id = 'display-slider-date')]),
                      width = 2)


#Not currently used
# date_picker = dbc.Col([
#     dbc.Row([html.Label('Select a Date')]),
#     dbc.Row([
#     dcc.DatePickerSingle(
#         id='date-picker',
#         min_date_allowed=min_date,
#         max_date_allowed=max_date,
#         initial_visible_month=min_date,
#         date = min_date
#     )])
# ])


# In[356]:


#Brief Explanation of How to Use the Dashboard
page_copy = dbc.Col(
    html.P('Use the provided filters to explore how COVID-19 has continued to develop around the globe. Use the date slider and dropdowns to view different metrics used to measure our progress against the pandemic.'),
    width={"size": 10, "offset": 1}, 
    style = {
        'fontSize' : '16px', 
        'padding' : '10px 0'
    }
)


# In[357]:


#Initialize Dash App
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# for app development:
# app = JupyterDash(__name__, external_stylesheets = external_stylesheets)


open_api_link = html.A('Open Coronavirus API', href = 'https://github.com/ExpDev07/coronavirus-tracker-api')

intro_text = html.P(['Data for this dashboard is provided by Johns Hopkins University, through the ', open_api_link, '. I assume no responsibility for any incorrect information, do not claim the accuracy of the information presented, and provide this data only for educational purposes. ', html.Br(), html.Br(),'Last Updated = {}'.format(last_updated)])

#Intro modal
introduction = html.Div(
    dbc.Modal(
        [
            dbc.ModalHeader('COVID-19 Reporting Dashboard'),
            dbc.ModalBody(intro_text),
            dbc.ModalFooter(
                dbc.Button("Close", id="close", className="ml-auto")
            ),
        ],
        id="intro-modal",
        is_open = True
    ),
    className = 'intro-text'
)

#Content Holds all Graphs and Analysis
content = dbc.Container(
    [   
        dbc.Row(page_copy),
        dbc.Container([ 
            dbc.Row([choropleth_map, fast_fact_card], 
                style = {'margin' : '20px 0'}
             )
        ]),
        dbc.Row([line_chart, top_15_table])],
        className = 'content'
    
)

#Controls Footer
controls = html.Div([
        dbc.Container([
            dbc.Row([
                country_dropdown,
                metric_dropdown,
                display_slider_date
            ]),
            dbc.Row([
                date_slider
            ])]
        ),
    ], 
        className = 'controls',
)

app.layout = html.Div([introduction, controls, content])


# In[360]:


#Callback function and Plotly components

#Choropleth Map callback
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
    fig.update_layout(title_x=0.3, title_font_size = 16)

    return fig

#Line Chart Callback
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
        'New Cases (n)' : 'COVID-19 Daily Case Count per Country',
        
        'Deaths': "COVID-19 Cumulative Death Count per Country",
        'Deaths per 1M' : 'COVID-19 Cumulative Population - Adjusted Deaths (Per 1M)',
        'New Deaths (n)' : 'COVID-19 Daily Deaths (n) per Country'
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
    fig.update_layout(hovermode='closest', font_size = 14, title_font_size = 16)

    return fig


#Data Table callbacks (Label, Header, and Values)
@app.callback(
    Output('top-15-title', 'children'), 
    [Input(component_id = 'date-slider', component_property = 'value'),
    Input(component_id = 'metric_toggle', component_property = 'value')]
)
def update_top_15_title(new_date_id, new_metric):
    
    data_table_titles = { 
        'Cases' : "Cumulative Cases", 
        'Cases per 1M' : 'Cumulative Population - Adjusted (Per 1M) Cases',
        'New Cases (n)' : 'Daily New Cases',
          
        'Deaths': "Cumulative Deaths",
        'Deaths per 1M' : 'Cumulative Population - Adjusted (Per 1M) Deaths',
        'New Deaths (n)' : 'Daily New Deaths'
    }   
    new_date = pd.to_datetime(unique_dates.loc[new_date_id, ['Date']]).dt.strftime("%B %d, %Y").values[0]
    new_metric_title = data_table_titles[new_metric]
    
    return ['Top 15 Countries,', html.Br(),  f'{new_metric_title} on {new_date}']


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

#Modal for Disclaimer
@app.callback(
    Output("intro-modal", "is_open"),
    Input("close", "n_clicks"), 
    State("intro-modal", "is_open")
)
def close_modal(click, is_open):
    if click:
        return not is_open
    return is_open

    


# In[359]:


#For Development
# import random
# a = random.randint(1000,5000)
# app.run_server(mode = 'external', port = a)

#For Production
if __name__ == '__main__':
    app.run_server(debug=True)



# In[ ]:




