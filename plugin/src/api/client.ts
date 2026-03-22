import type {
  HealthResponse,
  WorkflowPendingApprovalsResponse,
  WorkflowInvokeRequest,
  WorkflowInvokeResponse,
  WorkflowRollbackRequest,
  WorkflowRollbackResponse,
  WorkflowResumeRequest,
  WorkflowResumeResponse
} from "../contracts.ts";

export class KnowledgeStewardApiError extends Error {
  readonly status: number;
  readonly detail?: string;

  constructor(status: number, detail?: string) {
    super(detail ? `Request failed with status ${status}: ${detail}` : `Request failed with status ${status}`);
    this.name = "KnowledgeStewardApiError";
    this.status = status;
    this.detail = detail;
  }
}

export class KnowledgeStewardApiClient {
  private readonly baseUrl: string;
  private readonly timeoutMs: number;

  constructor(
    baseUrl: string,
    timeoutMs: number
  ) {
    this.baseUrl = baseUrl;
    this.timeoutMs = timeoutMs;
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        ...init,
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          ...(init?.headers ?? {})
        }
      });

      if (!response.ok) {
        throw new KnowledgeStewardApiError(
          response.status,
          await extractErrorDetail(response)
        );
      }

      return (await response.json()) as T;
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new Error(`Request timed out after ${this.timeoutMs}ms`);
      }
      throw error;
    } finally {
      window.clearTimeout(timeout);
    }
  }

  getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>("/health");
  }

  invokeWorkflow(payload: WorkflowInvokeRequest): Promise<WorkflowInvokeResponse> {
    return this.request<WorkflowInvokeResponse>("/workflows/invoke", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }

  resumeWorkflow(payload: WorkflowResumeRequest): Promise<WorkflowResumeResponse> {
    return this.request<WorkflowResumeResponse>("/workflows/resume", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }

  rollbackWorkflow(payload: WorkflowRollbackRequest): Promise<WorkflowRollbackResponse> {
    return this.request<WorkflowRollbackResponse>("/workflows/rollback", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }

  listPendingApprovals(): Promise<WorkflowPendingApprovalsResponse> {
    return this.request<WorkflowPendingApprovalsResponse>("/workflows/pending-approvals");
  }
}

export function formatApiErrorMessage(error: unknown): string {
  if (error instanceof KnowledgeStewardApiError) {
    return error.detail
      ? `Backend error ${error.status}: ${error.detail}`
      : `Backend error ${error.status}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

async function extractErrorDetail(response: Response): Promise<string | undefined> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (payload.detail !== undefined) {
      return JSON.stringify(payload.detail);
    }
  } catch {
    // 后端偶尔会返回空体或非 JSON 错误页，这里静默回落到状态码即可。
  }
  return undefined;
}
