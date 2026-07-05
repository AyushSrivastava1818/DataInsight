import { supabase } from "../components/Shared/AuthContext";

// Use a relative API path in development and rely on Vite proxy for /api.
// This avoids cross-origin issues when the app is accessed via localhost or a LAN address.
const API_BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : "/api";
export interface DatasetVersion {
  id: number;
  dataset_id: number;
  version_number: number;
  row_count: number;
  col_count: number;
  file_size: number;
  quality_score: number;
  change_summary: string;
  created_at: string;
  cleaning_logs?: any[];
}

export interface Dataset {
  id: number;
  name: string;
  created_at: string;
  versions: DatasetVersion[];
}

export interface ChatMessage {
  id: number;
  dataset_id: number;
  sender: "user" | "assistant";
  message: string;
  timestamp: string;
}

export interface PreviewData {
  headers: string[];
  types: Record<string, string>;
  null_counts: Record<string, number>;
  row_count: number;
  col_count: number;
  file_size: number;
  quality_score: number;
  data: Record<string, any>[];
}

export interface EDASummary {
  shape: [number, number];
  memory_usage: string;
  null_summary: Record<string, number>;
  dtypes: Record<string, string>;
  descriptive_stats: Record<string, Record<string, any>>;
  categorical_summary: Record<
    string,
    { unique_count: number; top_categories: Record<string, number> }
  >;
  correlation: {
    matrix: Record<string, Record<string, number>>;
    strong_relationships: Array<{
      column1: string;
      column2: string;
      coefficient: number;
      direction: "positive" | "negative";
    }>;
  };
  time_series_detected: string[];
  time_series_data?: {
    date_column: string;
    aggregated_columns: string[];
    data: Array<Record<string, any>>;
  };
}

export interface Insight {
  category: "trend" | "anomaly" | "correlation" | "recommendation";
  title: string;
  description: string;
  importance: "high" | "medium" | "low";
}

const getHeaders = async (
  isMultipart = false,
): Promise<Record<string, string>> => {
  const headers: Record<string, string> = {};
  if (!isMultipart) {
    headers["Content-Type"] = "application/json";
  }
  if (supabase) {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (session?.access_token) {
      headers["Authorization"] = `Bearer ${session.access_token}`;
    }
  }
  return headers;
};

