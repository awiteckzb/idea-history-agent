// src/components/HistoryGraph/CustomNode.tsx
import { memo, useState, useRef } from 'react';
import { Handle, Position } from 'reactflow';
import { Node } from './types';

import ExpandedNodeContent from './ExpandedNodeContent';

interface CustomNodeProps {
  data: Node;  // Update this with proper type from your types file
}

export default memo(function CustomNode({ data }: CustomNodeProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const nodeRef = useRef<HTMLDivElement>(null);
  const isHovering = useRef(false);

  const getExpandedPosition = () => {
    if (!nodeRef.current) return { x: 0, y: 0 };
    const rect = nodeRef.current.getBoundingClientRect();
    return {
      x: rect.left + rect.width / 2,
      y: rect.top + rect.height
    };
  };

  // Set up hover timers to prevent instant closing
  const startHover = () => {
    isHovering.current = true;
    setIsExpanded(true);
  };

  const endHover = () => {
    isHovering.current = false;
    // Small delay to check if we've moved to the popup
    setTimeout(() => {
      if (!isHovering.current) {
        setIsExpanded(false);
      }
    }, 100);
  };

  return (
    <div 
      ref={nodeRef}
      className="relative px-3 py-2 shadow-lg rounded-lg bg-white border-2 border-gray-200 w-[250px]"
      onMouseEnter={startHover}
      onMouseLeave={endHover}
    >
      <Handle type="target" position={Position.Left} />
      
      {/* Basic View */}
      <div className="font-bold text-sm border-b pb-1 mb-2 truncate">
        {data.time_period}
      </div>
      <div className="text-xs text-gray-700 overflow-hidden line-clamp-3">
        {data.main_idea_summary}
      </div>

      {/* Expanded View */}
      {isExpanded && (
        <ExpandedNodeContent
          data={data}
          position={getExpandedPosition()}
          onMouseEnter={() => { isHovering.current = true; }}
          onMouseLeave={() => endHover()}
        />
      )}
      
      <Handle type="source" position={Position.Right} />
    </div>
  );
});