#!/usr/bin/env python
# coding: utf-8

# In[347]:
from flask_sqlalchemy import SQLAlchemy
from numpy.core.numeric import identity
from pandas.io.parsers import read_csv
import plotly.express as px
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
import dash_table

#for Heroku Flask deployment
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

#import data preprocessing function
from db_api_methods import get_from_db
#Import db getter/setter methods
#Bootstrap frontend framework
import dash_bootstrap_components as dbc

#css sheet
import locale
locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'

external_stylesheets = [dbc.themes.YETI]

#Suppress CopyWityhSettings
# import warnings
# from pandas.core.common import SettingWithCopyWarning
# warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

#Load reference CSV
country_reference = pd.read_csv('./geodata/country_reference.csv')

#for development
# from jupyter_dash import JupyterDash
# import random as r


# In[348]:

df_columns = ['id', 'Country','Population','Date','ISO-3','Multiple_Territories','Month and Year','Day','Deaths','Deaths per 1M','Cases','Cases per 1M','New Deaths (n)','New Cases (n)', 'New Deaths (SMA)', 'New Cases (SMA)']

try:
    result = get_from_db('public.chart_ready')
    df = pd.DataFrame(result, columns = df_columns).set_index('id') 
    df[['Deaths per 1M','Cases per 1M', 'New Deaths (n)', 'New Cases (n)', 'New Deaths (SMA)', 'New Cases (SMA)']] = df[['Deaths per 1M','Cases per 1M', 'New Deaths (n)', 'New Cases (n)', 'New Deaths (SMA)', 'New Cases (SMA)']].astype(float).round(1)
    print('Successfully pulled data from Heroku psql db')
    
except Exception as e:
    print('Unable to pull data from db, Trying backup data from csv...')
    try:
        df = pd.read_csv('../df.csv', parse_dates = ['Date'], index_col = 0)
        print('Successfully pulled historical data from backup CSV')
    except Exception as e:
        print('CSV FAILED! ABANDON SHIP!!!')


#Available countries - used to populate several dropdowns
available_countries = country_reference.loc[(country_reference['ISO-3'].isin(df['ISO-3'])), ['Country', 'ISO-3']].drop_duplicates().values


#Filter out countries that are missing matching ISO information
df = df.loc[df['ISO-3'].isin(country_reference.loc[:, 'ISO-3'].drop_duplicates())]

#Last Updated variable
df['Date'] = pd.to_datetime(df['Date'])
last_updated = df['Date'].max().date().strftime("%B %d, %Y")

#Date Range for DatePicker
min_date, max_date = df['Date'].min().date(), df['Date'].max().date()
#Create Labels for Date Slider
#Get Unique Dates
unique_dates = pd.DataFrame(sorted(df['Date'].unique())).reset_index()
unique_dates.rename(columns = {'index':'id', 0 : 'Date'}, inplace = True)

#Merge map data with unique dates to assign 'id' value (for rendering choropleth map)
df = pd.merge(df, unique_dates, how = 'left', on = 'Date')

#Set Slider Range
slider_min = df['id'].min()
slider_max = df['id'].max()

day_filter = df['Day'] == 1
slider_tick_cols  = df.loc[day_filter,['id', 'Month and Year']].drop_duplicates()
slider_tick_labels = dict(slider_tick_cols.values)

#add var for all countries
countries = list(df.loc[:, 'Country'].unique())

#helper method for rendering top 15 most affected countries for a given date
def top_15(date_id = 0, metric = 'Deaths'):
    return df.loc[df['id'] == date_id, ['Country', metric]].sort_values(metric, ascending = False).head(15)
start_top_15 = top_15()

#References for Dynamically Rendered Chart Titles
chart_titles = { 
        'Cases' : "Cumulative Cases", 
        'Cases per 1M' : 'Cumulative Cases (Per 1M) ',
        'New Cases (n)' : 'Daily New Cases',
        'New Cases (SMA)' : 'Daily New Cases (Smoothed)',
          
        'Deaths': "Cumulative Deaths",
        'Deaths per 1M' : 'Cumulative Deaths (Per 1M)',
        'New Deaths (n)' : 'Daily New Deaths',
        'New Deaths (SMA)' : 'Daily New Deaths (Smoothed)'
    }  


# ### Create Each Webpage Component Separately

