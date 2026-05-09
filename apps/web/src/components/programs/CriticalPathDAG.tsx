"use client";

import React, { useEffect, useState } from 'react';
import { ReactFlow, MiniMap, Controls, Background, useNodesState, useEdgesState, MarkerType } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import { cn } from '@/lib/utils';

// Dagre setup for auto-layout
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 200;
const nodeHeight = 60;

const getLayoutedElements = (nodes: any[], edges: any[], direction = 'LR') => {
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const newNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    const newNode = {
      ...node,
      targetPosition: 'left',
      sourcePosition: 'right',
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
    return newNode;
  });

  return { nodes: newNodes, edges };
};

// Custom Node Component
const CustomNode = ({ data }: { data: any }) => {
  return (
    <div className={cn(
      "px-4 py-2 rounded shadow-md border-2 bg-background min-w-[150px]",
      data.isCritical ? "border-red-500" : "border-border"
    )}>
      <div className="font-bold text-xs">{data.label}</div>
      <div className="text-[10px] text-muted-foreground flex justify-between mt-1">
        <span>Float: {data.float}</span>
        <span>Dur: {data.duration}d</span>
      </div>
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

// Dummy Data
const initialNodes = [
  { id: '1', type: 'custom', data: { label: 'Phase 0 Complete', float: 0, duration: 1, isCritical: true } },
  { id: '2', type: 'custom', data: { label: 'Design Auth', float: 5, duration: 3, isCritical: false } },
  { id: '3', type: 'custom', data: { label: 'Implement Auth', float: 0, duration: 5, isCritical: true } },
  { id: '4', type: 'custom', data: { label: 'Phase 1 Complete', float: 0, duration: 1, isCritical: true } },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: false, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e1-3', source: '1', target: '3', animated: true, markerEnd: { type: MarkerType.ArrowClosed, color: '#ef4444' }, style: { stroke: '#ef4444', strokeWidth: 2 } },
  { id: 'e2-4', source: '2', target: '4', animated: false, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e3-4', source: '3', target: '4', animated: true, markerEnd: { type: MarkerType.ArrowClosed, color: '#ef4444' }, style: { stroke: '#ef4444', strokeWidth: 2 } },
];

export function CriticalPathDAG() {
  const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(initialNodes, initialEdges);
  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges);
  const [isSimulating, setIsSimulating] = useState(false);

  const onNodeDragStop = (event: any, node: any) => {
    // Simulate what-if slip
    setIsSimulating(true);
    setTimeout(() => {
      setNodes((nds) => 
        nds.map((n) => {
          if (n.id === '3' || n.id === '4') {
            return {
              ...n,
              data: { ...n.data, float: -2, isCritical: true },
              className: "ring-2 ring-red-500 ring-offset-2 ring-offset-black"
            };
          }
          return n;
        })
      );
      setIsSimulating(false);
    }, 600);
  };

  return (
    <div className="w-full h-[400px] border border-white/10 rounded-xl bg-black/40 overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDragStop={onNodeDragStop}
        nodeTypes={nodeTypes}
        fitView
        colorMode="dark"
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={12} size={1} color="#ffffff10" />
        <Controls />
      </ReactFlow>
      
      {isSimulating && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-black/80 border border-white/20 px-4 py-2 rounded-full text-xs font-medium text-white shadow-xl backdrop-blur-md flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          Simulating Slip Impact...
        </div>
      )}
    </div>
  );
}
