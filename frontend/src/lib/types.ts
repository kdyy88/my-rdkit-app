/**
 * Type definitions for RDKit AI Platform
 */

// AG2 structured molecule response types
export interface MolecularProperties {
  molecular_weight: number;
  logp: number;
  logp_source: string;
  hydrogen_bond_donors: number;
  hydrogen_bond_acceptors: number;
  formula: string;
}

export interface MoleculeVisualization {
  image_base64: string;
  width: number;
  height: number;
}

export interface ToolResult {
  tool_name: string;
  success: boolean;
  data: Record<string, unknown>;
  error?: string | null;
}

export interface MoleculeResponse {
  compound_name?: string | null;
  smiles: string;
  properties?: MolecularProperties | null;
  visualization?: MoleculeVisualization | null;
  summary: string;
  tool_calls: ToolResult[];
}

// Similarity calculation types
export interface SimilarityResult {
  score: number;
  percentage: string;
  status: "High Similarity" | "Common" | "Low Similarity";
}

// Chat types
export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatRequest {
  message: string;
  max_turns?: number;
}

export interface ChatResponse {
  result: MoleculeResponse;
  conversation_history: Array<{ role: string; content: string }>;
  tokens_used?: number | null;
}

// API Error response
export interface ApiError {
  error: string;
  details?: string;
}
