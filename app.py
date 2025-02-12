import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import re
import random
from collections import Counter

# ------------------------------------------------------------
# Load Data
# ------------------------------------------------------------
df = pd.read_csv("data/netflix_titles.csv")

# If your dataset truly has 'release_year'
if "release_year" in df.columns:
    df["release_year"] = pd.to_numeric(df["release_year"], errors="coerce")
else:
    df["release_year"] = None  # Fallback if no such column

# Convert 'duration' to numeric if it's "XX min"
df["duration_minutes"] = pd.to_numeric(df["duration"].str.replace(" min","",regex=False), errors="coerce")

# For the 'cast' field, replace NaN with "" so we can safely split
df["cast"] = df["cast"].fillna("")

# Figure out min/max release years for slider
year_min = int(df["release_year"].min()) if df["release_year"].notna().any() else 1920
year_max = int(df["release_year"].max()) if df["release_year"].notna().any() else 2022

# ------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------
def filter_data(selected_type, year_range):
    """Return a filtered DataFrame based on type and [start_year, end_year]."""
    dff = df.copy()
    start_year, end_year = year_range

    if selected_type != "All":
        dff = dff[dff["type"] == selected_type]

    # Filter by year range if valid
    if dff["release_year"].notna().any():
        dff = dff[(dff["release_year"] >= start_year) & (dff["release_year"] <= end_year)]
    
    return dff

def build_top_ratings(dff):
    """Build bar chart of top 10 ratings from filtered DataFrame."""
    top_ratings = dff["rating"].value_counts().nlargest(10)
    fig = px.bar(
        top_ratings, 
        x=top_ratings.index, 
        y=top_ratings.values, 
        title="Top 10 Ratings on Netflix",
        labels={"x": "Rating", "y": "Count"},
        color=top_ratings.values,
        color_continuous_scale="Tealgrn"
    )
    return fig

def build_top_genres(dff):
    """Build bar chart of top 10 genres from filtered DataFrame."""
    # Split the listed_in column, stack, count
    top_genres = dff["listed_in"].str.split(", ", expand=True).stack().value_counts().nlargest(10)
    fig = px.bar(
        top_genres,
        x=top_genres.index,
        y=top_genres.values,
        title="Top 10 Genres on Netflix",
        labels={"x": "Genre", "y": "Count"},
        color=top_genres.values,
        color_continuous_scale="Tealgrn"
    )
    return fig

def build_longest_movies(dff):
    """Build horizontal bar chart of the top 10 longest movies by minutes."""
    # Filter for Movies only
    movies = dff[dff["type"] == "Movie"].copy()
    # Get top 10
    longest = movies.nlargest(10, "duration_minutes")[["title", "duration_minutes"]]
    fig = px.bar(
        longest,
        x="duration_minutes",
        y="title",
        orientation="h",
        title="Top 10 Longest Movies (Minutes)",
        labels={"title": "Movie Title", "duration_minutes": "Duration (min)"}
    )
    return fig

def build_top_actors(dff):
    """
    Build a bar chart of the top 10 actors by frequency in 'cast'.
    We'll parse each row's cast by commas, strip whitespace, then count.
    """
    # Create a big list of all actors
    actor_list = []
    for c in dff["cast"]:
        # "Actor A, Actor B"
        actors = [a.strip() for a in c.split(",") if a.strip() != ""]
        actor_list.extend(actors)

    # Count frequency
    actor_counts = Counter(actor_list).most_common(10)
    if not actor_counts:
        return px.bar(title="No Actors Found")

    names = [ac[0] for ac in actor_counts]
    counts = [ac[1] for ac in actor_counts]
    fig = px.bar(
        x=counts,
        y=names,
        orientation="h",
        labels={"x": "Appearances", "y": "Actor"},
        title="Top 10 Actors (Most Appearances)"
    )
    return fig

def build_yearly_additions(dff):
    """Line chart of # of releases by year."""
    if "release_year" not in dff.columns or dff["release_year"].dropna().empty:
        return px.line(title="No 'release_year' data available")

    yearly = dff.groupby("release_year")["title"].count().reset_index()
    fig = px.line(
        yearly,
        x="release_year",
        y="title",
        title="Number of Releases by Year",
        labels={"release_year": "Year", "title": "Number of Titles"},
        markers=True
    )
    return fig

