from datetime import datetime
from assets.css_styles import styles
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input,Output, State
from dash.exceptions import PreventUpdate
import database_tools as dt
import rotation_analysis_tools as rat
from sklearn.linear_model import LinearRegression
import plotly.graph_objs as go

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__)

server = app.server

app.layout = html.Div([
    
    html.Div([
        html.Div([
            html.Label("Select a Module:", style = styles['label']), 
            dcc.Dropdown(
                id='module-list',
                placeholder='Module',
                style=styles['select']
                )], style=styles['col']),
        
        html.Div([
            html.Label("Select Date of Scan:", style = styles['label']), 
            dcc.Dropdown(
                id='date-list',
                placeholder='Date',
                style=styles['select']
                )], style=styles['col']),

        html.Div([
            html.Label("Select Time of Scan:", style = styles['label']), 
            dcc.Dropdown(
                id='time-list',
                placeholder='Time',
                style=styles['select']
                )], style=styles['col'])   
        ],
        style=styles['container']),
    html.Label("Choose a Scan Point to Inspect:", style=styles['label']),
    html.Div([
        dcc.Slider(
            id='scan-point',
            min=1,
            max=4,
            step=1,
            marks={i: 'Point {}'.format(i) for i in range(1,5)},
            value=1,
            included=False
        )
    ], style=styles['slider']),

    # Create a hidden button just so the first callback will have an input.  It doesn't do anything.
    html.Button(id='ignore', n_clicks = 0, children='firstLoad',style={'display':'none'}),

    dcc.Graph(id='scanGraph', 
            figure={
                'layout': go.Layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)')
                    },
            config={
                'modeBarButtonsToRemove' : ['select2d', 'toImage', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'toggleSpikelines', 'hoverClosestCartesian', 'hoverCompareCartesian', 'resetScale2d'],
                'displaylogo' : False
            },
            style=styles['maingraph']
        ),

    html.Div(id='measurment-result', style=styles['result']),

    html.Div(id='sensors-fit-plot'),
])

app.title = "Outer Tracker Sensor Scan Dashboard"

@app.callback(
    [
    Output('module-list','options'),
    Output('ignore', 'children'),
    Output('module-list','value')
    ],
    [Input('ignore', 'n_clicks')
    ],
    [
    State('ignore', 'children')
    ])
def initial_load(nclicks, ignore):
    session, modules, _ = dt.get_session()
    
    button = 'test'
    modules_from_db = [{'label': iq.name, 'value': iq.id} for iq in session.query(modules).order_by(modules.name)]

    session.close()
    return modules_from_db, button, modules_from_db[0]['value']


@app.callback(
    [Output('date-list','options'),
    Output('date-list','value')],
    [Input('module-list','value')])
def set_year_options(selected_module):
    session, _, scans = dt.get_session()
    
    if not selected_module:
        raise PreventUpdate
    scan_dates_from_db = [ {'label': iq.date.strftime("%m/%d/%Y"), 'value': iq.date} for iq in session.query(scans).distinct(scans.date).filter_by(moduleid=selected_module).order_by(scans.date)]

    session.close()
    return scan_dates_from_db, scan_dates_from_db[0]['value']

@app.callback(
    [Output('time-list','options'),
    Output('time-list','value')],
    [Input('date-list','value')],
    [State('module-list','value')])
def set_time_options(selected_date, selected_module):
    session, _, scans = dt.get_session()

    if not selected_date:
        raise PreventUpdate
    scan_times_from_db = [ {'label': iq.time.strftime("%-I:%M %p"), 'value': iq.time} for iq in session.query(scans).distinct(scans.time).filter_by(moduleid=selected_module).filter_by(date=selected_date).order_by(scans.time)]
    
    session.close()
    return scan_times_from_db, scan_times_from_db[0]['value']

@app.callback(
    [Output('scanGraph','figure'),
    Output('measurment-result','children'),
    Output('sensors-fit-plot','children')],
    [Input('scan-point','value'),
    Input('time-list','value')],
    [State('module-list','value'),
    State('date-list','value')]
    )
def populate_results(selected_point, selected_time, selected_module, selected_date):

    session, modules, scans = dt.get_session()

    layout=go.Layout(title='Scan Data',dragmode="zoom",paper_bgcolor='#fbfbfb', plot_bgcolor="#fbfbfb")

    if not selected_time:
        raise PreventUpdate        
    
    selected_module_name = session.query(modules).filter_by(id=selected_module).first().name
    date_and_time = datetime.strptime("{}_{}".format(selected_date,selected_time), '%Y-%m-%d_%H:%M:%S')

    df = rat.read_and_clean('sensor_scan_data/{}_{}_ScanPoint{}.csv'.format(selected_module_name,date_and_time.strftime("%m_%d_%y_%H%M"),selected_point))
    top,bot = rat.find_sensors(df)
    full_trace = go.Scattergl(x=df.z,y=df.d,mode='markers', showlegend=False)
    top_trace = go.Scattergl(x=top.z, y=top.d, mode='markers', marker={'color': 'orange'}, name="Top Sensor")
    bot_trace = go.Scattergl(x=bot.z, y=bot.d, mode='markers', marker={'color': 'red'}, name="Bottom Sensor")


    measurment_result = "Relative Misalignment = {} μrad".format([iq.misalignment for iq in session.query(scans).filter_by(moduleid=selected_module, date=selected_date, time=selected_time)][0])

    plot_file = 'fit_plots/{}_{}_sensor_fits.svg'.format(selected_module_name,date_and_time.strftime("%m_%d_%y_%H%M"))
    img_html = html.Img(src=app.get_asset_url(plot_file), style=styles['fitgraph'])

    session.close()
    return {'data':[full_trace, top_trace, bot_trace],'layout':layout}, measurment_result, img_html

if __name__ == "__main__":
    app.run_server(debug=True)

