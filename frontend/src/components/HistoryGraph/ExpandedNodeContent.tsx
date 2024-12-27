// src/components/HistoryGraph/ExpandedNodeContent.tsx
// First, create a new component for the expanded content
import { createPortal } from 'react-dom';
import { Node } from './types';

export default function ExpandedNodeContent({ 
  data, 
  position, 
  onMouseEnter,
  onMouseLeave
}: {
  data: Node;
  position: { x: number; y: number };
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}) {

  return createPortal(
    <div 
      className="expanded-node-content fixed z-50 bg-white shadow-xl rounded-lg w-[400px]"
      style={{
        top: `${position.y}px`,
        left: `${position.x}px`,
        maxHeight: '60vh',
        transform: 'translate(-50%, 20px)',
      }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <div className="overflow-y-auto" style={{ maxHeight: 'calc(60vh - 40px)' }}>
        <div className="p-4">
          {/* Basic Info */}
          <div className="mb-4">
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
            <div className="text-sm text-gray-700 mb-4">
              <span className="font-semibold">Summary:</span>
              <br />
              {data.main_idea_summary}
            </div>
          </div>

          {/* Sources Section */}
          <div className="border-t pt-3">
            <div className="font-semibold text-sm mb-2 text-gray-700">
              Sources ({data.sources.length}):
            </div>
            {data.sources.map((source, index) => (
              <div key={index} className="mb-3 pb-3 border-b border-gray-100 last:border-b-0">
                <a 
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:text-blue-800 font-medium mb-1 block"
                >
                  {source.title}
                </a>
                <div className="text-xs text-gray-600">
                  {source.snippet}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {source.source_type} • {new Date(source.retrieved_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}