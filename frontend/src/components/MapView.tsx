import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip } from "react-leaflet";
import type { GraphOut, RouteResult } from "../types";

interface Props {
  graph: GraphOut | null;
  route: RouteResult | null;
  start: string;
  goal: string;
}

const CENTER: [number, number] = [6.98, 79.95];

export default function MapView({ graph, route, start, goal }: Props) {
  if (!graph) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-slate-400">
        Loading graph…
      </div>
    );
  }

  const coordOf = (name: string): [number, number] | null => {
    const n = graph.nodes.find((x) => x.name === name);
    return n ? [n.lat, n.lon] : null;
  };

  const pathLatLngs: [number, number][] =
    route?.path?.map((n) => coordOf(n)).filter((c): c is [number, number] => c !== null) ?? [];

  const expandedSet = new Set(route?.expansion_order ?? []);
  const pathSet = new Set(route?.path ?? []);

  return (
    <MapContainer center={CENTER} zoom={11} className="h-full w-full">
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />

      {graph.edges.map((e, i) => {
        const a = coordOf(e.a);
        const b = coordOf(e.b);
        if (!a || !b) return null;
        return (
          <Polyline
            key={`edge-${i}`}
            positions={[a, b]}
            pathOptions={{ color: "#c9d6d3", weight: 1.2, opacity: 0.7 }}
          />
        );
      })}

      {pathLatLngs.length > 1 && (
        <Polyline
          positions={pathLatLngs}
          pathOptions={{ color: "#028090", weight: 4, opacity: 0.9 }}
        />
      )}

      {graph.nodes.map((n) => {
        const isHospital = n.type === "hospital";
        const isStart = n.name === start;
        const isGoal = n.name === goal;
        const isExpanded = expandedSet.has(n.name);
        const isOnPath = pathSet.has(n.name);

        let color = isHospital ? "#c0392b" : "#5b6c7d";
        let radius = isHospital ? 6 : 3.5;

        if (isExpanded) { color = "#4a6b8a"; radius = 5; }
        if (isOnPath) { color = "#028090"; radius = 6; }
        if (isStart) { color = "#00a896"; radius = 8; }
        if (isGoal) { color = "#c0392b"; radius = 8; }

        return (
          <CircleMarker
            key={n.name}
            center={[n.lat, n.lon]}
            radius={radius}
            pathOptions={{ color, fillColor: color, fillOpacity: 0.9, weight: 1.5 }}
          >
            <Tooltip>{n.name}{n.district ? ` (${n.district})` : ""}</Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
