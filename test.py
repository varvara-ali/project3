import dash
from dash import html, dcc, Input, Output, State, callback
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc


from config import Config
from accuweather import WeatherManager
import plotly.graph_objs as go

import plotly_graphs

app = dash.Dash(__name__)


parameters_map = Config.parameters_map



app.layout = html.Div([
    # Выбор отображаемых графиков
    html.H3("Выбор графиков"),
    dcc.Checklist(
        id='graph-checklist',
        options=[
            {'label': v[0], 'value': k} for k, v in parameters_map.items()
        ],
        value=['min_temperature'],
        inline=True
    ),

    # Выбор количества дней для прогноза
    html.H3("Количество дней для прогноза"),
    dcc.Input(
        id='forecast_days',
        type='number',
        value=4,
        min=1,
        max=5,
        step=1,
        style={'margin-top': '20px'}
    ),

    # Добавление и удаление точек маршрута
    html.H3("Широта и долгота точки маршрута(от -90 до 90): "),
    dbc.Row([
        dbc.Col(dbc.Input(id='latitude', placeholder='Широта', type='number', min=-90, max=90)),
        dbc.Col(dbc.Input(id='longitude', placeholder='Долгота', type='number', min=-90, max=90)),
        dbc.Col(dbc.Button("Добавить точку", id='add-button', n_clicks=0))
    ]),
    dcc.Textarea(
        id='points_textarea',
        value='',
        style={'width': '100%', 'height': 200, 'display': 'none'},
    ),
    dcc.Store(
        id='points_list',
        data=[]
    ),

    # Карта
    html.Div(id='points_cards'),
    dbc.Checklist(
        id='show_map',
        options=[{'label': 'Показать/Скрыть карту', 'value': 'show'}],
        value=['show']
    ),
    html.Div(id='route_map'),

    # Вывод графиков
    html.Div(id='output-graphs')
])


# Добавление точек
@app.callback(
    Output('points_cards', 'children'),
    Input('points_list', 'data')
)
def show_cards(points_list):
    cards = [
        dbc.Card([
            dbc.CardHeader(f"Точка {i + 1}"),
            dbc.CardBody([
                html.P(f"Широта: {lat}; Долгота: {lon}"),
                dbc.Button("Удалить", id={'type': 'delete-button', 'index': i}, n_clicks=0)
            ])
        ])
        for i, (lat, lon) in enumerate(points_list)
    ]
    return cards


@app.callback(  # Новая точка
    Output('points_list', 'data', allow_duplicate=True),
    Input('add-button', 'n_clicks'),
    State('points_list', 'data'),
    State('latitude', 'value'),
    State('longitude', 'value'),
    prevent_initial_call=True
)
def update_points(n_clicks, points_list, lat, lon):
    if lat is not None and lon is not None:
        if (lat, lon) not in points_list:
            points_list.append((lat, lon))
    return points_list


@app.callback(
    Output('points_list', 'data'),
    Input({'type': 'delete-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    State('points_list', 'data'),
)
def delete_point(n_clicks, points_list):
    if not all(n is None for n in n_clicks):
        index_to_delete = [i for i, n in enumerate(n_clicks) if n]
        if index_to_delete:
            # Удаляем последнюю нажатую кнопку
            last_index = max(index_to_delete)
            points_list.pop(last_index)

    return points_list


# # Отображение карты
# @app.callback(
#     Output('route_map', 'style'),
#     Input('show_map', 'value')
# )
# def show_map(value):
#     if 'show' in value:
#         return {'display': 'block'}
#     return {'display': 'none'}
#
#
# @app.callback(
#     Output('route_map', 'children'),
#     Input('points_textarea', 'value')
# )
# def create_map(points_textarea_value):
#     latitudes = []
#     longitudes = []
#     if points_textarea_value:
#         for el in points_textarea_value.split():
#             latitude, longitude = tuple(map(int, el.split(';')))
#             latitudes.append(latitude)
#             longitudes.append(longitude)
#     else:
#         return None
#
#     fig = go.Figure(go.Scattermapbox(
#         lon=longitudes,
#         lat=latitudes,
#         mode='markers',
#         marker=dict(size=10),
#         customdata=list(range(1, len(latitudes)+1)),
#         hovertemplate="<b>Точка %{customdata}</b><br>" +
#                       "Longitude: %{lon}<br>" +
#                       "Latitude: %{lat}<br><extra></extra>"
#
#     ))
#     fig.update_layout(
#         mapbox=dict(
#             style='carto-positron',  # Стиль карты
#             center=dict(lat=latitudes[0], lon=longitudes[0]),  # Центр карты
#             zoom=5  # Уровень приближения
#         ),
#         margin=dict(t=0, b=0, l=0, r=0)  # Отступы от границ фигуры
#     )
#     return dcc.Graph(figure=fig)


# Отображение графиков
@app.callback(
    Output('output-graphs', 'children'),
    Input('graph-checklist', 'value'),
    Input('forecast_days', 'value'),
    Input('points_list', 'data')
)
def update_graphs(selected_graphs, forecast_days, points_list):
    graphs = []
    if not points_list:
        return None
    weather_manager = WeatherManager()

    try:
        location_keys = [
            weather_manager.get_location_key(*point)
            for point in points_list
        ]
    except RuntimeError as e:
         return html.H2(f"Ошибка при получении ключа локации:\n {e}")

    try:
        weather_data = [
            weather_manager.get_weather(location_key, name='test')
            for location_key in location_keys
        ]
    except RuntimeError as e:
        return html.H2(f"Ошибка при получении погоды:\n {e}")


    graphs = plotly_graphs.make_weather_graph(weather_data, forecast_days, selected_graphs)
    # all_df = open_meteo.get_weather(latitudes, longitudes, forecast_days)
    # dates = all_df[0]['date']
    # for selected_graph in selected_graphs:
    #     fig = go.Figure()
    #
    #     # Линии полудня
    #     for x in dates[12::24]:
    #         fig.add_vline(x=x, line_color='orange', opacity=0.5, name='Полдень')
    #     # Линии полуночи
    #     for x in dates[0::24]:
    #         fig.add_vline(x=x, line_color='black', opacity=0.5, name='Полночь')
    #
    #     # Отрисовка графиков
    #     for index, df in enumerate(all_df, 1):
    #         fig.add_scatter(x=df["date"], y=df[selected_graph], name=f"Точка {index}", mode='lines+markers')
    #
    #     fig.update_layout(
    #         title=', '.join(parameters_map[selected_graph]),
    #         showlegend=True
    #     )
    #
    #     graphs.append(dcc.Graph(figure=fig))
    graphs = [dcc.Graph(figure=fig) for fig in graphs]
    return graphs


if __name__ == '__main__':
    app.run_server(debug=True, host=Config.url, port=Config.port)

