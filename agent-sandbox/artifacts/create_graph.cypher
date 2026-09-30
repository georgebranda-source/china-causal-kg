// ====================================================================
// 1920s Chinese Labor Strike Causal Knowledge Graph (Step 1)
// Visual Representation: 16 Dispersed, Unclustered Vocabulary Nodes
// (Identifying cluster colors & groupings removed for Step 1 baseline)
// ====================================================================

// 1. Schema Constraints & Indexes
CREATE CONSTRAINT word_id_unique IF NOT EXISTS
FOR (w:StrikeWord) REQUIRE w.id IS UNIQUE;

// 2. Clear existing demonstration nodes
MATCH (w:StrikeWord) DETACH DELETE w;

// 3. Create 16 Dispersed Nodes with uniform label :StrikeWord:Word
CREATE (:StrikeWord:Word {
    id: "node_1",
    word: "Wage Depression",
    chinese: "工資削滅",
    historical_source: "The China Mail (1921-1922)",
    context: "Stagnant daily laborer wages amidst sharp post-war currency fluctuations.",
    x: -81.0, y: 82.0, z: -37.7,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "A",
    latent_topic_name: "Economic Grievances & Inflation"
});
CREATE (:StrikeWord:Word {
    id: "node_2",
    word: "Seamen's Union",
    chinese: "中華海員工會",
    historical_source: "The China Mail (1922)",
    context: "The central maritime guild led by Su Zhaozheng organizing across Hong Kong and Canton.",
    x: -17.0, y: 70.0, z: 13.1,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "B",
    latent_topic_name: "Labor Organizing & Solidarity"
});
CREATE (:StrikeWord:Word {
    id: "node_3",
    word: "General Strike",
    chinese: "全港大罷工",
    historical_source: "The China Mail (1922)",
    context: "Complete stoppage of maritime and municipal work paralyzing the colony.",
    x: 20.0, y: 81.0, z: 33.5,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "C",
    latent_topic_name: "Strike Action & Work Stoppage"
});
CREATE (:StrikeWord:Word {
    id: "node_4",
    word: "Port Paralysis",
    chinese: "港口海運癱瘓",
    historical_source: "The China Mail (1922)",
    context: "Over 150 merchant vessels anchored idle with zero cargo discharge capacity.",
    x: 82.0, y: 67.0, z: -36.1,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "D",
    latent_topic_name: "Economic Paralysis & Colonial Impact"
});
CREATE (:StrikeWord:Word {
    id: "node_5",
    word: "Dockworker Walkout",
    chinese: "碼頭工人全體離工",
    historical_source: "The China Mail (1922)",
    context: "Stevedores and cargo loaders abandoning British ships in Victoria Harbour.",
    x: -68.0, y: 18.0, z: 3.4,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "C",
    latent_topic_name: "Strike Action & Work Stoppage"
});
CREATE (:StrikeWord:Word {
    id: "node_6",
    word: "Shipping Deadlock",
    chinese: "輪船停航停泊",
    historical_source: "The China Mail (1925)",
    context: "Complete standstill of coastal and trans-Pacific commercial steamer traffic.",
    x: -31.0, y: 33.0, z: 21.8,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "D",
    latent_topic_name: "Economic Paralysis & Colonial Impact"
});
CREATE (:StrikeWord:Word {
    id: "node_7",
    word: "Rice Inflation",
    chinese: "米價暴漲",
    historical_source: "Hong Kong MMIS Gazette (1922)",
    context: "Skyrocketing price of staple rice threatening subsistence of dock families.",
    x: 33.0, y: 19.0, z: -46.4,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "A",
    latent_topic_name: "Economic Grievances & Inflation"
});
CREATE (:StrikeWord:Word {
    id: "node_8",
    word: "Strike Committee",
    chinese: "罷工委員會",
    historical_source: "Canton Gazette (1925)",
    context: "Executive coordinating council managing strike logistics, food rations, and strategy.",
    x: 68.0, y: 30.0, z: -27.4,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "B",
    latent_topic_name: "Labor Organizing & Solidarity"
});
CREATE (:StrikeWord:Word {
    id: "node_9",
    word: "Picket Corps",
    chinese: "工人糾察隊",
    historical_source: "The China Mail (1925)",
    context: "Organized worker patrols enforcing the anti-colonial shipping embargo.",
    x: -83.0, y: -19.0, z: 11.4,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "B",
    latent_topic_name: "Labor Organizing & Solidarity"
});
CREATE (:StrikeWord:Word {
    id: "node_10",
    word: "Ten-Hour Shift",
    chinese: "每日十時工制",
    historical_source: "North-China Herald (1923)",
    context: "Exhausting operational hours demanded from maritime and transport coolies.",
    x: -20.0, y: -33.0, z: -57.5,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "A",
    latent_topic_name: "Economic Grievances & Inflation"
});
CREATE (:StrikeWord:Word {
    id: "node_11",
    word: "Market Interruption",
    chinese: "市面商業停滯",
    historical_source: "Hong Kong Chamber of Commerce (1922)",
    context: "Retail closures, supply shortages, and emergency rationing across Victoria.",
    x: 18.0, y: -18.0, z: -38.4,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "D",
    latent_topic_name: "Economic Paralysis & Colonial Impact"
});
CREATE (:StrikeWord:Word {
    id: "node_12",
    word: "Work Cessation",
    chinese: "停工停業",
    historical_source: "Hong Kong MMIS (1925)",
    context: "Sympathy strikes spreading to domestic servants, tram drivers, and clerks.",
    x: 81.0, y: -31.0, z: 12.2,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "C",
    latent_topic_name: "Strike Action & Work Stoppage"
});
CREATE (:StrikeWord:Word {
    id: "node_13",
    word: "Colonial Concessions",
    chinese: "當局讓步談判",
    historical_source: "The China Mail (1922)",
    context: "Colonial government and shipping conglomerates agreeing to wage hikes and union recognition.",
    x: -70.0, y: -80.0, z: 51.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "D",
    latent_topic_name: "Economic Paralysis & Colonial Impact"
});
CREATE (:StrikeWord:Word {
    id: "node_14",
    word: "Mass Demonstration",
    chinese: "群眾請願示威",
    historical_source: "The China Mail (1922)",
    context: "Gatherings of thousands marching through urban centers demanding rights and dignity.",
    x: -32.0, y: -69.0, z: -47.9,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "C",
    latent_topic_name: "Strike Action & Work Stoppage"
});
CREATE (:StrikeWord:Word {
    id: "node_15",
    word: "Boycott Manifesto",
    chinese: "抵制宣傳宣言",
    historical_source: "Shanghai Municipal Archives (1925)",
    context: "Leaflets distributed across treaty ports calling for national anti-imperial unity.",
    x: 31.0, y: -83.0, z: 3.2,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "B",
    latent_topic_name: "Labor Organizing & Solidarity"
});
CREATE (:StrikeWord:Word {
    id: "node_16",
    word: "Living Cost Spiral",
    chinese: "生活昂貴",
    historical_source: "The China Mail (1922)",
    context: "General cost-of-living index surges driving desperate economic petitions.",
    x: 67.0, y: -68.0, z: 20.9,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "A",
    latent_topic_name: "Economic Grievances & Inflation"
});

// ====================================================================
// Step 1 Query: Retrieve all 16 dispersed nodes with coordinates
// ====================================================================
MATCH (w:StrikeWord)
RETURN w.id AS id, w.word AS word, w.chinese AS chinese,
       w.x AS x, w.y AS y, w.z AS z, w.historical_source AS source;
