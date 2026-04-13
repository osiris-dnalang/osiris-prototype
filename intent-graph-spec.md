Intent Graph Specification

Purpose
- Capture decomposed natural language intents as a structured, auditable, and executable graph.

Core schema (JSON)
- root: string (node id)
- nodes: [ Node ]
- created_at: ISO timestamp

Node (object) fields
- id: string (unique node id)
- type: string ("intent" | "action" | "condition" | "parallel" | "decision")
- action: string (semantic action name, e.g., "analyze_repository")
- description: string (human-readable description)
- inputs: object (key/value inputs for this node)
- outputs: object (expected outputs or artifacts)
- params: object (tunable params for the action)
- confidence: number (0.0-1.0)
- source: string ("rule" | "router" | "llm" | "user")
- exec: optional object { tool: string, path: string, args: [str] }
- children: [node_id]
- metadata: object (freeform; e.g., estimated_cost, resources)

Execution semantics
- A node with exec is a leaf actionable task; orchestrator maps exec.tool to an executor adapter.
- Non-leaf nodes coordinate children (sequential by default). "parallel" type allows concurrent execution.
- All decisions default to "dry-run"; execution requires explicit confirmation.

Traceability & Audit
- Capture: original_text, decomposition_rules_used[], prompts (if LLM used), timestamps, and per-node execution logs.
- Store JSON traces alongside results for reproducibility and governance.

Example (high-level): "Analyze repository for security issues and produce a report"
{
  "root": "n0",
  "nodes": [
    {"id":"n0","type":"intent","action":"analyze_repository","description":"Top-level intent: analyze repository for security issues","confidence":0.95,"children":["n1"]},
    {"id":"n1","type":"action","action":"file_scan","description":"Scan filesystem for code files","inputs":{"target":"."},"children":["n2"]},
    {"id":"n2","type":"action","action":"static_analysis","description":"Run static heuristics","children":["n3"]},
    {"id":"n3","type":"action","action":"report","description":"Aggregate findings and write report","exec":{"tool":"osiris-code-analysis-demo","path":"/home/enki/osiris-code-analysis-demo","args":[]},"children":[]}
  ],
  "created_at":"2026-04-13T18:30:00Z"
}

Notes
- Keep the graph small for presentation; expand only when needed.
- Use deterministic rule-based decomposers for initial demos to ensure reproducibility.
