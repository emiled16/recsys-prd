import type {
  DiagnosticResponse,
  ReadinessResponse,
  RecommendationRequest,
  RecommendationResponse,
  TrackingEvent,
} from "../contracts";

const DEFAULT_HEADERS = {
  Accept: "application/json",
  "Content-Type": "application/json",
};

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export class RecsysApiClient {
  constructor(private readonly baseUrl: string) {}

  async recommend(payload: RecommendationRequest): Promise<RecommendationResponse> {
    return this.request<RecommendationResponse>("/recommendations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async emitEvent(payload: TrackingEvent): Promise<{ accepted: boolean; event_id: string }> {
    return this.request("/events", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async readiness(): Promise<ReadinessResponse> {
    return this.request<ReadinessResponse>("/readyz");
  }

  async diagnostics(): Promise<DiagnosticResponse> {
    return this.request<DiagnosticResponse>("/diagnostics");
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        ...DEFAULT_HEADERS,
        ...(init?.headers ?? {}),
      },
    });
    if (!response.ok) {
      throw new ApiError(`Request failed for ${path}`, response.status);
    }
    return (await response.json()) as T;
  }
}

export function createApiClient(): RecsysApiClient {
  return new RecsysApiClient(
    import.meta.env.VITE_RECSYS_API_BASE_URL ?? "http://127.0.0.1:8000",
  );
}
