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

type Message = {
  role: "user" | "model";
  content: string;
};

export default function Home() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [missingInformation, setMissingInformation] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
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