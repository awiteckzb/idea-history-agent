// src/components/HistoryGraph/CustomNode.tsx
import { memo, useState } from 'react';
import { Handle, Position } from 'reactflow';
import { Node } from './types';

interface CustomNodeProps {
  data: Node;  // Update this with proper type from your types file
}
export default memo(function CustomNode({ data }: CustomNodeProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div 
      className="relative px-3 py-2 shadow-lg rounded-lg bg-white border-2 border-gray-200 w-[250px]"  // Fixed width
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      <Handle type="target" position={Position.Left} />
      
      {/* Basic View - Tighter wrapping */}
      <div className="font-bold text-sm border-b pb-1 mb-2 truncate">
        {data.time_period}
      </div>
      <div className="text-xs text-gray-700 overflow-hidden line-clamp-3">
        {data.main_idea_summary}
      </div>

      {/* Expanded View - Positioned better */}
      {isExpanded && (
        <div className="absolute z-10 left-1/2 top-full mt-2 p-4 bg-white shadow-xl rounded-lg w-[300px] transform -translate-x-1/2">
          <div className="text-sm text-gray-600 mb-2">
            <span className="font-semibold">Region:</span> {data.region}
          </div>
          <div className="text-sm text-gray-600 mb-2">
            <span className="font-semibold">Year:</span> {data.year}
          </div>
          <div className="text-sm text-gray-600 mb-2">
            <span className="font-semibold">Contributors:</span>
            <br />
            {data.key_contributors.join(', ')}
          </div>
          <div className="text-sm text-gray-700">
            <span className="font-semibold">Summary:</span>
            <br />
            {data.main_idea_summary}
          </div>
        </div>
      )}
      
      <Handle type="source" position={Position.Right} />
    </div>
  );
});