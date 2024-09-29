import os
import io
import base64
from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update
import dash_cytoscape as cyto
import networkx as nx
from graph_logic import (
    carregar_grafo_txt, salvar_grafo_txt,
    gerar_elementos_cytoscape, adicionar_aresta, remover_aresta, remover_vertice
)
app = Dash(__name__, suppress_callback_exceptions=True)

#####################################################
################### SAVE GRAPH ######################
#####################################################

@app.callback(
    Output("download-graph", "data"),
    Input("btn-save-graph", "n_clicks"),
    prevent_initial_call=True,
)
def salvar_grafo(n_clicks):
    try:
        salvar_grafo_txt(G, "graph.txt")  
        return dcc.send_file("graph.txt")
    except Exception as e:
        return html.P(f"Erro ao salvar o grafo: {str(e)}")

#####################################################
################### ZOOM LEVEL ######################
#####################################################

zoom_level = 2.0  # Nível de zoom inicial

@app.callback(
    Output('cytoscape-grafo', 'zoom'),
    [Input('zoom-in', 'n_clicks'),
     Input('zoom-out', 'n_clicks')],
    prevent_initial_call=True
)
def update_zoom(n_clicks_in, n_clicks_out):
    global zoom_level
    ctx = callback_context

    # Determina qual botão foi clicado
    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Ajusta o zoom de acordo com o botão clicado
    if button_id == 'zoom-in':
        zoom_level += 0.5  # Aumenta o zoom em 50%
    elif button_id == 'zoom-out':
        zoom_level -= 0.5  # Diminui o zoom em 25%

    # Limitar o zoom a um intervalo entre 1.0 e 3.0
    zoom_level = max(1.0, min(zoom_level, 2.5))

    return zoom_level

#####################################################
################### CLEAR INPUT #####################
#####################################################

@app.callback(
    Output('add-node', 'value'),
    [Input('btn-add-node', 'n_clicks')]
)
def clear_add_node_input(n_clicks):
    return '' 

@app.callback(
    Output('add-edge-weight', 'value'),
    [Input('btn-add-weight', 'n_clicks')]
)
def clear_add_weight_input(n_clicks):
    # Retorna uma string vazia sempre que o botão 'Adicionar Peso' é clicado
    return '' 

