// src/components/HistoryGraph/types.ts
export interface Source {
  url: string;
  title: string;
  snippet: string;
  source_type: string;
  retrieved_at: string;
}

export interface Node {
  id: string;
  time_period: string;
  year: number;
  region: string;
  key_contributors: string[];
  main_idea_summary: string;
  sources: Source[];
}

export interface Edge {
  source_node_id: string;
  target_node_id: string;
  change_description: string;
  weight: number;
  sources: Source[];
}

export interface GraphData {
  concept: string;
  nodes: Node[];
  edges: Edge[];
  metadata: Record<string, unknown>;
}