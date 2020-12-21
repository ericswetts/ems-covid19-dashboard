#import statements for cholopleth map in Dash
from pandas.io.parsers import read_csv
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np


#css sheet
external_stylesheet = ['https://codepen.io/chriddyp/pen/bWLwgP.css']



#initialize app
app = dash.Dash(__name__, external_stylesheets=external_stylesheet)

app.layout = html.Div([
    html.Div([
        dcc.Graph(id = 'the_graph')]
        ),
    dcc.Slider(
        id='my-slider',
        min=0,
        max=20,
        step=0.5,
        value=10,
    ),
    html.Div(id='slider-output-container')
])


@app.callback(
    [dash.dependencies.Output('slider-output-container', 'children'),
    dash.dependencies.Output(component_id = 'my_graph', component_property = 'figure')],
    dash.dependencies.State(component_id='input_state', component_property='value')
    [dash.dependencies.Input('my-slider', 'value')])
def update_output(slide_value, new_value):
    return 'You have selected "{}"'.format(value)


if __name__ == '__main__':
    app.run_server(debug=True)




    