export const api = {
  // Datasets Endpoints
  async uploadDataset(file: File): Promise<DatasetVersion> {
    const formData = new FormData();
    formData.append("file", file);

    const authHeaders = await getHeaders(true); // isMultipart=true → no Content-Type added
    // Only pass headers if we actually have some (e.g. auth token).
    // IMPORTANT: Never manually set Content-Type for multipart/form-data.
    // The browser MUST generate it automatically so it includes the correct boundary string.
    // Passing an empty headers:{} object can cause some browsers to omit the boundary.
    const response = await fetch(`${API_BASE_URL}/datasets/upload`, {
      method: "POST",
      ...(Object.keys(authHeaders).length > 0 ? { headers: authHeaders } : {}),
      body: formData,
    });

    if (!response.ok) {
      const err = await response
        .json()
        .catch(() => ({ detail: "Upload failed." }));
      throw new Error(err.detail || "Failed to upload file.");
    }
    return response.json();
  },

  async listDatasets(): Promise<Dataset[]> {
    const headers = await getHeaders();
    const response = await fetch(`${API_BASE_URL}/datasets`, { headers });
    if (!response.ok) throw new Error("Failed to retrieve datasets.");
    return response.json();
  },

  async getDataset(id: number): Promise<Dataset> {
    const headers = await getHeaders();
    const response = await fetch(`${API_BASE_URL}/datasets/${id}`, { headers });
    if (!response.ok) throw new Error("Failed to retrieve dataset details.");
    return response.json();
  },

  async deleteDataset(id: number): Promise<void> {
    const headers = await getHeaders();
    const response = await fetch(`${API_BASE_URL}/datasets/${id}`, {
      method: "DELETE",
      headers,
    });
    if (!response.ok) throw new Error("Failed to delete dataset.");
  },

  async getPreview(id: number, version?: number): Promise<PreviewData> {
    const query = version ? `?version=${version}` : "";
    const headers = await getHeaders();
    const response = await fetch(
      `${API_BASE_URL}/datasets/${id}/preview${query}`,
      { headers },
    );
    if (!response.ok) throw new Error("Failed to retrieve preview.");
    return response.json();
  },

  // Cleaning Endpoints
  async imputeMissing(
    id: number,
    column: string,
    strategy: string,
  ): Promise<DatasetVersion> {
    const headers = await getHeaders();
    const response = await fetch(
      `${API_BASE_URL}/datasets/${id}/clean/missing-values`,
      {
        method: "POST",
        headers,
        body: JSON.stringify({ column, strategy }),
      },
    );
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Imputation failed.");
    }
    return response.json();
  },

  async removeDuplicates(id: number): Promise<DatasetVersion> {
    const headers = await getHeaders();
    const response = await fetch(
      `${API_BASE_URL}/datasets/${id}/clean/duplicates`,
      {
        method: "POST",
        headers,
      },
    );
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Duplicate removal failed.");
    }
    return response.json();
  },

  async typeCorrection(
    id: number,
    column: string,
    targetType: string,
    dateFormat?: string,
  ): Promise<DatasetVersion> {
    const headers = await getHeaders();
    const response = await fetch(
      `${API_BASE_URL}/datasets/${id}/clean/type-correction`,
      {
        method: "POST",
        headers,
        body: JSON.stringify({
          column,
          target_type: targetType,
          date_format: dateFormat,
        }),
      },
    );
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Type conversion failed.");
    }
    return response.json();
  },

  async handleOutliers(
    id: number,
    column: string,
    method: string,
    strategy: string,
    threshold = 3.0,
  ): Promise<DatasetVersion> {
    const headers = await getHeaders();
    const response = await fetch(
      `${API_BASE_URL}/datasets/${id}/clean/outliers`,
      {
        method: "POST",
        headers,
        body: JSON.stringify({ column, method, strategy, threshold }),
      },
    );
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Outlier handling failed.");
    }
    return response.json();
  },

  async cleanText(
    id: number,
    column: string,
    options: {
      remove_extra_spaces: boolean;
      casing?: string;
      remove_special_chars: boolean;
    },
  ): Promise<DatasetVersion> {
    const headers = await getHeaders();
    const response = await fetch(`${API_BASE_URL}/datasets/${id}/clean/text`, {
      method: "POST",
      headers,
      body: JSON.stringify({ column, ...options }),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Text cleaning failed.");
    }
    return response.json();
  },

  async columnOp(
    id: number,
    action: "rename" | "delete" | "create",
    column: string,
    newName?: string,
    expression?: string,
  ): Promise<DatasetVersion> {
    const headers = await getHeaders();
    const response = await fetch(
      `${API_BASE_URL}/datasets/${id}/clean/column-op`,
      {
        method: "POST",
        headers,
        body: JSON.stringify({ action, column, new_name: newName, expression }),
      },
    );
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Column operation failed.");
    }
    return response.json();
  },

  // EDA Endpoint
  async getEDA(id: number, version?: number): Promise<EDASummary> {
    const query = version ? `?version=${version}` : "";
    const headers = await getHeaders();
    const response = await fetch(`${API_BASE_URL}/datasets/${id}/eda${query}`, {
      headers,
    });
    if (!response.ok) throw new Error("Failed to retrieve EDA stats.");
    return response.json();
  },

  // Insights Endpoint
  async getInsights(id: number, version?: number): Promise<Insight[]> {
    const query = version ? `?version=${version}` : "";
    const headers = await getHeaders();
    const response = await fetch(
      `${API_BASE_URL}/datasets/${id}/insights${query}`,
      { headers },
    );
    if (!response.ok) throw new Error("Failed to retrieve insights.");
    return response.json();
  },

  // Chat Endpoints
  async getChatHistory(id: number): Promise<ChatMessage[]> {
    const headers = await getHeaders();
    const response = await fetch(`${API_BASE_URL}/datasets/${id}/chat`, {
      headers,
    });
    if (!response.ok) throw new Error("Failed to retrieve chat history.");
    return response.json();
  },

  async sendChatMessage(id: number, message: string): Promise<ChatMessage> {
    const headers = await getHeaders();
    const response = await fetch(`${API_BASE_URL}/datasets/${id}/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify({ message }),
    });
    if (!response.ok) throw new Error("Failed to send message.");
    return response.json();
  },

  async clearChat(id: number): Promise<void> {
    const headers = await getHeaders();
    const response = await fetch(`${API_BASE_URL}/datasets/${id}/chat`, {
      method: "DELETE",
      headers,
    });
    if (!response.ok) throw new Error("Failed to clear chat.");
  },

  // Download links helper
  getCSVDownloadUrl(id: number, version?: number): string {
    const query = version ? `?version=${version}` : "";
    return `${API_BASE_URL}/datasets/${id}/reports/csv${query}`;
  },

  getPDFDownloadUrl(id: number, version?: number): string {
    const query = version ? `?version=${version}` : "";
    return `${API_BASE_URL}/datasets/${id}/reports/pdf${query}`;
  },
};
