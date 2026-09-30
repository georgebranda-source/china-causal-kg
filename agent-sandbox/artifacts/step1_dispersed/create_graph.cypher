// ====================================================================
// Weather & Commuting Disruption: Causal Knowledge Graph (Step 1)
// Visual Representation: 16 Dispersed, Unclustered Everyday Words
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
    word: "Torrential Downpour",
    chinese: "暴雨傾盆",
    historical_source: "City Weather Bureau Report",
    context: "Extreme rainfall overwhelming municipal storm drains within minutes.",
    x: -82.0, y: 58.0, z: 28.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "A",
    latent_topic_name: "Heavy Rain"
});
CREATE (:StrikeWord:Word {
    id: "node_2",
    word: "Flash Floods",
    chinese: "突發積水",
    historical_source: "Emergency Alert Notification",
    context: "Rapidly rising water levels submerging roads and highway underpasses.",
    x: -54.0, y: 68.0, z: 22.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "A",
    latent_topic_name: "Heavy Rain"
});
CREATE (:StrikeWord:Word {
    id: "node_3",
    word: "Heavy Rain",
    chinese: "強降雨",
    historical_source: "Morning Commute Advisory",
    context: "Prolonged rainfall severely reducing vehicle braking distance and visibility.",
    x: -74.0, y: 32.0, z: 14.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "A",
    latent_topic_name: "Heavy Rain"
});
CREATE (:StrikeWord:Word {
    id: "node_4",
    word: "Flooded Streets",
    chinese: "街道淹水",
    historical_source: "Municipal Traffic Camera Feed",
    context: "Deep standing water covering main lanes and preventing vehicle passage.",
    x: -46.0, y: 40.0, z: 34.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "A",
    latent_topic_name: "Heavy Rain"
});
CREATE (:StrikeWord:Word {
    id: "node_5",
    word: "High Winds",
    chinese: "狂風大作",
    historical_source: "Gale Warning Advisory",
    context: "Severe gale-force gusts buffeting bridges and exposed commuter corridors.",
    x: -78.0, y: -36.0, z: -16.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "B",
    latent_topic_name: "High Winds"
});
CREATE (:StrikeWord:Word {
    id: "node_6",
    word: "Fallen Trees",
    chinese: "樹木倒塌",
    historical_source: "Public Works Service Log",
    context: "Uprooted trees falling directly across arterial travel avenues.",
    x: -48.0, y: -28.0, z: -26.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "B",
    latent_topic_name: "High Winds"
});
CREATE (:StrikeWord:Word {
    id: "node_7",
    word: "Broken Branches",
    chinese: "路面斷枝",
    historical_source: "Road Maintenance Dispatch",
    context: "Heavy branches littering intersections and blocking transit pathways.",
    x: -72.0, y: -66.0, z: -34.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "B",
    latent_topic_name: "High Winds"
});
CREATE (:StrikeWord:Word {
    id: "node_8",
    word: "Flying Debris",
    chinese: "飛散雜物",
    historical_source: "Highway Patrol Incident Record",
    context: "Loose signs and materials blown across multilane traffic lanes.",
    x: -44.0, y: -58.0, z: -18.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "B",
    latent_topic_name: "High Winds"
});
CREATE (:StrikeWord:Word {
    id: "node_9",
    word: "Traffic Jam",
    chinese: "交通堵塞",
    historical_source: "Metro Transit Broadcast",
    context: "Miles of bumper-to-bumper standstill traffic during rush hour.",
    x: -12.0, y: 16.0, z: 12.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "C",
    latent_topic_name: "Traffic Gridlock"
});
CREATE (:StrikeWord:Word {
    id: "node_10",
    word: "Road Closures",
    chinese: "道路封閉",
    historical_source: "Department of Transportation",
    context: "Police barricades closing blocked avenues and detouring vehicles.",
    x: 22.0, y: 20.0, z: -10.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "C",
    latent_topic_name: "Traffic Gridlock"
});
CREATE (:StrikeWord:Word {
    id: "node_11",
    word: "Stalled Cars",
    chinese: "車輛拋錨",
    historical_source: "Roadside Assistance Dispatch",
    context: "Disabled and hydroplaned vehicles stranded in active driving lanes.",
    x: -8.0, y: -18.0, z: -12.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "C",
    latent_topic_name: "Traffic Gridlock"
});
CREATE (:StrikeWord:Word {
    id: "node_12",
    word: "Highway Gridlock",
    chinese: "高速癱瘓",
    historical_source: "State Highway Traffic Command",
    context: "Total operational standstill across primary expressway corridors.",
    x: 24.0, y: -12.0, z: 10.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "C",
    latent_topic_name: "Traffic Gridlock"
});
CREATE (:StrikeWord:Word {
    id: "node_13",
    word: "Late for Work",
    chinese: "上班遲到",
    historical_source: "Employee Office Notification",
    context: "Commuters arriving hours late for morning shifts and meetings.",
    x: 58.0, y: 18.0, z: 28.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "D",
    latent_topic_name: "Daily Delays"
});
CREATE (:StrikeWord:Word {
    id: "node_14",
    word: "Missed Flights",
    chinese: "錯過航班",
    historical_source: "Airport Terminal Operations",
    context: "Travelers unable to navigate blocked airport roads prior to gate closure.",
    x: 92.0, y: 22.0, z: 14.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "D",
    latent_topic_name: "Daily Delays"
});
CREATE (:StrikeWord:Word {
    id: "node_15",
    word: "School Delays",
    chinese: "學校停課延期",
    historical_source: "District School Board Bulletin",
    context: "Bus transit suspended and morning bell times delayed for student safety.",
    x: 62.0, y: -18.0, z: 18.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "D",
    latent_topic_name: "Daily Delays"
});
CREATE (:StrikeWord:Word {
    id: "node_16",
    word: "Cancelled Meetings",
    chinese: "會議取消",
    historical_source: "Corporate Schedule Updates",
    context: "Business appointments postponed due to stranded attendees.",
    x: 90.0, y: -10.0, z: 24.0,
    step: 1,
    status: "dispersed_unclustered",
    latent_topic_id: "D",
    latent_topic_name: "Daily Delays"
});

// ====================================================================
// Step 1 Query: Retrieve all 16 dispersed nodes with coordinates
// ====================================================================
MATCH (w:StrikeWord)
RETURN w.id AS id, w.word AS word, w.chinese AS chinese,
       w.x AS x, w.y AS y, w.z AS z, w.historical_source AS source;
