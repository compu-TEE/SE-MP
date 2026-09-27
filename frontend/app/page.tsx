"use client";

import { useState } from "react";

type Requirement = {
  id: string;
  statement: string;
  category: string;
  source_stakeholder?: string | null;
  business_justification?: string | null;
  priority?: string | null;
  dependencies: string[];
  assumptions: string[];
  acceptance_criteria: string[];
  applicable_regulations: string[];
  risk_level?: string | null;
  confidence_score?: number | null;
  approval_status: string;
};

type QualityIssue = {
  type: string;
  severity: string;
  description: string;
  affected_requirement?: string | null;
  suggestion: string;
};

type QualityAnalysis = {
  completeness_score: number;
  issues: QualityIssue[];
  summary: string;
};

type ComplianceFinding = {
  requirement_id: string;
  status: string;
  finding: string;
  evidence: string[];
  recommendation: string;
};

type ComplianceAnalysis = {
  findings: ComplianceFinding[];
  summary: string;
};

type RiskFinding = {
  requirement_id: string;
  risk_type: string;
  severity: string;
  description: string;
  mitigation: string;
};

type RiskAnalysis = {
  findings: RiskFinding[];
  summary: string;
};

type Message = {
  role: "user" | "model";
  content: string;
};

export default function Home() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [missingInformation, setMissingInformation] = useState<string[]>([]);
  const [clarificationQuestions, setClarificationQuestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [qualityAnalysis, setQualityAnalysis] = useState<QualityAnalysis | null>(null);
  const [complianceAnalysis, setComplianceAnalysis] = useState<ComplianceAnalysis | null>(null);
  const [riskAnalysis, setRiskAnalysis] = useState<RiskAnalysis | null>(null);
  const [ragQuery, setRagQuery] = useState("");
  const [ragAnswer, setRagAnswer] = useState("");
  const [ragSources, setRagSources] = useState<
    {
      source: string;
      chunk_id: number;
      distance: number;
    }[]
  >([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  const sendMessage = async () => {
    if (!message.trim() || loading) return;

    const userMessage: Message = {
      role: "user",
      content: message,
    };

    const updatedMessages = [...messages, userMessage];

    setMessages(updatedMessages);
    setMessage("");
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: updatedMessages,
        }),
      });

      const data = await res.json();

      const modelMessage: Message = {
        role: "model",
        content: data.response,
      };

      setMessages([...updatedMessages, modelMessage]);

      setRequirements(data.requirements || []);
      setMissingInformation(data.missing_information || []);
      setClarificationQuestions(data.clarification_questions || []);
    } catch (error) {
      setMessages([
        ...updatedMessages,
        {
          role: "model",
          content: "Failed to connect to the backend.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const updateRequirementStatus = (
  id: string,
  status: string
) => {
  setRequirements((current) =>
    current.map((req) =>
      req.id === id
        ? { ...req, approval_status: status }
        : req
    )
  );
};

const startEditing = (req: Requirement) => {
  setEditingId(req.id);
  setEditText(req.statement);
};

const saveEdit = (id: string) => {
  if (!editText.trim()) return;

  setRequirements((current) =>
    current.map((req) =>
      req.id === id
        ? {
            ...req,
            statement: editText.trim(),
          }
        : req
    )
  );

  setEditingId(null);
  setEditText("");
};

const cancelEdit = () => {
  setEditingId(null);
  setEditText("");
};

const regenerateRequirement = async (id: string) => {
  const requirement = requirements.find(
    (req) => req.id === id
  );

  if (!requirement) return;

  setLoading(true);

  try {
    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        messages: [
          {
            role: "user",
            content: `Regenerate and improve this requirement:\n${requirement.statement}`,
          },
        ],
      }),
    });

    const data = await res.json();

    if (data.requirements?.length > 0) {
      const regenerated = data.requirements[0];

      setRequirements((current) =>
        current.map((req) =>
          req.id === id
            ? {
                ...regenerated,
                id: id,
              }
            : req
        )
      );
    }
  } finally {
    setLoading(false);
  }
};

const analyzeRequirements = async () => {
  if (requirements.length === 0 || loading) return;

  setLoading(true);

  try {
    const res = await fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        requirements,
        missing_information: missingInformation,
        clarification_questions: [],
      }),
    });

    const data = await res.json();

    setQualityAnalysis(data);
  } catch (error) {
    console.error("Quality analysis failed:", error);
  } finally {
    setLoading(false);
  }
};

