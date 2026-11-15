import networkx as nx
import random
import pandas as pd

def create_social_network(model_type="Small-World", num_nodes=60, failure_rate=0.0, congestion_rate=0.0, malicious_rate=0.0):
    if model_type == "Real-World (Karate Club)":
        G = nx.karate_club_graph()
        num_nodes = G.number_of_nodes()
    elif model_type == "Small-World":
        G = nx.watts_strogatz_graph(n=num_nodes, k=6, p=0.15, seed=42)
    else:
        G = nx.barabasi_albert_graph(n=num_nodes, m=3, seed=42)

    communities = nx.community.louvain_communities(G, seed=42)
    node_community = {}
    for comm_id, members in enumerate(communities):
        for node in members:
            node_community[node] = comm_id

    betweenness = nx.betweenness_centrality(G)
    degree = dict(G.degree())

    random.seed(42)
    sorted_nodes = sorted(G.nodes(), key=lambda n: betweenness[n], reverse=True)
    
    congested_count = int(num_nodes * congestion_rate)
    congested_set = set(sorted_nodes[:congested_count])
    
    # Ensure source and destination are never malicious or offline
    malicious_candidates = [n for n in G.nodes() if n not in [0, num_nodes-1]]
    malicious_count = int(num_nodes * malicious_rate)
    malicious_set = set(random.sample(malicious_candidates, min(malicious_count, len(malicious_candidates)))) if malicious_count > 0 else set()

    for node in G.nodes():
        G.nodes[node]["community"] = node_community.get(node, 0)
        G.nodes[node]["betweenness"] = betweenness[node]
        G.nodes[node]["degree"] = degree[node]
        # Keep source and target safe from random dropouts for a better demo experience
        if node in [0, num_nodes - 1]:
            G.nodes[node]["online"] = True
            G.nodes[node]["malicious"] = False
        else:
            G.nodes[node]["online"] = random.random() >= failure_rate
            G.nodes[node]["malicious"] = (node in malicious_set) and G.nodes[node]["online"]

        G.nodes[node]["congested"] = (node in congested_set) and G.nodes[node]["online"]

    for u, v in G.edges():
        if G.nodes[u]["community"] == G.nodes[v]["community"]:
            G.edges[u, v]["trust"] = round(random.uniform(0.80, 1.0), 2)
        else:
            G.edges[u, v]["trust"] = round(random.uniform(0.30, 0.70), 2)

    return G

def route_dijkstra(G, source, target):
    active_nodes = [n for n, d in G.nodes(data=True) if d["online"] and not d["malicious"]]
    if source not in active_nodes or target not in active_nodes:
        return None, "Source or Target is Offline/Malicious"
    
    subG = G.subgraph(active_nodes)
    try:
        path = nx.shortest_path(subG, source=source, target=target)
        for n in path[1:-1]:
            if G.nodes[n]["malicious"]:
                return None, "Intercepted by Black-Hole Node!"
        return path, "Delivered Successfully (Dijkstra)"
    except nx.NetworkXNoPath:
        return None, "No Valid Path (Network Partitioned)"

def route_social_aware(G, source, target, max_hops=40):
    if not G.nodes[source]["online"] or not G.nodes[target]["online"]:
        return None, "Source/Target Node is Offline"

    target_comm = G.nodes[target]["community"]
    current = source
    path = [current]
    visited = {current}

    for _ in range(max_hops):
        if current == target:
            return path, "Delivered Successfully (TrustHop)"

        neighbors = [n for n in G.neighbors(current) if G.nodes[n]["online"] and n not in visited]
        if not neighbors:
            return None, "Trapped in Dead-End (No Available Neighbors)"

        # Filter out malicious nodes
        safe_neighbors = [n for n in neighbors if not G.nodes[n]["malicious"]]
        if not safe_neighbors:
            return None, "Surrounded by Black-Hole Attackers!"

        if target in safe_neighbors:
            path.append(target)
            return path, "Delivered Successfully (TrustHop)"

        # Prioritize uncongested and high-trust community nodes
        uncongested = [n for n in safe_neighbors if not G.nodes[n].get("congested", False)]
        candidates = uncongested if uncongested else safe_neighbors

        same_comm = [n for n in candidates if G.nodes[n]["community"] == target_comm]
        if same_comm:
            next_hop = max(same_comm, key=lambda n: G.nodes[n]["degree"] * G.edges[current, n]["trust"])
        else:
            next_hop = max(candidates, key=lambda n: (G.nodes[n]["betweenness"] + 0.01) * G.edges[current, n]["trust"])

        path.append(next_hop)
        visited.add(next_hop)
        current = next_hop

    return None, "Max Hop Limit Reached (Routing Loop Avoided)"

def run_batch_benchmark(G, num_trials=100):
    online_nodes = [n for n, d in G.nodes(data=True) if d["online"] and not d["malicious"]]
    if len(online_nodes) < 2:
        return None

    results = {"Dijkstra": {"delivered": 0, "hops": []}, "Social-Aware": {"delivered": 0, "hops": []}}

    random.seed(101)
    for _ in range(num_trials):
        src, dst = random.sample(online_nodes, 2)
        
        d_path, _ = route_dijkstra(G, src, dst)
        if d_path:
            results["Dijkstra"]["delivered"] += 1
            results["Dijkstra"]["hops"].append(len(d_path) - 1)

        s_path, _ = route_social_aware(G, src, dst)
        if s_path:
            results["Social-Aware"]["delivered"] += 1
            results["Social-Aware"]["hops"].append(len(s_path) - 1)

    summary = pd.DataFrame({
        "Algorithm": ["Dijkstra (Baseline)", "TrustHop (Social-Aware)"],
        "Delivery Success Rate (%)": [
            round((results["Dijkstra"]["delivered"] / num_trials) * 100, 1),
            round((results["Social-Aware"]["delivered"] / num_trials) * 100, 1)
        ],
        "Average Hop Count": [
            round(sum(results["Dijkstra"]["hops"]) / len(results["Dijkstra"]["hops"]), 2) if results["Dijkstra"]["hops"] else 0,
            round(sum(results["Social-Aware"]["hops"]) / len(results["Social-Aware"]["hops"]), 2) if results["Social-Aware"]["hops"] else 0
        ]
    })
    return summary