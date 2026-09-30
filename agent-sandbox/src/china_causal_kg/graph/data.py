"""
Data definitions for the Causal Knowledge Graph demonstration.

Theme: Weather & City Commuting Disruption (Intuitive Everyday Causal Chain)
- Cluster A: Heavy Rain (Precondition Cause: A -> C)
- Cluster B: High Winds (Secondary Cause: B -> C)
- Cluster C: Traffic Gridlock (Central Event: A, B -> C -> D)
- Cluster D: Daily Delays (Consequence: C -> D)

Key Principle:
16 vocabulary nodes placed at fixed (x, y, z) coordinates.
The nodes DO NOT MOVE when clustered or causally linked.
"""

from typing import List, Dict, Any
import copy

# Primary uniform theme color for Step 1 unclustered nodes (neutral slate for pure white background)
UNIFORM_NODE_COLOR = "#475569"

# The 4 Thematic Topic Clusters
TOPICS: Dict[str, Dict[str, Any]] = {
    "A": {
        "id": "A",
        "name": "Heavy Rain",
        "chinese_name": "暴雨積水",
        "short_label": "Topic A: Heavy Rain",
        "description": "Severe downpours, flash floods, and waterlogged roadway surfaces.",
        "causal_role": "Cause (A ➔ C)",
        "color": "#0284C7",          # Sky / Rain Blue
        "bg_color": "rgba(2, 132, 199, 0.08)",
        "border_color": "rgba(2, 132, 199, 0.45)",
        "centroid_2d": {"x": -64.0, "y": 49.5},
        "centroid_3d": {"x": -64.0, "y": 49.5, "z": 24.5},
    },
    "B": {
        "id": "B",
        "name": "High Winds",
        "chinese_name": "強風斷枝",
        "short_label": "Topic B: High Winds",
        "description": "Gale gusts, fallen trees, and flying debris obstructing travel corridors.",
        "causal_role": "Cause (B ➔ C)",
        "color": "#0D9488",          # Deep Teal
        "bg_color": "rgba(13, 148, 136, 0.08)",
        "border_color": "rgba(13, 148, 136, 0.45)",
        "centroid_2d": {"x": -60.5, "y": -47.0},
        "centroid_3d": {"x": -60.5, "y": -47.0, "z": -23.5},
    },
    "C": {
        "id": "C",
        "name": "Traffic Gridlock",
        "chinese_name": "交通癱瘓",
        "short_label": "Topic C: Traffic Gridlock",
        "description": "Road closures, standstill traffic jams, and immobilized highway lanes.",
        "causal_role": "Central Event (A, B ➔ C ➔ D)",
        "color": "#EA580C",          # Traffic Amber / Orange
        "bg_color": "rgba(234, 88, 12, 0.08)",
        "border_color": "rgba(234, 88, 12, 0.45)",
        "centroid_2d": {"x": 6.5, "y": 1.5},
        "centroid_3d": {"x": 6.5, "y": 1.5, "z": 0.0},
    },
    "D": {
        "id": "D",
        "name": "Daily Delays",
        "chinese_name": "日程延誤",
        "short_label": "Topic D: Daily Delays",
        "description": "Late work arrivals, missed flights, school delays, and cancelled meetings.",
        "causal_role": "Consequence (C ➔ D)",
        "color": "#7C3AED",          # Purple / Violet
        "bg_color": "rgba(124, 58, 237, 0.08)",
        "border_color": "rgba(124, 58, 237, 0.45)",
        "centroid_2d": {"x": 75.5, "y": 3.0},
        "centroid_3d": {"x": 75.5, "y": 3.0, "z": 21.0},
    },
}

