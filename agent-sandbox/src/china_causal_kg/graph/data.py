"""
Data definitions for the 1920s Chinese Strike Causal Knowledge Graph.

Supports:
- Step 1: Dispersed, unclustered baseline (16 uniform nodes, Latin-square dispersed).
- Step 2: Thematic Topic Clusters (16 nodes visibly clustered into 4 topics A, B, C, D with overall cluster labels).
"""

from typing import List, Dict, Any
import copy

# Primary uniform theme color for Step 1 unclustered nodes (high contrast for white background)
UNIFORM_NODE_COLOR = "#0284C7"  # Vibrant ocean blue

# The 4 Thematic Topic Clusters
TOPICS: Dict[str, Dict[str, Any]] = {
    "A": {
        "id": "A",
        "name": "Economic Grievances & Inflation",
        "chinese_name": "生活成本與工資削減",
        "short_label": "Topic A: Economic Grievances",
        "description": "Post-WWI economic depression, soaring rice prices, currency volatility, and unlivable laborer wages.",
        "causal_role": "Pre-condition / Cause (A -> C)",
        "color": "#E11D48",          # Crimson / Rose
        "bg_color": "rgba(225, 29, 72, 0.08)",
        "border_color": "rgba(225, 29, 72, 0.4)",
        "centroid_2d": {"x": -64.0, "y": 49.5},
        "centroid_3d": {"x": -64.0, "y": 49.5, "z": 24.5},
    },
    "B": {
        "id": "B",
        "name": "Labor Organizing & Solidarity",
        "chinese_name": "工會組織與工人動員",
        "short_label": "Topic B: Labor Organizing",
        "description": "Establishment of labor syndicates, strike committees, boycott manifestos, and picket enforcement.",
        "causal_role": "Catalyst / Cause (B -> C)",
        "color": "#0D9488",          # Deep Teal
        "bg_color": "rgba(13, 148, 136, 0.08)",
        "border_color": "rgba(13, 148, 136, 0.4)",
        "centroid_2d": {"x": -60.5, "y": -47.0},
        "centroid_3d": {"x": -60.5, "y": -47.0, "z": -23.5},
    },
    "C": {
        "id": "C",
        "name": "Strike Action & Work Stoppage",
        "chinese_name": "全港大罷工行動",
        "short_label": "Topic C: General Strike Action",
        "description": "Mass walkouts, dock shutdowns, street demonstrations, and systemic withdrawal of maritime and municipal labor.",
        "causal_role": "Central Strike Event (A, B -> C -> D)",
        "color": "#2563EB",          # Royal Blue
        "bg_color": "rgba(37, 99, 235, 0.08)",
        "border_color": "rgba(37, 99, 235, 0.4)",
        "centroid_2d": {"x": 6.5, "y": 1.5},
        "centroid_3d": {"x": 6.5, "y": 1.5, "z": 0.0},
    },
    "D": {
        "id": "D",
        "name": "Harbor Paralysis & Colonial Impact",
        "chinese_name": "港口癱瘓與殖民談判",
        "short_label": "Topic D: Harbor & Market Paralysis",
        "description": "Harbor standstill, 150+ stranded steamships, commercial food shortages, and imperial legislative negotiations.",
        "causal_role": "Consequence (C -> D)",
        "color": "#7C3AED",          # Purple / Violet
        "bg_color": "rgba(124, 58, 237, 0.08)",
        "border_color": "rgba(124, 58, 237, 0.4)",
        "centroid_2d": {"x": 75.5, "y": 3.0},
        "centroid_3d": {"x": 75.5, "y": 3.0, "z": 21.0},
    },
}