# ### BEGIN COUNTRY TAB COMPONENTS
#Country Card with Summary Statistics
country_card_list = dbc.Col(
    id = 'country-card-list',
    style = {
#         'border': 'none', 
        'fontSize' : '14px',
        'backgroundColor' : '#ede7c6',
        'paddingTop' : '20px' 
    },
    width = 4
)

#Country Tab Single Country Dropdown
country_dropdown_country = dbc.Col( 
    children = [
        html.Label('Countries'),
        dcc.Dropdown(
            id = 'country-dropdown-country',
            options = [{'label': country, 'value' : iso} for country, iso in available_countries],
            style = {'fontSize': '14px'}, 
            value = 'USA', 
            optionHeight = 22, 
            clearable = False,
            persistence = True, 
            persistence_type = 'memory'
        )
    ],
    xs = 12,
    md = 5,
)

region_line = dbc.Col(
    dcc.Graph(id = 'region-line'),
    width = 12
)

map_country = dbc.Col(
    dcc.Graph(id = 'map-country'), 
    width = 8, 
    style={'position':'relative', 'zIndex':'1', 'paddingTop' : '20px'}, 
)

metric_dropdown_country = dbc.Col(
    children = [
    html.Label('Country'),   
    dcc.Dropdown(
        id = 'metric-dropdown-country',
        options = [
            # Confirmed Case Metrics
            {'label':'Cumulative Cases', 'value': 'Cases'},
            {'label':'Cumulative Cases per 1M', 'value': 'Cases per 1M'}, 
            {'label':'Daily Cases (n)', 'value': 'New Cases (n)'},
            {'label':'Daily Cases (Smoothed)', 'value':'New Cases (SMA)'},

            #Confirmed Death Metrics
            {'label':'Cumulative Deaths', 'value': 'Deaths'},
            {'label':'Cumulative Deaths per 1M', 'value': 'Deaths per 1M'},
            {'label':'Daily Deaths (n)', 'value': 'New Deaths (n)'},
            {'label':'Daily Deaths (Smoothed)', 'value':'New Deaths (SMA)'},
        ],
        value='Cases',
        optionHeight = 22,
        persistence = True, 
        persistence_type = 'memory'
    )
    ],
    xs = 12,
    md = 3, 
)

country_card_description = dbc.Col(id = 'country-card-description', width = 12)


# ### END COUNTRY TAB COMPONENTS

# In[349]:
### BEGIN GLOBAL TAB COMPONENTS

group_dropdown_global = dbc.Col(
    children = [ 
        html.Label('Country Grouping (Boxplot)'),
        dcc.Dropdown(
            id = 'group-dropdown-global',
            options = [
                {'label': 'Income Group', 'value': 'Income Group'},
                {'label': 'UN Region', 'value': 'UN Group'}
            ],
            value = 'Income Group',
            persistence = True, 
            persistence_type = 'memory',
            clearable = False)],
    width = 3
    # xs = 12,
    # md = 3
    )

group_dropdown_country = dbc.Col(
    children = [ 
        html.Label('Country Grouping'),
        dcc.Dropdown(
            id = 'group-dropdown-country',
            options = [
            #     {'label': 'Income Group', 'value': 'Income Group'},
            #     {'label': 'UN Region', 'value': 'UN Group'}
                {'label': 'Coming Soon!', 'value': 'Coming Soon!'}
            ],
            value = 'Coming Soon!',
            persistence = True, 
            persistence_type = 'memory',
            clearable = False,
            disabled=True)],
    width = 3
    # xs = 12,
    # md = 3
    )

#Variables for Fast Facts Card
fast_facts_filter = (df['Date'] == df['Date'].max())
latest_data = df.loc[fast_facts_filter, ['Country', "Deaths", 'Cases', 'New Cases (n)', 'New Deaths (n)','Date']]    .sort_values('Country', axis = 0)

pandemic_length = df['Date'].unique().size
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
metric_dropdown_global = dbc.Col(
    children = [
    html.Label('Metric (Map, Linechart, and Boxplot)', style = {"fontSize" : '14px'}),   
    dcc.Dropdown(
        id = 'metric-dropdown-global',
        options = [
            # Confirmed Case Metrics
            {'label':'Cumulative Cases', 'value': 'Cases'},
            {'label':'Cumulative Cases per 1M', 'value': 'Cases per 1M'}, 
            {'label':'Daily Cases (n)', 'value': 'New Cases (n)'},
            {'label':'Daily Cases (Smoothed)', 'value':'New Cases (SMA)'},

            #Confirmed Death Metrics
            {'label':'Cumulative Deaths', 'value': 'Deaths'},
            {'label':'Cumulative Deaths per 1M', 'value': 'Deaths per 1M'},
            {'label':'Daily Deaths (n)', 'value': 'New Deaths (n)'},
            {'label':'Daily Deaths (Smoothed)', 'value':'New Deaths (SMA)'},
        ],
    value='Deaths',
    optionHeight = 22,
    persistence = True, 
    persistence_type = 'memory'
    )
    ],
    xs = 12,
    md = 3,
)

