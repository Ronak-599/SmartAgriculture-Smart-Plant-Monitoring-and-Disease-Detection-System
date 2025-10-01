const soilTypes = [
  {
    id: "black_soil",
    name: "Black Soil",
    description: "Black soil, or Regur soil, is rich in clay minerals, calcium carbonate, magnesium, potash, and lime. It has excellent water retention capacity and is highly suitable for cotton cultivation.",
    color: "#2d2d2d",
    characteristics: [
      "High water retention",
      "Rich in nutrients",
      "Clay-like texture",
      "Self-ploughing nature"
    ],
    suitable_crops: ["Cotton", "Sugarcane", "Jowar", "Wheat", "Linseed"],
    regions: ["Vidarbha", "Marathwada"]
  },
  {
    id: "red_soil",
    name: "Red Soil",
    description: "Red soil gets its color from iron oxide. It is generally poor in nitrogen, phosphoric acid, and organic matter but rich in potash. It's porous with good drainage properties.",
    color: "#8B2500",
    characteristics: [
      "Porous and well-drained",
      "Rich in iron oxides",
      "Poor in nitrogen",
      "Sandy to clayey texture"
    ],
    suitable_crops: ["Rice", "Jowar", "Bajra", "Groundnut", "Pulses"],
    regions: ["Western Maharashtra"]
  },
  {
    id: "laterite_soil",
    name: "Laterite Soil",
    description: "Laterite soil is formed under tropical conditions due to intense weathering. It's rich in iron and aluminum but poor in nitrogen, potash, potassium, lime, and magnesium.",
    color: "#BA8759",
    characteristics: [
      "Highly weathered",
      "Rich in iron and aluminum",
      "Poor in organic matter",
      "Acidic nature"
    ],
    suitable_crops: ["Rice", "Cashew", "Coconut", "Rubber", "Mango"],
    regions: ["Konkan"]
  },
  {
    id: "medium_black_soil",
    name: "Medium Black Soil",
    description: "Medium black soil is less clayey than pure black soil but still has good moisture retention and nutrient content. It's versatile and supports a wide range of crops.",
    color: "#4A4A4A",
    characteristics: [
      "Moderate water retention",
      "Well-balanced texture",
      "Good fertility",
      "Mixed clayey and loamy"
    ],
    suitable_crops: ["Cotton", "Wheat", "Bajra", "Jowar", "Pulses"],
    regions: ["North Maharashtra"]
  },
  {
    id: "alluvial_soil",
    name: "Alluvial Soil",
    description: "Alluvial soil is formed by sediment deposited by rivers. It's extremely fertile with high amounts of potash, phosphoric acid, and lime but varying proportions of organic matter.",
    color: "#D3C1AD",
    characteristics: [
      "Very fertile",
      "Rich in minerals",
      "Variable texture",
      "Renewable fertility"
    ],
    suitable_crops: ["Rice", "Wheat", "Sugarcane", "Vegetables", "Oilseeds"],
    regions: ["Various river basins in Maharashtra"]
  }
];

export default soilTypes; 