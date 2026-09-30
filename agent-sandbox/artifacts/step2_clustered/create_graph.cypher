// ====================================================================
// 1920s Chinese Labor Strike Causal Knowledge Graph (Step 2)
// Thematic Topic Clustering: 16 Nodes Grouped into 4 Visible Topics
// Topic Structure: (A: Economic) -> (C: Strike) <- (B: Union)
//                  (C: Strike) -> (D: Paralysis)
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
    name: "Economic Grievances & Inflation",
    short_label: "Topic A: Economic Grievances",
    chinese_name: "生活成本與工資削減",
    causal_role: "Pre-condition / Cause (A -> C)",
    description: "Post-WWI economic depression, soaring rice prices, currency volatility, and unlivable laborer wages.",
    color: "#E11D48",
    centroid_x: -64.0, centroid_y: 48.0, centroid_z: 25.0,
    step: 2
});
CREATE (:TopicCluster {
    id: "Topic_B",
    topic_id: "B",
    name: "Labor Organizing & Solidarity",
    short_label: "Topic B: Labor Organizing",
    chinese_name: "工會組織與工人動員",
    causal_role: "Catalyst / Cause (B -> C)",
    description: "Establishment of labor syndicates, strike committees, boycott manifestos, and picket enforcement.",
    color: "#0D9488",
    centroid_x: -64.0, centroid_y: -48.0, centroid_z: -25.0,
    step: 2
});
CREATE (:TopicCluster {
    id: "Topic_C",
    topic_id: "C",
    name: "Strike Action & Work Stoppage",
    short_label: "Topic C: General Strike Action",
    chinese_name: "全港大罷工行動",
    causal_role: "Central Strike Event (A, B -> C -> D)",
    description: "Mass walkouts, dock shutdowns, street demonstrations, and systemic withdrawal of maritime and municipal labor.",
    color: "#2563EB",
    centroid_x: 5.0, centroid_y: 0.0, centroid_z: 0.0,
    step: 2
});
CREATE (:TopicCluster {
    id: "Topic_D",
    topic_id: "D",
    name: "Harbor Paralysis & Colonial Impact",
    short_label: "Topic D: Harbor & Market Paralysis",
    chinese_name: "港口癱瘓與殖民談判",
    causal_role: "Consequence (C -> D)",
    description: "Harbor standstill, 150+ stranded steamships, commercial food shortages, and imperial legislative negotiations.",
    color: "#7C3AED",
    centroid_x: 76.0, centroid_y: 0.0, centroid_z: 20.0,
    step: 2
});