# Base definitions of the 16 vocabulary nodes (Everyday intuitive terms)
BASE_VOCABULARY: List[Dict[str, Any]] = [
    # Topic A (Heavy Rain)
    {
        "id": "node_1",
        "word": "Torrential Downpour",
        "chinese": "暴雨傾盆",
        "topic_id": "A",
        "historical_source": "City Weather Bureau Report",
        "context": "Extreme rainfall overwhelming municipal storm drains within minutes.",
    },
    {
        "id": "node_2",
        "word": "Flash Floods",
        "chinese": "突發積水",
        "topic_id": "A",
        "historical_source": "Emergency Alert Notification",
        "context": "Rapidly rising water levels submerging roads and highway underpasses.",
    },
    {
        "id": "node_3",
        "word": "Heavy Rain",
        "chinese": "強降雨",
        "topic_id": "A",
        "historical_source": "Morning Commute Advisory",
        "context": "Prolonged rainfall severely reducing vehicle braking distance and visibility.",
    },
    {
        "id": "node_4",
        "word": "Flooded Streets",
        "chinese": "街道淹水",
        "topic_id": "A",
        "historical_source": "Municipal Traffic Camera Feed",
        "context": "Deep standing water covering main lanes and preventing vehicle passage.",
    },

    # Topic B (High Winds)
    {
        "id": "node_5",
        "word": "High Winds",
        "chinese": "狂風大作",
        "topic_id": "B",
        "historical_source": "Gale Warning Advisory",
        "context": "Severe gale-force gusts buffeting bridges and exposed commuter corridors.",
    },
    {
        "id": "node_6",
        "word": "Fallen Trees",
        "chinese": "樹木倒塌",
        "topic_id": "B",
        "historical_source": "Public Works Service Log",
        "context": "Uprooted trees falling directly across arterial travel avenues.",
    },
    {
        "id": "node_7",
        "word": "Broken Branches",
        "chinese": "路面斷枝",
        "topic_id": "B",
        "historical_source": "Road Maintenance Dispatch",
        "context": "Heavy branches littering intersections and blocking transit pathways.",
    },
    {
        "id": "node_8",
        "word": "Flying Debris",
        "chinese": "飛散雜物",
        "topic_id": "B",
        "historical_source": "Highway Patrol Incident Record",
        "context": "Loose signs and materials blown across multilane traffic lanes.",
    },

    # Topic C (Traffic Gridlock)
    {
        "id": "node_9",
        "word": "Traffic Jam",
        "chinese": "交通堵塞",
        "topic_id": "C",
        "historical_source": "Metro Transit Broadcast",
        "context": "Miles of bumper-to-bumper standstill traffic during rush hour.",
    },
    {
        "id": "node_10",
        "word": "Road Closures",
        "chinese": "道路封閉",
        "topic_id": "C",
        "historical_source": "Department of Transportation",
        "context": "Police barricades closing blocked avenues and detouring vehicles.",
    },
    {
        "id": "node_11",
        "word": "Stalled Cars",
        "chinese": "車輛拋錨",
        "topic_id": "C",
        "historical_source": "Roadside Assistance Dispatch",
        "context": "Disabled and hydroplaned vehicles stranded in active driving lanes.",
    },
    {
        "id": "node_12",
        "word": "Highway Gridlock",
        "chinese": "高速癱瘓",
        "topic_id": "C",
        "historical_source": "State Highway Traffic Command",
        "context": "Total operational standstill across primary expressway corridors.",
    },

    # Topic D (Daily Delays)
    {
        "id": "node_13",
        "word": "Late for Work",
        "chinese": "上班遲到",
        "topic_id": "D",
        "historical_source": "Employee Office Notification",
        "context": "Commuters arriving hours late for morning shifts and meetings.",
    },
    {
        "id": "node_14",
        "word": "Missed Flights",
        "chinese": "錯過航班",
        "topic_id": "D",
        "historical_source": "Airport Terminal Operations",
        "context": "Travelers unable to navigate blocked airport roads prior to gate closure.",
    },
    {
        "id": "node_15",
        "word": "School Delays",
        "chinese": "學校停課延期",
        "topic_id": "D",
        "historical_source": "District School Board Bulletin",
        "context": "Bus transit suspended and morning bell times delayed for student safety.",
    },
    {
        "id": "node_16",
        "word": "Cancelled Meetings",
        "chinese": "會議取消",
        "topic_id": "D",
        "historical_source": "Corporate Schedule Updates",
        "context": "Business appointments postponed due to stranded attendees.",
    },
]

