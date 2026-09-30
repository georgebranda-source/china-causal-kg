// ====================================================================
// 1920s Chinese Labor Strike Causal Knowledge Graph (Step 1)
// Visual Representation: 16 Dispersed Words from 1920s Newspaper Press
// Causal Target Structure: (A: Economic) -> (C: Strike) <- (B: Union)
//                          (C: Strike) -> (D: Paralysis)
// ====================================================================

// 1. Schema Constraints & Indexes
CREATE CONSTRAINT word_id_unique IF NOT EXISTS
FOR (w:StrikeWord) REQUIRE w.id IS UNIQUE;

CREATE INDEX word_topic_idx IF NOT EXISTS
FOR (w:StrikeWord) REQUIRE w.topic_id;

// 2. Clear existing demonstration nodes
MATCH (w:StrikeWord) DETACH DELETE w;

// 3. Create 16 Dispersed Nodes (Pre-clustered)
CREATE (:A_Group:StrikeWord:Word {
    id: "node_1",
    word: "Wage Depression",
    chinese: "工資削滅",
    topic_id: "A",
    topic_name: "Economic Grievances & Inflation",
    causal_role: "Cause (A -> C)",
    historical_source: "The China Mail (1921-1922)",
    context: "Stagnant daily laborer wages amidst sharp post-war currency fluctuations.",
    x: -55.0, y: 45.0, z: 60.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:A_Group:StrikeWord:Word {
    id: "node_2",
    word: "Rice Inflation",
    chinese: "米價暴漲",
    topic_id: "A",
    topic_name: "Economic Grievances & Inflation",
    causal_role: "Cause (A -> C)",
    historical_source: "Hong Kong MMIS Gazette (1922)",
    context: "Skyrocketing price of staple rice threatening subsistence of dock families.",
    x: -35.0, y: 75.0, z: 20.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:A_Group:StrikeWord:Word {
    id: "node_3",
    word: "Ten-Hour Shift",
    chinese: "每日十時工制",
    topic_id: "A",
    topic_name: "Economic Grievances & Inflation",
    causal_role: "Cause (A -> C)",
    historical_source: "North-China Herald (1923)",
    context: "Exhausting operational hours demanded from maritime and transport coolies.",
    x: -70.0, y: 20.0, z: 45.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:A_Group:StrikeWord:Word {
    id: "node_4",
    word: "Living Cost Spiral",
    chinese: "生活昂貴",
    topic_id: "A",
    topic_name: "Economic Grievances & Inflation",
    causal_role: "Cause (A -> C)",
    historical_source: "The China Mail (1922)",
    context: "General cost-of-living index surges driving desperate economic petitions.",
    x: -45.0, y: 60.0, z: 80.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:B_Group:StrikeWord:Word {
    id: "node_5",
    word: "Seamen's Union",
    chinese: "中華海員工會",
    topic_id: "B",
    topic_name: "Labor Organizing & Solidarity",
    causal_role: "Cause (B -> C)",
    historical_source: "The China Mail (1922)",
    context: "The central maritime guild led by Su Zhaozheng organizing across Hong Kong and Canton.",
    x: 55.0, y: 60.0, z: -35.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:B_Group:StrikeWord:Word {
    id: "node_6",
    word: "Strike Committee",
    chinese: "罷工委員會",
    topic_id: "B",
    topic_name: "Labor Organizing & Solidarity",
    causal_role: "Cause (B -> C)",
    historical_source: "Canton Gazette (1925)",
    context: "Executive coordinating council managing strike logistics, food rations, and strategy.",
    x: 75.0, y: 30.0, z: -50.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:B_Group:StrikeWord:Word {
    id: "node_7",
    word: "Picket Corps",
    chinese: "工人糾察隊",
    topic_id: "B",
    topic_name: "Labor Organizing & Solidarity",
    causal_role: "Cause (B -> C)",
    historical_source: "The China Mail (1925)",
    context: "Organized worker patrols enforcing the anti-colonial shipping embargo.",
    x: 35.0, y: 80.0, z: -20.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:B_Group:StrikeWord:Word {
    id: "node_8",
    word: "Boycott Manifesto",
    chinese: "抵制宣傳宣言",
    topic_id: "B",
    topic_name: "Labor Organizing & Solidarity",
    causal_role: "Cause (B -> C)",
    historical_source: "Shanghai Municipal Archives (1925)",
    context: "Leaflets distributed across treaty ports calling for national anti-imperial unity.",
    x: 60.0, y: 45.0, z: -70.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:C_Group:StrikeWord:Word {
    id: "node_9",
    word: "General Strike",
    chinese: "全港大罷工",
    topic_id: "C",
    topic_name: "Strike Action & Work Stoppage",
    causal_role: "Central Strike Event (A, B -> C -> D)",
    historical_source: "The China Mail (1922)",
    context: "Complete stoppage of maritime and municipal work paralyzing the colony.",
    x: 15.0, y: -55.0, z: -65.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:C_Group:StrikeWord:Word {
    id: "node_10",
    word: "Dockworker Walkout",
    chinese: "碼頭工人全體離工",
    topic_id: "C",
    topic_name: "Strike Action & Work Stoppage",
    causal_role: "Central Strike Event (A, B -> C -> D)",
    historical_source: "The China Mail (1922)",
    context: "Stevedores and cargo loaders abandoning British ships in Victoria Harbour.",
    x: -25.0, y: -70.0, z: -45.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:C_Group:StrikeWord:Word {
    id: "node_11",
    word: "Work Cessation",
    chinese: "停工停業",
    topic_id: "C",
    topic_name: "Strike Action & Work Stoppage",
    causal_role: "Central Strike Event (A, B -> C -> D)",
    historical_source: "Hong Kong MMIS (1925)",
    context: "Sympathy strikes spreading to domestic servants, tram drivers, and clerks.",
    x: 40.0, y: -65.0, z: -30.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:C_Group:StrikeWord:Word {
    id: "node_12",
    word: "Mass Demonstration",
    chinese: "群眾請願示威",
    topic_id: "C",
    topic_name: "Strike Action & Work Stoppage",
    causal_role: "Central Strike Event (A, B -> C -> D)",
    historical_source: "The China Mail (1922)",
    context: "Gatherings of thousands marching through urban centers demanding rights and dignity.",
    x: -10.0, y: -40.0, z: -85.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:D_Group:StrikeWord:Word {
    id: "node_13",
    word: "Port Paralysis",
    chinese: "港口海運癱瘓",
    topic_id: "D",
    topic_name: "Economic Paralysis & Colonial Impact",
    causal_role: "Consequence (C -> D)",
    historical_source: "The China Mail (1922)",
    context: "Over 150 merchant vessels anchored idle with zero cargo discharge capacity.",
    x: 45.0, y: -30.0, z: 75.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:D_Group:StrikeWord:Word {
    id: "node_14",
    word: "Shipping Deadlock",
    chinese: "輪船停航停泊",
    topic_id: "D",
    topic_name: "Economic Paralysis & Colonial Impact",
    causal_role: "Consequence (C -> D)",
    historical_source: "The China Mail (1925)",
    context: "Complete standstill of coastal and trans-Pacific commercial steamer traffic.",
    x: 70.0, y: -45.0, z: 50.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:D_Group:StrikeWord:Word {
    id: "node_15",
    word: "Market Interruption",
    chinese: "市面商業停滯",
    topic_id: "D",
    topic_name: "Economic Paralysis & Colonial Impact",
    causal_role: "Consequence (C -> D)",
    historical_source: "Hong Kong Chamber of Commerce (1922)",
    context: "Retail closures, supply shortages, and emergency rationing across Victoria.",
    x: 20.0, y: -60.0, z: 65.0,
    step: 1,
    status: "dispersed_unclustered"
});
CREATE (:D_Group:StrikeWord:Word {
    id: "node_16",
    word: "Colonial Concessions",
    chinese: "當局讓步談判",
    topic_id: "D",
    topic_name: "Economic Paralysis & Colonial Impact",
    causal_role: "Consequence (C -> D)",
    historical_source: "The China Mail (1922)",
    context: "Colonial government and shipping conglomerates agreeing to wage hikes and union recognition.",
    x: 65.0, y: -15.0, z: 85.0,
    step: 1,
    status: "dispersed_unclustered"
});

// ====================================================================
// Step 1 Query: Retrieve all 16 dispersed nodes with 3D coordinates
// ====================================================================
MATCH (w:StrikeWord)
RETURN w.id AS id, w.word AS word, w.chinese AS chinese,
       w.topic_id AS topic_id, w.topic_name AS topic_name,
       w.x AS x, w.y AS y, w.z AS z, w.causal_role AS causal_role;
