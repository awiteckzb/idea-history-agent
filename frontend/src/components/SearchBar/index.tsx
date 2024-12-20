// src/components/SearchBar/index.tsx
import { useState } from 'react';

interface SearchBarProps {
  onSearch: (concept: string) => void;
  isLoading: boolean;
}

export default function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [concept, setConcept] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (concept.trim()) {
      onSearch(concept.trim());
    }
  };

  return (
    <div className="absolute top-4 left-4 z-10 w-96">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={concept}
          onChange={(e) => setConcept(e.target.value)}
          placeholder="Enter a concept (e.g., democracy, individualism)"
          className="flex-1 px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading}
          className={`px-4 py-2 rounded-lg bg-blue-500 text-white font-medium 
            ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-600'}`}
        >
          {isLoading ? 'Generating...' : 'Generate Graph'}
        </button>
      </form>
    </div>
  );
}