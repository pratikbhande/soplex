#!/usr/bin/env python3
"""
Fixed Soplex Graph Visualizer
Handles different graph JSON structures properly
"""

import json
import networkx as nx
import plotly.graph_objects as go
import plotly.utils
from pathlib import Path

class FixedSoplexGraphVisualizer:
    def __init__(self):
        self.node_colors = {
            'llm': '#ff6b6b',
            'code': '#4ecdc4',
            'api': '#ffd93d',
            'branch': '#a8a8b3',
            'end': '#48bb78',
            'start': '#667eea',
            'unknown': '#888888'
        }
        self.node_icons = {
            'llm': '🧠',
            'code': '⚡',
            'api': '🔌',
            'branch': '🔀',
            'end': '🎯',
            'start': '🚀',
            'unknown': '⭕'
        }

    def load_compiled_graph(self, graph_file_path):
        """Load compiled soplex graph from JSON file"""
        try:
            with open(graph_file_path, 'r') as f:
                data = json.load(f)
            print(f"Loaded graph data type: {type(data)}")
            print(f"Graph keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            return data
        except Exception as e:
            print(f"Error loading graph: {e}")
            return None

    def create_networkx_graph(self, soplex_graph):
        """Convert soplex graph to NetworkX format - handles multiple structures"""
        G = nx.DiGraph()

        print(f"Processing graph structure: {type(soplex_graph)}")

        # Handle different possible structures
        nodes_data = None
        edges_data = None

        if isinstance(soplex_graph, dict):
            # Structure 1: {nodes: {...}, edges: [...]}
            if 'nodes' in soplex_graph:
                nodes_data = soplex_graph['nodes']
                edges_data = soplex_graph.get('edges', [])
            # Structure 2: {node_id: node_data, ...} (flat structure)
            else:
                nodes_data = soplex_graph
                edges_data = []
        elif isinstance(soplex_graph, list):
            # Structure 3: [node1, node2, ...] (list of nodes)
            nodes_data = {f"node_{i}": node for i, node in enumerate(soplex_graph)}
            edges_data = []

        # Process nodes
        if nodes_data:
            if isinstance(nodes_data, dict):
                for node_id, node_data in nodes_data.items():
                    self._add_node_to_graph(G, node_id, node_data)
            elif isinstance(nodes_data, list):
                for i, node_data in enumerate(nodes_data):
                    node_id = node_data.get('id', f'node_{i}')
                    self._add_node_to_graph(G, node_id, node_data)

        # Process edges
        if edges_data and isinstance(edges_data, list):
            for edge in edges_data:
                self._add_edge_to_graph(G, edge)

        # If no edges found, create a simple chain
        if len(G.edges()) == 0 and len(G.nodes()) > 1:
            nodes = list(G.nodes())
            for i in range(len(nodes) - 1):
                G.add_edge(nodes[i], nodes[i + 1])

        print(f"Created graph with {len(G.nodes())} nodes and {len(G.edges())} edges")
        return G

    def _add_node_to_graph(self, G, node_id, node_data):
        """Add a node to the NetworkX graph"""
        if isinstance(node_data, dict):
            node_type = node_data.get('type', 'unknown').lower()
            action = node_data.get('action', node_data.get('name', ''))
        else:
            node_type = 'unknown'
            action = str(node_data)

        icon = self.node_icons.get(node_type, '⭕')

        G.add_node(node_id,
                  type=node_type,
                  action=action,
                  label=f"{icon} {node_id}")

    def _add_edge_to_graph(self, G, edge):
        """Add an edge to the NetworkX graph"""
        if isinstance(edge, dict):
            from_node = edge.get('from_node', edge.get('from', edge.get('source')))
            to_node = edge.get('to_node', edge.get('to', edge.get('target')))
            condition = edge.get('condition', '')
        elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
            from_node, to_node = edge[0], edge[1]
            condition = edge[2] if len(edge) > 2 else ''
        else:
            return

        if from_node and to_node:
            G.add_edge(from_node, to_node, condition=condition)

    def generate_plotly_graph(self, graph_file_path):
        """Generate interactive Plotly graph visualization"""
        soplex_graph = self.load_compiled_graph(graph_file_path)
        if not soplex_graph:
            return None

        G = self.create_networkx_graph(soplex_graph)

        if len(G.nodes()) == 0:
            # Create a sample graph if none found
            G.add_node("start", type="start", action="Begin Process")
            G.add_node("process", type="code", action="Process Data")
            G.add_node("end", type="end", action="Complete")
            G.add_edge("start", "process")
            G.add_edge("process", "end")

        # Create layout
        try:
            pos = nx.spring_layout(G, k=2, iterations=50)
        except:
            pos = nx.random_layout(G)

        # Create edges for plotly
        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=3, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        # Create nodes for plotly
        node_x, node_y, node_text, node_colors, node_info = [], [], [], [], []

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            node_data = G.nodes[node]
            node_type = node_data.get('type', 'unknown')
            color = self.node_colors.get(node_type, '#888888')
            node_colors.append(color)

            # Node label
            icon = self.node_icons.get(node_type, '⭕')
            label = f"{icon}<br>{node}"
            node_text.append(label)

            # Hover info
            action = node_data.get('action', 'No action specified')
            info = f"<b>{node}</b><br>Type: {node_type.upper()}<br>Action: {action}"
            node_info.append(info)

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            textfont=dict(size=12, color="white"),
            hovertext=node_info,
            marker=dict(
                size=60,
                color=node_colors,
                line=dict(width=3, color='white')
            )
        )

        # Create figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=dict(
                    text='Soplex Execution Graph',
                    x=0.5,
                    font=dict(size=24, color='white')
                ),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    text="Click and drag nodes • Hover for details",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002,
                    xanchor='left', yanchor='bottom',
                    font=dict(color='white', size=14)
                ) ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
        )

        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def get_graph_stats(self, graph_file_path):
        """Get statistics about the graph"""
        soplex_graph = self.load_compiled_graph(graph_file_path)
        if not soplex_graph:
            return {}

        G = self.create_networkx_graph(soplex_graph)

        # Count node types
        node_type_counts = {}
        for node in G.nodes():
            node_type = G.nodes[node].get('type', 'unknown')
            node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1

        # Execution flow
        flow_pattern = []
        try:
            for node in list(G.nodes())[:8]:  # First 8 nodes
                node_type = G.nodes[node].get('type', 'unknown')
                icon = self.node_icons.get(node_type, '⭕')
                flow_pattern.append(f"{icon} {node}")
        except:
            pass

        return {
            'total_nodes': len(G.nodes()),
            'total_edges': len(G.edges()),
            'node_types': node_type_counts,
            'execution_flow': flow_pattern,
            'cost_optimization': self._analyze_optimization(node_type_counts)
        }

    def _analyze_optimization(self, node_type_counts):
        """Analyze cost optimization"""
        llm_nodes = node_type_counts.get('llm', 0)
        code_nodes = node_type_counts.get('code', 0) + node_type_counts.get('api', 0)
        total_nodes = sum(node_type_counts.values())

        if total_nodes == 0:
            return {"optimization_level": "Unknown"}

        code_percentage = (code_nodes / total_nodes) * 100

        return {
            'llm_percentage': (llm_nodes / total_nodes) * 100,
            'code_percentage': code_percentage,
            'optimization_level': 'High' if code_percentage > 60 else 'Medium' if code_percentage > 30 else 'Low'
        }