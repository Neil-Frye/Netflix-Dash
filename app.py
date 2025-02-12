import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.express as px
import pandas as pd

# ------------------------------------------------------------
# Load Data
# ------------------------------------------------------------
df = pd.read_csv("data/netflix_titles.csv")

# Optional transformations: 
df["release_year"] = pd.to_numeric(df["release_year"], errors="coerce")

top_ratings = df["rating"].value_counts().nlargest(10)
top_genres = df["listed_in"].str.split(", ", expand=True).stack().value_counts().nlargest(10)
yearly_additions = df.groupby("release_year")["title"].count().reset_index()

# ------------------------------------------------------------
# Build Figures
# ------------------------------------------------------------
fig_top_ratings = px.bar(
    top_ratings, 
    x=top_ratings.index, 
    y=top_ratings.values, 
    title="Top 10 Ratings on Netflix",
    labels={"x": "Rating", "y": "Count"},
    color=top_ratings.values,
    color_continuous_scale="Tealgrn"
)

fig_top_genres = px.bar(
    top_genres, 
    x=top_genres.index, 
    y=top_genres.values, 
    title="Top 10 Genres on Netflix",
    labels={"x": "Genre", "y": "Count"},
    color=top_genres.values,
    color_continuous_scale="Tealgrn"
)

fig_yearly_additions = px.line(
    yearly_additions, 
    x="release_year", 
    y="title",
    title="Number of Releases by Year",
    labels={"release_year": "Year", "title": "Number of Titles"},
    markers=True
)

# ------------------------------------------------------------
# Dash App Initialization
# ------------------------------------------------------------
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.FLATLY],  # or any Dash Bootstrap theme
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

app.title = "Cool Reporting Dashboard"

# ------------------------------------------------------------
# Layout
# ------------------------------------------------------------
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col(html.H1("Netflix Titles Dashboard", className="text-center my-4"), width=12)
    ]),
    
    # Row of Cards or Graphs
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Top 10 Ratings", className="card-title"),
                dcc.Graph(figure=fig_top_ratings, config={"displayModeBar": False})
            ])
        ], className="mb-4"), width=6),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Top 10 Genres", className="card-title"),
                dcc.Graph(figure=fig_top_genres, config={"displayModeBar": False})
            ])
        ], className="mb-4"), width=6),
    ]),
    
    # Another Row
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Releases By Year", className="card-title"),
                dcc.Graph(figure=fig_yearly_additions, config={"displayModeBar": False})
            ])
        ], className="mb-4"), width=12),
    ]),
    
    # Footer
    dbc.Row([
        dbc.Col(html.P("Powered by Dash • Data from Netflix", className="text-center text-muted"), width=12)
    ])
], fluid=True)

# ------------------------------------------------------------
# Run Server
# ------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")
