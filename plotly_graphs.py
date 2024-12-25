from accuweather import WeatherManager
import plotly.graph_objs as go
from config import Config

parameters_map = Config.parameters_map


def make_weather_graph(all_weather_data: list[dict], forecast_days: int, selected_graphs: list[str]):


    dates = all_weather_data[0]['date'][:forecast_days]

    all_graphs = []
    for selected_graph in selected_graphs:
        fig = go.Figure()

        for index, point_data in enumerate(all_weather_data, 1):
            fig.add_scatter(x=point_data["date"][:forecast_days], y=point_data[selected_graph][:forecast_days], name=f"Точка {index}", mode='lines+markers')

        fig.update_layout(
            title=', '.join(parameters_map[selected_graph]),
            showlegend=True
        )
        all_graphs.append(fig)
    return all_graphs
