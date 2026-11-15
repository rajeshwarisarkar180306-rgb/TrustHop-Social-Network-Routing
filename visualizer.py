from pyvis.network import Network
import networkx as nx
import tempfile
import json

PALETTE = ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F", "#EDC948", "#B07AA1", "#FF9DA7"]

def render_graph(G, active_path=None, source=None, target=None):
    net = Network(height="520px", width="100%", bgcolor="#0E1117", font_color="white")
    pos = nx.spring_layout(G, seed=42)

    for node, data in G.nodes(data=True):
        comm_color = PALETTE[data["community"] % len(PALETTE)]
        color = comm_color if data["online"] else "#3A3A3A"
        shape = "dot"
        size = 14 + (data["betweenness"] * 120)
        label = f"N{node}"

        if data["malicious"]:
            color = "#8B0000"
            shape = "box"
            label = f"N{node} [MALICIOUS]"
        elif data["congested"]:
            color = "#FF9900"
            shape = "triangle"

        if node == source:
            color = "#00FF88"
            shape = "star"
            label = f"SRC ({node})"
            size = 26
        elif node == target:
            color = "#FF3366"
            shape = "star"
            label = f"DST ({node})"
            size = 26

        status = "Online"
        if not data["online"]: status = "OFFLINE"
        elif data["malicious"]: status = "BLACK-HOLE ATTACKER"
        elif data["congested"]: status = "CONGESTED"

        title = f"Node {node} [{status}]\nCommunity: {data['community']}\nCentrality: {data['betweenness']:.3f}"
        x_coord = float(pos[node][0] * 450)
        y_coord = float(pos[node][1] * 450)

        net.add_node(node, label=label, color=color, size=size, title=title, shape=shape, x=x_coord, y=y_coord, physics=False)

    for u, v, data in G.edges(data=True):
        edge_id = f"{u}-{v}"
        net.add_edge(u, v, id=edge_id, color="#2C313A", width=1, title=f"Trust: {data['trust']}")

    html_string = net.generate_html()

    # Inject client-side JS animation so it highlights smoothly without flickering
    if active_path and len(active_path) > 1:
        path_edges = []
        for i in range(len(active_path) - 1):
            u, v = active_path[i], active_path[i+1]
            path_edges.append(f"{u}-{v}")
            path_edges.append(f"{v}-{u}")

        path_json = json.dumps(path_edges)
        
        js_injection = f"""
        <script>
        setTimeout(function() {{
            if (typeof edges !== 'undefined' && typeof network !== 'undefined') {{
                let pathEdges = {path_json};
                let idx = 0;
                let interval = setInterval(function() {{
                    if (idx < pathEdges.length) {{
                        let edgeId = pathEdges[idx];
                        try {{
                            edges.update({{id: edgeId, color: {{color: '#00E5FF', highlight: '#00E5FF'}}, width: 4}});
                        }} catch(e) {{}}
                        idx++;
                    }} else {{
                        clearInterval(interval);
                    }}
                }}, 500);
            }}
        }}, 400);
        </script>
        """
        html_string = html_string.replace("</body>", js_injection + "</body>")

    return html_string