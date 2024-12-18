// src/App.tsx
import HistoryGraph from './components/HistoryGraph';
import sampleData from './sample-data.json';

export default function App() {
  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <HistoryGraph graphData={sampleData} />
    </div>
  );
}