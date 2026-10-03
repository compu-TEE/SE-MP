import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel
from rag import rag_answer, retrieve_documents

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

class ComplianceFinding(BaseModel):
    requirement_id: str
    status: str
    finding: str
    evidence: list[str] = []
    recommendation: str

class SingleComplianceAnalysis(BaseModel):
    status: str
    finding: str
    evidence: list[str] = []
    recommendation: str

class ComplianceAnalysis(BaseModel):
    findings: list[ComplianceFinding] = []
    summary: str

class RiskFinding(BaseModel):
    requirement_id: str
    risk_type: str
    severity: str
    description: str
    mitigation: str

class SingleRiskAnalysis(BaseModel):
    risk_type: str
    severity: str
    description: str
    mitigation: str
class RiskAnalysis(BaseModel):
    findings: list[RiskFinding] = []
    summary: str

class ProjectCharacteristics(BaseModel):
    project_type: str
    regulatory_criticality: str
    change_frequency: str
    risk_level: str
    complexity: str
    delivery_priority: str
    requirements_clarity: str


class SDLCRecommendation(BaseModel):
    recommended_model: str
    reasoning: str
    key_factors: list[str] = []

class SDLCWorkflowStep(BaseModel):
    step: int
    phase: str
    description: str


class SDLCWorkflow(BaseModel):
    model: str
    workflow: list[SDLCWorkflowStep]

class DocumentationArtifact(BaseModel):
    title: str
    content: str


class DocumentationPackage(BaseModel):
    srs: DocumentationArtifact
    user_stories: DocumentationArtifact
    use_cases: DocumentationArtifact
    acceptance_criteria: DocumentationArtifact
    traceability: DocumentationArtifact

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

COMPLIANCE_PROMPT = """
You are a Financial Software Compliance Analysis Agent.

Analyze the provided software requirement using the provided
knowledge-base evidence.

For the requirement:

1. Identify relevant compliance, security, audit, privacy,
   or financial-control considerations.

2. Do not claim that a regulation or policy applies unless
   the provided evidence supports the claim.

3. Do not invent regulations or policies.

4. If the evidence is insufficient, explicitly say so.

5. Identify the evidence sources that support the finding.

6. Provide a practical recommendation when appropriate.

Possible statuses:
- relevant
- no_relevant_evidence
- insufficient_evidence

Return only structured output.
"""


def compliance_agent(
    requirements: list[Requirement],
) -> ComplianceAnalysis:

    if not requirements:
        return ComplianceAnalysis(
            findings=[],
            summary="No requirements were provided for compliance analysis."
        )

    all_findings = []

    for requirement in requirements:
        retrieved = retrieve_documents(requirement.statement)

        context = "\n\n".join(
            f"""
SOURCE: {item["source"]}
CHUNK: {item["chunk_id"]}
CONTENT:
{item["content"]}
"""
            for item in retrieved
        )

        prompt = (
            COMPLIANCE_PROMPT
            + "\n\nREQUIREMENT:\n"
            + f"ID: {requirement.id}\n"
            + f"Statement: {requirement.statement}\n"
            + "\n\nKNOWLEDGE BASE EVIDENCE:\n"
            + context
        )

        response = client.models.generate_content(
            model=os.getenv(
                "GEMINI_MODEL",
                "gemini-3.5-flash-lite"
            ),
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": SingleComplianceAnalysis,
            },
        )

        result = response.parsed

        all_findings.append(
            ComplianceFinding(
                requirement_id=requirement.id,
                status=result.status,
                finding=result.finding,
                evidence=result.evidence,
                recommendation=result.recommendation,
            )
        )

    return ComplianceAnalysis(
        findings=all_findings,
        summary="Compliance analysis was performed using the available knowledge-base evidence."
    )

RISK_PROMPT = """
You are a Security and Risk Analysis Agent for financial software.

Analyze the provided software requirement and identify realistic
security, privacy, financial, operational, or availability risks.

Consider:

- Authentication and authorization
- Sensitive financial data
- Fraud
- Unauthorized transactions
- Auditability
- Data integrity
- Availability
- Failure handling
- Access control
- Privacy
- Transaction limits

Rules:

1. Only identify risks that are supported by the requirement
   and provided knowledge-base evidence.

2. Do not invent regulations.

3. Do not assume a specific attack has occurred.

4. Give each risk a severity:
   low, medium, or high.

5. Provide a practical mitigation for each identified risk.

6. If there are no meaningful risks supported by the available
   information, return an empty findings list.

Return structured output only.
"""
def risk_agent(
    requirements: list[Requirement],
) -> RiskAnalysis:

    if not requirements:
        return RiskAnalysis(
            findings=[],
            summary="No requirements were provided for risk analysis."
        )

    all_findings = []

    for requirement in requirements:
        retrieved = retrieve_documents(requirement.statement)

        context = "\n\n".join(
            f"""
SOURCE: {item["source"]}
CHUNK: {item["chunk_id"]}
CONTENT:
{item["content"]}
"""
            for item in retrieved
        )

        prompt = (
            RISK_PROMPT
            + "\n\nREQUIREMENT:\n"
            + f"ID: {requirement.id}\n"
            + f"Statement: {requirement.statement}\n"
            + "\n\nKNOWLEDGE BASE EVIDENCE:\n"
            + context
        )

        response = client.models.generate_content(
            model=os.getenv(
                "GEMINI_MODEL",
                "gemini-3.5-flash-lite"
            ),
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": SingleRiskAnalysis,
            },
        )

        result = response.parsed

        all_findings.append(
            RiskFinding(
                requirement_id=requirement.id,
                risk_type=result.risk_type,
                severity=result.severity,
                description=result.description,
                mitigation=result.mitigation,
            )
        )

    return RiskAnalysis(
        findings=all_findings,
        summary="Risk analysis was performed using the available requirements and knowledge-base evidence."
    )