// 4. Create 16 Clustered Vocabulary Nodes and Connect to Clusters
CREATE (w_node_1:Topic_A:StrikeWord:Word {
    id: "node_1",
    word: "Wage Depression",
    chinese: "工資削滅",
    topic_id: "A",
    topic_name: "Economic Grievances & Inflation",
    cluster_label: "Topic A: Economic Grievances",
    causal_role: "Pre-condition / Cause (A -> C)",
    historical_source: "The China Mail (1921-1922)",
    context: "Stagnant daily laborer wages amidst sharp post-war currency fluctuations.",
    color: "#E11D48",
    x: -78.0, y: 62.0, z: 32.0,
    step: 2,
    status: "clustered"
})
WITH w_node_1
MATCH (c:TopicCluster {topic_id: "A"})
CREATE (w_node_1)-[:BELONGS_TO {topic_id: "A"}]->(c);
CREATE (w_node_2:Topic_A:StrikeWord:Word {
    id: "node_2",
    word: "Rice Inflation",
    chinese: "米價暴漲",
    topic_id: "A",
    topic_name: "Economic Grievances & Inflation",
    cluster_label: "Topic A: Economic Grievances",
    causal_role: "Pre-condition / Cause (A -> C)",
    historical_source: "Hong Kong MMIS Gazette (1922)",
    context: "Skyrocketing price of staple rice threatening subsistence of dock families.",
    color: "#E11D48",
    x: -50.0, y: 64.0, z: 22.0,
    step: 2,
    status: "clustered"
})
WITH w_node_2
MATCH (c:TopicCluster {topic_id: "A"})
CREATE (w_node_2)-[:BELONGS_TO {topic_id: "A"}]->(c);
CREATE (w_node_3:Topic_A:StrikeWord:Word {
    id: "node_3",
    word: "Ten-Hour Shift",
    chinese: "每日十時工制",
    topic_id: "A",
    topic_name: "Economic Grievances & Inflation",
    cluster_label: "Topic A: Economic Grievances",
    causal_role: "Pre-condition / Cause (A -> C)",
    historical_source: "North-China Herald (1923)",
    context: "Exhausting operational hours demanded from maritime and transport coolies.",
    color: "#E11D48",
    x: -76.0, y: 34.0, z: 18.0,
    step: 2,
    status: "clustered"
})
WITH w_node_3
MATCH (c:TopicCluster {topic_id: "A"})
CREATE (w_node_3)-[:BELONGS_TO {topic_id: "A"}]->(c);
CREATE (w_node_4:Topic_A:StrikeWord:Word {
    id: "node_4",
    word: "Living Cost Spiral",
    chinese: "生活昂貴",
    topic_id: "A",
    topic_name: "Economic Grievances & Inflation",
    cluster_label: "Topic A: Economic Grievances",
    causal_role: "Pre-condition / Cause (A -> C)",
    historical_source: "The China Mail (1922)",
    context: "General cost-of-living index surges driving desperate economic petitions.",
    color: "#E11D48",
    x: -52.0, y: 32.0, z: 28.0,
    step: 2,
    status: "clustered"
})
WITH w_node_4
MATCH (c:TopicCluster {topic_id: "A"})
CREATE (w_node_4)-[:BELONGS_TO {topic_id: "A"}]->(c);
CREATE (w_node_5:Topic_B:StrikeWord:Word {
    id: "node_5",
    word: "Seamen's Union",
    chinese: "中華海員工會",
    topic_id: "B",
    topic_name: "Labor Organizing & Solidarity",
    cluster_label: "Topic B: Labor Organizing",
    causal_role: "Catalyst / Cause (B -> C)",
    historical_source: "The China Mail (1922)",
    context: "The central maritime guild led by Su Zhaozheng organizing across Hong Kong and Canton.",
    color: "#0D9488",
    x: -78.0, y: -34.0, z: -18.0,
    step: 2,
    status: "clustered"
})
WITH w_node_5
MATCH (c:TopicCluster {topic_id: "B"})
CREATE (w_node_5)-[:BELONGS_TO {topic_id: "B"}]->(c);
CREATE (w_node_6:Topic_B:StrikeWord:Word {
    id: "node_6",
    word: "Strike Committee",
    chinese: "罷工委員會",
    topic_id: "B",
    topic_name: "Labor Organizing & Solidarity",
    cluster_label: "Topic B: Labor Organizing",
    causal_role: "Catalyst / Cause (B -> C)",
    historical_source: "Canton Gazette (1925)",
    context: "Executive coordinating council managing strike logistics, food rations, and strategy.",
    color: "#0D9488",
    x: -50.0, y: -32.0, z: -28.0,
    step: 2,
    status: "clustered"
})
WITH w_node_6
MATCH (c:TopicCluster {topic_id: "B"})
CREATE (w_node_6)-[:BELONGS_TO {topic_id: "B"}]->(c);
CREATE (w_node_7:Topic_B:StrikeWord:Word {
    id: "node_7",
    word: "Picket Corps",
    chinese: "工人糾察隊",
    topic_id: "B",
    topic_name: "Labor Organizing & Solidarity",
    cluster_label: "Topic B: Labor Organizing",
    causal_role: "Catalyst / Cause (B -> C)",
    historical_source: "The China Mail (1925)",
    context: "Organized worker patrols enforcing the anti-colonial shipping embargo.",
    color: "#0D9488",
    x: -76.0, y: -62.0, z: -32.0,
    step: 2,
    status: "clustered"
})
WITH w_node_7
MATCH (c:TopicCluster {topic_id: "B"})
CREATE (w_node_7)-[:BELONGS_TO {topic_id: "B"}]->(c);
CREATE (w_node_8:Topic_B:StrikeWord:Word {
    id: "node_8",
    word: "Boycott Manifesto",
    chinese: "抵制宣傳宣言",
    topic_id: "B",
    topic_name: "Labor Organizing & Solidarity",
    cluster_label: "Topic B: Labor Organizing",
    causal_role: "Catalyst / Cause (B -> C)",
    historical_source: "Shanghai Municipal Archives (1925)",
    context: "Leaflets distributed across treaty ports calling for national anti-imperial unity.",
    color: "#0D9488",
    x: -52.0, y: -64.0, z: -22.0,
    step: 2,
    status: "clustered"
})
WITH w_node_8
MATCH (c:TopicCluster {topic_id: "B"})
CREATE (w_node_8)-[:BELONGS_TO {topic_id: "B"}]->(c);
CREATE (w_node_9:Topic_C:StrikeWord:Word {
    id: "node_9",
    word: "General Strike",
    chinese: "全港大罷工",
    topic_id: "C",
    topic_name: "Strike Action & Work Stoppage",
    cluster_label: "Topic C: General Strike Action",
    causal_role: "Central Strike Event (A, B -> C -> D)",
    historical_source: "The China Mail (1922)",
    context: "Complete stoppage of maritime and municipal work paralyzing the colony.",
    color: "#2563EB",
    x: -8.0, y: 14.0, z: 10.0,
    step: 2,
    status: "clustered"
})
WITH w_node_9
MATCH (c:TopicCluster {topic_id: "C"})
CREATE (w_node_9)-[:BELONGS_TO {topic_id: "C"}]->(c);
CREATE (w_node_10:Topic_C:StrikeWord:Word {
    id: "node_10",
    word: "Dockworker Walkout",
    chinese: "碼頭工人全體離工",
    topic_id: "C",
    topic_name: "Strike Action & Work Stoppage",
    cluster_label: "Topic C: General Strike Action",
    causal_role: "Central Strike Event (A, B -> C -> D)",
    historical_source: "The China Mail (1922)",
    context: "Stevedores and cargo loaders abandoning British ships in Victoria Harbour.",
    color: "#2563EB",
    x: 20.0, y: 16.0, z: -8.0,
    step: 2,
    status: "clustered"
})
WITH w_node_10
MATCH (c:TopicCluster {topic_id: "C"})
CREATE (w_node_10)-[:BELONGS_TO {topic_id: "C"}]->(c);
CREATE (w_node_11:Topic_C:StrikeWord:Word {
    id: "node_11",
    word: "Work Cessation",
    chinese: "停工停業",
    topic_id: "C",
    topic_name: "Strike Action & Work Stoppage",
    cluster_label: "Topic C: General Strike Action",
    causal_role: "Central Strike Event (A, B -> C -> D)",
    historical_source: "Hong Kong MMIS (1925)",
    context: "Sympathy strikes spreading to domestic servants, tram drivers, and clerks.",
    color: "#2563EB",
    x: -10.0, y: -16.0, z: -10.0,
    step: 2,
    status: "clustered"
})
WITH w_node_11
MATCH (c:TopicCluster {topic_id: "C"})
CREATE (w_node_11)-[:BELONGS_TO {topic_id: "C"}]->(c);
CREATE (w_node_12:Topic_C:StrikeWord:Word {
    id: "node_12",
    word: "Mass Demonstration",
    chinese: "群眾請願示威",
    topic_id: "C",
    topic_name: "Strike Action & Work Stoppage",
    cluster_label: "Topic C: General Strike Action",
    causal_role: "Central Strike Event (A, B -> C -> D)",
    historical_source: "The China Mail (1922)",
    context: "Gatherings of thousands marching through urban centers demanding rights and dignity.",
    color: "#2563EB",
    x: 18.0, y: -14.0, z: 8.0,
    step: 2,
    status: "clustered"
})
WITH w_node_12
MATCH (c:TopicCluster {topic_id: "C"})
CREATE (w_node_12)-[:BELONGS_TO {topic_id: "C"}]->(c);
CREATE (w_node_13:Topic_D:StrikeWord:Word {
    id: "node_13",
    word: "Port Paralysis",
    chinese: "港口海運癱瘓",
    topic_id: "D",
    topic_name: "Harbor Paralysis & Colonial Impact",
    cluster_label: "Topic D: Harbor & Market Paralysis",
    causal_role: "Consequence (C -> D)",
    historical_source: "The China Mail (1922)",
    context: "Over 150 merchant vessels anchored idle with zero cargo discharge capacity.",
    color: "#7C3AED",
    x: 62.0, y: 14.0, z: 25.0,
    step: 2,
    status: "clustered"
})
WITH w_node_13
MATCH (c:TopicCluster {topic_id: "D"})
CREATE (w_node_13)-[:BELONGS_TO {topic_id: "D"}]->(c);
CREATE (w_node_14:Topic_D:StrikeWord:Word {
    id: "node_14",
    word: "Shipping Deadlock",
    chinese: "輪船停航停泊",
    topic_id: "D",
    topic_name: "Harbor Paralysis & Colonial Impact",
    cluster_label: "Topic D: Harbor & Market Paralysis",
    causal_role: "Consequence (C -> D)",
    historical_source: "The China Mail (1925)",
    context: "Complete standstill of coastal and trans-Pacific commercial steamer traffic.",
    color: "#7C3AED",
    x: 90.0, y: 16.0, z: 15.0,
    step: 2,
    status: "clustered"
})
WITH w_node_14
MATCH (c:TopicCluster {topic_id: "D"})
CREATE (w_node_14)-[:BELONGS_TO {topic_id: "D"}]->(c);
CREATE (w_node_15:Topic_D:StrikeWord:Word {
    id: "node_15",
    word: "Market Interruption",
    chinese: "市面商業停滯",
    topic_id: "D",
    topic_name: "Harbor Paralysis & Colonial Impact",
    cluster_label: "Topic D: Harbor & Market Paralysis",
    causal_role: "Consequence (C -> D)",
    historical_source: "Hong Kong Chamber of Commerce (1922)",
    context: "Retail closures, supply shortages, and emergency rationing across Victoria.",
    color: "#7C3AED",
    x: 64.0, y: -16.0, z: 20.0,
    step: 2,
    status: "clustered"
})
WITH w_node_15
MATCH (c:TopicCluster {topic_id: "D"})
CREATE (w_node_15)-[:BELONGS_TO {topic_id: "D"}]->(c);
CREATE (w_node_16:Topic_D:StrikeWord:Word {
    id: "node_16",
    word: "Colonial Concessions",
    chinese: "當局讓步談判",
    topic_id: "D",
    topic_name: "Harbor Paralysis & Colonial Impact",
    cluster_label: "Topic D: Harbor & Market Paralysis",
    causal_role: "Consequence (C -> D)",
    historical_source: "The China Mail (1922)",
    context: "Colonial government and shipping conglomerates agreeing to wage hikes and union recognition.",
    color: "#7C3AED",
    x: 88.0, y: -14.0, z: 22.0,
    step: 2,
    status: "clustered"
})
WITH w_node_16
MATCH (c:TopicCluster {topic_id: "D"})
CREATE (w_node_16)-[:BELONGS_TO {topic_id: "D"}]->(c);

// ====================================================================
// Step 2 Query: Retrieve all Topic Clusters and Member Words
// ====================================================================
MATCH (c:TopicCluster)<-[r:BELONGS_TO]-(w:StrikeWord)
RETURN c, r, w;
