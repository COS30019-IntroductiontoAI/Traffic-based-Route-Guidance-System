import fs from 'fs';

async function buildMap() {
  // Boroondara Area (Hawthorn, Kew, Camberwell)
  const bbox = "-37.840,145.020,-37.800,145.070";
  const query = `
    [out:json];
    way["highway"~"primary|secondary|tertiary|trunk|residential|unclassified"](${bbox});
    (._;>;);
    out body;
  `;
  
  console.log("Fetching from Overpass API...");
  const res = await fetch("https://overpass-api.de/api/interpreter", {
    method: "POST",
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: "data=" + encodeURIComponent(query)
  });
  const data = await res.json();
  
  const nodes = {}; // id -> {lat, lon, id}
  const ways = [];
  
  data.elements.forEach(el => {
    if (el.type === 'node') {
      nodes[el.id] = el;
    } else if (el.type === 'way') {
      ways.push(el);
    }
  });

  const wayNodesCounts = new Map();
  ways.forEach(way => {
    if(!way.nodes) return;
    way.nodes.forEach(nId => {
       wayNodesCounts.set(nId, (wayNodesCounts.get(nId) || 0) + 1);
    });
  });

  let validNodesMap = new Map();
  let edgesList = [];
  
  ways.forEach(way => {
    const wayNodes = way.nodes;
    if (!wayNodes) return;
    let wayName = way.tags && way.tags.name ? way.tags.name : "Unknown Street";

    let lastIntersectionIndex = 0;

    for (let i = 1; i < wayNodes.length; i++) {
      const isIntersection = wayNodesCounts.get(wayNodes[i]) > 1;
      const isEnd = i === wayNodes.length - 1;

      if (isIntersection || isEnd) {
        const n1 = nodes[wayNodes[lastIntersectionIndex]];
        const n2 = nodes[wayNodes[i]];
        
        if (n1 && n2) {
          validNodesMap.set(n1.id, {...n1, name: wayName});
          validNodesMap.set(n2.id, {...n2, name: wayName});
          
          const dx = (n1.lon - n2.lon) * Math.cos(n1.lat * Math.PI / 180) * 111.32;
          const dy = (n1.lat - n2.lat) * 111.32;
          const dist = Math.sqrt(dx*dx + dy*dy);
          
          // Assumption (i): 60km/h speed limit. Time = distance (km) / 60km/h * 60 minutes = distance in minutes
          // Assumption (iii): 30 seconds (0.5 mins) delay to pass each intersection
          const travelTime = dist + 0.5;
          const weight = Math.max(0.1, travelTime); 
          
          edgesList.push({from: n1.id.toString(), to: n2.id.toString(), weight: Math.round(weight * 100) / 100});
          
          const oneway = way.tags && way.tags.oneway === 'yes';
          if (!oneway) {
            edgesList.push({from: n2.id.toString(), to: n1.id.toString(), weight: Math.round(weight * 100) / 100});
          }
        }
        
        lastIntersectionIndex = i;
      }
    }
  });

  const finalNodes = Array.from(validNodesMap.values()).map(n => ({
    id: n.id.toString(),
    lat: n.lat,
    lng: n.lon,
    x: 0,
    y: 0,
    label: n.name
  }));

  fs.writeFileSync('src/components/route-guidance/nodes.json', JSON.stringify(finalNodes, null, 2));
  fs.writeFileSync('src/components/route-guidance/edges.json', JSON.stringify(edgesList, null, 2));

  console.log(`Successfully wrote ${finalNodes.length} nodes and ${edgesList.length} edges!`);
}

buildMap().catch(console.error);