# The 16 Node Coordinates (Initial Spatial Layout)
# Identical for Step 1 (unclustered baseline), Step 2 (clusters with boundaries), and Step 3 (causal graph).
# The nodes DO NOT MOVE when clustered or causally linked.
INITIAL_NODE_COORDINATES: Dict[str, Dict[str, float]] = {
    # Region A (Heavy Rain - Top-Left)
    "node_1":  {"x": -82.0, "y":  58.0, "z":  28.0},  # Torrential Downpour
    "node_2":  {"x": -54.0, "y":  68.0, "z":  22.0},  # Flash Floods
    "node_3":  {"x": -74.0, "y":  32.0, "z":  14.0},  # Heavy Rain
    "node_4":  {"x": -46.0, "y":  40.0, "z":  34.0},  # Flooded Streets

    # Region B (High Winds - Bottom-Left)
    "node_5":  {"x": -78.0, "y": -36.0, "z": -16.0},  # High Winds
    "node_6":  {"x": -48.0, "y": -28.0, "z": -26.0},  # Fallen Trees
    "node_7":  {"x": -72.0, "y": -66.0, "z": -34.0},  # Broken Branches
    "node_8":  {"x": -44.0, "y": -58.0, "z": -18.0},  # Flying Debris

    # Region C (Traffic Gridlock - Center Hub)
    "node_9":  {"x": -12.0, "y":  16.0, "z":  12.0},  # Traffic Jam
    "node_10": {"x":  22.0, "y":  20.0, "z": -10.0},  # Road Closures
    "node_11": {"x":  -8.0, "y": -18.0, "z": -12.0},  # Stalled Cars
    "node_12": {"x":  24.0, "y": -12.0, "z":  10.0},  # Highway Gridlock

    # Region D (Daily Delays - Right Hub)
    "node_13": {"x":  58.0, "y":  18.0, "z":  28.0},  # Late for Work
    "node_14": {"x":  92.0, "y":  22.0, "z":  14.0},  # Missed Flights
    "node_15": {"x":  62.0, "y": -18.0, "z":  18.0},  # School Delays
    "node_16": {"x":  90.0, "y": -10.0, "z":  24.0},  # Cancelled Meetings
}

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
        n["color"] = UNIFORM_NODE_COLOR
        n["size"] = 12
        n["step"] = 1
        n["latent_topic_id"] = item["topic_id"]
        n["latent_topic_name"] = TOPICS[item["topic_id"]]["name"]
        nodes.append(n)
    return nodes


def get_step2_nodes() -> List[Dict[str, Any]]:
    """Return nodes for Step 2 (Stationary coordinates, colored by topic cluster)."""
    nodes = []
    for item in BASE_VOCABULARY:
        n = dict(item)
        c = INITIAL_NODE_COORDINATES[item["id"]]
        topic = TOPICS[item["topic_id"]]

        n["x"] = c["x"]
        n["y"] = c["y"]
        n["z"] = c["z"]
        n["color"] = topic["color"]
        n["size"] = 14
        n["step"] = 2
        n["topic_name"] = topic["name"]
        n["cluster_label"] = topic["short_label"]
        n["causal_role"] = topic["causal_role"]
        n["border_color"] = topic["border_color"]
        nodes.append(n)
    return nodes


def get_step2_intra_links() -> List[Dict[str, Any]]:
    """Generate subtle connection lines between nodes within the same cluster to highlight grouping."""
    links = []
    nodes = get_step2_nodes()
    topic_groups: Dict[str, List[Dict[str, Any]]] = {}
    for n in nodes:
        topic_groups.setdefault(n["topic_id"], []).append(n)

    for topic_id, group_nodes in topic_groups.items():
        color = TOPICS[topic_id]["color"]
        # Ring connections + cross connect
        for i in range(len(group_nodes)):
            target_idx = (i + 1) % len(group_nodes)
            links.append({
                "source": group_nodes[i]["id"],
                "target": group_nodes[target_idx]["id"],
                "color": color,
                "weight": 1.0,
                "type": "INTRA_CLUSTER",
            })
    return links