const askKnowledgeBase = async () => {
  if (!ragQuery.trim() || loading) return;

  setLoading(true);

  try {
    const res = await fetch("http://127.0.0.1:8000/rag", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: ragQuery,
      }),
    });

    const data = await res.json();

    setRagAnswer(data.answer || "No answer returned.");
    setRagSources(data.sources || []);
  } catch (error) {
    console.error("RAG request failed:", error);
    setRagAnswer("Failed to query the knowledge base.");
  } finally {
    setLoading(false);
  }
};

const analyzeCompliance = async () => {
  if (requirements.length === 0 || loading) return;

  setLoading(true);

  try {
    const res = await fetch("http://127.0.0.1:8000/compliance", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        requirements,
        missing_information: missingInformation,
        clarification_questions: clarificationQuestions,
      }),
    });

    const data = await res.json();

    setComplianceAnalysis(data);
  } catch (error) {
    console.error("Compliance analysis failed:", error);
  } finally {
    setLoading(false);
  }
};

const getComplianceStatus = (requirementId: string) => {
  return complianceAnalysis?.findings.find(
    (finding) => finding.requirement_id === requirementId
  )?.status;
};

const analyzeRisk = async () => {
  if (requirements.length === 0 || loading) return;

  setLoading(true);

  try {
    const res = await fetch("http://127.0.0.1:8000/risk", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        requirements,
        missing_information: missingInformation,
        clarification_questions: clarificationQuestions,
      }),
    });

    const data = await res.json();

    setRiskAnalysis(data);
  } catch (error) {
    console.error("Risk analysis failed:", error);
  } finally {
    setLoading(false);
  }
};

