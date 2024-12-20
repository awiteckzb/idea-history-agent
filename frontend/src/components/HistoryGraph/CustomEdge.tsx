// src/components/HistoryGraph/CustomEdge.tsx
import { memo, useMemo } from 'react';
import { EdgeProps, getBezierPath, MarkerType } from 'reactflow';

interface CustomEdgeProps extends EdgeProps {
  data?: {
    weight?: number;
  };
}

const LABEL_WIDTH = 200;
const LABEL_HEIGHT = 50;
const LABEL_OFFSET_X = LABEL_WIDTH / 2;
const LABEL_OFFSET_Y = 25;

export default memo(function CustomEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  label,
  style = {},
  data,
}: CustomEdgeProps) {
    console.log('CustomEdge being rendered with:', {
        id,
        sourceX,
        sourceY,
        targetX,
        targetY,
        label,
        style,
        data
    });
  const [edgePath, labelX, labelY] = useMemo(() => getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    curvature: 0.05,
  }), [sourceX, sourceY, targetX, targetY]);

  const edgeStyle = useMemo(() => ({
    ...style,
    strokeWidth: data?.weight ? Math.max(1, Math.min(5, data.weight)) : 2,
    markerEnd: MarkerType.ArrowClosed,
  }), [style, data?.weight]);

  return (
    <>
      <path
        id={id}
        style={edgeStyle}
        className="react-flow__edge-path transition-all duration-300"
        d={edgePath}
        aria-label={label ? `Connection: ${label}` : 'Graph connection'}
      />
      {label && (
        <foreignObject
          x={labelX - LABEL_OFFSET_X}
          y={labelY - LABEL_OFFSET_Y}
          width={LABEL_WIDTH}
          height={LABEL_HEIGHT}
          className="overflow-visible"
        >
          <div className="p-2 text-xs bg-white bg-opacity-90 rounded shadow-sm hover:bg-opacity-100 transition-all duration-200">
            <p className="text-center text-gray-700 select-none">
              {label}
            </p>
          </div>
        </foreignObject>
      )}
    </>
  );
});