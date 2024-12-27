// src/components/HistoryGraph/index.tsx
import { useEffect, useState, useCallback } from 'react';
import dagre from 'dagre';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  MarkerType,
  ReactFlowInstance,
} from 'reactflow';
import 'reactflow/dist/style.css';
import CustomNode from './CustomNode';
import CustomEdge from './CustomEdge';
import { GraphData } from './types';

const nodeTypes = {
  custom: CustomNode,
};

const edgeTypes = {
  custom: CustomEdge,
};

interface HistoryGraphProps {
  graphData: GraphData;
}

const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
  const g = new dagre.graphlib.Graph();
  // Increase spacing between nodes
  g.setGraph({ 
    rankdir: 'LR',     // Left to right layout
    ranksep: 500,      // Increased horizontal spacing between nodes (was 200)
    nodesep: 300,      // Increased vertical spacing between nodes (was 100)
    edgesep: 200,      // Add minimum spacing between edges
  });
  g.setDefaultEdgeLabel(() => ({}));

  // Make nodes smaller in the layout calculation
  nodes.forEach((node) => {
    g.setNode(node.id, { width: 100, height: 120 });  // Reduced from 250 width
  });

  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  const positionedNodes = nodes.map((node) => {
    const nodeWithPosition = g.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x,
        y: nodeWithPosition.y,
      },
    };
  });

  return {
    nodes: positionedNodes,
    edges,
  };
};

export default function HistoryGraph({ graphData }: HistoryGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);

  // Update nodes and edges when graphData changes
  useEffect(() => {
    console.log('GraphData updated:', graphData);

    const newNodes = graphData.nodes.map((node) => ({
      id: node.id,
      type: 'custom',
      position: { x: 0, y: 0 },
      data: node,
    }));

    const newEdges = graphData.edges.map((edge, index) => ({
      id: `edge-${index}`,
      source: edge.source_node_id,
      target: edge.target_node_id,
      label: edge.change_description,
      type: 'custom',
      animated: false,
      data: {
        weight: edge.weight,
      },
      style: {
        stroke: '#666',
        strokeWidth: 2,
      },
      markerEnd: MarkerType.ArrowClosed,
    }));

    // Get layouted elements
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      newNodes,
      newEdges
    );

    setNodes(layoutedNodes);
    setEdges(layoutedEdges);

    // Fit view after nodes are updated
    setTimeout(() => {
      if (reactFlowInstance) {
        reactFlowInstance.fitView({
          padding: 0.2,
          duration: 500
        });
      }
    }, 50);
  }, [graphData, reactFlowInstance]);

  const onInit = useCallback((instance: ReactFlowInstance) => {
    setReactFlowInstance(instance);
  }, []);

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{
          padding: 0.2,
          minZoom: 0.1,
          maxZoom: 2,
        }}
        defaultViewport={{
          x: 0,
          y: 0,
          zoom: 1
        }}
        onInit={onInit}
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}