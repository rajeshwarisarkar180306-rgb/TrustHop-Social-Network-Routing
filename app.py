import streamlit as st
import streamlit.components.v1 as components
from graph_engine import create_social_network, route_dijkstra, route_social_aware, run_batch_benchmark
from visualizer import render_graph

st.set_page_config(page_title="TrustHop Advanced Lab", layout="wide")
st.title("🛡️ TrustHop: Advanced Decentralized Routing Simulator")

def analyze_route_advantage(G, source, target, trusthop_path):
    d_path, d_status = route_dijkstra(G, source, target)
    
    th_hops = len(trusthop_path) - 1
    th_trusts = [G.edges[trusthop_path[i], trusthop_path[i+1]]["trust"] for i in range(th_hops)]
    avg_th_trust = round((sum(th_trusts) / len(th_trusts)) * 100, 1) if th_trusts else 100.0
    th_congested = sum(1 for n in trusthop_path[1:-1] if G.nodes[n].get("congested", False))

    reasons = []
    
    if not d_path:
        reasons.append(f"🛡️ **Resilience Win:** Baseline Dijkstra completely failed (`{d_status}`), whereas TrustHop dynamically discovered a safe path.")
    else:
        d_hops = len(d_path) - 1
        d_trusts = [G.edges[d_path[i], d_path[i+1]]["trust"] for i in range(d_hops)]
        avg_d_trust = round((sum(d_trusts) / len(d_trusts)) * 100, 1) if d_trusts else 100.0
        d_congested = sum(1 for n in d_path[1:-1] if G.nodes[n].get("congested", False))

        if d_congested > th_congested:
            reasons.append(f"🚦 **Bottleneck Avoidance:** Dijkstra walked into **{d_congested} congested hub(s)**, while TrustHop routed around traffic ({th_congested} congested).")
        if avg_th_trust > avg_d_trust:
            reasons.append(f"🤝 **Higher Social Trust:** TrustHop achieved **{avg_th_trust}%** average link trust vs. Dijkstra's **{avg_d_trust}%**.")
        if th_hops == d_hops:
            reasons.append(f"⚡ **Zero Hop Penalty:** Matched shortest-path distance (**{th_hops} hops**) while prioritizing trusted community bridges.")
        elif th_hops > d_hops:
            reasons.append(f"🧭 **Calculated Detour (+{th_hops - d_hops} hop):** Took {th_hops - d_hops} extra hop(s) to avoid risky/congested hubs and ensure packet survival.")

    malicious_count = sum(1 for _, d in G.nodes(data=True) if d.get("malicious", False))
    if malicious_count > 0:
        reasons.append(f"🔒 **Black-Hole Immunity:** Screened out **{malicious_count} malicious node(s)** using local trust evaluation.")

    if not reasons:
        reasons.append(f"✅ **Optimal Community Routing:** Delivered in **{th_hops} hops** with **{avg_th_trust}%** average peer trust.")

    return reasons, avg_th_trust

# Sidebar
st.sidebar.header("1. Network Settings")
model_type = st.sidebar.selectbox("Topology Model", ["Small-World", "Scale-Free", "Real-World (Karate Club)"])
num_nodes = 65 if model_type != "Real-World (Karate Club)" else 34

st.sidebar.header("2. Security & Stress Testing")
failure_rate = st.sidebar.slider("Node Dropout Rate", 0.0, 0.4, 0.05, 0.05)
congestion_rate = st.sidebar.slider("Traffic Congestion Rate", 0.0, 0.4, 0.1, 0.05)
malicious_rate = st.sidebar.slider("Malicious (Black-Hole) Rate", 0.0, 0.3, 0.1, 0.05)

G = create_social_network(model_type, num_nodes, failure_rate, congestion_rate, malicious_rate)
online_nodes = [n for n, d in G.nodes(data=True) if d["online"] and not d["malicious"]]

tab1, tab2 = st.tabs(["Live Interactive Routing & Playback", "Automated Benchmark & CSV Export"])

