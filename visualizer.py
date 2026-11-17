from pyvis.network import Network
import networkx as nx
import json

# Removed red/coral/orange shades from community palette so only malicious/congested nodes use them
PALETTE = ["#4E79A7", "#76B7B2", "#59A14F", "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#8CD17D"]

def render_graph(G, active_path=None, source=None, target=None):
    net = Network(height="560px", width="100%", bgcolor="#0E1117", font_color="white")
    
    # Spread clusters out cleanly with zero overlap
    pos = nx.spring_layout(G, k=1.8, iterations=120, seed=42)

    for node, data in G.nodes(data=True):
        comm_color = PALETTE[data["community"] % len(PALETTE)]
        color = comm_color if data["online"] else "#3A3A3A"
        shape = "dot"
        size = 14 + (data["betweenness"] * 100)
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
            size = 24
        elif node == target:
            color = "#FF3366"
            shape = "star"
            label = f"DST ({node})"
            size = 24

        status = "Online"
        if not data["online"]:
            status = "OFFLINE"
        elif data["malicious"]:
            status = "BLACK-HOLE ATTACKER"
        elif data["congested"]:
            status = "CONGESTED"

        title = f"Node {node} [{status}]\nCommunity: {data['community']}\nCentrality: {data['betweenness']:.3f}"
        
        x_coord = float(pos[node][0] * 750)
        y_coord = float(pos[node][1] * 750)

        net.add_node(
            node,
            label=label,
            color=color,
            size=size,
            title=title,
            shape=shape,
            x=x_coord,
            y=y_coord,
            physics=False,
            font={"size": 14, "color": "white", "strokeWidth": 3, "strokeColor": "#0E1117"}
        )

    for u, v, data in G.edges(data=True):
        edge_id = f"{u}-{v}"
        net.add_edge(
            u,
            v,
            id=edge_id,
            color="#2C313A",
            width=1.2,
            smooth={"type": "curvedCW", "roundness": 0.12},
            title=f"Trust: {data['trust']}"
        )

    html_string = net.generate_html()

    # Determine which nodes the camera should automatically zoom & center on
    focus_nodes = []
    if active_path and len(active_path) > 0:
        focus_nodes = active_path
    else:
        if source is not None:
            focus_nodes.append(source)
        if target is not None:
            focus_nodes.append(target)

    focus_json = json.dumps(focus_nodes)

    path_edges = []
    if active_path and len(active_path) > 1:
        for i in range(len(active_path) - 1):
            u, v = active_path[i], active_path[i+1]
            path_edges.append(f"{u}-{v}")
            path_edges.append(f"{v}-{u}")
    path_json = json.dumps(path_edges)

    # Inject JS for automatic camera focus + smooth cyan route animation
    # Inject JS for reliable camera focus (local + cloud) + smooth cyan route animation
    js_injection = f"""
    <script>
    (function() {{
        let focusNodes = {focus_json};
        let pathEdges = {path_json};
        let hasFocused = false;

        function applyCameraFocus() {{
            if (typeof network !== 'undefined' && !hasFocused) {{
                hasFocused = true;
                if (focusNodes.length > 0) {{
                    network.fit({{
                        nodes: focusNodes,
                        animation: {{
                            duration: 750,
                            easingFunction: "easeInOutQuad"
                        }}
                    }});
                }} else {{
                    network.fit({{ animation: {{ duration: 500 }} }});
                }}
            }}
        }}

        function startRouteAnimation() {{
            if (typeof edges !== 'undefined' && pathEdges.length > 0) {{
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
                }}, 350);
            }}
        }}

        function initVisuals() {{
            if (typeof network !== 'undefined') {{
                network.once("afterDrawing", function() {{
                    setTimeout(applyCameraFocus, 150);
                }});
                // Fallback in case afterDrawing already fired
                setTimeout(applyCameraFocus, 600);
                setTimeout(startRouteAnimation, 500);
            }} else {{
                setTimeout(initVisuals, 150);
            }}
        }}

        initVisuals();
    }})();
    </script>
    """
    html_string = html_string.replace("</body>", js_injection + "</body>")

    return html_string