const getRiskSeverity = (requirementId: string) => {
  return riskAnalysis?.findings.find(
    (risk) => risk.requirement_id === requirementId
  )?.severity;
};

  return (
    <main className="min-h-screen p-8">
      <div className="mx-auto max-w-6xl">
        <h1 className="mb-2 text-3xl font-bold">
          Financial Requirements AI
        </h1>

        <p className="mb-8 text-gray-600">
          AI assistant for software requirements engineering
        </p>

        <div className="grid gap-8 lg:grid-cols-2">
          {/* Chat */}
          <div>
            <h2 className="mb-4 text-xl font-semibold">Conversation</h2>

            <div className="mb-6 space-y-4">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`rounded-lg p-4 ${
                    msg.role === "user"
                      ? "bg-gray-800 text-white"
                      : "border bg-gray-900 text-white"
                  }`}
                >
                  <div className="mb-1 font-semibold">
                    {msg.role === "user" ? "You" : "AI"}
                  </div>

                  <div className="whitespace-pre-wrap">
                    {msg.content}
                  </div>
                </div>
              ))}
            </div>

            <textarea
              className="mb-4 w-full rounded-lg border p-4"
              rows={4}
              placeholder="Enter your requirements or ask a question..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
            />

            <button
              onClick={sendMessage}
              disabled={loading}
              className="rounded-lg bg-black px-6 py-3 text-white disabled:opacity-50"
            >
              {loading ? "Thinking..." : "Send"}
            </button>
          </div>

          {/* Requirements */}
          <div>
            <h2 className="mb-4 text-xl font-semibold">
              Requirements
            </h2>

            {requirements.length === 0 ? (
              <div className="rounded-lg border p-6 text-gray-500">
                No requirements extracted yet.
              </div>
            ) : (
              <div className="space-y-4">
                {requirements.map((req) => (
                  <div
                    key={req.id}
                    className="rounded-lg border p-5"
                  >
                    <div className="mb-4">
                      <div className="mb-2 flex items-center justify-between">
                        <span className="font-semibold">
                          {req.id}
                        </span>

                        <span className="rounded-full bg-gray-100 px-3 py-1 text-sm text-black">
                          {req.approval_status}
                        </span>
                        {getRiskSeverity(req.id) && (
                          <span className="rounded-full bg-gray-100 px-3 py-1 text-sm text-black">
                            Risk: {getRiskSeverity(req.id)}
                          </span>
                        )}
                        {getComplianceStatus(req.id) && (
                          <span className="rounded-full bg-gray-100 px-3 py-1 text-sm text-black">
                            Compliance: {getComplianceStatus(req.id)}
                          </span>
                        )}
                      </div>

                      {editingId === req.id ? (
                        <div className="mb-4">
                          <textarea
                            className="w-full rounded-lg border p-3 text-white"
                            rows={4}
                            value={editText}
                            onChange={(e) => setEditText(e.target.value)}
                          />

                          <div className="mt-2 flex gap-2">
                            <button
                              onClick={() => saveEdit(req.id)}
                              className="rounded bg-black px-3 py-1 text-sm text-white"
                            >
                              Save
                            </button>

                            <button
                              onClick={cancelEdit}
                              className="rounded border px-3 py-1 text-sm"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <p className="mb-4">
                          {req.statement}
                        </p>
                      )}

                      <div className="flex flex-wrap gap-2">
                        <button
                          onClick={() => startEditing(req)}
                          className="rounded border px-3 py-1 text-sm"
                        >
                          Edit
                        </button>

                        <button
                          onClick={() =>
                            updateRequirementStatus(req.id, "approved")
                          }
                          className="rounded border px-3 py-1 text-sm"
                        >
                          Approve
                        </button>

                        <button
                          onClick={() =>
                            updateRequirementStatus(req.id, "rejected")
                          }
                          className="rounded border px-3 py-1 text-sm"
                        >
                          Reject
                        </button>

                        <button
                          onClick={() => regenerateRequirement(req.id)}
                          className="rounded border px-3 py-1 text-sm"
                        >
                          Regenerate
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <span className="font-medium">Category:</span>{" "}
                        {req.category}
                      </div>

                      <div>
                        <span className="font-medium">Priority:</span>{" "}
                        {req.priority || "Not specified"}
                      </div>

                      <div>
                        <span className="font-medium">Risk:</span>{" "}
                        {req.risk_level || "Not specified"}
                      </div>

                      <div>
                        <span className="font-medium">Confidence:</span>{" "}
                        {req.confidence_score != null
                          ? `${Math.round(req.confidence_score * 100)}%`
                          : "Not specified"}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {requirements.length > 0 && (
              <button
                onClick={analyzeRequirements}
                disabled={loading}
                className="mt-4 rounded-lg bg-black px-4 py-2 text-white disabled:opacity-50"
              >
                {loading ? "Analyzing..." : "Analyze Requirements"}
              </button>
            )}
            {requirements.length > 0 && (
              <button
                onClick={analyzeCompliance}
                disabled={loading}
                className="mt-2 rounded-lg bg-black px-4 py-2 text-white disabled:opacity-50"
              >
                {loading ? "Checking..." : "Analyze Compliance"}
              </button>
            )}
            {requirements.length > 0 && (
              <button
                onClick={analyzeRisk}
                disabled={loading}
                className="mt-2 rounded-lg bg-black px-4 py-2 text-white disabled:opacity-50"
              >
                {loading ? "Analyzing..." : "Analyze Risk"}
              </button>
            )}
            {complianceAnalysis && (
              <div className="mt-6 rounded-lg border p-5">
                <h3 className="mb-4 text-xl font-semibold">
                  Compliance Analysis
                </h3>

                <p className="mb-5 text-sm">
                  {complianceAnalysis.summary}
                </p>

                <div className="space-y-4">
                  {complianceAnalysis.findings.map((finding, index) => (
                    <div
                      key={index}
                      className="rounded-lg border p-4"
                    >
                      <div className="mb-2 flex items-center justify-between">
                        <span className="font-semibold">
                          {finding.requirement_id}
                        </span>

                        <span className="rounded-full bg-gray-100 px-2 py-1 text-xs text-black">
                          {finding.status}
                        </span>
                      </div>

                      <p className="mb-3 text-sm">
                        {finding.finding}
                      </p>

                      <div className="mb-3">
                        <p className="mb-1 text-sm font-medium">
                          Evidence
                        </p>

                        <ul className="list-disc pl-5 text-sm">
                          {finding.evidence.map((source, sourceIndex) => (
                            <li key={sourceIndex}>
                              {source}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <p className="text-sm">
                        <span className="font-medium">
                          Recommendation:
                        </span>{" "}
                        {finding.recommendation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {riskAnalysis && (
            <div className="mt-6 rounded-lg border p-5">
              <h3 className="mb-4 text-xl font-semibold">
                Security & Risk Analysis
              </h3>

              <p className="mb-5 text-sm">
                {riskAnalysis.summary}
              </p>

              <div className="space-y-4">
                {riskAnalysis.findings.map((risk, index) => (
                  <div
                    key={index}
                    className="rounded-lg border p-4"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <span className="font-semibold">
                        {risk.risk_type}
                      </span>

                      <span className="rounded-full bg-gray-100 px-2 py-1 text-xs text-black">
                        {risk.severity}
                      </span>
                    </div>

                    <p className="mb-2 text-xs text-gray-500">
                      Requirement: {risk.requirement_id}
                    </p>

                    <p className="mb-3 text-sm">
                      {risk.description}
                    </p>

                    <p className="text-sm">
                      <span className="font-medium">
                        Mitigation:
                      </span>{" "}
                      {risk.mitigation}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
            {qualityAnalysis && (
  <div className="mt-6 rounded-lg border p-5">
    <h3 className="mb-4 text-xl font-semibold">
      Quality Analysis
    </h3>

    <div className="mb-5">
      <div className="mb-2 flex justify-between">
        <span className="font-medium">
          Completeness
        </span>

        <span className="font-semibold">
          {qualityAnalysis.completeness_score}%
        </span>
      </div>

      <div className="h-3 rounded-full bg-gray-800">
        <div
          className="h-3 rounded-full bg-white"
          style={{
            width: `${qualityAnalysis.completeness_score}%`,
          }}
        />
      </div>
    </div>

    <p className="mb-5 text-sm">
      {qualityAnalysis.summary}
          </p>

          <div className="space-y-4">
            {qualityAnalysis.issues.map((issue, index) => (
              <div
                key={index}
                className="rounded-lg border p-4"
              >
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-semibold">
                    {issue.type}
                  </span>

                  <span className="rounded-full bg-gray-100 px-2 py-1 text-xs text-black">
                    {issue.severity}
                  </span>
                </div>

                <p className="mb-2 text-sm">
                  {issue.description}
                </p>

                {issue.affected_requirement && (
                  <p className="mb-2 text-xs text-gray-400">
                    Requirement: {issue.affected_requirement}
                  </p>
                )}

                <p className="text-sm">
                  <span className="font-medium">
                    Suggestion:
                  </span>{" "}
                  {issue.suggestion}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    <div className="mt-6 rounded-lg border p-5">
      <h3 className="mb-2 text-xl font-semibold">
        Financial Knowledge Base
      </h3>

      <p className="mb-4 text-sm text-gray-500">
        Ask questions using the project's financial regulations,
        policies, and security documents.
      </p>

      <textarea
        className="mb-3 w-full rounded-lg border p-3 text-white"
        rows={3}
        placeholder="Ask about financial regulations, security controls, policies..."
        value={ragQuery}
        onChange={(e) => setRagQuery(e.target.value)}
      />

      <button
        onClick={askKnowledgeBase}
        disabled={loading}
        className="rounded-lg bg-black px-4 py-2 text-white disabled:opacity-50"
      >
        {loading ? "Searching..." : "Search Knowledge Base"}
      </button>

      {ragAnswer && (
        <div className="mt-5 rounded-lg border p-4">
          <h4 className="mb-2 font-semibold">
            Answer
          </h4>

          <p className="whitespace-pre-wrap text-sm">
            {ragAnswer}
          </p>
          {ragSources.length > 0 && (
            <div className="mt-5">
              <h4 className="mb-2 font-semibold">
                Evidence Used
              </h4>

              <div className="space-y-2">
                {ragSources.map((source, index) => (
                  <div
                    key={index}
                    className="rounded border p-3 text-sm"
                  >
                    <div className="font-medium">
                      {source.source}
                    </div>

                    <div className="text-gray-500">
                      Chunk: {source.chunk_id}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
      {clarificationQuestions.length > 0 && (
        <div className="mt-6 rounded-lg border p-5">
          <h3 className="mb-3 font-semibold">
            Clarification Questions
          </h3>

          <ul className="list-disc space-y-2 pl-5">
            {clarificationQuestions.map((question, index) => (
              <li key={index}>
                {question}
              </li>
            ))}
          </ul>
        </div>
      )}

            {missingInformation.length > 0 && (
              <div className="mt-6 rounded-lg border p-5">
                <h3 className="mb-3 font-semibold">
                  Information Still Needed
                </h3>

                <ul className="list-disc space-y-1 pl-5">
                  {missingInformation.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}