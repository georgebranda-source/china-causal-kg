// ====================================================================
// Weather & Commuting Disruption: Causal Knowledge Graph (Step 3)
// Full Causal Induction: Directed Relationships Between Topic Clusters
// Causal Flow Architecture: (A: Heavy Rain) ──➔ (C: Traffic Gridlock) ── (B: High Winds)
//                           (C: Traffic Gridlock) ──➔ (D: Daily Delays)
// Note: No labels on edges for clean visual representation
// ====================================================================

// 1. Schema Constraints & Indexes
CREATE CONSTRAINT word_id_unique IF NOT EXISTS
FOR (w:StrikeWord) REQUIRE w.id IS UNIQUE;

CREATE CONSTRAINT cluster_id_unique IF NOT EXISTS
FOR (c:TopicCluster) REQUIRE c.id IS UNIQUE;

// 2. Clear existing demonstration nodes
MATCH (w:StrikeWord) DETACH DELETE w;
MATCH (c:TopicCluster) DETACH DELETE c;

// 3. Create 4 Topic Cluster Entity Nodes
CREATE (:TopicCluster {
    id: "Topic_A",
    topic_id: "A",
    name: "Heavy Rain",
    short_label: "Topic A: Heavy Rain",
    chinese_name: "暴雨積水",
    causal_role: "Cause (A ➔ C)",
    description: "Severe downpours, flash floods, and waterlogged roadway surfaces.",
    color: "#0284C7",
    centroid_x: -64.0, centroid_y: 49.5, centroid_z: 24.5,
    step: 3
});
CREATE (:TopicCluster {
    id: "Topic_B",
    topic_id: "B",
    name: "High Winds",
    short_label: "Topic B: High Winds",
    chinese_name: "強風斷枝",
    causal_role: "Cause (B ➔ C)",
    description: "Gale gusts, fallen trees, and flying debris obstructing travel corridors.",
    color: "#0D9488",
    centroid_x: -60.5, centroid_y: -47.0, centroid_z: -23.5,
    step: 3
});
CREATE (:TopicCluster {
    id: "Topic_C",
    topic_id: "C",
    name: "Traffic Gridlock",
    short_label: "Topic C: Traffic Gridlock",
    chinese_name: "交通癱瘓",
    causal_role: "Central Event (A, B ➔ C ➔ D)",
    description: "Road closures, standstill traffic jams, and immobilized highway lanes.",
    color: "#EA580C",
    centroid_x: 6.5, centroid_y: 1.5, centroid_z: 0.0,
    step: 3
});
CREATE (:TopicCluster {
    id: "Topic_D",
    topic_id: "D",
    name: "Daily Delays",
    short_label: "Topic D: Daily Delays",
    chinese_name: "日程延誤",
    causal_role: "Consequence (C ➔ D)",
    description: "Late work arrivals, missed flights, school delays, and cancelled meetings.",
    color: "#7C3AED",
    centroid_x: 75.5, centroid_y: 3.0, centroid_z: 21.0,
    step: 3
});

