#!/usr/bin/env python3
"""
Soplex AI Demo Web UI
Fancy interface for comparing traditional vs soplex approaches
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
import json
import subprocess
import threading
import time
import os
from pathlib import Path
import plotly.graph_objs as go
import plotly.utils
from fixed_graph_visualizer import FixedSoplexGraphVisualizer

app = Flask(__name__)
graph_visualizer = FixedSoplexGraphVisualizer()

# Global variables to store demo results
demo_results = {
    'traditional': None,
    'soplex': None,
    'running': False,
    'current_step': None,
    'logs': []
}

def run_traditional_demo():
    """Run traditional approach and capture results"""
    demo_results['current_step'] = 'Running Traditional Approach'
    demo_results['logs'].append('🏛️ Starting Traditional Pure-LLM Approach...')

    try:
        result = subprocess.run([
            'python3', '../traditional_approach/run_traditional.py'
        ], capture_output=True, text=True, cwd=Path(__file__).parent)

        # Load results
        results_file = Path(__file__).parent.parent / 'results' / 'traditional_results.json'
        if results_file.exists():
            with open(results_file, 'r') as f:
                demo_results['traditional'] = json.load(f)
            demo_results['logs'].append('✅ Traditional approach completed')
        else:
            demo_results['logs'].append('❌ Traditional results not found')

    except Exception as e:
        demo_results['logs'].append(f'❌ Traditional demo failed: {str(e)}')

def run_soplex_demo():
    """Run soplex approach and capture results"""
    demo_results['current_step'] = 'Running Soplex Hybrid Approach'
    demo_results['logs'].append('🚀 Starting Soplex Hybrid Approach...')

    try:
        # Activate venv and run soplex demo
        result = subprocess.run([
            'bash', '-c', 'source ../../venv/bin/activate && python3 ../soplex_approach/run_soplex.py'
        ], capture_output=True, text=True, cwd=Path(__file__).parent)

        # Load results
        results_file = Path(__file__).parent.parent / 'results' / 'soplex_results.json'
        if results_file.exists():
            with open(results_file, 'r') as f:
                demo_results['soplex'] = json.load(f)
            demo_results['logs'].append('✅ Soplex approach completed')
        else:
            demo_results['logs'].append('❌ Soplex results not found')

    except Exception as e:
        demo_results['logs'].append(f'❌ Soplex demo failed: {str(e)}')

def run_comparison_demo():
    """Run both demos in sequence"""
    demo_results['running'] = True
    demo_results['logs'] = []
    demo_results['traditional'] = None
    demo_results['soplex'] = None

    # Run traditional first
    run_traditional_demo()
    time.sleep(1)

    # Run soplex second
    run_soplex_demo()

    demo_results['current_step'] = 'Comparison Complete'
    demo_results['running'] = False

@app.route('/')
def index():
    """Main demo page"""
    return render_template('index.html')

@app.route('/start_comparison', methods=['POST'])
def start_comparison():
    """Start the comparison demo"""
    if not demo_results['running']:
        # Run demo in background thread
        thread = threading.Thread(target=run_comparison_demo)
        thread.daemon = True
        thread.start()
        return jsonify({'status': 'started'})
    else:
        return jsonify({'status': 'already_running'})

@app.route('/demo_status')
def demo_status():
    """Get current demo status and results"""
    return jsonify({
        'running': demo_results['running'],
        'current_step': demo_results['current_step'],
        'logs': demo_results['logs'][-10:],  # Last 10 logs
        'traditional': demo_results['traditional'],
        'soplex': demo_results['soplex']
    })

@app.route('/generate_graphs')
def generate_graphs():
    """Generate comparison graphs"""
    if not demo_results['traditional'] or not demo_results['soplex']:
        return jsonify({'error': 'No data available for graphs'})

    trad = demo_results['traditional']
    soplex = demo_results['soplex']

    # Cost comparison chart
    cost_fig = go.Figure(data=[
        go.Bar(name='Traditional', x=['Total Cost'], y=[trad['total_cost']], marker_color='#ff6b6b'),
        go.Bar(name='Soplex', x=['Total Cost'], y=[soplex['total_cost']], marker_color='#4ecdc4')
    ])
    cost_fig.update_layout(
        title='Cost Comparison: Traditional vs Soplex',
        yaxis_title='Cost ($)',
        template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    # LLM Calls comparison
    calls_fig = go.Figure(data=[
        go.Bar(name='Traditional', x=['LLM Calls'], y=[trad['total_llm_calls']], marker_color='#ff6b6b'),
        go.Bar(name='Soplex', x=['LLM Calls'], y=[soplex['total_llm_calls']], marker_color='#4ecdc4')
    ])
    calls_fig.update_layout(
        title='LLM Calls: Traditional vs Soplex',
        yaxis_title='Number of Calls',
        template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    # Execution time comparison
    time_fig = go.Figure(data=[
        go.Bar(name='Traditional', x=['Execution Time'], y=[trad['total_time']], marker_color='#ff6b6b'),
        go.Bar(name='Soplex', x=['Execution Time'], y=[soplex['total_time']], marker_color='#4ecdc4')
    ])
    time_fig.update_layout(
        title='Execution Time: Traditional vs Soplex',
        yaxis_title='Time (seconds)',
        template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    # Calculate savings
    cost_savings = ((trad['total_cost'] - soplex['total_cost']) / trad['total_cost']) * 100
    time_savings = ((trad['total_time'] - soplex['total_time']) / trad['total_time']) * 100
    call_reduction = ((trad['total_llm_calls'] - soplex['total_llm_calls']) / trad['total_llm_calls']) * 100

    return jsonify({
        'cost_chart': json.dumps(cost_fig, cls=plotly.utils.PlotlyJSONEncoder),
        'calls_chart': json.dumps(calls_fig, cls=plotly.utils.PlotlyJSONEncoder),
        'time_chart': json.dumps(time_fig, cls=plotly.utils.PlotlyJSONEncoder),
        'metrics': {
            'cost_savings': round(cost_savings, 1),
            'time_savings': round(time_savings, 1),
            'call_reduction': round(call_reduction, 1),
            'traditional_cost': trad['total_cost'],
            'soplex_cost': soplex['total_cost'],
            'traditional_time': trad['total_time'],
            'soplex_time': soplex['total_time']
        }
    })

@app.route('/sops/<filename>')
def show_sop(filename):
    """Display SOP file content"""
    sop_path = Path(__file__).parent.parent / 'sops' / filename
    if sop_path.exists():
        with open(sop_path, 'r') as f:
            content = f.read()
        return jsonify({'content': content})
    return jsonify({'error': 'SOP file not found'})

@app.route('/graph_visualization')
def graph_visualization():
    """Generate interactive graph visualization"""
    # Look for compiled graph files
    compiled_dir = Path(__file__).parent.parent / 'compiled'
    graph_files = list(compiled_dir.glob('*.json'))

    if not graph_files:
        return jsonify({'error': 'No compiled graphs found. Run soplex compile first.'})

    # Use the first available graph file
    graph_file = graph_files[0]

    try:
        # Generate visualization
        graph_data = graph_visualizer.generate_plotly_graph(str(graph_file))
        stats = graph_visualizer.get_graph_stats(str(graph_file))

        return jsonify({
            'graph_data': graph_data,
            'stats': stats,
            'graph_file': graph_file.name
        })
    except Exception as e:
        return jsonify({'error': f'Failed to generate graph: {str(e)}'})

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Create results directory if it doesn't exist
    results_dir = Path(__file__).parent.parent / 'results'
    results_dir.mkdir(exist_ok=True)

    print("🚀 Starting Soplex AI Demo UI...")
    print("📱 Open your browser to: http://localhost:5000")
    print("🎬 Ready for demo recording!")

    app.run(host='0.0.0.0', port=5000, debug=True)