#####################################################
################## HTML/CSS (INTERFACE) #############
#####################################################

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        {%css%}
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
            <style>
                html, body {
                    margin: 0;
                    padding: 0;
                    width: 100%;
                }

                .button-green {
                    background-color: #A1C057; 
                    color: white;              
                    border: 2px solid #A1C057; 
                }

                .button-green:hover {
                    background-color: #A1C057; 
                    border-color: #A1C057;  
                    color: white;              
                    /* Cor da borda ao passar o mouse */
                }

                
                .button-black {
                    background-color: #252525;  
                    color: white;             
                    border: 2px solid #252525; 
                }

                .button-black:hover {
                    background-color: #252525; 
                    border-color: #252525;  
                    color: white;            
            </style>
    </head>
    <body>
        {%app_entry%}
        {%config%}
        {%scripts%}
        {%renderer%}
    </body>
</html>
'''
# Variáveis globais para armazenar o grafo
G = nx.Graph()
ponderado = False
orientado = False

app.layout = html.Div([
    # Cabeçalho com imagem
    html.H2([
        html.Img(src='https://d1nhio0ox7pgb.cloudfront.net/_img/o_collection_png/green_dark_grey/256x256/plain/graph.png', style={'width': 'auto', 'height': '120px', 'margin-right': '5px'}),
        html.B('Grafo Visualizador')
    ], style={
        'text-align': 'center', 
        'padding': '5px', 
        'border-bottom': '2px solid #ddd',
        'font-family': 'Arial',
        'display': 'flex',
        'align-items': 'center',
        'justify-content': 'center'
    }),

    # Container principal
    html.Div(className='container', children=[
        html.Div(className='row', children=[
            # Coluna para as funcionalidades
            html.Div(className='col-md-3', children=[
                # Gerenciar Vértices
                html.Div(className='card p-3 mb-4 shadow-sm', children=[
                    html.H4('Gerenciar Vértices', className='card-title'),
                    dcc.Input(id='add-node', type='text', placeholder="ID do Vértice", className='form-control'),
                    html.Button('Adicionar Vértice', id='btn-add-node', className='btn button-green mt-2 w-100'),
                    html.Button('Remover Vértice', id='btn-remove-node', className='btn btn-danger mt-2 w-100'),
                ]),

                # Gerenciar Arestas
                html.Div(className='card p-3 mb-4 shadow-sm', children=[
                    html.H4('Gerenciar Arestas', className='card-title'),
                    html.Button('Adicionar Aresta', id='btn-add-edge', className='btn button-green w-100'),
                    html.Button('Remover Aresta', id='btn-remove-edge', className='btn btn-danger w-100 mt-2'),
                    dcc.Input(id='add-edge-weight', type='number', placeholder="Peso (Opcional)", className='form-control rounded mt-2'),
                    html.Button('Adicionar Peso', id='btn-add-weight', className='btn button-black w-100 mt-2'),
                ]),

                # Tipo de Grafo
                html.Div(className='card p-3 mb-4 shadow-sm', children=[
                    html.H4('Tipo de Grafo', className='card-title'),
                    html.Button('Orientado', id='btn-to-directed', className='btn button-green w-100 mb-2'),
                    html.Button('Não Orientado', id='btn-to-undirected', className='btn button-black w-100'),
                ]),

                # Ponderação
                html.Div(className='card p-3 mb-4 shadow-sm', children=[
                    html.H4('Ponderação do Grafo', className='card-title'),
                    html.Button('Ponderado', id='btn-make-weighted', className='btn button-green w-100 mb-2'),
                    html.Button('Não Ponderado', id='btn-make-unweighted', className='btn button-black w-100'),
                ]),

                # Algoritmos de Busca
                html.Div(className='card p-3 mb-4 shadow-sm', children=[
                    html.H4('Algoritmos de Busca', className='card-title'),
                    html.Button('BFS', id='btn-bfs', className='btn button-green w-100 mb-2'),
                    html.Button('DFS', id='btn-dfs', className='btn button-black w-100'),
                ]),
            ]),

            # Coluna para o visualizador do grafo
            html.Div(className='col-md-9', style={'padding-bottom': '100px'}, children=[
                # Visualizador do grafo
                cyto.Cytoscape(
                    className='shadow-sm card p-3 mb-2',
                    id='cytoscape-grafo',
                    layout={'name': 'cose'},
                    panningEnabled=True,
                    userZoomingEnabled=True,
                    zoomingEnabled=True,
                    minZoom=1.0,
                    maxZoom=2.5,
                    stylesheet=[
                        {'selector': 'node', 
                        'style': {'content': 'data(label)', 
                        'text-valign': 'center', 
                        'text-halign': 'center', 
                        'color': 'black'}},

                        {'selector': 'edge', 
                        'style': {'curve-style': 'bezier'}}
                    ],
                    tapNodeData={'selector': 'node'},
                    tapEdgeData={'selector': 'edge'},
                    style={
                        'width': '100%',
                        'height': '550px',
                        'margin': '0 auto',
                        'position': 'relative'
                    },
                    elements=[],  # Usar os elementos gerados
                ),

                # Nova linha para informações, botões de zoom e upload/download
                html.Div(className='row', children=[

                    # Coluna para os botões de upload e download
                    html.Div(className='col-md-6 d-flex justify-content-start', children=[
                        dcc.Upload(
                            id='upload-data',
                            children=html.Button('Enviar Grafo', className='btn button-green', style={'margin-left': '0px', 'width': '120px', 'height': '38px'})
                        ),
                        html.Button('Salvar Grafo', id='btn-save-graph', className='btn button-black', style={'margin-left': '5px', 'width': '120px', 'height': '38px'}),
                    ], style={
                        'z-index': '1000',
                        'margin-bottom': '3px'
                    }),
                    dcc.Download(id="download-graph"),
                    
                    # Coluna para os botões de zoom
                    html.Div(className='col-md-6 d-flex justify-content-end',children=[
                        html.Div(
                            [
                                html.Button(
                                    html.I(className="fa-solid fa-arrows-rotate"),
                                    id='refresh-button',
                                    n_clicks=0,
                                    className='btn button-black',
                                    style={'margin-right': '5px'}
                                ),
                                dcc.Location(id='url-refresh', refresh=True),
                                html.Button(
                                    html.I(className="fa-solid fa-magnifying-glass-plus"),
                                    id='zoom-in',
                                    n_clicks=0,
                                    className='btn button-black',
                                    style={'margin-right': '5px'}
                                ),
                                html.Button(
                                    html.I(className="fa-solid fa-magnifying-glass-minus"),
                                    id='zoom-out',
                                    n_clicks=0,
                                    className='btn button-black',
                                )
                            ],
                            style={
                                'z-index': '1000'
                            }
                        ),
                    ]),
                    # Coluna para as informações
                    html.Div(className='col-md-12 card p-1 mb-4 shadow-sm',style={'margin': '5px 0 0 12px', 'padding-top': '20px', 'width': '98%'}, children=[
                        html.Div(id='grafo-info', style={
                            'font-family': 'Arial',
                            'padding': '10px 0 7px 10px',
                        }),
                    ]),
                ]),
            ])
        ]),
    ]),
])

#####################################################
################## UPDATE GRAPH #####################
#####################################################

@app.callback(
    [Output('cytoscape-grafo', 'elements'),
     Output('grafo-info', 'children')],
    [Input('upload-data', 'contents'),
     Input('btn-add-node', 'n_clicks'),
     Input('btn-add-edge', 'n_clicks'),
     Input('btn-remove-node', 'n_clicks'),
     Input('btn-remove-edge', 'n_clicks'),
     Input('btn-to-directed', 'n_clicks'),
     Input('btn-to-undirected', 'n_clicks'),
     Input('btn-add-weight', 'n_clicks'),
     Input('btn-make-weighted', 'n_clicks'),
     Input('btn-make-unweighted', 'n_clicks'),
     Input('btn-bfs', 'n_clicks'),
     Input('btn-dfs', 'n_clicks'),
     Input('refresh-button', 'n_clicks'),
     Input('cytoscape-grafo', 'selectedNodeData'),
     Input('cytoscape-grafo', 'selectedEdgeData')],
    [State('upload-data', 'filename'),
     State('add-node', 'value'),
     State('add-edge-weight', 'value'),
     State('cytoscape-grafo', 'elements')]
)

def update_graph(contents, add_node_clicks, add_edge_clicks, remove_node_clicks, remove_edge_clicks, refresh_button,
                to_directed_clicks, to_undirected_clicks, add_weight_clicks, bfs_clicks, btn_make_weighted_clicks, 
                btn_make_unweighted_clicks, dfs_clicks, selected_nodes, selected_edges, filename, add_node, add_edge_weight, elements):
    
    global G, ponderado, orientado
    ctx = callback_context
    
    if not ctx.triggered:
        return gerar_elementos_cytoscape(G), [html.P("Nenhum grafo carregado.")]
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    try:
        if button_id == 'upload-data' and contents is not None:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string).decode('utf-8')
            
            temp_filename = 'temp_graph.txt'
            with open(temp_filename, 'w') as temp_file:
                temp_file.write(decoded)
            
            G, ponderado, orientado = carregar_grafo_txt(temp_filename)
            os.remove(temp_filename)
            elements = gerar_elementos_cytoscape(G)
        
        elif button_id == 'btn-add-node':
            # Verifica se o input não está vazio e se o vértice não existe
            if add_node and add_node not in G.nodes():
                G.add_node(add_node)
                elements = gerar_elementos_cytoscape(G)
            else:
                # Retorna uma mensagem de erro se o input estiver vazio ou o vértice já existir
                return elements, html.P(f"Erro: Vértice '{add_node}' já existe ou o campo está vazio.")
        
        elif button_id == 'btn-remove-node':

            if G.number_of_nodes() == 0:
                return elements, html.P("Nenhum grafo carregado.")

            if selected_nodes:
                for node_data in selected_nodes:
                    remover_vertice(G, node_data['id'])
                elements = gerar_elementos_cytoscape(G)
            else:
                return elements, html.P("Nenhum vértice selecionado.")

        elif button_id == 'btn-add-edge':

            if G.number_of_nodes() == 0:
                return elements, html.P("Nenhum grafo carregado.")
            
            if len(selected_nodes) == 1:
                # Caso o mesmo nó seja clicado duas vezes, force a criação do auto-loop
                source = selected_nodes[0]['id']
                target = source  # Auto-loop (source == target)
                
                adicionar_aresta(G, source, target)
                elements = gerar_elementos_cytoscape(G)

            elif len(selected_nodes) == 2:
                source = selected_nodes[0]['id']
                target = selected_nodes[1]['id']
                
                # Adiciona a aresta normalmente, seja entre dois nós diferentes ou iguais
                adicionar_aresta(G, source, target)
                elements = gerar_elementos_cytoscape(G)
            else:
                return elements, html.P("Selecione um (auto-loop) ou dois vértices para adicionar uma aresta.")

        elif button_id == 'remove-edge-btn':
            if selected_edges:
                for edge_data in selected_edges:
                    source = edge_data['source']
                    target = edge_data['target']
                    if G.has_edge(source, target):
                        G.remove_edge(source, target)
                        grafo_atualizado = True
            else:
                return dash.no_update, html.P("Nenhuma aresta selecionada.")

        elif button_id == 'btn-add-weight':

            if G.number_of_nodes() == 0:
                return elements, html.P("Nenhum grafo carregado.") 

            if selected_edges and add_edge_weight is not None:
                weight = float(add_edge_weight)
                if not ponderado:
                    ponderado = True
                    for edge in G.edges():
                        G[edge[0]][edge[1]]['weight'] = 1.0
                for edge_data in selected_edges:
                    G[edge_data['source']][edge_data['target']]['weight'] = weight
                elements = gerar_elementos_cytoscape(G)
            else:
                return elements, html.P("Nenhuma aresta selecionada ou peso não fornecido.")

        elif button_id == 'btn-bfs':

            if G.number_of_nodes() == 0:
                return elements, html.P("Nenhum grafo carregado.")

            if selected_nodes is None or len(selected_nodes) != 1:
                return elements, html.P("Selecione exatamente um nó para iniciar a busca BFS.")
            
            start_node = selected_nodes[0]['id']
            bfs_result = list(nx.bfs_edges(G, source=start_node))
            bfs_nodes = set([start_node] + [node for edge in bfs_result for node in edge])  # Coleta todos os nós visitados
            elements = gerar_elementos_cytoscape(G)
            
            # Reset color for all edges and nodes
            for element in elements:
                if 'data' in element:
                    if 'source' in element['data'] and 'target' in element['data']:
                        element['style'] = element.get('style', {})
                        element['style']['line-color'] = '#252525'  # Cor padrão
                    elif 'id' in element['data']:  # Assumindo que a identificação do nó está em 'id'
                        element['style'] = element.get('style', {})
                        element['style']['background-color'] = '#FFFFFF'  # Cor padrão para nós
            
            
            # Destaque o caminho percorrido e os nós visitados
            for u, v in bfs_result:
                for edge in elements:
                    if 'data' in edge and 'source' in edge['data'] and 'target' in edge['data']:
                        if edge['data']['source'] == u and edge['data']['target'] == v:
                            edge['style'] = edge.get('style', {})
                            edge['style']['line-color'] = 'red'  # Cor para destacar o caminho BFS
            
            adjacency_list = [
                html.P(
                    children=[
                        html.B(sorted(node)),  # Vértice em negrito
                        " -> ",
                        ', '.join(map(str, sorted(neighbors)))  # Ordena os vizinhos em ordem crescente
                    ],
                    style={'margin': '0', 'padding': '0'}  # Remove margens e espaçamentos
                ) for node, neighbors in nx.to_dict_of_lists(G).items()
            ]

            info = [
                html.P(f"Número de Vértices: ", style={'display': 'inline'}),
                html.B(f"{len(G.nodes)}", style={'display': 'inline'}),
                html.Br(),
                html.P(f"Número de Arestas: ", style={'display': 'inline'}),
                html.B(f"{len(G.edges)}", style={'display': 'inline'}),
                html.Br(),
                html.P(f"Ponderado: ", style={'display': 'inline'}),
                html.B(f"{'Sim' if ponderado else 'Não'}", style={'display': 'inline'}),
                html.Br(),
                html.P(f"Orientado: ", style={'display': 'inline'}),
                html.B(f"{'Sim' if orientado else 'Não'}", style={'display': 'inline'}),
                html.Br(),
                html.Br(),
                html.P(f"Lista de Adjacência: "),
                *adjacency_list,  # Exibindo a lista de adjacência formatada
                html.Br(),
                html.P(f"Resultado BFS a partir do nó: ", style={'display': 'inline'}),
                html.B(f"'{start_node}': {bfs_result}", style={'display': 'inline'}),
            ] 
            return elements, info

        elif button_id == 'btn-dfs':

            if G.number_of_nodes() == 0:
                return elements, html.P("Nenhum grafo carregado.")

            if selected_nodes is None or len(selected_nodes) != 1:
                return elements, html.P("Selecione exatamente um nó para iniciar a busca DFS.")
            
            start_node = selected_nodes[0]['id']
            dfs_result = list(nx.dfs_edges(G, source=start_node))
            dfs_nodes = set([start_node] + [node for edge in dfs_result for node in edge])  # Coleta todos os nós visitados
            elements = gerar_elementos_cytoscape(G)
            
            # Reset color for all edges and nodes
            for element in elements:
                if 'data' in element:
                    if 'source' in element['data'] and 'target' in element['data']:
                        element['style'] = element.get('style', {})
                        element['style']['line-color'] = '#252525'  # Cor padrão
                    elif 'id' in element['data']:  # Assumindo que a identificação do nó está em 'id'
                        element['style'] = element.get('style', {})
                        element['style']['background-color'] = '#FFFFFF'  # Cor padrão para nós
            
            # Destaque o caminho percorrido e os nós visitados
            for u, v in dfs_result:
                for edge in elements:
                    if 'data' in edge and 'source' in edge['data'] and 'target' in edge['data']:
                        if edge['data']['source'] == u and edge['data']['target'] == v:
                            edge['style'] = edge.get('style', {})
                            edge['style']['line-color'] = 'blue'  # Cor para destacar o caminho DFS

            adjacency_list = [
                html.P(
                    children=[
                        html.B(sorted(node)),  # Vértice em negrito
                        " -> ",
                        ', '.join(map(str, sorted(neighbors)))  # Ordena os vizinhos em ordem crescente
                    ],
                    style={'margin': '0', 'padding': '0'}  # Remove margens e espaçamentos
                ) for node, neighbors in nx.to_dict_of_lists(G).items()
            ]

            info = [
                html.P(f"Número de Vértices: ", style={'display': 'inline'}),
                html.B(f"{len(G.nodes)}", style={'display': 'inline'}),
                html.Br(),
                html.P(f"Número de Arestas: ", style={'display': 'inline'}),
                html.B(f"{len(G.edges)}", style={'display': 'inline'}),
                html.Br(),
                html.P(f"Ponderado: ", style={'display': 'inline'}),
                html.B(f"{'Sim' if ponderado else 'Não'}", style={'display': 'inline'}),
                html.Br(),
                html.P(f"Orientado: ", style={'display': 'inline'}),
                html.B(f"{'Sim' if orientado else 'Não'}", style={'display': 'inline'}),
                html.Br(),
                html.Br(),
                html.P(f"Lista de Adjacência: "),
                *adjacency_list,  # Exibindo a lista de adjacência formatada
                html.Br(),
                html.P(f"Resultado DFS a partir do nó: ", style={'display': 'inline'}),
                html.B(f"'{start_node}': {dfs_result}", style={'display': 'inline'}),
            ] 
            return elements, info

        elif button_id == 'btn-to-directed':

            if G.number_of_nodes() == 0:
                return elements, html.P("Nenhum grafo carregado.")

            if len(G.edges) <= 0:
                return elements, html.P("Número de arestas insuficiente para converter.")

            if G.is_directed():
                return elements, html.P("O grafo já é orientado.")
            
            G_dir = nx.DiGraph()
            for u, v, data in G.edges(data=True):
                G_dir.add_edge(u, v, **data)  # Mantém a direção das arestas conforme a entrada original
            
            G = G_dir
            orientado = True
            elements = gerar_elementos_cytoscape(G)

        elif button_id == 'btn-to-undirected':

            if G.number_of_nodes() == 0:
                return elements, html.P("Nenhum grafo carregado.")

            if G.is_directed():
                G = nx.Graph(G)  
                orientado = False
                elements = gerar_elementos_cytoscape(G)
            else:
                return elements, html.P("O grafo já é não-orientado.")

        elif button_id == 'btn-make-weighted':

            if G.number_of_nodes() == 0:
                return elements, html.P("Nenhum grafo carregado.")

            if ponderado == True:
                return elements, html.P("O grafo já é ponderado.")

            for u, v in G.edges():
                G[u][v]['weight'] = G[u][v].get('weight', 1.0)
            ponderado = True
            elements = gerar_elementos_cytoscape(G)

        elif button_id == 'btn-make-unweighted':

            if G.number_of_nodes() == 0:
                return elements, html.P("Nenhum grafo carregado.")

            if ponderado == False:
                return elements, html.P("O grafo já é não-ponderado.")

            for u, v in G.edges():
                G[u][v].pop('weight', None)  # Remove o atributo 'weight' se existir
            ponderado = False
            elements = gerar_elementos_cytoscape(G)

        elif button_id == 'refresh-button':
            if G.number_of_nodes() == 0:
                return elements, html.P("Nenhum grafo carregado.")
    
            elements = gerar_elementos_cytoscape(G)

        adjacency_list = [
            html.P(
                children=[
                    html.B(sorted(node)),  # Vértice em negrito
                    " -> ",
                    ', '.join(map(str, sorted(neighbors)))  # Ordena os vizinhos em ordem crescente
                ],
                style={'margin': '0', 'padding': '0'}  # Remove margens e espaçamentos
            ) for node, neighbors in nx.to_dict_of_lists(G).items()
        ]

        info = [
            html.P(f"Número de Vértices: ", style={'display': 'inline'}),
            html.B(f"{len(G.nodes)}", style={'display': 'inline'}),
            html.Br(),
            html.P(f"Número de Arestas: ", style={'display': 'inline'}),
            html.B(f"{len(G.edges)}", style={'display': 'inline'}),
            html.Br(),
            html.P(f"Ponderado: ", style={'display': 'inline'}),
            html.B(f"{'Sim' if ponderado else 'Não'}", style={'display': 'inline'}),
            html.Br(),
            html.P(f"Orientado: ", style={'display': 'inline'}),
            html.B(f"{'Sim' if orientado else 'Não'}", style={'display': 'inline'}),
            html.Br(),
            html.Br(),
            html.P(f"Lista de Adjacência: "),
            *adjacency_list,  # Exibindo a lista de adjacência formatada
        ]
        
        return elements, info
    
    except Exception as e:
        return elements, html.P(f"Erro: {str(e)}")


if __name__ == '__main__':
    app.run_server(debug=True, port=8052)