#Country Dropdown
country_dropdown_global = dbc.Col( 
    children = [
        html.Label('Countries (Map, Linechart, and Boxplot)'),
        dcc.Dropdown(
            id = 'country-dropdown-global',
            options = [{'label': i, 'value' : i} for i in countries],
            multi = True, 
            style = {'fontSize': '14px'}, 
            value = ['Brazil', 'France', 'Italy', 'United States'], 
            optionHeight = 22,
            persistence = True, 
            persistence_type = 'memory'
        )
    ],
    xs = 12,
    md = 6,
)


# In[352]:

#Displays the Current Date Slider Value (Global)
display_slider_date = html.P(id = 'display-slider-date')

#Date Slider for Choropleth Map and DataTable
date_slider = dbc.Col(
    children = [
        display_slider_date,
        dcc.Slider(
            id ='date-slider',
            min = slider_min,
            max = slider_max,
            step = 1,
            value = slider_max,
            marks = slider_tick_labels,
            persistence = True, 
            persistence_type = 'memory'
        )
    ],
    width = 12,
    style = {'marginTop': '2vh'}
)


# In[353]:


#Choropleth Map (Global)
map_global = dbc.Col(
    dcc.Graph(id = 'map-global'), 
    width = 9, 
    style={'position':'relative', 'zIndex':'1'}
)

#Line Chart (Global)
line_chart = dbc.Col(
    dcc.Graph(id = 'line-chart'), 
    width = 8, 
    style={'position':'relative', 'zIndex':'1'}
)

boxplot_global = dbc.Col(
    dcc.Graph(id = 'boxplot-global'),
    width = 12
)


# In[354]:


