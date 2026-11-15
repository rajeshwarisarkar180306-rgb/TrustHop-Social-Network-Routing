# TrustHop: Social-Aware Decentralized Routing Simulator

TrustHop is an interactive network routing lab built to explore how social graph structure can make decentralized packet routing more resilient. Instead of relying purely on shortest-path distance like traditional protocols, TrustHop factors in peer trust, community clustering, and hub congestion to route around bottlenecks and malicious black-hole nodes.

## Why I Built This
Standard shortest-path algorithms (like Dijkstra) work great in clean, static graphs, but in real-world peer-to-peer and social networks, the shortest path often cuts straight through overloaded central hubs or untrusted nodes. I wanted to build a visual sandbox to test how incorporating graph-theoretic metrics—specifically Louvain community detection and betweenness centrality—improves packet delivery under adversarial conditions.

## Core Features
* **Interactive Network Topologies:** Test routing behavior across Small-World (Watts-Strogatz), Scale-Free (Barabási-Albert), and Zachary's Karate Club social graphs.
* **Adversarial Stress Controls:** Dynamically adjust node dropout rates, bridge hub congestion, and malicious black-hole attackers in real time.
* **Step-by-Step Packet Playback:** Watch packets traverse the network with client-side animated path highlighting and a manual hop scrubber.
* **Live Route Diagnostics:** Automatically compares TrustHop's chosen path against baseline Dijkstra on the exact same source/destination pair, breaking down why detours were taken (e.g., congestion avoided, social trust gained).
* **100-Packet Stress Benchmark:** Runs randomized Monte Carlo trials across the network to compare delivery success rates and average hop counts, complete with downloadable CSV reports.

## Project Structure
* `app.py` — Streamlit web interface, state management, route explainability panel, and benchmark dashboard.
* `graph_engine.py` — Network generation, community detection, centrality scoring, Dijkstra vs. TrustHop routing logic, and batch benchmarking.
* `visualizer.py` — PyVis interactive graph rendering with custom JavaScript injection for smooth, flicker-free packet animation.
* `requirements.txt` — Python dependencies.

## Running Locally

1. **Clone the repository**
   ```bash
   git clone [https://github.com/rajeshwarisarkar180306-rgb/TrustHop-Social-Network-Routing.git](https://github.com/rajeshwarisarkar180306-rgb/TrustHop-Social-Network-Routing.git)
   cd TrustHop-Social-Network-Routing