with tab1:
    col_ctrl, col_vis = st.columns([1, 3])
    with col_ctrl:
        st.subheader("Route Packet")
        if len(online_nodes) >= 2:
            source = st.selectbox("Source Node", online_nodes, index=0)
            target = st.selectbox("Destination Node", online_nodes, index=len(online_nodes)-1)
            algo = st.radio("Routing Algorithm", ["TrustHop (Social-Aware)", "Dijkstra (Baseline)"])
            
            calc_btn = st.button("Calculate Path", type="primary", use_container_width=True)
        else:
            st.error("Too many nodes offline/malicious!")
            st.stop()

        st.markdown("---")
        st.markdown("### 🗺️ Network Legend")
        st.markdown("""
        <div style="display: flex; flex-direction: column; gap: 10px; font-size: 14px; line-height: 1.4;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: #00FF88; font-size: 20px; line-height: 1;">★</span>
            <span><b>Green Star:</b> Source Node (Sender)</span>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: #FF3366; font-size: 20px; line-height: 1;">★</span>
            <span><b>Pink Star:</b> Destination Node (Receiver)</span>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="display: inline-block; width: 18px; height: 4px; background-color: #00E5FF; border-radius: 2px;"></span>
            <span><b>Cyan Line:</b> Active Packet Route</span>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="display: inline-block; width: 15px; height: 15px; background-color: #8B0000; border: 1px solid #ff4d4d; border-radius: 2px;"></span>
            <span><b>Dark Red Box:</b> Malicious / Black-Hole Node</span>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: #FF9900; font-size: 18px; line-height: 1;">▲</span>
            <span><b>Orange Triangle:</b> Congested Bridge Hub</span>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="display: inline-block; width: 14px; height: 14px; background-color: #3A3A3A; border-radius: 50%;"></span>
            <span><b>Dark Gray Dot:</b> Offline / Failed Node</span>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="display: inline-flex; gap: 3px;">
              <span style="width: 10px; height: 10px; background-color: #4E79A7; border-radius: 50%;"></span>
              <span style="width: 10px; height: 10px; background-color: #59A14F; border-radius: 50%;"></span>
              <span style="width: 10px; height: 10px; background-color: #B07AA1; border-radius: 50%;"></span>
            </span>
            <span><b>Colored Dots:</b> Healthy Social Communities</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    if "last_path" not in st.session_state:
        st.session_state.last_path = None
        st.session_state.last_status = ""
        st.session_state.last_algo = ""
        st.session_state.last_pair = None

    # Clear outdated path if user changes topology, source, or destination
    current_pair = (model_type, source, target)
    if st.session_state.last_pair != current_pair and not calc_btn:
        st.session_state.last_path = None
        st.session_state.last_status = ""
        st.session_state.last_pair = current_pair

    if calc_btn:
        if "Social-Aware" in algo:
            path, status_msg = route_social_aware(G, source, target)
        else:
            path, status_msg = route_dijkstra(G, source, target)
        
        st.session_state.last_path = path
        st.session_state.last_status = status_msg
        st.session_state.last_algo = algo
        st.session_state.last_pair = current_pair

    with col_vis:
        path = st.session_state.last_path
        status_msg = st.session_state.last_status
        active_algo = st.session_state.last_algo

        if path and len(path) > 1:
            st.success(f"Status: {status_msg} | Total Hops: {len(path)-1} | Path: `{' → '.join(map(str, path))}`")
            
            step = st.slider("🎬 Packet Step-by-Step Viewer", 1, len(path), len(path))
            display_path = path[:step]
            
            html_graph = render_graph(G, display_path, source, target)
            components.html(html_graph, height=560)

            # Live Route Justification Panel
            if "Social-Aware" in active_algo:
                reasons, avg_trust = analyze_route_advantage(G, source, target, path)
                with st.expander(f"🧠 Why TrustHop Chose This Path (Avg Social Trust: {avg_trust}%)", expanded=True):
                    for r in reasons:
                        st.markdown(f"- {r}")
            else:
                d_congested = sum(1 for n in path[1:-1] if G.nodes[n].get("congested", False))
                with st.expander("⚠️ Dijkstra Baseline Diagnostics", expanded=True):
                    st.markdown(f"- **Greedy Shortest Path:** Ignored social trust weights and community boundaries.")
                    if d_congested > 0:
                        st.markdown(f"- **Congestion Penalty:** Routed directly through **{d_congested} congested hub(s)**, causing real-world packet delay.")
                    else:
                        st.markdown(f"- **Vulnerability:** Operates without black-hole reputation screening or traffic load balancing.")

        elif path and len(path) == 1:
            st.success(f"Status: {status_msg}")
            html_graph = render_graph(G, path, source, target)
            components.html(html_graph, height=560)
        else:
            if calc_btn or status_msg:
                st.error(f"Routing Failed: {status_msg}")
            else:
                st.info("Select source and destination, then click 'Calculate Path'.")
            
            html_graph = render_graph(G, None, source, target)
            components.html(html_graph, height=560)

with tab2:
    st.subheader("📊 100-Packet Stress Benchmark Suite")
    st.write("Test the resilience of TrustHop against Dijkstra under active network attacks and black-hole nodes.")
    
    if st.button("Run Benchmark Suite", type="primary"):
        df_results = run_batch_benchmark(G, num_trials=100)
        st.dataframe(df_results, use_container_width=True, hide_index=True)
        
        csv_data = df_results.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Benchmark Report (CSV)",
            data=csv_data,
            file_name="trusthop_benchmark_report.csv",
            mime="text/csv",
        )
        
        st.bar_chart(df_results.set_index("Algorithm")["Delivery Success Rate (%)"])