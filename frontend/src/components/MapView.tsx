import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip } from "react-leaflet";
import type { GraphOut, RouteResult } from "../types";

interface Props {
  graph: GraphOut | null;
  route: RouteResult | null;
  start: string;
  goal: string;
}

const CENTER: [number, number] = [6.98, 79.95];
const EXPANSION_STEP_MS = 55;
const PATH_STEP_MS = 90;

export default function MapView({ graph, route, start, goal }: Props) {
  const [revealedExpansionCount, setRevealedExpansionCount] = useState(0);
  const [revealedPathCount, setRevealedPathCount] = useState(0);

  // Depend on `route` itself (object identity), not on start/goal/algorithm:
  // every /api/route response is a freshly-parsed object, even for an
  // identical start/goal/algorithm re-run, so this naturally re-animates on
  // every "Run search" click without needing a separate request-id field.
  useEffect(() => {
    setRevealedExpansionCount(0);
    setRevealedPathCount(0);

    if (!route) return;

    let cancelled = false;
    const timers: ReturnType<typeof setTimeout>[] = [];
    const expansionLength = route.expansion_order?.length ?? 0;
    const pathLength = route.path?.length ?? 0;

    const runPathStep = (i: number) => {
      if (cancelled) return;
      setRevealedPathCount(i);
      if (i < pathLength) {
        timers.push(setTimeout(() => runPathStep(i + 1), PATH_STEP_MS));
      }
    };

    const runExpansionStep = (i: number) => {
      if (cancelled) return;
      setRevealedExpansionCount(i);
      if (i < expansionLength) {
        timers.push(setTimeout(() => runExpansionStep(i + 1), EXPANSION_STEP_MS));
      } else if (pathLength > 0) {
        timers.push(setTimeout(() => runPathStep(1), PATH_STEP_MS));
      }
    };

    if (expansionLength > 0) {
      timers.push(setTimeout(() => runExpansionStep(1), EXPANSION_STEP_MS));
    } else if (pathLength > 0) {
      timers.push(setTimeout(() => runPathStep(1), PATH_STEP_MS));
    }

    return () => {
      cancelled = true;
      timers.forEach(clearTimeout);
    };
  }, [route]);

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

  const expansionLength = route?.expansion_order?.length ?? 0;
  const pathLength = route?.path?.length ?? 0;

  const visibleExpanded = route?.expansion_order?.slice(0, revealedExpansionCount) ?? [];
  const visiblePath = route?.path?.slice(0, revealedPathCount) ?? [];

  const visiblePathLatLngs: [number, number][] = visiblePath
    .map(coordOf)
    .filter((c): c is [number, number] => c !== null);

  const expandedSet = new Set(visibleExpanded);
  const pathSet = new Set(visiblePath);

  // While a route is actively animating (expansion or path phase still
  // running), don't paint start/goal yet — let the reveal finish first, then
  // fall back to always showing the selected start/goal (matches the
  // pre-animation behaviour for the initial/idle map state).
  const animating =
    !!route &&
    (revealedExpansionCount < expansionLength ||
      (pathLength > 0 && revealedPathCount < pathLength));

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

      {visiblePathLatLngs.length > 1 && (
        <Polyline
          positions={visiblePathLatLngs}
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
        if (!animating && isStart) { color = "#00a896"; radius = 8; }
        if (!animating && isGoal) { color = "#c0392b"; radius = 8; }

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