# Base definitions of the 16 vocabulary nodes
BASE_VOCABULARY: List[Dict[str, Any]] = [
    # Topic A (Economic Grievance)
    {
        "id": "node_1",
        "word": "Wage Depression",
        "chinese": "工資削滅",
        "topic_id": "A",
        "historical_source": "The China Mail (1921-1922)",
        "context": "Stagnant daily laborer wages amidst sharp post-war currency fluctuations.",
    },
    {
        "id": "node_2",
        "word": "Rice Inflation",
        "chinese": "米價暴漲",
        "topic_id": "A",
        "historical_source": "Hong Kong MMIS Gazette (1922)",
        "context": "Skyrocketing price of staple rice threatening subsistence of dock families.",
    },
    {
        "id": "node_3",
        "word": "Ten-Hour Shift",
        "chinese": "每日十時工制",
        "topic_id": "A",
        "historical_source": "North-China Herald (1923)",
        "context": "Exhausting operational hours demanded from maritime and transport coolies.",
    },
    {
        "id": "node_4",
        "word": "Living Cost Spiral",
        "chinese": "生活昂貴",
        "topic_id": "A",
        "historical_source": "The China Mail (1922)",
        "context": "General cost-of-living index surges driving desperate economic petitions.",
    },

    # Topic B (Labor Organizing)
    {
        "id": "node_5",
        "word": "Seamen's Union",
        "chinese": "中華海員工會",
        "topic_id": "B",
        "historical_source": "The China Mail (1922)",
        "context": "The central maritime guild led by Su Zhaozheng organizing across Hong Kong and Canton.",
    },
    {
        "id": "node_6",
        "word": "Strike Committee",
        "chinese": "罷工委員會",
        "topic_id": "B",
        "historical_source": "Canton Gazette (1925)",
        "context": "Executive coordinating council managing strike logistics, food rations, and strategy.",
    },
    {
        "id": "node_7",
        "word": "Picket Corps",
        "chinese": "工人糾察隊",
        "topic_id": "B",
        "historical_source": "The China Mail (1925)",
        "context": "Organized worker patrols enforcing the anti-colonial shipping embargo.",
    },
    {
        "id": "node_8",
        "word": "Boycott Manifesto",
        "chinese": "抵制宣傳宣言",
        "topic_id": "B",
        "historical_source": "Shanghai Municipal Archives (1925)",
        "context": "Leaflets distributed across treaty ports calling for national anti-imperial unity.",
    },

    # Topic C (Strike Action)
    {
        "id": "node_9",
        "word": "General Strike",
        "chinese": "全港大罷工",
        "topic_id": "C",
        "historical_source": "The China Mail (1922)",
        "context": "Complete stoppage of maritime and municipal work paralyzing the colony.",
    },
    {
        "id": "node_10",
        "word": "Dockworker Walkout",
        "chinese": "碼頭工人全體離工",
        "topic_id": "C",
        "historical_source": "The China Mail (1922)",
        "context": "Stevedores and cargo loaders abandoning British ships in Victoria Harbour.",
    },
    {
        "id": "node_11",
        "word": "Work Cessation",
        "chinese": "停工停業",
        "topic_id": "C",
        "historical_source": "Hong Kong MMIS (1925)",
        "context": "Sympathy strikes spreading to domestic servants, tram drivers, and clerks.",
    },
    {
        "id": "node_12",
        "word": "Mass Demonstration",
        "chinese": "群眾請願示威",
        "topic_id": "C",
        "historical_source": "The China Mail (1922)",
        "context": "Gatherings of thousands marching through urban centers demanding rights and dignity.",
    },

    # Topic D (Harbor Paralysis & Impact)
    {
        "id": "node_13",
        "word": "Port Paralysis",
        "chinese": "港口海運癱瘓",
        "topic_id": "D",
        "historical_source": "The China Mail (1922)",
        "context": "Over 150 merchant vessels anchored idle with zero cargo discharge capacity.",
    },
    {
        "id": "node_14",
        "word": "Shipping Deadlock",
        "chinese": "輪船停航停泊",
        "topic_id": "D",
        "historical_source": "The China Mail (1925)",
        "context": "Complete standstill of coastal and trans-Pacific commercial steamer traffic.",
    },
    {
        "id": "node_15",
        "word": "Market Interruption",
        "chinese": "市面商業停滯",
        "topic_id": "D",
        "historical_source": "Hong Kong Chamber of Commerce (1922)",
        "context": "Retail closures, supply shortages, and emergency rationing across Victoria.",
    },
    {
        "id": "node_16",
        "word": "Colonial Concessions",
        "chinese": "當局讓步談判",
        "topic_id": "D",
        "historical_source": "The China Mail (1922)",
        "context": "Colonial government and shipping conglomerates agreeing to wage hikes and union recognition.",
    },
]

