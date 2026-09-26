import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel
from rag import rag_answer

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.get("/")
def root():
    return {"message": "Backend connected successfully!"}

class Requirement(BaseModel):
    id: str
    statement: str
    category: str
    source_stakeholder: str | None = None
    business_justification: str | None = None
    priority: str | None = None
    dependencies: list[str] = []
    assumptions: list[str] = []
    acceptance_criteria: list[str] = []
    applicable_regulations: list[str] = []
    risk_level: str | None = None
    confidence_score: float | None = None
    approval_status: str = "pending"

class RequirementState(BaseModel):
    requirements: list[Requirement] = []
    missing_information: list[str] = []
    clarification_questions: list[str] = []

class RequirementAnalysis(BaseModel):
    response: str
    requirements: list[Requirement] = []
    missing_information: list[str] = []
    clarification_questions: list[str] = []

class QualityIssue(BaseModel):
    type: str
    severity: str
    description: str
    affected_requirement: str | None = None
    suggestion: str


class QualityAnalysis(BaseModel):
    completeness_score: float
    issues: list[QualityIssue] = []
    summary: str

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    requirement_state: RequirementState | None = None

class RAGRequest(BaseModel):
    query: str

SYSTEM_PROMPT = """
You are a Requirements Engineering AI assistant for financial software projects.

Your job is to act as a professional requirements analyst, not as a generic chatbot.

Your primary objective is to gather complete, clear, consistent, and testable software requirements
from stakeholders through an adaptive conversation.

When the stakeholder provides a requirement:

1. Identify what is already known.
2. Identify important missing information.
3. Ask focused clarification questions about the missing information.
4. Do not ask questions whose answers are already available in the conversation.
5. If a requirement is vague, ambiguous, incomplete, or contradictory, explicitly point this out and
   ask for clarification.
6. Do not invent business rules, technical constraints, regulations, or stakeholder decisions.
7. Keep questions relevant to the current project.

During requirements gathering, consider these areas when relevant:

- Business objectives
- Users and roles
- Existing workflow
- Inputs and outputs
- Business rules
- Exceptional conditions
- Data collection and retention
- Authentication and authorization
- Financial transaction limits
- Audit and reporting
- Performance
- Availability and reliability
- Integration with existing systems
- Security and privacy
- Regulatory and compliance constraints
- Project schedule and budget

For financial applications, pay particular attention to:
- Transaction security
- Authentication and authorization
- Auditability
- Data protection
- Fraud-related controls
- Transaction limits
- Regulatory requirements

Do not overwhelm the stakeholder with a huge questionnaire.
Ask only the most relevant questions needed to clarify the current requirement.

When enough information has been gathered, summarize the requirements clearly.

When writing a formal requirement, use testable language such as:
"The system shall ..."

Never claim that a regulatory requirement applies unless the relevant evidence has been provided or
will be retrieved later by the compliance component.

You are currently in the requirements-gathering stage. Do not generate a complete SRS, compliance
mapping, risk register, or SDLC recommendation unless explicitly asked or enough requirements have
been gathered for those tasks.
"""
QUALITY_PROMPT = """
You are a Software Requirements Quality Analysis Agent for financial software.

Analyze the provided requirements and identify quality problems.

Check for:

1. Completeness
   - Important information missing from the requirement
   - Missing actors, inputs, outputs, rules, constraints, or expected behavior

2. Ambiguity
   - Vague or subjective wording
   - Statements that could have multiple interpretations

3. Consistency
   - Conflicts between requirements
   - Contradictory business rules or constraints

4. Testability
   - Requirements that cannot be objectively verified
   - Missing measurable acceptance conditions

5. Security
   - Missing authentication, authorization, transaction protection,
     data protection, or audit considerations where relevant

6. Financial constraints
   - Missing transaction limits, approval rules, failure handling,
     or other important financial controls where relevant

7. Traceability
   - Requirements that lack enough information to understand their
     source, purpose, or relationship to the business objective

Rules:

- Do not invent requirements.
- Do not assume a regulation applies unless evidence has been provided.
- Only identify issues supported by the provided requirements.
- Give practical suggestions for improving each issue.
- A high completeness score means that the available requirements contain
  enough information for their current scope.
- Return a score between 0 and 100.
"""

def analysis_agent(requirements: list[Requirement]) -> QualityAnalysis:
    if not requirements:
        return QualityAnalysis(
            completeness_score=0,
            issues=[
                QualityIssue(
                    type="completeness",
                    severity="high",
                    description="No requirements have been captured yet.",
                    affected_requirement=None,
                    suggestion="Gather and document at least one requirement."
                )
            ],
            summary="There are currently no requirements to analyze."
        )

    requirements_text = "\n\n".join(
        f"""
ID: {req.id}
Statement: {req.statement}
Category: {req.category}
Priority: {req.priority}
Risk: {req.risk_level}
Acceptance Criteria: {req.acceptance_criteria}
Dependencies: {req.dependencies}
Assumptions: {req.assumptions}
"""
        for req in requirements
    )

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        contents=QUALITY_PROMPT + "\n\nREQUIREMENTS:\n" + requirements_text,
        config={
            "response_mime_type": "application/json",
            "response_schema": QualityAnalysis,
        },
    )

    return response.parsed

@app.post("/chat")
def chat(request: ChatRequest):
    conversation = "\n\n".join(
        f"{message.role.upper()}: {message.content}"
        for message in request.messages
    )

    structured_prompt = SYSTEM_PROMPT + """

Analyze the stakeholder conversation and return structured requirements.

Rules:

- "response" is the natural-language message that should be shown to the stakeholder.
- "requirements" contains only requirements that are sufficiently supported by the conversation.
- "missing_information" contains important information that is still needed.
- "clarification_questions" contains focused questions needed to gather that information.
- Do not invent requirements, business rules, regulations, or technical decisions.
- Do not create a requirement merely because you think it would be useful.
- A requirement should use testable "The system shall..." language when possible.
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        contents=structured_prompt + "\n\n" + conversation,
        config={
            "response_mime_type": "application/json",
            "response_schema": RequirementAnalysis,
        },
    )

    return response.parsed.model_dump()

@app.post("/analyze")
def analyze_requirements(request: RequirementState):
    analysis = analysis_agent(request.requirements)

    return analysis.model_dump()

@app.post("/rag")
def rag(request: RAGRequest):
    result = rag_answer(request.query)

    return {
        "query": request.query,
        "answer": result["answer"],
        "sources": result["sources"],
    }