// 4. Create 16 Vocabulary Nodes with Initial Coordinates and BELONGS_TO links
CREATE (w_node_1:Topic_A:StrikeWord:Word {
    id: "node_1",
    word: "Torrential Downpour",
    chinese: "暴雨傾盆",
    topic_id: "A",
    topic_name: "Heavy Rain",
    cluster_label: "Topic A: Heavy Rain",
    causal_role: "Cause (A ➔ C)",
    historical_source: "City Weather Bureau Report",
    context: "Extreme rainfall overwhelming municipal storm drains within minutes.",
    color: "#0284C7",
    x: -82.0, y: 58.0, z: 28.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_1
MATCH (c:TopicCluster {topic_id: "A"})
CREATE (w_node_1)-[:BELONGS_TO {topic_id: "A"}]->(c);
CREATE (w_node_2:Topic_A:StrikeWord:Word {
    id: "node_2",
    word: "Flash Floods",
    chinese: "突發積水",
    topic_id: "A",
    topic_name: "Heavy Rain",
    cluster_label: "Topic A: Heavy Rain",
    causal_role: "Cause (A ➔ C)",
    historical_source: "Emergency Alert Notification",
    context: "Rapidly rising water levels submerging roads and highway underpasses.",
    color: "#0284C7",
    x: -54.0, y: 68.0, z: 22.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_2
MATCH (c:TopicCluster {topic_id: "A"})
CREATE (w_node_2)-[:BELONGS_TO {topic_id: "A"}]->(c);
CREATE (w_node_3:Topic_A:StrikeWord:Word {
    id: "node_3",
    word: "Heavy Rain",
    chinese: "強降雨",
    topic_id: "A",
    topic_name: "Heavy Rain",
    cluster_label: "Topic A: Heavy Rain",
    causal_role: "Cause (A ➔ C)",
    historical_source: "Morning Commute Advisory",
    context: "Prolonged rainfall severely reducing vehicle braking distance and visibility.",
    color: "#0284C7",
    x: -74.0, y: 32.0, z: 14.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_3
MATCH (c:TopicCluster {topic_id: "A"})
CREATE (w_node_3)-[:BELONGS_TO {topic_id: "A"}]->(c);
CREATE (w_node_4:Topic_A:StrikeWord:Word {
    id: "node_4",
    word: "Flooded Streets",
    chinese: "街道淹水",
    topic_id: "A",
    topic_name: "Heavy Rain",
    cluster_label: "Topic A: Heavy Rain",
    causal_role: "Cause (A ➔ C)",
    historical_source: "Municipal Traffic Camera Feed",
    context: "Deep standing water covering main lanes and preventing vehicle passage.",
    color: "#0284C7",
    x: -46.0, y: 40.0, z: 34.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_4
MATCH (c:TopicCluster {topic_id: "A"})
CREATE (w_node_4)-[:BELONGS_TO {topic_id: "A"}]->(c);
CREATE (w_node_5:Topic_B:StrikeWord:Word {
    id: "node_5",
    word: "High Winds",
    chinese: "狂風大作",
    topic_id: "B",
    topic_name: "High Winds",
    cluster_label: "Topic B: High Winds",
    causal_role: "Cause (B ➔ C)",
    historical_source: "Gale Warning Advisory",
    context: "Severe gale-force gusts buffeting bridges and exposed commuter corridors.",
    color: "#0D9488",
    x: -78.0, y: -36.0, z: -16.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_5
MATCH (c:TopicCluster {topic_id: "B"})
CREATE (w_node_5)-[:BELONGS_TO {topic_id: "B"}]->(c);
CREATE (w_node_6:Topic_B:StrikeWord:Word {
    id: "node_6",
    word: "Fallen Trees",
    chinese: "樹木倒塌",
    topic_id: "B",
    topic_name: "High Winds",
    cluster_label: "Topic B: High Winds",
    causal_role: "Cause (B ➔ C)",
    historical_source: "Public Works Service Log",
    context: "Uprooted trees falling directly across arterial travel avenues.",
    color: "#0D9488",
    x: -48.0, y: -28.0, z: -26.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_6
MATCH (c:TopicCluster {topic_id: "B"})
CREATE (w_node_6)-[:BELONGS_TO {topic_id: "B"}]->(c);
CREATE (w_node_7:Topic_B:StrikeWord:Word {
    id: "node_7",
    word: "Broken Branches",
    chinese: "路面斷枝",
    topic_id: "B",
    topic_name: "High Winds",
    cluster_label: "Topic B: High Winds",
    causal_role: "Cause (B ➔ C)",
    historical_source: "Road Maintenance Dispatch",
    context: "Heavy branches littering intersections and blocking transit pathways.",
    color: "#0D9488",
    x: -72.0, y: -66.0, z: -34.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_7
MATCH (c:TopicCluster {topic_id: "B"})
CREATE (w_node_7)-[:BELONGS_TO {topic_id: "B"}]->(c);
CREATE (w_node_8:Topic_B:StrikeWord:Word {
    id: "node_8",
    word: "Flying Debris",
    chinese: "飛散雜物",
    topic_id: "B",
    topic_name: "High Winds",
    cluster_label: "Topic B: High Winds",
    causal_role: "Cause (B ➔ C)",
    historical_source: "Highway Patrol Incident Record",
    context: "Loose signs and materials blown across multilane traffic lanes.",
    color: "#0D9488",
    x: -44.0, y: -58.0, z: -18.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_8
MATCH (c:TopicCluster {topic_id: "B"})
CREATE (w_node_8)-[:BELONGS_TO {topic_id: "B"}]->(c);
CREATE (w_node_9:Topic_C:StrikeWord:Word {
    id: "node_9",
    word: "Traffic Jam",
    chinese: "交通堵塞",
    topic_id: "C",
    topic_name: "Traffic Gridlock",
    cluster_label: "Topic C: Traffic Gridlock",
    causal_role: "Central Event (A, B ➔ C ➔ D)",
    historical_source: "Metro Transit Broadcast",
    context: "Miles of bumper-to-bumper standstill traffic during rush hour.",
    color: "#EA580C",
    x: -12.0, y: 16.0, z: 12.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_9
MATCH (c:TopicCluster {topic_id: "C"})
CREATE (w_node_9)-[:BELONGS_TO {topic_id: "C"}]->(c);
CREATE (w_node_10:Topic_C:StrikeWord:Word {
    id: "node_10",
    word: "Road Closures",
    chinese: "道路封閉",
    topic_id: "C",
    topic_name: "Traffic Gridlock",
    cluster_label: "Topic C: Traffic Gridlock",
    causal_role: "Central Event (A, B ➔ C ➔ D)",
    historical_source: "Department of Transportation",
    context: "Police barricades closing blocked avenues and detouring vehicles.",
    color: "#EA580C",
    x: 22.0, y: 20.0, z: -10.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_10
MATCH (c:TopicCluster {topic_id: "C"})
CREATE (w_node_10)-[:BELONGS_TO {topic_id: "C"}]->(c);
CREATE (w_node_11:Topic_C:StrikeWord:Word {
    id: "node_11",
    word: "Stalled Cars",
    chinese: "車輛拋錨",
    topic_id: "C",
    topic_name: "Traffic Gridlock",
    cluster_label: "Topic C: Traffic Gridlock",
    causal_role: "Central Event (A, B ➔ C ➔ D)",
    historical_source: "Roadside Assistance Dispatch",
    context: "Disabled and hydroplaned vehicles stranded in active driving lanes.",
    color: "#EA580C",
    x: -8.0, y: -18.0, z: -12.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_11
MATCH (c:TopicCluster {topic_id: "C"})
CREATE (w_node_11)-[:BELONGS_TO {topic_id: "C"}]->(c);
CREATE (w_node_12:Topic_C:StrikeWord:Word {
    id: "node_12",
    word: "Highway Gridlock",
    chinese: "高速癱瘓",
    topic_id: "C",
    topic_name: "Traffic Gridlock",
    cluster_label: "Topic C: Traffic Gridlock",
    causal_role: "Central Event (A, B ➔ C ➔ D)",
    historical_source: "State Highway Traffic Command",
    context: "Total operational standstill across primary expressway corridors.",
    color: "#EA580C",
    x: 24.0, y: -12.0, z: 10.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_12
MATCH (c:TopicCluster {topic_id: "C"})
CREATE (w_node_12)-[:BELONGS_TO {topic_id: "C"}]->(c);
CREATE (w_node_13:Topic_D:StrikeWord:Word {
    id: "node_13",
    word: "Late for Work",
    chinese: "上班遲到",
    topic_id: "D",
    topic_name: "Daily Delays",
    cluster_label: "Topic D: Daily Delays",
    causal_role: "Consequence (C ➔ D)",
    historical_source: "Employee Office Notification",
    context: "Commuters arriving hours late for morning shifts and meetings.",
    color: "#7C3AED",
    x: 58.0, y: 18.0, z: 28.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_13
MATCH (c:TopicCluster {topic_id: "D"})
CREATE (w_node_13)-[:BELONGS_TO {topic_id: "D"}]->(c);
CREATE (w_node_14:Topic_D:StrikeWord:Word {
    id: "node_14",
    word: "Missed Flights",
    chinese: "錯過航班",
    topic_id: "D",
    topic_name: "Daily Delays",
    cluster_label: "Topic D: Daily Delays",
    causal_role: "Consequence (C ➔ D)",
    historical_source: "Airport Terminal Operations",
    context: "Travelers unable to navigate blocked airport roads prior to gate closure.",
    color: "#7C3AED",
    x: 92.0, y: 22.0, z: 14.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_14
MATCH (c:TopicCluster {topic_id: "D"})
CREATE (w_node_14)-[:BELONGS_TO {topic_id: "D"}]->(c);
CREATE (w_node_15:Topic_D:StrikeWord:Word {
    id: "node_15",
    word: "School Delays",
    chinese: "學校停課延期",
    topic_id: "D",
    topic_name: "Daily Delays",
    cluster_label: "Topic D: Daily Delays",
    causal_role: "Consequence (C ➔ D)",
    historical_source: "District School Board Bulletin",
    context: "Bus transit suspended and morning bell times delayed for student safety.",
    color: "#7C3AED",
    x: 62.0, y: -18.0, z: 18.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_15
MATCH (c:TopicCluster {topic_id: "D"})
CREATE (w_node_15)-[:BELONGS_TO {topic_id: "D"}]->(c);
CREATE (w_node_16:Topic_D:StrikeWord:Word {
    id: "node_16",
    word: "Cancelled Meetings",
    chinese: "會議取消",
    topic_id: "D",
    topic_name: "Daily Delays",
    cluster_label: "Topic D: Daily Delays",
    causal_role: "Consequence (C ➔ D)",
    historical_source: "Corporate Schedule Updates",
    context: "Business appointments postponed due to stranded attendees.",
    color: "#7C3AED",
    x: 90.0, y: -10.0, z: 24.0,
    step: 3,
    status: "causally_linked"
})
WITH w_node_16
MATCH (c:TopicCluster {topic_id: "D"})
CREATE (w_node_16)-[:BELONGS_TO {topic_id: "D"}]->(c);

// 5. Create Macro Directed Causal Relationships Between Clusters (Clean without edge labels)
MATCH (src:TopicCluster {topic_id: 'A'}), (tgt:TopicCluster {topic_id: 'C'})
CREATE (src)-[:CAUSES {
    id: 'causal_A_C',
    causal_type: 'PRECONDITION',
    relationship: 'A ➔ C',
    mechanism: "Torrential downpours and flash floods submerge roads, causing widespread traffic gridlock.",
    weight: 3.0,
    step: 3
}]->(tgt);
MATCH (src:TopicCluster {topic_id: 'B'}), (tgt:TopicCluster {topic_id: 'C'})
CREATE (src)-[:CAUSES {
    id: 'causal_B_C',
    causal_type: 'CATALYST',
    relationship: 'B ➔ C',
    mechanism: "High winds topple trees and scatter debris onto streets, blocking travel corridors.",
    weight: 3.0,
    step: 3
}]->(tgt);
MATCH (src:TopicCluster {topic_id: 'C'}), (tgt:TopicCluster {topic_id: 'D'})
CREATE (src)-[:CAUSES {
    id: 'causal_C_D',
    causal_type: 'CONSEQUENCE',
    relationship: 'C ➔ D',
    mechanism: "Severe traffic gridlock paralyzes transportation, making people late for work and causing missed appointments.",
    weight: 3.5,
    step: 3
}]->(tgt);

// 6. Create Micro Semantic Causal Relationships Between Representative Words
MATCH (w1:StrikeWord {id: 'node_1'}), (w2:StrikeWord {id: 'node_9'})
CREATE (w1)-[:LEADS_TO {
    mechanism: "Torrential downpour triggers massive traffic jams",
    type: "MICRO_CAUSAL"
}]->(w2);
MATCH (w1:StrikeWord {id: 'node_2'}), (w2:StrikeWord {id: 'node_10'})
CREATE (w1)-[:LEADS_TO {
    mechanism: "Flash floods force road closures",
    type: "MICRO_CAUSAL"
}]->(w2);
MATCH (w1:StrikeWord {id: 'node_6'}), (w2:StrikeWord {id: 'node_10'})
CREATE (w1)-[:LEADS_TO {
    mechanism: "Fallen trees cause road closures",
    type: "MICRO_CAUSAL"
}]->(w2);
MATCH (w1:StrikeWord {id: 'node_8'}), (w2:StrikeWord {id: 'node_12'})
CREATE (w1)-[:LEADS_TO {
    mechanism: "Flying debris triggers highway gridlock",
    type: "MICRO_CAUSAL"
}]->(w2);
MATCH (w1:StrikeWord {id: 'node_9'}), (w2:StrikeWord {id: 'node_13'})
CREATE (w1)-[:LEADS_TO {
    mechanism: "Traffic jam causes workers to be late",
    type: "MICRO_CAUSAL"
}]->(w2);
MATCH (w1:StrikeWord {id: 'node_10'}), (w2:StrikeWord {id: 'node_14'})
CREATE (w1)-[:LEADS_TO {
    mechanism: "Road closures lead to missed flights",
    type: "MICRO_CAUSAL"
}]->(w2);
MATCH (w1:StrikeWord {id: 'node_12'}), (w2:StrikeWord {id: 'node_16'})
CREATE (w1)-[:LEADS_TO {
    mechanism: "Highway gridlock leads to cancelled meetings",
    type: "MICRO_CAUSAL"
}]->(w2);

// ====================================================================
// Step 3 Queries: Explore the Causal Knowledge Graph
// ====================================================================
// Query 1: Retrieve Macro Causal Backbone (Clusters & Directed Causal Links)
MATCH (c1:TopicCluster)-[r:CAUSES]->(c2:TopicCluster)
RETURN c1.name AS Cause, c2.name AS Effect, r.mechanism AS Mechanism;

// Query 2: Retrieve Full Graph (Clusters, Words, and Causal Connections)
MATCH (c:TopicCluster)<-[:BELONGS_TO]-(w:StrikeWord)
OPTIONAL MATCH (c)-[r:CAUSES]->(c2:TopicCluster)
RETURN c, w, r, c2;