def build_word_bubble(dff):
    """Simple 'word bubble' from descriptions in the filtered DataFrame."""
    desc = " ".join(str(x) for x in dff["description"].dropna())
    desc = re.sub(r"[^\w\s]", "", desc.lower())  # remove punctuation
    tokens = desc.split()

    # Basic stopwords
    stopwords = {
        "the","and","to","of","in","a","for","is","on","this","that","it","at","by","as","an","with",
        "be","he","she","they","from","his","her","are","was","were","which","or","who","when","them","their",
        "also","has","had","have","not","into","but","about","film","movie","show","series"
    }
    filtered = [t for t in tokens if t not in stopwords and len(t) > 3]
    word_counts = Counter(filtered).most_common(30)
    if not word_counts:
        return px.scatter(title="No Words Found")

    words = [wc[0] for wc in word_counts]
    counts = [wc[1] for wc in word_counts]

    # random x,y
    random.seed(42)
    xs = [random.random() for _ in range(len(words))]
    ys = [random.random() for _ in range(len(words))]

    fig = px.scatter(
        x=xs,
        y=ys,
        size=counts,
        text=words,
        title="Word Bubble from Descriptions",
        size_max=60
    )
    fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False)
    fig.update_traces(mode="text+markers", textposition="top center")
    return fig

# ------------------------------------------------------------
# Dash App Initialization
# ------------------------------------------------------------
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.FLATLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)
app.title = "Cool Reporting Dashboard"

# ------------------------------------------------------------
# Layout
# ------------------------------------------------------------
app.layout = dbc.Container(fluid=True, children=[
    dbc.Row([
        dbc.Col(
            html.H1([
                # "Netflix" in red + the rest in normal
                html.Span("Netflix", style={"color": "#E50914", "fontWeight": "bold"}),
                " Titles Dashboard"
            ], className="text-center my-4"),
            width=12
        )
    ]),

    # Filters: Type dropdown + Year range slider
    dbc.Row([
        dbc.Col([
            html.Label("Select Type:"),
            dcc.Dropdown(
                id="type-dropdown",
                options=[
                    {"label": "All", "value": "All"},
                    {"label": "Movie", "value": "Movie"},
                    {"label": "TV Show", "value": "TV Show"}
                ],
                value="All",
                clearable=False
            )
        ], width=3),
        dbc.Col([
            html.Label("Select Year Range:"),
            dcc.RangeSlider(
                id="year-range",
                min=year_min,
                max=year_max,
                value=[year_min, year_max],
                marks={str(y): str(y) for y in range(year_min, year_max+1, 10)},  # mark every 10 years
                step=1
            )
        ], width=9)
    ], className="mb-4"),

    # Graphs: 2 x 2 layout plus word bubble
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Top 10 Ratings", className="card-title"),
                dcc.Graph(id="top-ratings-graph", config={"displayModeBar": False})
            ])
        ], className="mb-4"), width=6),

        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Top 10 Genres", className="card-title"),
                dcc.Graph(id="top-genres-graph", config={"displayModeBar": False})
            ])
        ], className="mb-4"), width=6),
    ]),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Releases By Year", className="card-title"),
                dcc.Graph(id="yearly-additions-graph", config={"displayModeBar": False})
            ])
        ], className="mb-4"), width=6),

        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Top 10 Actors", className="card-title"),
                dcc.Graph(id="top-actors-graph", config={"displayModeBar": False})
            ])
        ], className="mb-4"), width=6),
    ]),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Longest Movies", className="card-title"),
                dcc.Graph(id="longest-movies-graph", config={"displayModeBar": False})
            ])
        ], className="mb-4"), width=6),

        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Word Bubble (Descriptions)", className="card-title"),
                dcc.Graph(id="word-bubble-graph", config={"displayModeBar": False})
            ])
        ], className="mb-4"), width=6),
    ]),

    # Footer
    dbc.Row([
        dbc.Col(
            html.P("Made by Neil F. • Data from Netflix", className="text-center text-muted"),
            width=12
        )
    ])
])

# ------------------------------------------------------------
# Callbacks
# ------------------------------------------------------------
@app.callback(
    [
        Output("top-ratings-graph", "figure"),
        Output("top-genres-graph", "figure"),
        Output("yearly-additions-graph", "figure"),
        Output("top-actors-graph", "figure"),
        Output("longest-movies-graph", "figure"),
        Output("word-bubble-graph", "figure"),
    ],
    [
        Input("type-dropdown", "value"),
        Input("year-range", "value")
    ]
)
def update_charts(selected_type, year_range):
    # Filter data based on user input
    dff = filter_data(selected_type, year_range)

    # Rebuild each figure with the filtered data
    fig_ratings = build_top_ratings(dff)
    fig_genres = build_top_genres(dff)
    fig_yearly = build_yearly_additions(dff)
    fig_actors = build_top_actors(dff)
    fig_longest = build_longest_movies(dff)
    fig_bubble = build_word_bubble(dff)
    return fig_ratings, fig_genres, fig_yearly, fig_actors, fig_longest, fig_bubble

# ------------------------------------------------------------
# Run Server
# ------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")
