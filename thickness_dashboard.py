import pandas as pd
import numpy as np
from dash import Dash, dcc, html, dash_table
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import webbrowser
import threading

# ---------------------------------------------
# File path
# ---------------------------------------------
CSV_FILE = "../data/processed/daily_upperair_climate.csv"

# ---------------------------------------------
# Load CSV
# ---------------------------------------------
df = pd.read_csv(CSV_FILE)
df["date"] = pd.to_datetime(df["date"])
df["mmdd"] = df["date"].dt.strftime("%m-%d")

# Drop rows missing thickness or high temp
df = df.dropna(subset=["thickness_1000_850", "high_temp"])

# ---------------------------------------------
# Compute row-to-row changes
# ---------------------------------------------
df["thickness_change"] = df["thickness_1000_850"].diff()
df["temp_change"] = df["high_temp"].diff()

# ---------------------------------------------
# Compute regression
# ---------------------------------------------
x = df["thickness_1000_850"].values
y = df["high_temp"].values

slope = np.cov(x, y, ddof=0)[0, 1] / np.var(x)
intercept = y.mean() - slope * x.mean()

df["predicted"] = intercept + slope * df["thickness_1000_850"]
df["error"] = df["high_temp"] - df["predicted"]
df["error_rounded"] = df["error"].round(1)

# ---------------------------------------------
# Identify outliers
# ---------------------------------------------
ERROR_THRESHOLD = 2
outliers = df[np.abs(df["error"]) >= ERROR_THRESHOLD]

# ---------------------------------------------
# Identify most recent day
# ---------------------------------------------
latest_row = df.loc[df["date"].idxmax()]

# ---------------------------------------------
# Plot with Plotly
# ---------------------------------------------
hover_text = (
    "Date: " + df["date"].dt.strftime("%Y-%m-%d") +
    "<br>Thickness: " + df["thickness_1000_850"].astype(str) +
    "<br>High Temp: " + df["high_temp"].astype(str) +
    "<br>Thickness Δ: " + df["thickness_change"].astype(str) +
    "<br>Temp Δ: " + df["temp_change"].astype(str) +
    "<br>Mean Wind: " + df["mean_wind_speed"].astype(str) +
    "<br>Highest Wind: " + df["highest_wind_speed"].astype(str) +
    "<br>Wind Dir: " + df["highest_wind_dir"].astype(str) +
    "<br>Remark: " + df["remark"].fillna("")
)

fig = go.Figure()

# Scatter all points
fig.add_trace(go.Scatter(
    x=df["thickness_1000_850"],
    y=df["high_temp"],
    mode="markers",
    name="All Days",
    hoverinfo="text",
    text=hover_text
))

# Regression line
fig.add_trace(go.Scatter(
    x=df["thickness_1000_850"],
    y=df["predicted"],
    mode="lines",
    name="Regression Line",
    line=dict(color="black")
))

# Outliers
fig.add_trace(go.Scatter(
    x=outliers["thickness_1000_850"],
    y=outliers["high_temp"],
    mode="markers+text",
    name="Outliers",
    marker=dict(color="red", size=10),
    text=outliers["mmdd"],
    textposition="top right"
))

# Highlight most recent day
fig.add_trace(go.Scatter(
    x=[latest_row["thickness_1000_850"]],
    y=[latest_row["high_temp"]],
    mode="markers",
    name="Latest Day",
    marker=dict(
        color="green",
        size=16,
        line=dict(color="black", width=2)
    ),
    hoverinfo="skip"
))

fig.update_layout(
    title="1000–850 mb Thickness vs High Temperature",
    xaxis_title="1000–850 mb Thickness (m)",
    yaxis_title="High Temperature (°F)",
    template="plotly_white",
    height=800
)

# ---------------------------------------------
# Dash app
# ---------------------------------------------
app = Dash(__name__)

# Layout
app.layout = html.Div([
    html.H2("Daily Upper-Air Thickness Analysis"),

    # Plot
    dcc.Graph(figure=fig),

    # Input box for prediction (initially blank)
    html.Div([
        html.H4("Predict High Temp from Thickness"),
        dcc.Input(
            id="thickness-input",
            type="number",
            placeholder="Enter thickness (m)",
            debounce=True,
            style={"marginRight": "10px"}
        ),
        html.Span(id="predicted-temp-output")
    ], style={"marginTop": "20px", "marginBottom": "20px"}),

    # Outlier diagnostic table
    html.H4("Outlier Diagnostics"),
    dash_table.DataTable(
        id="outlier-table",
        columns=[{"name": col, "id": col} for col in [
            "date", "thickness_change", "temp_change", "error_rounded"
        ]],
        data=outliers[["date", "thickness_change", "temp_change", "error_rounded"]]
            .fillna("")
            .to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "center"},
        style_header={"fontWeight": "bold"}
    )
])

# ---------------------------------------------
# Callback for thickness prediction
# ---------------------------------------------
@app.callback(
    Output("predicted-temp-output", "children"),
    Input("thickness-input", "value")
)
def update_predicted_temp(thickness_value):
    if thickness_value is None:
        return ""
    predicted_temp = intercept + slope * thickness_value
    return f"Predicted High Temp: {predicted_temp:.1f} °F"

# ---------------------------------------------
# Run server
# ---------------------------------------------
if __name__ == "__main__":

    threading.Timer(
        1.5,
        lambda: webbrowser.open("http://127.0.0.1:8050")
    ).start()

    app.run(
        debug=False,
        host="127.0.0.1",
        port=8050
    )
