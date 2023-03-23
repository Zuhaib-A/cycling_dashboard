# Statistics page
from dash import html, dcc, Dash
import dash_bootstrap_components as dbc
import main_flask_app.dash_app_cycling.app2 as app2 # barcharts
import main_flask_app.dash_app_cycling.app3 as app3 # linecharts
import main_flask_app.dash_app_cycling.app4 as app4# choropleths

def create_dash_app(flask_app):
    """Creates Dash as a route in Flask

    :param flask_app: A confired Flask app
    :return dash_app: A configured Dash app registered to the Flask app
    """
    # Register the Dash app to a route '/dashboard/' on a Flask app
    dash_app = Dash(
        __name__,
        server=flask_app,
        url_base_pathname="/dash_app/",
        meta_tags=[
            {
                "name": "viewport",
                "content": "width=device-width, initial-scale=1",
            }
        ],
        external_stylesheets=[dbc.themes.BOOTSTRAP],
    )

    def all_boroughs():
        """Return a dropdown widget to select the borough."""
        return dcc.Dropdown(
            id="dropdown_borough",
            options=app2.borough_names.loc[:, "name"],
            value="All Boroughs",
            clearable=False)


    def stats_layout():
        """Define the statistic page layout."""
        return dbc.Container(children=[
            dbc.Row(children=[
                dbc.Col(app4.app4_layout(), width="100%", align="evenly",),
            ]),
            dbc.Row(children=[
                dbc.Col(all_boroughs(), width="100%"),
            ]),
            dbc.Row(children=[
                    dbc.Col(
                        (app2.app2_layout()),
                        md=4,
                        xs=12,
                        sm=12,
                        align="evenly",
                    ),
                    dbc.Col(
                        (app3.app3_layout()),
                        md=8,
                        xs=12,
                        sm=12,
                        align="evenly",
                    ),
                    ]
                    ),
        ], fluid=True
        )
    
    dash_app.layout = stats_layout()
    return dash_app