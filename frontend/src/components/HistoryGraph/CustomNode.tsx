// src/components/HistoryGraph/CustomNode.tsx
import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Node } from './types';

interface CustomNodeProps {
  data: Node;
}

export default memo(function CustomNode({ data }: CustomNodeProps) {
  return (
    <div className="px-4 py-2 shadow-lg rounded-lg bg-white border-2 border-gray-200 min-w-[200px]">
      <Handle type="target" position={Position.Left} />
      <div className="font-bold text-lg border-b pb-2">{data.time_period}</div>
      <div className="text-sm text-gray-600 pt-2">{data.region}</div>
      <div className="text-xs text-gray-500 pt-1">
        {data.key_contributors.join(', ')}
      </div>
      <div className="text-sm mt-2 text-gray-700">
        {data.main_idea_summary}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
});