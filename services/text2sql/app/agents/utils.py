import os
import webbrowser
from pathlib import Path


def visualize_graph(graph, filename="workflow_graph.png"):
    """Generate and display the workflow graph visualization"""
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Save the graph as PNG
    graph_path = output_dir / filename

    # Check if it's a compiled graph or a StateGraph
    if hasattr(graph, "get_graph"):
        graph_image = graph.get_graph().draw_mermaid_png()
    else:
        # For non-compiled StateGraph
        graph_image = graph.draw_mermaid_png()

    with open(graph_path, "wb") as f:
        f.write(graph_image)

    # Open the image in the default viewer
    abs_path = os.path.abspath(graph_path)
    print(f"Graph visualization saved to: {abs_path}")
    webbrowser.open(f"file://{abs_path}")