SDLC_PROMPT = """
You are an expert Software Development Life Cycle (SDLC) methodology advisor.

Based on the given project characteristics, recommend exactly ONE SDLC model.

You may ONLY recommend one of these 7 models:

1. Waterfall
2. V-Model
3. Prototyping
4. Iterative/Incremental
5. RAD
6. Spiral
7. Agile

Consider these factors carefully:

- Project type
- Regulatory criticality
- Change frequency
- Risk level
- Complexity
- Delivery priority
- Requirements clarity

General guidance:

Waterfall:
Use when requirements are stable, clearly defined, change frequency is low,
and a sequential development process is appropriate.

V-Model:
Use when requirements are stable but strong verification, validation,
testing, quality assurance, and regulatory assurance are important.

Prototyping:
Use when requirements are unclear, user feedback is important,
or stakeholders need an early working representation to clarify requirements.

Iterative/Incremental:
Use when the system can be developed and delivered in multiple increments,
with requirements and functionality refined across iterations.

RAD:
Use when rapid development is important, requirements are reasonably understood,
the project has relatively low risk, and quick delivery with frequent user feedback
is desired.

Spiral:
Use when project risk and complexity are high, especially when continuous
risk identification, analysis, prototyping, and mitigation are required.

Agile:
Use when requirements change frequently, continuous stakeholder feedback is
important, and the project benefits from short iterative development cycles.

Requirements clarity:
- unclear: strongly consider Prototyping
- partially clear: consider Iterative/Incremental or Prototyping
- clear: consider Waterfall, V-Model, RAD, or Agile depending on other factors

Do not recommend a model outside the seven listed above.

Return the result in the following structure:

{
  "recommended_model": "one of the 7 models",
  "reasoning": "clear explanation of why this model fits the project",
  "key_factors": [
    "factor 1",
    "factor 2",
    "factor 3"
  ]
}

Project characteristics:

Project type: {project_type}
Regulatory criticality: {regulatory_criticality}
Change frequency: {change_frequency}
Risk level: {risk_level}
Complexity: {complexity}
Delivery priority: {delivery_priority}
Requirements clarity: {requirements_clarity}
"""

def sdlc_agent(characteristics: ProjectCharacteristics):
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL"),
        contents=(
            SDLC_PROMPT
            + "\n\nProject Characteristics:\n"
            + characteristics.model_dump_json(indent=2)
        ),
        config={
            "response_mime_type": "application/json",
            "response_schema": SDLCRecommendation,
        },
    )

    return response.parsed

SDLC_WORKFLOW_PROMPT = """
You are an SDLC workflow generation agent for financial software projects.

Generate a project-specific development workflow based on:
- The selected SDLC model
- Project characteristics

The workflow should include appropriate phases such as:
requirements, analysis, architecture/design, development, testing,
security/compliance validation, approval, deployment, and monitoring.

Adapt the workflow to the selected SDLC model and project risk.

Return ONLY valid JSON in this format:

{
  "model": "string",
  "workflow": [
    {
      "step": 1,
      "phase": "string",
      "description": "string"
    }
  ]
}

Do not invent specific regulations or external facts.
"""

def sdlc_workflow_agent(
    characteristics: ProjectCharacteristics,
    recommendation: SDLCRecommendation
):
    prompt = (
        SDLC_WORKFLOW_PROMPT
        + "\n\nProject Characteristics:\n"
        + characteristics.model_dump_json(indent=2)
        + "\n\nSDLC Recommendation:\n"
        + recommendation.model_dump_json(indent=2)
    )

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL"),
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": SDLCWorkflow,
        },
    )

    return response.parsed

DOCUMENTATION_PROMPT = """
You are a software documentation agent for financial software projects.

Generate documentation from the provided validated requirements.

Create the following five artifacts:

1. SRS
   - System overview
   - Functional requirements
   - Non-functional requirements
   - Constraints

2. User Stories
   - Convert the requirements into clear user stories.
   - Use the format:
     As a <user>, I want <goal>, so that <benefit>.

3. Use Cases
   - Identify relevant actors.
   - Describe the main interactions between actors and the system.

4. Acceptance Criteria
   - Provide testable acceptance criteria for the requirements.

5. Traceability
   - Map each requirement to the generated documentation artifacts.
   - Use requirement IDs where available.

Only use information contained in the provided requirements.
Do not invent regulations, requirements, users, or system capabilities.

Return ONLY valid JSON matching the requested schema.
"""

def documentation_agent(requirements: list[Requirement]):
    prompt = (
        DOCUMENTATION_PROMPT
        + "\n\nValidated Requirements:\n"
        + "\n".join(
            req.model_dump_json(indent=2)
            for req in requirements
        )
    )

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL"),
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": DocumentationPackage,
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

@app.post("/compliance")
def analyze_compliance(request: RequirementState):
    analysis = compliance_agent(request.requirements)

    return analysis.model_dump()

@app.post("/risk")
def analyze_risk(request: RequirementState):
    analysis = risk_agent(request.requirements)

    return analysis.model_dump()

@app.post("/sdlc", response_model=SDLCRecommendation)
def recommend_sdlc(characteristics: ProjectCharacteristics):
    return sdlc_agent(characteristics)

@app.post("/sdlc/workflow", response_model=SDLCWorkflow)
def generate_sdlc_workflow(
    characteristics: ProjectCharacteristics
):
    recommendation = sdlc_agent(characteristics)

    return sdlc_workflow_agent(
        characteristics,
        recommendation
    )

@app.post("/documentation", response_model=DocumentationPackage)
def generate_documentation(requirements: list[Requirement]):
    return documentation_agent(requirements)