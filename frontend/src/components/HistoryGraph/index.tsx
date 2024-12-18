// src/components/HistoryGraph/index.tsx
import { useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import CustomNode from './CustomNode';
import { GraphData } from './types';

const nodeTypes = {
  custom: CustomNode,
};

interface HistoryGraphProps {
  graphData: GraphData;
}

export default function HistoryGraph({ graphData }: HistoryGraphProps) {
  const initialNodes = graphData.nodes.map((node) => ({
    id: node.id,
    type: 'custom',
    position: { x: 0, y: 0 },
    data: node,
  }));

  const initialEdges = graphData.edges.map((edge, index) => ({
    id: `edge-${index}`,
    source: edge.source_node_id,
    target: edge.target_node_id,
    label: edge.change_description,
    type: 'smoothstep',
    animated: true,
  }));

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    const newNodes = nodes.map((node, index) => ({
      ...node,
      position: {
        x: index * 300,
        y: (index % 2) * 200,
      },
    }));
    setNodes(newNodes);
  }, []);

  return (
    <div style={{ width: '100vw', height: '100vh' }}> 
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}