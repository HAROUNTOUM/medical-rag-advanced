"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { cn } from "@/lib/utils";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
});

type EntityGroup = "disease" | "medication" | "symptom";

interface GraphNode {
  id: string;
  label: string;
  group: EntityGroup;
}

interface GraphLink {
  source: string;
  target: string;
  label: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

interface Props {
  graphData?: GraphData | null;
}

const EMPTY_GRAPH: GraphData = { nodes: [], links: [] };

const GROUP_COLORS: Record<EntityGroup, string> = {
  disease: "#ef4444",
  medication: "#22c55e",
  symptom: "#f59e0b",
};

const GROUP_BADGE_CLASSES: Record<EntityGroup, string> = {
  disease: "bg-red-500/20 text-red-300 border-red-500/30",
  medication: "bg-green-500/20 text-green-300 border-green-500/30",
  symptom: "bg-amber-500/20 text-amber-300 border-amber-500/30",
};

export default function MedicalKnowledgeGraph({ graphData }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const activeGraph = useMemo((): GraphData => {
    if (!graphData || (!graphData.nodes?.length && !graphData.links?.length)) {
      return EMPTY_GRAPH;
    }
    return graphData;
  }, [graphData]);

  useEffect(() => {
    const updateDimensions = () => {
      if (!containerRef.current) return;
      setDimensions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
      });
    };

    updateDimensions();
    const observer = new ResizeObserver(updateDimensions);
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    return () => observer.disconnect();
  }, []);

  const handleNodeClick = useCallback((node: object) => {
    setSelectedNode(node as GraphNode);
  }, []);

  const paintNode = useCallback(
    (node: object, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const graphNode = node as GraphNode & { x?: number; y?: number };
      const radius = 10;
      const group = (graphNode.group as EntityGroup) || "symptom";
      const color = GROUP_COLORS[group];

      ctx.beginPath();
      ctx.arc(graphNode.x ?? 0, graphNode.y ?? 0, radius, 0, 2 * Math.PI, false);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = "rgba(255, 255, 255, 0.35)";
      ctx.lineWidth = 1.5 / globalScale;
      ctx.stroke();

      const fontSize = Math.max(11 / globalScale, 3);
      ctx.font = `${fontSize}px Inter, system-ui, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "#e2e8f0";
      ctx.fillText(
        graphNode.label,
        graphNode.x ?? 0,
        (graphNode.y ?? 0) + radius + fontSize
      );
    },
    []
  );

  const isEmpty = activeGraph.nodes.length === 0;

  return (
    <div className="flex h-full min-h-0 flex-col bg-slate-900 w-full">
      <div className="border-b border-slate-800 px-6 py-4">
        <h2 className="text-lg font-semibold text-white">Knowledge Graph</h2>
        <p className="mt-0.5 text-sm text-slate-400">
          {isEmpty
            ? "Send a message to see live entity relationships"
            : `${activeGraph.nodes.length} entities · ${activeGraph.links.length} relationships`}
        </p>
      </div>

      <div ref={containerRef} className="relative min-h-0 flex-1">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 px-6 text-center">
            <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <p className="text-sm">Graph will populate with live entity relationships after your first query</p>
          </div>
        ) : dimensions.width > 0 && dimensions.height > 0 ? (
          <ForceGraph2D
            graphData={activeGraph}
            width={dimensions.width}
            height={dimensions.height}
            backgroundColor="rgba(15, 23, 42, 1)"
            nodeRelSize={10}
            linkColor={() => "rgba(148, 163, 184, 0.45)"}
            linkWidth={1.5}
            linkDirectionalArrowLength={5}
            linkDirectionalArrowRelPos={1}
            linkLabel={(link) => (link as GraphLink).label}
            linkCanvasObjectMode={() => "after"}
            linkCanvasObject={(link, ctx, globalScale) => {
              const typedLink = link as GraphLink & {
                source: GraphNode & { x?: number; y?: number };
                target: GraphNode & { x?: number; y?: number };
              };
              const start = typedLink.source;
              const end = typedLink.target;
              if (start.x == null || start.y == null || end.x == null || end.y == null) return;
              const textPos = {
                x: start.x + (end.x - start.x) / 2,
                y: start.y + (end.y - start.y) / 2,
              };
              const fontSize = Math.max(9 / globalScale, 2.5);
              ctx.font = `${fontSize}px Inter, system-ui, sans-serif`;
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillStyle = "rgba(148, 163, 184, 0.9)";
              ctx.fillText(typedLink.label, textPos.x, textPos.y);
            }}
            nodeCanvasObject={paintNode}
            nodeCanvasObjectMode={() => "replace"}
            onNodeClick={handleNodeClick}
            cooldownTicks={80}
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.3}
          />
        ) : null}
      </div>

      <div className="border-t border-slate-800 p-4">
        <div className="rounded-xl border border-white/10 bg-white/5 p-4 shadow-xl backdrop-blur-xl">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Entity Inspector
          </h3>

          {selectedNode ? (
            <div className="mt-3 space-y-2">
              <p className="text-lg font-medium text-white">{selectedNode.label}</p>
              <span
                className={cn(
                  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize",
                  GROUP_BADGE_CLASSES[(selectedNode.group as EntityGroup) || "symptom"]
                )}
              >
                {selectedNode.group}
              </span>
            </div>
          ) : (
            <p className="mt-3 text-sm text-slate-400">
              {isEmpty
                ? "No entities yet. Ask a medical question to populate the graph."
                : "Click a node in the graph to inspect its label and clinical group."}
            </p>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="border-t border-slate-800 px-4 py-3">
        <div className="flex gap-4 justify-center">
          {(Object.entries(GROUP_COLORS) as [EntityGroup, string][]).map(([group, color]) => (
            <div key={group} className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-xs text-slate-400 capitalize">{group}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
