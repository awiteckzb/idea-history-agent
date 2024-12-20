// src/App.tsx
import { useState } from 'react';
import HistoryGraph from './components/HistoryGraph';
import SearchBar from './components/SearchBar';
import { GraphData } from './components/HistoryGraph/types';

export default function App() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');  // Add status for user feedback

  const handleSearch = async (concept: string) => {
    setIsLoading(true);
    setError(null);
    setGraphData(null);

    try {
      const response = await fetch('http://localhost:8000/research', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ concept, stream: true })
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const eventData = JSON.parse(line.slice(6));
              console.log('Received event:', eventData);

              if (eventData.type === 'error') {
                setError(eventData.data);
                break;
              }

              // Update status based on event type
              switch (eventData.type) {
                case 'start':
                  setStatus('Starting research...');
                  break;
                case 'query':
                  setStatus(`Searching: ${eventData.data.query}`);
                  break;
                case 'sources_found':
                  setStatus(`Found ${eventData.data.count} sources`);
                  break;
                case 'graph_updated':
                  setStatus(`Updating graph: ${eventData.data.nodes} nodes, ${eventData.data.edges} edges`);
                  break;
                case 'complete':
                  setStatus('Research complete');
                  break;
              }

              // Update graph data whenever we receive new graph state
              if (eventData.graph) {
                setGraphData(prevData => {
                  // Only update if the new graph has content
                  if (eventData.graph.nodes.length > 0 || eventData.graph.edges.length > 0) {
                    return eventData.graph;
                  }
                  return prevData;
                });
              }
            } catch (e) {
              console.error('Error parsing event data:', e);
            }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <SearchBar onSearch={handleSearch} isLoading={isLoading} />
      
      {/* Status message */}
      {status && (
        <div className="absolute top-20 left-4 z-10 p-4 bg-blue-100 text-blue-700 rounded-lg">
          {status}
        </div>
      )}
      
      {/* Error message */}
      {error && (
        <div className="absolute top-36 left-4 z-10 p-4 bg-red-100 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {graphData ? (
        <HistoryGraph graphData={graphData} />
      ) : (
        <div className="flex items-center justify-center h-full text-gray-500">
          {isLoading ? 'Generating graph...' : 'Enter a concept to generate a graph'}
        </div>
      )}
    </div>
  );
}