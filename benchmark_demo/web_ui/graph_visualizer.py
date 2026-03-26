#!/usr/bin/env python3
"""
Soplex Graph Visualizer
Shows the actual compiled graph structure with nodes and edges
"""

import json
import networkx as nx
import plotly.graph_objects as go
import plotly.utils
from pathlib import Path

class SoplexGraphVisualizer:
    def __init__(self):
        self.node_colors = {
            'llm': '#ff6b6b',
            'code': '#4ecdc4',
            'api': '#ffd93d',
            'branch': '#a8a8b3',
            'end': '#48bb78',
            'start': '#667eea'
        }
        self.node_icons = {
            'llm': '🧠',
            'code': '⚡',
            'api': '🔌',
            'branch': '🔀',
            'end': '🎯',
            'start': '🚀'
        }

    def load_compiled_graph(self, graph_file_path):
        """Load compiled soplex graph from JSON file"""
        try:
            with open(graph_file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading graph: {e}")
            return None

    def create_networkx_graph(self, soplex_graph):
        """Convert soplex graph to NetworkX format"""
        G = nx.DiGraph()

        # Add nodes
        if 'nodes' in soplex_graph:
            for node_id, node_data in soplex_graph['nodes'].items():
                node_type = node_data.get('type', 'unknown').lower()
                G.add_node(node_id,
                          type=node_type,
                          action=node_data.get('action', ''),
                          label=f"{self.node_icons.get(node_type, '⭕')} {node_id}")

        # Add edges
        if 'edges' in soplex_graph:
            for edge in soplex_graph['edges']:
                from_node = edge.get('from_node', edge.get('from'))
                to_node = edge.get('to_node', edge.get('to'))
                condition = edge.get('condition', '')

                if from_node and to_node:
                    G.add_edge(from_node, to_node, condition=condition)

        return G

    def generate_plotly_graph(self, graph_file_path):
        """Generate interactive Plotly graph visualization"""
        soplex_graph = self.load_compiled_graph(graph_file_path)
        if not soplex_graph:
            return None

        G = self.create_networkx_graph(soplex_graph)

        # Use hierarchical layout
        try:
            pos = nx.spring_layout(G, k=3, iterations=50)
        except:
            pos = nx.random_layout(G)

        # Create edges
        edge_x = []
        edge_y = []
        edge_info = []

        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

            condition = G[edge[0]][edge[1]].get('condition', '')
            edge_info.append(f"{edge[0]} → {edge[1]}" + (f"<br>Condition: {condition}" if condition else ""))

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        # Create nodes
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_info = []

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            node_data = G.nodes[node]
            node_type = node_data.get('type', 'unknown')
            node_colors.append(self.node_colors.get(node_type, '#888'))

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
            textfont=dict(size=10, color="white"),
            hovertext=node_info,
            marker=dict(
                size=50,
                color=node_colors,
                line=dict(width=2, color='white')
            )
        )

        # Create figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=dict(
                    text='Soplex Execution Graph',
                    x=0.5,
                    font=dict(size=20, color='white')
                ),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    text="Interactive Graph: Hover over nodes for details",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002,
                    xanchor='left', yanchor='bottom',
                    font=dict(color='white', size=12)
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

        return {
            'total_nodes': len(G.nodes()),
            'total_edges': len(G.edges()),
            'node_types': node_type_counts,
            'execution_flow': self._get_execution_flow(G),
            'cost_optimization': self._analyze_cost_optimization(node_type_counts)
        }

    def _get_execution_flow(self, G):
        """Analyze execution flow pattern"""
        flow_pattern = []
        try:
            # Simple topological sort for flow
            for node in nx.topological_sort(G):
                node_type = G.nodes[node].get('type', 'unknown')
                icon = self.node_icons.get(node_type, '⭕')
                flow_pattern.append(f"{icon} {node}")
        except:
            # If graph has cycles, just list nodes
            for node in G.nodes():
                node_type = G.nodes[node].get('type', 'unknown')
                icon = self.node_icons.get(node_type, '⭕')
                flow_pattern.append(f"{icon} {node}")

        return flow_pattern[:10]  # First 10 steps

    def _analyze_cost_optimization(self, node_type_counts):
        """Analyze cost optimization potential"""
        llm_nodes = node_type_counts.get('llm', 0)
        code_nodes = node_type_counts.get('code', 0) + node_type_counts.get('api', 0)
        total_nodes = sum(node_type_counts.values())

        if total_nodes == 0:
            return {}

        cost_efficiency = (code_nodes / total_nodes) * 100

        return {
            'llm_percentage': (llm_nodes / total_nodes) * 100,
            'code_percentage': (code_nodes / total_nodes) * 100,
            'cost_efficiency_score': cost_efficiency,
            'optimization_level': 'High' if cost_efficiency > 60 else 'Medium' if cost_efficiency > 30 else 'Low'
        }