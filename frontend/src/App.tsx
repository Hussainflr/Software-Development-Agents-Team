import { FormEvent, useEffect, useMemo, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const AGENTS = [
  "Planner Agent",
  "Backend Agent",
  "Frontend Agent",
  "Reviewer Agent",
  "Security Agent",
  "Tester Agent",
  "Evaluator Agent",
  "Deployment Agent",
];

const EXAMPLE_PROMPTS = [
  "Build a FastAPI task tracker with a React dashboard, tests, review, and Docker setup.",
  "Create a Rock Paper Scissors game with an API endpoint, frontend controls, tests, and deployment files.",
  "Build a small inventory app with CRUD APIs, a simple UI, validation, tests, and Docker Compose.",
];

const RUN_FLOW = ["Plan", "Build", "Review", "Test", "Evaluate", "Approve", "Deploy"];
const ACTIVE_RUN_STATUSES = ["running", "waiting_approval", "deployment"];

const STAGE_PROGRESS: Record<string, number> = {
  requirement: 5,
  planning: 12,
  backend: 24,
  backend_revision: 30,
  frontend: 40,
  frontend_revision: 45,
  review: 55,
  security: 65,
  testing: 75,
  evaluation: 82,
  deployment_approval: 88,
  deployment: 92,
  completed: 100,
  stopped: 0,
  interrupted: 0,
};

type ProviderOption = {
  id: string;
  label: string;
  default_model: string;
  requires_api_key: boolean;
  api_key_configured: boolean;
};

type ProvidersResponse = {
  default_provider: string;
  default_model: string;
  options: ProviderOption[];
  ollama_running: boolean;
  ollama_models: string[];
  detected_model: string | null;
  suggested_provider: string;
  suggested_model: string;
  max_parallel_runs: number;
  active_run_count: number;
  message: string;
};

type Run = {
  id: number;
  requirement: string;
  provider: string;
  model: string;
  status: string;
  current_stage: string;
  approved_for_deployment: boolean;
  stop_requested: boolean;
  error: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
};

type AgentStatus = {
  agent_name: string;
  status: string;
  updated_at: string;
};

type Log = {
  id: number;
  timestamp: string;
  agent_name: string;
  action: string;
  status: string;
  output_summary: string;
};

type GeneratedFile = {
  id: number;
  path: string;
  content: string;
  agent_name: string;
  created_at: string;
};

type Message = {
  id: number;
  timestamp: string;
  agent_name: string;
  role: string;
  content: string;
};

type ContextSnapshot = {
  id: number;
  timestamp: string;
  agent_name: string;
  payload_json: string;
};

type Evaluation = {
  id: number;
  timestamp: string;
  correctness: number;
  completeness: number;
  code_quality: number;
  passed: boolean;
  summary: string;
};

type MemoryItem = {
  id: number;
  key?: string;
  category?: string;
  value?: string;
  summary?: string;
  updated_at?: string;
  created_at?: string;
  source_run_id?: number | null;
};

type RunDetail = Run & {
  statuses: AgentStatus[];
  logs: Log[];
  files: GeneratedFile[];
  messages: Message[];
  contexts: ContextSnapshot[];
  short_term_memory: MemoryItem[];
  long_term_memory: MemoryItem[];
  evaluations: Evaluation[];
};

type ValidationResult = {
  allowed: boolean;
  reason: string;
  guidance: string;
};

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

function formatTime(value?: string) {
  if (!value) return "n/a";
  return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function logSummary(value: string) {
  try {
    const payload = JSON.parse(value);
    return payload.summary ?? value;
  } catch {
    return value;
  }
}

function parseJsonObject(value?: string): Record<string, unknown> | null {
  if (!value) return null;
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed as Record<string, unknown> : null;
  } catch {
    return null;
  }
}

function asText(value: unknown) {
  if (typeof value === "string") return value;
  if (value === null || value === undefined) return "";
  return JSON.stringify(value, null, 2);
}

function compactText(value?: string, max = 280) {
  if (!value) return "";
  const normalized = value.replace(/\s+/g, " ").trim();
  return normalized.length > max ? `${normalized.slice(0, max).trim()}...` : normalized;
}

function memoryLabel(item: MemoryItem) {
  const raw = item.key ?? item.category ?? "memory";
  const parts = raw.split(":");
  if (parts[0] === "context") return `${parts[1] ?? "Agent"} context`;
  if (parts[0] === "output") return `${parts[1] ?? "Agent"} output`;
  if (raw === "latest_evaluation") return "Latest evaluation";
  return raw.replaceAll("_", " ");
}

function memoryMeta(item: MemoryItem) {
  const raw = item.key ?? item.category ?? "";
  const parts = raw.split(":");
  if (parts.length >= 3) return parts.slice(2).join(" -> ");
  if (item.source_run_id) return `Run ${item.source_run_id}`;
  return item.updated_at ? formatTime(item.updated_at) : item.created_at ? formatTime(item.created_at) : "";
}

function memoryBody(item: MemoryItem) {
  const value = item.value ?? item.summary ?? "";
  const parsed = parseJsonObject(value);
  if (parsed?.summary) return asText(parsed.summary);
  if (parsed) return JSON.stringify(parsed, null, 2);
  return value;
}

function isActiveRun(run: Run) {
  return ACTIVE_RUN_STATUSES.includes(run.status);
}

function runTone(run: Run) {
  if (run.status === "completed") return "success";
  if (["failed", "interrupted"].includes(run.status)) return "danger";
  if (run.status === "stopped") return "neutral";
  if (run.status === "waiting_approval") return "approval";
  if (isActiveRun(run)) return "running";
  return "neutral";
}

function statusTone(status: string) {
  if (["completed", "success", "online", "connected"].includes(status)) return "success";
  if (["failed", "error", "offline", "unavailable"].includes(status)) return "danger";
  if (["running", "thinking", "working", "waiting_approval", "warning", "stopped", "interrupted"].includes(status)) return "warning";
  return "neutral";
}

function progressFor(run: Run | RunDetail | null, statuses: Record<string, string>) {
  if (!run) return { value: 0, label: "No active run" };
  if (run.status === "completed") return { value: 100, label: "Completed" };
  if (run.status === "failed") return { value: Math.max(STAGE_PROGRESS[run.current_stage] ?? 5, 5), label: "Failed" };
  if (run.status === "stopped") return { value: Math.max(STAGE_PROGRESS[run.current_stage] ?? 5, 5), label: "Stopped" };
  if (run.status === "interrupted") return { value: Math.max(STAGE_PROGRESS[run.current_stage] ?? 5, 5), label: "Interrupted" };

  const completedAgents = Object.values(statuses).filter((status) => status === "completed").length;
  const value = Math.min((STAGE_PROGRESS[run.current_stage] ?? 5) + Math.min(completedAgents * 5, 20), 99);
  const labels: Record<string, string> = {
    requirement: "Requirement accepted",
    planning: "Planning",
    backend: "Backend",
    backend_revision: "Backend revision",
    frontend: "Frontend",
    frontend_revision: "Frontend revision",
    review: "Review",
    security: "Security review",
    testing: "Testing",
    evaluation: "Evaluation",
    deployment_approval: "Waiting approval",
    deployment: "Deployment",
  };
  return { value, label: labels[run.current_stage] ?? "Running" };
}

export function App() {
  const [providers, setProviders] = useState<ProvidersResponse | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [requirement, setRequirement] = useState("");
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("auto");
  const [tab, setTab] = useState("logs");
  const [selectedFile, setSelectedFile] = useState("");
  const [selectedContext, setSelectedContext] = useState<number | null>(null);
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<ProvidersResponse>("/api/providers")
      .then((data) => {
        setProviders(data);
        setProvider(data.default_provider);
        setModel(data.default_model);
      })
      .catch((error) => setNotice(error.message));
  }, []);

  const refreshRuns = () => {
    api<Run[]>("/api/runs?limit=20")
      .then((data) => setRuns(data))
      .catch((error) => setNotice(error.message));
  };

  useEffect(refreshRuns, []);

  useEffect(() => {
    if (!selectedRunId) return;
    setTab("logs");
    setSelectedFile("");
    setSelectedContext(null);
    let cancelled = false;
    const load = () => {
      api<RunDetail>(`/api/runs/${selectedRunId}`)
        .then((data) => {
          if (!cancelled) {
            setDetail(data);
            setSelectedFile((current) => current || data.files[0]?.path || "");
            setSelectedContext((current) => current ?? data.contexts.at(-1)?.id ?? null);
          }
        })
        .catch((error) => setNotice(error.message));
    };
    load();
    const timer = window.setInterval(load, 2500);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [selectedRunId]);

  const selectedProvider = providers?.options.find((item) => item.id === provider);
  const modelOptions = useMemo(() => {
    if (provider !== "ollama") return [];
    return Array.from(new Set([providers?.detected_model, ...(providers?.ollama_models ?? []), "auto"].filter(Boolean))) as string[];
  }, [provider, providers]);

  const statuses = useMemo(
    () => Object.fromEntries((detail?.statuses ?? []).map((item) => [item.agent_name, item.status])),
    [detail],
  );
  const progress = progressFor(detail, statuses);
  const latestEval = detail?.evaluations.at(-1);
  const activeRunCount = runs.filter(isActiveRun).length;
  const maxParallelRuns = providers?.max_parallel_runs ?? 5;
  const creationLimitReached = activeRunCount >= maxParallelRuns;
  const displayedRuns = useMemo(
    () => [...runs].sort((a, b) => {
      const activeDelta = Number(isActiveRun(b)) - Number(isActiveRun(a));
      if (activeDelta !== 0) return activeDelta;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    }),
    [runs],
  );
  const selectedFileData = detail?.files.find((file) => file.path === selectedFile);
  const selectedContextData = detail?.contexts.find((context) => context.id === selectedContext);
  const orderedContexts = useMemo(
    () => [...(detail?.contexts ?? [])].sort((a, b) => b.id - a.id),
    [detail],
  );

  async function startRun(event: FormEvent) {
    event.preventDefault();
    if (creationLimitReached) {
      setNotice(`${activeRunCount} runs are already active. Finish, stop, or approve one before starting another.`);
      return;
    }
    setBusy(true);
    setNotice("");
    try {
      const validation = await api<ValidationResult>("/api/requirements/validate", {
        method: "POST",
        body: JSON.stringify({ requirement }),
      });
      if (!validation.allowed) {
        setNotice(`${validation.reason} ${validation.guidance}`);
        return;
      }
      const created = await api<Run>("/api/runs", {
        method: "POST",
        body: JSON.stringify({ requirement, provider, model }),
      });
      setTab("logs");
      setSelectedRunId(created.id);
      refreshRuns();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Could not start run.");
    } finally {
      setBusy(false);
    }
  }

  async function runAction(action: "approve-deployment" | "stop" | "restart" | "resume") {
    if (!detail) return;
    setBusy(true);
    setNotice("");
    try {
      const result = await api<{ run?: Run } | Run>(`/api/runs/${detail.id}/${action}`, { method: "POST" });
      if ("id" in result) setSelectedRunId(result.id);
      refreshRuns();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Action failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">M</div>
          <div>
            <strong>Mission Control</strong>
            <span>Agentic OS</span>
          </div>
        </div>

        <section className="side-section">
          <label>Provider</label>
          <select value={provider} onChange={(event) => setProvider(event.target.value)}>
            {(providers?.options ?? [{ id: "ollama", label: "Ollama" } as ProviderOption]).map((item) => (
              <option key={item.id} value={item.id}>{item.label}</option>
            ))}
          </select>

          <label>Model</label>
          {provider === "ollama" && modelOptions.length ? (
            <select value={model} onChange={(event) => setModel(event.target.value)}>
              {modelOptions.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          ) : (
            <input value={model} onChange={(event) => setModel(event.target.value)} />
          )}
          <div className={`status-pill ${providers?.ollama_running ? "success" : "danger"}`}>
            Ollama {providers?.ollama_running ? "online" : "offline"}
          </div>
          {selectedProvider?.requires_api_key && !selectedProvider.api_key_configured ? (
            <div className="hint">API key missing</div>
          ) : null}
        </section>

        <section className="side-section recent-runs-section">
          <div className="side-section-head">
            <h3>Recent runs</h3>
            <span>{activeRunCount}/{maxParallelRuns}</span>
          </div>
          <div className={`active-runs-meter ${creationLimitReached ? "full" : ""}`}>
            {creationLimitReached
              ? "Parallel run limit reached"
              : `${Math.max(maxParallelRuns - activeRunCount, 0)} run slot${maxParallelRuns - activeRunCount === 1 ? "" : "s"} available`}
          </div>
          <div className="run-list">
            {displayedRuns.map((run) => (
              <button
                className={`run-item ${run.id === selectedRunId ? "active" : ""} ${runTone(run)}`}
                key={run.id}
                onClick={() => {
                  setTab("logs");
                  setSelectedRunId(run.id);
                }}
              >
                <span>
                  Run {run.id}
                  {isActiveRun(run) ? <i>Running</i> : null}
                </span>
                <small>{run.status.replace("_", " ")} · {run.current_stage} · {formatTime(run.created_at)}</small>
              </button>
            ))}
          </div>
        </section>
      </aside>

      <section className="content">
        <header className="hero">
          <div>
            <span className="eyebrow">Local-first AI software team</span>
            <h1>Mission Control</h1>
          </div>
          <div className="hero-note">
            <strong>Clean workspace</strong>
            <span>Start a new run or open one from Recent runs when you are ready.</span>
          </div>
        </header>

        {notice ? <div className="notice">{notice}</div> : null}

        <section className="grid two">
          <form className="panel requirement-panel" onSubmit={startRun}>
            <div className="section-head">
              <span>{detail ? "Manager input" : "Ready to build"}</span>
              <strong>{detail ? "New run" : "Describe the outcome"}</strong>
            </div>
            {activeRunCount ? (
              <div className={`parallel-note ${creationLimitReached ? "blocked" : ""}`}>
                {creationLimitReached
                  ? `${activeRunCount} runs are already active. You can draft here, but launch is disabled until one finishes, stops, or gets approved.`
                  : `${activeRunCount} active run${activeRunCount === 1 ? "" : "s"}. You can start ${maxParallelRuns - activeRunCount} more parallel run${maxParallelRuns - activeRunCount === 1 ? "" : "s"}.`}
              </div>
            ) : null}
            <textarea
              value={requirement}
              onChange={(event) => setRequirement(event.target.value)}
              placeholder="Build a FastAPI task tracker with a React dashboard, tests, review, and Docker setup."
            />
            <div className="examples">
              <span>Try one:</span>
              {EXAMPLE_PROMPTS.map((example) => (
                <button key={example} type="button" onClick={() => setRequirement(example)}>
                  {example}
                </button>
              ))}
            </div>
            <button className="primary" disabled={busy || creationLimitReached || !requirement.trim()}>
              {busy ? "Starting..." : creationLimitReached ? "Parallel Limit Reached" : "Start Run"}
            </button>
          </form>

          <section className="panel featured-run">
            {detail ? (
              <>
                <div className="section-head">
                  <span>Active run</span>
                  <strong>Run {detail.id}</strong>
                </div>
                <div className="progress-card">
                  <div>
                    <strong>{progress.label}</strong>
                    <span>{progress.value}% complete</span>
                  </div>
                  <div className="progress-track"><div style={{ width: `${progress.value}%` }} /></div>
                </div>
                <div className="kpis">
                  <Metric label="Status" value={detail.status} />
                  <Metric label="Stage" value={detail.current_stage} />
                  <Metric label="Agents done" value={`${Object.values(statuses).filter((item) => item === "completed").length}/${AGENTS.length}`} />
                  <Metric label="Quality" value={latestEval ? (latestEval.passed ? "pass" : "review") : "pending"} />
                </div>
                <div className="actions">
                  <button disabled={busy || detail.status !== "waiting_approval"} onClick={() => runAction("approve-deployment")}>Approve</button>
                  <button disabled={busy || !["failed", "stopped", "interrupted"].includes(detail.status)} onClick={() => runAction("resume")}>Resume</button>
                  <button disabled={busy || !["running", "waiting_approval"].includes(detail.status)} onClick={() => runAction("stop")}>Stop</button>
                  <button disabled={busy} onClick={() => runAction("restart")}>Restart</button>
                </div>
              </>
            ) : (
              <div className="launch-guide">
                <div className="section-head">
                  <span>How this run works</span>
                  <strong>Agent workflow</strong>
                </div>
                <p>
                  Submit a requirement and Mission Control will coordinate the specialist agents, keep logs cleanly separated,
                  and pause before deployment for your approval.
                </p>
                <ol>
                  {RUN_FLOW.map((step) => (
                    <li key={step}>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>
                <div className="launch-note">
                  Logs, artifacts, memory, and evaluations stay empty until you start or open a run.
                </div>
              </div>
            )}
          </section>
        </section>

        {detail ? (
          <>
            <section className="agents">
              {AGENTS.map((agent) => <AgentCard key={agent} name={agent} status={statuses[agent] ?? "idle"} />)}
            </section>

            <section className="panel workspace" key={tab}>
              <nav className="tabs">
                {["logs", "files", "messages", "memory", "evaluation"].map((item) => (
                  <button className={tab === item ? "active" : ""} key={item} onClick={() => setTab(item)}>
                    {item}
                  </button>
                ))}
              </nav>

              {tab === "logs" ? <Logs logs={detail.logs} hasRun /> : null}
              {tab === "files" ? (
                <div className="split">
                  <div className="list">
                    {detail.files.map((file) => (
                      <button className={selectedFile === file.path ? "active" : ""} key={file.id} onClick={() => setSelectedFile(file.path)}>
                        <span>{file.path}</span>
                        <small>{file.agent_name}</small>
                      </button>
                    ))}
                  </div>
                  <pre>{selectedFileData?.content ?? "Generated files will appear here."}</pre>
                </div>
              ) : null}
              {tab === "messages" ? <Messages messages={detail.messages} /> : null}
              {tab === "memory" ? (
                <MemoryContextTab
                  contexts={orderedContexts}
                  selectedContext={selectedContext}
                  selectedContextData={selectedContextData}
                  setSelectedContext={setSelectedContext}
                  shortTermMemory={detail.short_term_memory}
                  longTermMemory={detail.long_term_memory}
                />
              ) : null}
              {tab === "evaluation" ? <Evaluations evaluations={detail.evaluations} /> : null}
            </section>
          </>
        ) : null}
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

function AgentCard({ name, status }: { name: string; status: string }) {
  return (
    <article className={`agent ${statusTone(status)} ${["thinking", "working", "running"].includes(status) ? "is-live" : ""}`}>
      <span>{name}</span>
      <strong>{status}</strong>
    </article>
  );
}

function Logs({ logs, hasRun }: { logs: Log[]; hasRun: boolean }) {
  if (!hasRun) return <div className="empty">No run selected. Logs will appear after you start or open a run.</div>;
  if (!logs.length) return <div className="empty">This run has no activity yet.</div>;
  return (
    <div className="table">
      {logs.slice(-80).reverse().map((log) => (
        <div className="row" key={log.id}>
          <span>{formatTime(log.timestamp)}</span>
          <strong>{log.agent_name}</strong>
          <span>{log.action}</span>
          <p>{logSummary(log.output_summary)}</p>
        </div>
      ))}
    </div>
  );
}

function Messages({ messages }: { messages: Message[] }) {
  if (!messages.length) return <div className="empty">No agent messages yet.</div>;
  return <div className="cards">{messages.map((message) => (
    <article key={message.id}>
      <strong>{message.agent_name}</strong>
      <small>{formatTime(message.timestamp)}</small>
      <p>{message.content}</p>
    </article>
  ))}</div>;
}

function MemoryList({ items }: { items: MemoryItem[] }) {
  if (!items.length) return <div className="empty">No memory stored yet.</div>;
  return <div className="memory-cards">{items.map((item) => (
    <article key={item.id} className="memory-card">
      <div>
        <strong>{memoryLabel(item)}</strong>
        {memoryMeta(item) ? <small>{memoryMeta(item)}</small> : null}
      </div>
      <p>{memoryBody(item)}</p>
    </article>
  ))}</div>;
}

function MemoryContextTab({
  contexts,
  selectedContext,
  selectedContextData,
  setSelectedContext,
  shortTermMemory,
  longTermMemory,
}: {
  contexts: ContextSnapshot[];
  selectedContext: number | null;
  selectedContextData?: ContextSnapshot;
  setSelectedContext: (id: number) => void;
  shortTermMemory: MemoryItem[];
  longTermMemory: MemoryItem[];
}) {
  return (
    <div className="memory-layout">
      <section className="memory-column">
        <div className="memory-summary">
          <Metric label="Short term" value={String(shortTermMemory.length)} />
          <Metric label="Long term" value={String(longTermMemory.length)} />
          <Metric label="Contexts" value={String(contexts.length)} />
        </div>
        <div className="memory-section-head">
          <div>
            <h3>Short-term memory</h3>
            <p>Run-specific notes, outputs, and evaluation state.</p>
          </div>
        </div>
        <MemoryList items={shortTermMemory} />
        <div className="memory-section-head">
          <div>
            <h3>Long-term memory</h3>
            <p>Reusable patterns remembered across runs.</p>
          </div>
        </div>
        <MemoryList items={longTermMemory} />
      </section>
      <section className="context-column">
        <div className="memory-section-head">
          <div>
            <h3>Context sent to agents</h3>
            <p>Latest snapshots are shown first. Select one to see what the agent received.</p>
          </div>
        </div>
        <div className="context-browser">
          <div className="context-list">
            {contexts.length ? contexts.map((context) => {
              const payload = parseJsonObject(context.payload_json);
              const task = asText(payload?.current_task) || "context";
              return (
                <button key={context.id} className={selectedContext === context.id ? "active" : ""} onClick={() => setSelectedContext(context.id)}>
                  <span>{context.agent_name}</span>
                  <small>{task} - {formatTime(context.timestamp)}</small>
                </button>
              );
            }) : <div className="empty">No context snapshots yet.</div>}
          </div>
          <ContextSnapshotView context={selectedContextData} />
        </div>
      </section>
    </div>
  );
}

function ContextSnapshotView({ context }: { context?: ContextSnapshot }) {
  if (!context) return <div className="empty">Select a context snapshot to inspect it.</div>;
  const payload = parseJsonObject(context.payload_json);
  if (!payload) return <pre>{context.payload_json}</pre>;
  const fields: Array<[string, unknown]> = [
    ["Agent", context.agent_name],
    ["Current task", payload.current_task],
    ["Role", payload.agent_role],
    ["Constraints", payload.constraints],
    ["Errors or feedback", payload.errors_or_feedback],
    ["Relevant outputs", payload.relevant_outputs],
    ["User requirement", payload.user_requirement],
  ];
  return (
    <div className="context-detail">
      {fields.map(([label, value]) => {
        const text = asText(value);
        if (!text) return null;
        return (
          <article key={label}>
            <span>{label}</span>
            <p>{text}</p>
          </article>
        );
      })}
    </div>
  );
}

function Evaluations({ evaluations }: { evaluations: Evaluation[] }) {
  if (!evaluations.length) return <div className="empty">Evaluation scores appear after testing.</div>;
  return <div className="cards compact">{evaluations.map((evaluation) => (
    <article key={evaluation.id}>
      <strong>{evaluation.passed ? "Passed" : "Needs review"}</strong>
      <small>{formatTime(evaluation.timestamp)}</small>
      <div className="score-grid">
        <Metric label="Correctness" value={`${evaluation.correctness}/10`} />
        <Metric label="Completeness" value={`${evaluation.completeness}/10`} />
        <Metric label="Code quality" value={`${evaluation.code_quality}/10`} />
      </div>
      <p>{evaluation.summary}</p>
    </article>
  ))}</div>;
}
