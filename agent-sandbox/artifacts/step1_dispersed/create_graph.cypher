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
    x: -82.0, y: 58.0, z: 28.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "A",
    latent_topic_name: "Economic Grievances & Inflation"
});
CREATE (:StrikeWord:Word {
    id: "node_2",
    word: "Rice Inflation",
    chinese: "米價暴漲",
    historical_source: "Hong Kong MMIS Gazette (1922)",
    context: "Skyrocketing price of staple rice threatening subsistence of dock families.",
    x: -54.0, y: 68.0, z: 22.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "A",
    latent_topic_name: "Economic Grievances & Inflation"
});
CREATE (:StrikeWord:Word {
    id: "node_3",
    word: "Ten-Hour Shift",
    chinese: "每日十時工制",
    historical_source: "North-China Herald (1923)",
    context: "Exhausting operational hours demanded from maritime and transport coolies.",
    x: -74.0, y: 32.0, z: 14.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "A",
    latent_topic_name: "Economic Grievances & Inflation"
});
CREATE (:StrikeWord:Word {
    id: "node_4",
    word: "Living Cost Spiral",
    chinese: "生活昂貴",
    historical_source: "The China Mail (1922)",
    context: "General cost-of-living index surges driving desperate economic petitions.",
    x: -46.0, y: 40.0, z: 34.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "A",
    latent_topic_name: "Economic Grievances & Inflation"
});
CREATE (:StrikeWord:Word {
    id: "node_5",
    word: "Seamen's Union",
    chinese: "中華海員工會",
    historical_source: "The China Mail (1922)",
    context: "The central maritime guild led by Su Zhaozheng organizing across Hong Kong and Canton.",
    x: -78.0, y: -36.0, z: -16.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "B",
    latent_topic_name: "Labor Organizing & Solidarity"
});
CREATE (:StrikeWord:Word {
    id: "node_6",
    word: "Strike Committee",
    chinese: "罷工委員會",
    historical_source: "Canton Gazette (1925)",
    context: "Executive coordinating council managing strike logistics, food rations, and strategy.",
    x: -48.0, y: -28.0, z: -26.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "B",
    latent_topic_name: "Labor Organizing & Solidarity"
});
CREATE (:StrikeWord:Word {
    id: "node_7",
    word: "Picket Corps",
    chinese: "工人糾察隊",
    historical_source: "The China Mail (1925)",
    context: "Organized worker patrols enforcing the anti-colonial shipping embargo.",
    x: -72.0, y: -66.0, z: -34.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "B",
    latent_topic_name: "Labor Organizing & Solidarity"
});
CREATE (:StrikeWord:Word {
    id: "node_8",
    word: "Boycott Manifesto",
    chinese: "抵制宣傳宣言",
    historical_source: "Shanghai Municipal Archives (1925)",
    context: "Leaflets distributed across treaty ports calling for national anti-imperial unity.",
    x: -44.0, y: -58.0, z: -18.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "B",
    latent_topic_name: "Labor Organizing & Solidarity"
});
CREATE (:StrikeWord:Word {
    id: "node_9",
    word: "General Strike",
    chinese: "全港大罷工",
    historical_source: "The China Mail (1922)",
    context: "Complete stoppage of maritime and municipal work paralyzing the colony.",
    x: -12.0, y: 16.0, z: 12.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "C",
    latent_topic_name: "Strike Action & Work Stoppage"
});
CREATE (:StrikeWord:Word {
    id: "node_10",
    word: "Dockworker Walkout",
    chinese: "碼頭工人全體離工",
    historical_source: "The China Mail (1922)",
    context: "Stevedores and cargo loaders abandoning British ships in Victoria Harbour.",
    x: 22.0, y: 20.0, z: -10.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "C",
    latent_topic_name: "Strike Action & Work Stoppage"
});
CREATE (:StrikeWord:Word {
    id: "node_11",
    word: "Work Cessation",
    chinese: "停工停業",
    historical_source: "Hong Kong MMIS (1925)",
    context: "Sympathy strikes spreading to domestic servants, tram drivers, and clerks.",
    x: -8.0, y: -18.0, z: -12.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "C",
    latent_topic_name: "Strike Action & Work Stoppage"
});
CREATE (:StrikeWord:Word {
    id: "node_12",
    word: "Mass Demonstration",
    chinese: "群眾請願示威",
    historical_source: "The China Mail (1922)",
    context: "Gatherings of thousands marching through urban centers demanding rights and dignity.",
    x: 24.0, y: -12.0, z: 10.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "C",
    latent_topic_name: "Strike Action & Work Stoppage"
});
CREATE (:StrikeWord:Word {
    id: "node_13",
    word: "Port Paralysis",
    chinese: "港口海運癱瘓",
    historical_source: "The China Mail (1922)",
    context: "Over 150 merchant vessels anchored idle with zero cargo discharge capacity.",
    x: 58.0, y: 18.0, z: 28.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "D",
    latent_topic_name: "Harbor Paralysis & Colonial Impact"
});
CREATE (:StrikeWord:Word {
    id: "node_14",
    word: "Shipping Deadlock",
    chinese: "輪船停航停泊",
    historical_source: "The China Mail (1925)",
    context: "Complete standstill of coastal and trans-Pacific commercial steamer traffic.",
    x: 92.0, y: 22.0, z: 14.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "D",
    latent_topic_name: "Harbor Paralysis & Colonial Impact"
});
CREATE (:StrikeWord:Word {
    id: "node_15",
    word: "Market Interruption",
    chinese: "市面商業停滯",
    historical_source: "Hong Kong Chamber of Commerce (1922)",
    context: "Retail closures, supply shortages, and emergency rationing across Victoria.",
    x: 62.0, y: -18.0, z: 18.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "D",
    latent_topic_name: "Harbor Paralysis & Colonial Impact"
});
CREATE (:StrikeWord:Word {
    id: "node_16",
    word: "Colonial Concessions",
    chinese: "當局讓步談判",
    historical_source: "The China Mail (1922)",
    context: "Colonial government and shipping conglomerates agreeing to wage hikes and union recognition.",
    x: 90.0, y: -10.0, z: 24.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "D",
    latent_topic_name: "Harbor Paralysis & Colonial Impact"
});

// ====================================================================
// Step 1 Query: Retrieve all 16 dispersed nodes with coordinates
// ====================================================================
MATCH (w:StrikeWord)
RETURN w.id AS id, w.word AS word, w.chinese AS chinese,
       w.x AS x, w.y AS y, w.z AS z, w.historical_source AS source;
