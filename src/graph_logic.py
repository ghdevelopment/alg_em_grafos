import os
import networkx as nx

def carregar_grafo_txt(arquivo):
    G = nx.DiGraph()
    ponderado = False
    orientado = True

    try:
        with open(arquivo, 'r') as f:
            linhas = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

    if not linhas:
        return G, ponderado, orientado

    try:
        num_vertices, num_arestas = map(int, linhas[0].split())
    except ValueError:
        raise ValueError("Formato de arquivo inválido.")

    for linha in linhas[1:]:
        aresta = linha.split()
        if len(aresta) == 2:
            G.add_edge(aresta[0], aresta[1])
        elif len(aresta) == 3:
            G.add_edge(aresta[0], aresta[1], weight=float(aresta[2]))
            ponderado = True
        else:
            raise ValueError("Formato de aresta inválido.")

    # Verificar se o grafo é direcionado (DiGraph)
    if isinstance(G, nx.DiGraph):
        orientado = True

    return G, ponderado, orientado

def salvar_grafo_txt(G, filename='graph.txt'):
    if not isinstance(G, (nx.Graph, nx.DiGraph)):
        raise ValueError("O objeto fornecido não é um grafo válido do NetworkX.")
    
    dir_name = os.path.dirname(filename)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)

    with open(filename, 'w') as f:
        try:
            f.write(f"{G.number_of_nodes()} {G.number_of_edges()}\n")
            for source, target, data in G.edges(data=True):
                if 'weight' in data:
                    f.write(f"{source} {target} {float(data['weight'])}\n")
                else:
                    f.write(f"{source} {target}\n")
        except Exception as e:
            raise IOError(f"Erro ao salvar o grafo no arquivo '{filename}': {e}")

def adicionar_aresta(G, source, target, weight=None):
    # Verifica se os vértices existem no grafo
    if source not in G.nodes or target not in G.nodes:
        raise ValueError("Um ou ambos os vértices não existem no grafo.")
    
    # Adiciona a aresta, mesmo se for um auto-loop (source == target)
    if weight is not None:
        G.add_edge(source, target, weight=float(weight))
    else:
        G.add_edge(source, target)
    
    # Atualiza as variáveis globais ponderado e orientado
    global ponderado, orientado
    ponderado = any('weight' in data for _, _, data in G.edges(data=True))
    orientado = isinstance(G, nx.DiGraph)

def remover_aresta(G, source, target):
    if not G.has_edge(source, target):
        raise ValueError("Aresta não existe.")
    G.remove_edge(source, target)
    
    # Verifica se ainda existem arestas ponderadas
    global ponderado
    ponderado = any('weight' in data for _, _, data in G.edges(data=True))

def remover_vertice(G, node):
    if node not in G.nodes:
        raise ValueError("Vértice não existe.")
    G.remove_node(node)


def gerar_elementos_cytoscape(G):
    elements = []

    # Adicionar os nós
    for node in G.nodes():
        elements.append({
            'data': {'id': str(node), 'label': str(node)},
            'classes': 'node'  # Classe para aplicar estilos gerais do stylesheet
        })

    # Adicionar as arestas
    for edge in G.edges(data=True):
        source, target, data = edge
        label = data.get('weight', '')

        # Defina a forma da seta dependendo se o grafo é direcionado ou não
        target_arrow_shape = 'triangle' if G.is_directed() else 'none'

        elements.append({
            'data': {
                'source': str(source),
                'target': str(target),
                'label': str(label) if label else ''
            },
            'classes': 'edge',  # Classe para aplicar estilos gerais do stylesheet
            'style': {
                'target-arrow-shape': target_arrow_shape, # Define a seta condicionalmente
                'arrow-scale': 1.2,  
            }
        })

    return elements