# ====================================================================
# Step 3: Causal Directed Relationships (A, B ➔ C ➔ D)
# Visual Principle: NO TEXT LABELS ON EDGES. Clean directional arrows.
# ====================================================================
CAUSAL_EDGES: List[Dict[str, Any]] = [
    {
        "id": "causal_A_C",
        "source": "A",
        "target": "C",
        "source_name": "Heavy Rain",
        "target_name": "Traffic Gridlock",
        "type": "CAUSES",
        "causal_type": "PRECONDITION",
        "relationship": "A ➔ C",
        "mechanism": "Torrential downpours and flash floods submerge roads, causing widespread traffic gridlock.",
        "color": "#0284C7",
        "arrow_color": "#0284C7",
        "weight": 3.0,
    },
    {
        "id": "causal_B_C",
        "source": "B",
        "target": "C",
        "source_name": "High Winds",
        "target_name": "Traffic Gridlock",
        "type": "CAUSES",
        "causal_type": "CATALYST",
        "relationship": "B ➔ C",
        "mechanism": "High winds topple trees and scatter debris onto streets, blocking travel corridors.",
        "color": "#0D9488",
        "arrow_color": "#0D9488",
        "weight": 3.0,
    },
    {
        "id": "causal_C_D",
        "source": "C",
        "target": "D",
        "source_name": "Traffic Gridlock",
        "target_name": "Daily Delays",
        "type": "CAUSES",
        "causal_type": "CONSEQUENCE",
        "relationship": "C ➔ D",
        "mechanism": "Severe traffic gridlock paralyzes transportation, making people late for work and causing missed appointments.",
        "color": "#EA580C",
        "arrow_color": "#7C3AED",
        "weight": 3.5,
    },
]

# Micro causal semantic chains connecting specific representative words
WORD_CAUSAL_LINKS: List[Dict[str, Any]] = [
    {"source": "node_1", "target": "node_9", "type": "MICRO_CAUSAL", "mechanism": "Torrential downpour triggers massive traffic jams"},
    {"source": "node_2", "target": "node_10", "type": "MICRO_CAUSAL", "mechanism": "Flash floods force road closures"},
    {"source": "node_6", "target": "node_10", "type": "MICRO_CAUSAL", "mechanism": "Fallen trees cause road closures"},
    {"source": "node_8", "target": "node_12", "type": "MICRO_CAUSAL", "mechanism": "Flying debris triggers highway gridlock"},
    {"source": "node_9", "target": "node_13", "type": "MICRO_CAUSAL", "mechanism": "Traffic jam causes workers to be late"},
    {"source": "node_10", "target": "node_14", "type": "MICRO_CAUSAL", "mechanism": "Road closures lead to missed flights"},
    {"source": "node_12", "target": "node_16", "type": "MICRO_CAUSAL", "mechanism": "Highway gridlock leads to cancelled meetings"},
]


def get_step3_nodes() -> List[Dict[str, Any]]:
    """Return nodes for Step 3 (Identical coordinates, marked for step 3)."""
    nodes = get_step2_nodes()
    for n in nodes:
        n["step"] = 3
    return nodes


def get_causal_edges() -> List[Dict[str, Any]]:
    """Return the macro directed causal edges between clusters."""
    return copy.deepcopy(CAUSAL_EDGES)


def get_word_causal_links() -> List[Dict[str, Any]]:
    """Return the micro directed causal links between words."""
    return copy.deepcopy(WORD_CAUSAL_LINKS)


# Backward-compatible aliases
STRIKE_NODES = get_step1_nodes()
get_nodes_as_dict = get_step1_nodes