#Dash Datatable (Global)
top_15_table = dbc.Col([
    html.Label(id = 'top-15-title', style = {'fontSize': 16, 'paddingTop': '1vh', 'font-weight' : 'bold'}),
    dash_table.DataTable(
        id='top_15',
        columns = [ {'name' : i , 'id' : i} for i in start_top_15.columns],
        data=start_top_15.to_dict('records'),
        style_as_list_view = True,
        style_table={'height': '310px', 'overflowY': 'hidden'},
        fixed_rows={'headers': True},

        style_data = {
            'padding' : '5px',
            'font_size': '12px',
            'text_align': 'left'
        },
        style_header = {
            'backgroundColor': 'white',
            'padding' : '5px',
            'font_size': '12px',
            'text_align': 'left', 
            'font_weight' : 'bold'
        }, 
        
        style_cell = {
            'whiteSpace': 'normal',
            'height': 'auto',
            'lineHeight': '14px'
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



# In[356]:


#Brief Explanation of How to Use the Dashboard
page_copy = dbc.Col(
    html.P('Use the provided filters to explore how COVID-19 has continued to develop around the globe. Use the date slider and dropdowns to view different metrics used to measure our progress against the pandemic.'),
    width={"offset": 1}, 
    style = {
        'fontSize' : '16px', 
        'padding' : '10px 0'
    }
)

#Disclaimer for Mobile Devices (Passed through header
mobile_warning = dbc.Row(
    dbc.Col(
        html.H4("Oh no! This dashboard is not optimized for mobile devices. \
            Please view on a laptop computer for a better experience. Thanks!",
            style = {'color': '#ff0000', 'fontWeight': 'bold'}
        )
    ),
    className='d-lg-none'
)

header = html.Div(children = [html.H3('Coronavirus 2019 Dashboard +++'), mobile_warning], 
                 style = {
                     'backgroundColor': '#ede7c6',
                     'padding': '15px', 
                     'color' : '##efd9ce'
                 })





### BEGIN APP LAYOUT
# Overall layout:
# All individual components
# tab-specific controls, controls container
# tab content, inividual tab layouts, tabs

### Controls
controls_country = html.Div([
        dbc.Container([
            dbc.Row([
                country_dropdown_country,
                metric_dropdown_country,
                group_dropdown_country
            ]),
            ]
        ),
    ], 
        id = 'controls-country'
)

controls_global = html.Div(
        children = [dbc.Row([
            country_dropdown_global,
            metric_dropdown_global,
            group_dropdown_global
        ], 
        no_gutters = True),
        dbc.Row([
            date_slider
        ])], 
        id = 'controls-global')


controls_container = html.Div(
    id = 'controls-container', 
    children = [controls_country, controls_global])


### Tabs
content_global = dbc.Container(
    [   
        dbc.Row(page_copy),
        dbc.Container([ 
            dbc.Row([map_global, fast_fact_card], 
                style = {'margin' : '10px 0'}
             )
        ]),
        dbc.Row([line_chart, top_15_table]),
        dbc.Row(boxplot_global)
    ],
        id = 'content-global'
    
)

content_country = dbc.Container(
        [
            dbc.Row([map_country, country_card_list]),
            dbc.Row(country_card_description)
            ], 
            id = 'content-country'
        )


country_tab =  dcc.Tab(
    id = 'country-tab',
    value = 'country-tab',
    label='Country Focus',  
    children = content_country,
    style={'backgroundColor': 'white'}
)

global_tab = dcc.Tab(
    id = 'global-tab', 
    label='Global Overview', 
    value='global-tab', 
    children = content_global,
    style={'backgroundColor': 'white'}
)

        
tabs = dcc.Tabs(
        id = 'tabs',
        value='global-tab', 
        children=[global_tab, country_tab], 
        colors={ "border": "#2F4F4F", "primary": "ede712", "background": "#ede7c6" },
        className = "pb-10 mb-10"
)







### END APP LAYOUT

# In[357]:


#Initialize Dash App
server = Flask(__name__)
app = dash.Dash(__name__, server = server, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# for app development:
# app = JupyterDash(__name__, external_stylesheets = external_stylesheets)

#For live heroku database connection

app.server.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://uzewvaalfzgguu:172f70cfc760489384a4ccb4d118c1c29aba8\
98dd9670b08fbc45ccae18cf54e@ec2-54-175-243-75.compute-1.amazonaws.com:5432/d2vg5i9noo69g1'

db = SQLAlchemy(app.server)


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


app.layout = html.Div([
    introduction,
    controls_container,
    tabs
    ], 
    id = 'app', 
    style={'backgroundColor': '#EDE7C5', 'paddingBottom' : '5vh'}
)

# In[360]:


#Callback function and Plotly components

#Callback to adjust controls / layout content
@app.callback(
    Output('tabs', 'className'),
    Input('tabs', 'value')
)
def adjust_top_margin(tab):
    return 'tabs-country-shift' if tab == 'country-tab' else 'tabs-global-shift'

#Callback for Tab Layout with Sticky Controls header
@app.callback(
    Output('controls-container', 'children'),
    Input('tabs', 'value')
)
def populate_controls(tab):
    if tab == 'global-tab':
        return [header, controls_global]
    return [header, controls_country]

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

### BEGIN GLOBAL TAB CALLBACKS
#Global Choropleth Map callback
@app.callback(
    Output('map-global', 'figure'),
    [Input(component_id = 'date-slider', component_property = 'value'),
    Input(component_id = 'metric-dropdown-global', component_property = 'value')]
)
def update_map(new_date_id, new_metric):
    
    #helper function for color scale
    def max_range(x,y):
        return (x if x > y else y)
    
    filtered_df = df[df['id']  == new_date_id]
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
    fig.update_layout(height=450, margin={"r":10,"t":30,"l":10,"b":30})
    fig.update_layout(transition_duration=500)
    fig.update_layout(coloraxis_colorbar = dict(thickness = 8))
    fig.update_layout(title_x = 0)

    return fig

#Line Chart Callback
@app.callback(
Output('line-chart', 'figure'),
    [Input('date-slider', 'value'),
    Input('metric-dropdown-global', 'value'), 
    Input('country-dropdown-global', 'value')]
)
def update_line_chart(new_date_id, new_metric, new_countries):
    
    line_chart_df = df.loc[df['Country'].isin(new_countries)]
    fig = px.line(line_chart_df,
        x = 'Date', 
        y = new_metric, 
        title = chart_titles[new_metric] + ' by Country', 
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
    fig.update_layout(title = {'x': 0})
    fig.update_layout(template = 'plotly_white')

    return fig


#Data Table callbacks (Label, Header, and Values)
@app.callback(
    Output('top-15-title', 'children'), 
    [Input(component_id = 'date-slider', component_property = 'value'),
    Input(component_id = 'metric-dropdown-global', component_property = 'value')]
)
def update_top_15_title(new_date_id, new_metric): 

    new_date = pd.to_datetime(unique_dates.loc[new_date_id, ['Date']]).dt.strftime("%B %d, %Y").values[0]
    new_metric_title = chart_titles[new_metric]
    
    return ['Top 15 Countries,', html.Br(),  f'{new_metric_title} on {new_date}']

@app.callback(
    Output('top_15', 'data'), 
    [Input(component_id = 'date-slider', component_property = 'value'),
    Input(component_id = 'metric-dropdown-global', component_property = 'value')]
)
def update_top_15_data(new_date_id, new_metric):
    return df.loc[df['id'] == new_date_id, ['Country', new_metric]].sort_values(new_metric, ascending = False).head(15).to_dict('records')


@app.callback(
    Output('top_15', 'columns'), 
    [Input(component_id = 'date-slider', component_property = 'value'),
    Input(component_id = 'metric-dropdown-global', component_property = 'value')]
)
def update_top_15_headers(new_date, new_metric):
    return [{'name' : i , 'id' : i} for i in ['Country', new_metric]]

#Display Date Selected on Date Slider
@app.callback(
    Output('display-slider-date', 'children'),
    Input('date-slider', 'value'),
)
def show_selected_date(date_id):
     dt = pd.to_datetime(unique_dates.loc[date_id, ['Date']].iloc[0]).date().strftime("%B %d, %Y")
     return html.Label(f'Date Selector (Map & Linechart) || Selected Date: {dt}')

#Callback to update global boxplots

@app.callback(
    Output('boxplot-global', 'figure'),
    [Input('group-dropdown-global', 'value'),
    Input('metric-dropdown-global', 'value')]
)
def update_boxplot_global(new_group, new_metric):

    def metric_for_box(new_metric):
        if new_metric == 'New Cases (SMA)' : return 'New Cases (n)'
        if new_metric == 'New Deaths (SMA)' : return 'New Deaths (n)'
        return new_metric

    new_metric = metric_for_box(new_metric)

# Code to populate boxplots
    df_filtered = df.loc[df['Date'] == df['Date'].max(), ['Cases per 1M', 'Cases', 'New Cases (n)', 'Deaths per 1M', 'Deaths','New Deaths (n)', 'Country', 'ISO-3', 'Population']]
    group = country_reference.loc[:, ['ISO-3', new_group]]
    df_box = df_filtered.merge(group, how = 'left', on = 'ISO-3', copy = False)
    df_box.dropna(axis = 0, how = 'any', inplace = True)

    fig = go.Figure()
    fig.update_layout(
        margin=dict(l=30, r=30, b=30, t=50, pad=20),
        yaxis_type = 'log', 
        yaxis_title = new_metric)
    fig.update_layout(title = 'Distribution of ' + chart_titles[new_metric] + ' ' + 'by ' + new_group + ' and Country')
    # fig.update_layout(legend=dict(x=0, y=1, traceorder='normal', font=dict(size=12)))
    # fig.add_annotation(xref="paper", yref="paper",x=0, y=1, text="*Point sizes reflect country population", showarrow=False)

    colors = ["#8f3985","#98dfea","#07beb8","#efd9ce","#937b63","#8a9b68","#ff5e5b","#25283d"]
    income_order = ['Low income', 'Lower middle income', 'Upper middle income', 'High income']
    un_order = ['African Group', 'Asia and the Pacific Group', 'Eastern European Group', 'Latin American and Caribbean Group (GRULAC)', 'Western European and Others Group (WEOG)']
    order = un_order if new_group == 'UN Group' else income_order
    
    hovertemplate = "<br>".join(["<b>Country</b>: %{customdata[0]}", "<b>Population</b>: %{customdata[1]}","<b>%{customdata[2]}</b>:%{y}", "<b>Group</b>:%{customdata[3]}"])
    i = 0

    pop_min = df_box['Population'].min()
    pop_max = df_box['Population'].max()
    pop = df_box['Population']
    norm_min, norm_max  = 5, 40
    # df_box['pop_norm'] = (((norm_max - norm_min) * (pop - pop_min)) / (pop_max - pop_min)) + norm_min
    # df_box['pop_norm'] = ((40 - 5) * (df_box['Population'] - df_box['Population'].min()) / (df_box['Population'].max() - df_box['Population'].min())) + 5
    df_box['pop_norm'] = 5
    for grp in order:

        data = df_box.loc[df_box[new_group] == grp]

        data['metric'] = data[new_metric].name
        data['jitter'] = np.random.randint(0,7, size=len(data)) + (20 * i)
        data['jitter'] = np.where(data['Population'] == data['Population'].mean(), data['jitter'].median(), data['jitter'] )
        
        #customdata parameter to format hovertemplates
        cd = np.stack((data['Country'], data['Population'], data['metric'], data[new_group]), axis=-1)


        fig.add_trace(go.Box(
            x = data[new_group],
            y = data[new_metric],
            name=str(grp),
            orientation = 'v',
            pointpos= 2, # Shows data point 
            boxpoints= 'all', # represent all points
            fillcolor = colors[i],
            marker_color = colors[i],
            marker_line=dict( width = 1, color = 'black'),
            line=dict( width = 2, color = 'black'),
            width = 0.2,
            customdata = cd
            
        ))
    
        fig.update_traces(hovertemplate= hovertemplate)
        fig.update_layout(template='plotly_white')
            
        i += 1

    # fig.update_xaxes(visible=False)

    return fig

### END GLOBAL TAB CALLBACKS

### START COUNTRY TAB CALLBACKS
@app.callback(
    Output('map-country', 'figure'),
    [Input('country-dropdown-country', 'value'),
    Input('metric-dropdown-country', 'value')]
)
def update_country_map(iso3, new_metric):

    #Helper Function for color scale
    def max_range(x,y):
        return (x if x > y else y)
    
    #Helper Function
    def metric_for_global_map(new_metric):
        if new_metric == 'New Cases (SMA)' : return 'New Cases (n)'
        if new_metric == 'New Deaths (SMA)' : return 'New Deaths (n)'
        return new_metric
    
    new_metric = metric_for_global_map(new_metric)
    
    filtered_df = df.loc[(df['Date']  == df['Date'].max())]
    
    #Centering and Zoom height variables
    projection = country_reference.loc[country_reference['ISO-3'] == iso3, 'Projection'].item()
    lat = country_reference.loc[country_reference['ISO-3'] == iso3, 'Lat'].item()
    lon = country_reference.loc[country_reference['ISO-3'] == iso3, 'Lon'].item()
    color_scale_min = filtered_df[new_metric].min()
    color_scale_max = max_range(filtered_df[new_metric].max(), 200)
    
    fig = px.choropleth(filtered_df,
                locations = "ISO-3",               
                color = new_metric,
                hover_name = "Country",  
                color_continuous_scale = 'algae',
                range_color = (color_scale_min, color_scale_max),
                title = '{} by Country'.format(new_metric), 
                template = 'plotly_white'
    )

    # Custom fitbounds using center properties
    fig.update_geos(center_lon = lon, center_lat = lat)
    fig.update_geos(lataxis_showgrid=True, lonaxis_showgrid=True)
    
    fig.update_geos(projection_type="natural earth")
    fig.update_layout(height=450, margin={"r":10,"t":30,"l":10,"b":30})
    fig.update_layout(transition_duration=500)
    fig.update_layout(title_x=0.3, title_font_size = 16)
    fig.update_layout(coloraxis_colorbar = dict(thickness = 8))
    fig.update_geos(projection_scale=projection)
    
    return fig

@app.callback(
    [Output('country-card-description', 'children'),
    Output('country-card-list', 'children')],
    [Input('country-dropdown-country', 'value'),
     Input('metric-dropdown-country', 'value'), 
    Input ('group-dropdown-country', 'value')]
)
def update_country_card(iso3, new_metric, new_group):
    
    #helper method for card text
    def trend(n): return "increased" if n > 1 else 'decreased'
            
    #Country-Specific Epidemiology
    new_country =  country_reference.loc[country_reference['ISO-3'] == iso3, 'Country'].iloc[0]
    df_c = df[df['ISO-3'] == iso3]
    last_two_weeks = df_c.loc[:, ['New Deaths (SMA)','New Cases (SMA)', 'Date']].tail(14)
    pct_deaths_two_weeks = round((last_two_weeks.loc[:,'New Deaths (SMA)'].iloc[0] / last_two_weeks.loc[:,'New Deaths (SMA)'].iloc[13] * 100 ) - 100, 2)
    pct_cases_two_weeks = round((last_two_weeks.loc[:,'New Cases (SMA)'].iloc[0] / last_two_weeks.loc[:,'New Cases (SMA)'].iloc[13] * 100) - 100, 2)
    days_since_first_case = (df_c['Date'].max() - df_c['Date'].min()).days
    first_case_date = df_c.loc[(df_c['Cases'] > 0), ['Date']].iloc[0].dt.strftime('%B %d, %Y').iloc[0]
    country_cases = df_c.loc[:,['Cases']].iloc[-1][0]
    country_deaths = df_c.loc[:,['Deaths']].iloc[-1][0]
    country_cases_per_1m = df_c.loc[:,['Deaths per 1M']].iloc[-1][0] 
    country_deaths_per_1m = df_c.loc[:,['Cases per 1M']].iloc[-1][0]

    new_cases = df_c.loc[:,['New Cases (n)']].astype('int').iloc[-1][0]
    under_control = "widespread" if new_cases > 500 else "limited"

    # Non-COVID19 Country Data
    wfpi_score = country_reference.loc[country_reference['ISO-3'] == iso3, 'WPFI Score'].iloc[0]
    wfpi_rank = country_reference.loc[country_reference['ISO-3'] == iso3, 'WPFI Rank'].iloc[0]
    wfpi_max_rank = country_reference['WPFI Rank'].max()
    country_life_exp = country_reference.loc[country_reference['ISO-3'] == iso3, 'Life Exp 2018'].round(2).iloc[0]
    
    #Regional Line Chart Variable
    un_group = country_reference.loc[country_reference['ISO-3'] == iso3, 'UN Group'].iloc[0]
    income_group = country_reference.loc[country_reference['ISO-3'] == iso3, 'Income Group'].iloc[0]

    country_card_text = (f"{new_country} reported its first case on {first_case_date}. The country has reported a total of {country_cases:n} " 
    f"cases and {country_deaths:n} deaths. Currently, COVID-19 transmission is {under_control} in {new_country}, and the number of new cases " 
    f"per day is approximately {new_cases:n}. In the past two weeks, the average daily case count in {new_country} has {trend(pct_cases_two_weeks)} by " 
    f"{pct_cases_two_weeks}%, and the death rate has {trend(pct_deaths_two_weeks)} by {pct_deaths_two_weeks}%.")
    
    country_card_description_content = dbc.Card(
            [html.H3('Country Overview', className = 'card-title'),
            html.P(country_card_text, className = 'card-text')
            ], 
            style = {'border': 'none', 'marginBottom' : '5vh'}, 
            
        )

    country_card_list_content = dbc.ListGroup(
            dbc.ListGroupItem(
                children = [
                    dbc.ListGroupItemHeading(html.H4('{} Summary'.format(new_country))),
                    html.Hr(),
#                     dbc.ListGroupItemHeading(country_card_text),
#                     html.Hr(),
                    dbc.ListGroupItemHeading("Statistics"),
                    dbc.ListGroupItemText(f"Total Cases : {int(country_cases):n}"),
                    dbc.ListGroupItemText(f"Cases per 1M : {int(country_cases_per_1m):n}"),
                    dbc.ListGroupItemText(f"Total Deaths : {int(country_deaths):n}"),
                    dbc.ListGroupItemText(f"Deaths per 1M : {int(country_deaths_per_1m):n}"),
                    dbc.ListGroupItemText(f"Life Expectancy (2018) : {country_life_exp} years"),
                    dbc.ListGroupItemText(f"Press Freedom Index Rank (2020) : {int(wfpi_rank)} out of {int(wfpi_max_rank)}"),
                    dbc.ListGroupItemText(f"United Nations Regional Group : {un_group}"), 
                    dbc.ListGroupItemText(f"World Bank ATLAS Group : {income_group}")

                ], 
                style = {'color': '#2f4f4f', 'backgroundColor' : '#ede7c6' }
            ),
        flush = True
    )
    return(country_card_description_content, country_card_list_content)




# In[359]:


#For Development
# import random
# a = random.randint(1000,5000)
# app.run_server(mode = 'external', port = a, debug = True)
if __name__ == '__main__':
    app.run_server(debug=True, port = 8353)


# In[ ]:




