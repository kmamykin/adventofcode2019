import networkx as nx

# print(nx.algorithms.tree.recognition.is_tree(G))
# print(G.number_of_nodes())
# print(G.number_of_edges())
# print(list(G.nodes))
# print(list(G.edges))
# print(list(G.successors('COM')))
# print(list(G.predecessors('COM')))
# print(list(G.predecessors('1Z6')))
# Gr = G.reverse(copy=True)
# print(list(Gr.successors('COM')))

def graph_from(edges):
    G = nx.DiGraph()
    G.add_edges_from(edges)
    return G


def graph_from_map(map_text):
    input = [s.strip().split(")") for s in map_text.splitlines() if len(s.strip())>0]
    G = nx.DiGraph()
    [G.add_edge(e[1], e[0]) for e in input]
    return G


def all_successors(G, nodes):
    successors = []
    for node in nodes:
        successors += G.successors(node)
    return successors


def number_of_orbits(G_orbits):
    G = G_orbits.reverse(copy=True)
    orbits = 0
    level = 1
    nodes_at_level = all_successors(G, ['COM'])
    orbits += level * len(nodes_at_level)
    while len(nodes_at_level) > 0:
        level += 1
        nodes_at_level = all_successors(G, nodes_at_level)
        orbits += level * len(nodes_at_level)
    return orbits


def number_of_orbital_transfers(G_orbits, from_node, to_node):
    source = list(G_orbits.successors(from_node))[0]
    target = list(G_orbits.successors(to_node))[0]
    G = G_orbits.to_undirected()
    path = nx.shortest_path(G, source, target)
    return len(path) - 1


assert number_of_orbits(graph_from([('1', 'COM')])) == 1
g1 = """
COM)B
B)C
C)D
D)E
E)F
B)G
G)H
D)I
E)J
J)K
K)L
"""
assert number_of_orbits(graph_from_map(g1)) == 42
print(number_of_orbits(graph_from_map(open("day06/input.txt").read())))

g2 = """
COM)B
B)C
C)D
D)E
E)F
B)G
G)H
D)I
E)J
J)K
K)L
K)YOU
I)SAN
"""

assert number_of_orbital_transfers(graph_from_map(g2), 'YOU', 'SAN') == 4
print(number_of_orbital_transfers(graph_from_map(open("day06/input2.txt").read()), 'YOU', 'SAN'))