# The 16 Node Coordinates (Initial Spatial Layout)
# Identical for Step 1 (unclustered baseline) and Step 2 (clusters with boundaries).
# The nodes DO NOT MOVE when clustered; clusters are chosen based on these initial positions.
INITIAL_NODE_COORDINATES: Dict[str, Dict[str, float]] = {
    # Region A (Economic Grievances - Top-Left)
    "node_1":  {"x": -82.0, "y":  58.0, "z":  28.0},  # Wage Depression
    "node_2":  {"x": -54.0, "y":  68.0, "z":  22.0},  # Rice Inflation
    "node_3":  {"x": -74.0, "y":  32.0, "z":  14.0},  # Ten-Hour Shift
    "node_4":  {"x": -46.0, "y":  40.0, "z":  34.0},  # Living Cost Spiral

    # Region B (Labor Organizing - Bottom-Left)
    "node_5":  {"x": -78.0, "y": -36.0, "z": -16.0},  # Seamen's Union
    "node_6":  {"x": -48.0, "y": -28.0, "z": -26.0},  # Strike Committee
    "node_7":  {"x": -72.0, "y": -66.0, "z": -34.0},  # Picket Corps
    "node_8":  {"x": -44.0, "y": -58.0, "z": -18.0},  # Boycott Manifesto

    # Region C (Strike Action - Center Hub)
    "node_9":  {"x": -12.0, "y":  16.0, "z":  12.0},  # General Strike
    "node_10": {"x":  22.0, "y":  20.0, "z": -10.0},  # Dockworker Walkout
    "node_11": {"x":  -8.0, "y": -18.0, "z": -12.0},  # Work Cessation
    "node_12": {"x":  24.0, "y": -12.0, "z":  10.0},  # Mass Demonstration

    # Region D (Harbor Paralysis - Right Hub)
    "node_13": {"x":  58.0, "y":  18.0, "z":  28.0},  # Port Paralysis
    "node_14": {"x":  92.0, "y":  22.0, "z":  14.0},  # Shipping Deadlock
    "node_15": {"x":  62.0, "y": -18.0, "z":  18.0},  # Market Interruption
    "node_16": {"x":  90.0, "y": -10.0, "z":  24.0},  # Colonial Concessions
}

# Aliases ensuring backward compatibility and identical coordinates across steps
STEP1_COORDINATES = INITIAL_NODE_COORDINATES
STEP2_COORDINATES = INITIAL_NODE_COORDINATES


def get_step1_nodes() -> List[Dict[str, Any]]:
    """Return nodes for Step 1 (Initial positions, unclustered baseline, uniform styling)."""
    nodes = []
    for item in BASE_VOCABULARY:
        n = dict(item)
        c = INITIAL_NODE_COORDINATES[item["id"]]
        n["x"] = c["x"]
        n["y"] = c["y"]
        n["z"] = c["z"]
        n["latent_topic_id"] = item["topic_id"]
        n["latent_topic_name"] = TOPICS[item["topic_id"]]["name"]
        n["step"] = 1
        n["status"] = "initial_unclustered"
        n["color"] = UNIFORM_NODE_COLOR
        nodes.append(n)
    return nodes


def get_step2_nodes() -> List[Dict[str, Any]]:
    """Return nodes for Step 2 (Nodes stay at exact initial positions; recolored by cluster with labels)."""
    nodes = []
    for item in BASE_VOCABULARY:
        n = dict(item)
        c = INITIAL_NODE_COORDINATES[item["id"]]
        t = TOPICS[item["topic_id"]]
        n["x"] = c["x"]
        n["y"] = c["y"]
        n["z"] = c["z"]
        n["topic_id"] = item["topic_id"]
        n["topic_name"] = t["name"]
        n["topic_chinese"] = t["chinese_name"]
        n["cluster_label"] = t["short_label"]
        n["color"] = t["color"]
        n["bg_color"] = t["bg_color"]
        n["border_color"] = t["border_color"]
        n["causal_role"] = t["causal_role"]
        n["step"] = 2
        n["status"] = "clustered"
        nodes.append(n)
    return nodes


def get_step2_intra_links() -> List[Dict[str, Any]]:
    """Return intra-cluster visual links connecting nodes within the same topic cluster."""
    links = []
    # Fully connect each 4-node cluster or ring connect
    for topic_id in ["A", "B", "C", "D"]:
        nodes = [n for n in BASE_VOCABULARY if n["topic_id"] == topic_id]
        color = TOPICS[topic_id]["color"]
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                links.append({
                    "source": nodes[i]["id"],
                    "target": nodes[j]["id"],
                    "topic_id": topic_id,
                    "color": color,
                    "type": "INTRA_CLUSTER",
                })
    return links


# Backward-compatible alias for Step 1
STRIKE_NODES = get_step1_nodes()
get_nodes_as_dict = get_step1_nodes
