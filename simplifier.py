import json
import base64
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
import os

# Glossary file
GLOSSARY_FILE = "glossary.json"

def load_glossary():
    if os.path.exists(GLOSSARY_FILE):
        with open(GLOSSARY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_glossary(glossary):
    with open(GLOSSARY_FILE, "w") as f:
        json.dump(glossary, f, indent=2)

glossary = load_glossary()

# Simplify text without nltk - only glossary lookup
def simplify_text(text, glossary):
    words = text.split()
    simplified = []
    trace = {}
    simplified_count = 0
    for word in words:
        clean = word.lower().strip(",.()")
        simple = glossary.get(clean)
        if simple:
            trace[word] = simple
            simplified.append(simple)
            simplified_count += 1
        else:
            simplified.append(word)
    confidence = round((simplified_count / len(words)) * 100, 1) if words else 0
    return " ".join(simplified), trace, confidence

# App setup with Bootstrap FLATLY theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Plain Skies - Glossary Simplifier"

app.layout = dbc.Container([
    html.Div([
        html.H1("☁️ Plain Skies", className="text-center text-white p-3 mb-4", style={
            "background": "linear-gradient(to right, #6fb1fc, #4364f7)",
            "borderRadius": "10px"
        }),
    ]),

    dbc.Row([
        dbc.Col([
            html.H5("Input Text"),
            dcc.Textarea(
                id='input-text',
                placeholder='Enter technical text...',
                style={'width': '100%', 'height': '200px', 'borderRadius': '8px'},
                className='mb-2'
            ),
            dbc.Button("Simplify", id='simplify-btn', color='primary', className='mb-2'),
            html.Div(id='confidence-display', className='text-muted mt-2')
        ], md=6),

        dbc.Col([
            html.H5("Simplified Output"),
            html.Div(id='simplified-output', className='border p-3 bg-light rounded shadow-sm'),
            html.Hr(),
            html.H6("Trace (what got simplified)"),
            html.Div(id='trace-output', className='small text-secondary')
        ], md=6)
    ], className='mb-4'),

    html.Hr(),
    html.H4("Glossary Tools", className="mb-3"),

    dbc.Row([
        dbc.Col([
            dbc.Input(id='glossary-search', placeholder='Search glossary term...', className='mb-1'),
            html.Div(id='glossary-definition', className='text-info')
        ], md=4),

        dbc.Col([
            dbc.InputGroup([
                dbc.Input(id='new-term', placeholder='New term'),
                dbc.Input(id='new-def', placeholder='Definition'),
                dbc.Button("Add Term", id='add-term-btn', color='success')
            ])
        ], md=8)
    ]),

    html.Div(id='glossary-stats', className='mt-3 text-secondary'),

    html.Hr(),
    html.H4("Upload & Download", className="mb-3"),
    dbc.Row([
        dbc.Col([
            dcc.Upload(
                id='upload-file',
                children=html.Div(['Drag and Drop or ', html.A('Select File')]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'backgroundColor': '#f9f9f9'
                },
                multiple=False
            ),
            html.Div(id='file-upload-output', className='mt-2')
        ], md=6),

        dbc.Col([
            dbc.Button("Download Simplified Text", id='download-btn', color='info'),
            dcc.Download(id='download-text')
        ], md=6)
    ])
], fluid=True)

# Callbacks

@app.callback(
    Output('simplified-output', 'children'),
    Output('trace-output', 'children'),
    Output('confidence-display', 'children'),
    Input('simplify-btn', 'n_clicks'),
    State('input-text', 'value')
)
def update_output(n, text):
    if not text:
        return '', '', ''
    simplified, trace, confidence = simplify_text(text, glossary)
    trace_html = [html.Div(f"{k} → {v}") for k, v in trace.items()]
    return simplified, trace_html, f"Simplification Confidence: {confidence}%"


@app.callback(
    Output('glossary-definition', 'children'),
    Input('glossary-search', 'value')
)
def search_glossary(term):
    if term:
        return glossary.get(term.lower(), 'Not in glossary.')
    return ''


@app.callback(
    Output('glossary-stats', 'children'),
    Input('add-term-btn', 'n_clicks'),
    State('new-term', 'value'),
    State('new-def', 'value')
)
def add_term(n, term, definition):
    if n and term and definition:
        glossary[term.lower()] = definition
        save_glossary(glossary)
    return f"Glossary contains {len(glossary)} terms."


@app.callback(
    Output('file-upload-output', 'children'),
    Input('upload-file', 'contents'),
    State('upload-file', 'filename')
)
def handle_file(contents, name):
    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            text = decoded.decode('utf-8')
            simplified, trace, confidence = simplify_text(text, glossary)
            return dbc.Alert(f"File '{name}' uploaded. Simplification confidence: {confidence}%", color='success')
        except Exception:
            return dbc.Alert("Failed to read file.", color='danger')
    return ''


@app.callback(
    Output('download-text', 'data'),
    Input('download-btn', 'n_clicks'),
    State('input-text', 'value')
)
def download_simplified(n, text):
    if n and text:
        simplified, _, _ = simplify_text(text, glossary)
        return dict(content=simplified, filename='simplified.txt')
    return dash.no_update


if __name__ == '__main__':
    app.run(debug=True)
