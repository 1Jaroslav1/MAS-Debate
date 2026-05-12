"""Generate the software-engineering deliberation configs for all three levels.

Single source of truth for configs/se/level_{1,2,3}. Each topic defines 3 experts
per team; levels slice that pool and set the round count:

    level_1 -> 1 round,  1 person per team   (members[:1])
    level_2 -> 2 rounds, 2 people per team   (members[:2])
    level_3 -> 3 rounds, 3 people per team   (members[:3])

Format mirrors the consolidated single-file configs in configs/medium_processed/
(id, topic, max_rounds, teams[pro+opposition], audience, output_file,
include_user_interaction). The generic 50-persona audience block is reused verbatim
from the template; architecture is "cot".
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "configs", "medium_processed", "commercial_space.json")
SE_DIR = os.path.join(ROOT, "configs", "se")

ARCH = "cot"

# rounds + member-slice size per level
LEVELS = {1: 1, 2: 2, 3: 3}

with open(TEMPLATE, "r", encoding="utf-8") as fh:
    template = json.load(fh)
AUDIENCE = template["audience"]


def member(name, education, experience, expertise, role, thinking, comm, argpref,
           core_values, stance, risk, decision, evidence, counter, industry,
           culture, perspective):
    return {
        "name": name,
        "education": education,
        "experience": experience,
        "expertise_domains": expertise,
        "current_role": role,
        "thinking_style": thinking,
        "communication_style": comm,
        "argumentation_preference": argpref,
        "core_values": core_values,
        "philosophical_stance": stance,
        "risk_tolerance": risk,
        "decision_making_style": decision,
        "preferred_evidence_types": evidence,
        "typical_counterargument_approach": counter,
        "industry_background": industry,
        "cultural_background": culture,
        "notable_biases": [],
        "perspective": perspective,
        "max_iterations": 3,
        "use_personalization": False,
        "use_context_analysis": False,
        "knowledge_active": False,
        "knowledge_use_rag": False,
        "knowledge_use_web_search": False,
        "evaluation_active": False,
    }


def team(team_name, team_type, perspective_description, viewpoint, focus_keywords,
         typical_arguments, members):
    return {
        "team_name": team_name,
        "team_type": team_type,
        "perspective_description": perspective_description,
        "priority_aspects": [
            "engineering trade-offs",
            "maintainability and reliability",
            "delivery velocity and cost",
            "feasibility",
        ],
        "evidence_preferences": [
            "empirical software-engineering studies",
            "industry case studies",
            "benchmark and incident data",
            "expert practitioner experience",
        ],
        "counterargument_strategy": "Address opponent concerns while highlighting core benefits",
        "rhetorical_emphasis": "data-driven",
        "focus_keywords": focus_keywords,
        "avoid_keywords": ["ad hominem", "slippery slope", "strawman"],
        "viewpoint_orientation": viewpoint,
        "interests_and_concerns": [
            "deliver reliable software",
            "minimize long-term maintenance cost",
            "support sustainable delivery velocity",
            "respect practical engineering constraints",
        ],
        "typical_arguments": typical_arguments,
        "architecture": ARCH,
        "members": members,
    }


PRO_ARGS = [
    "Support this proposal based on evidence",
    "Consider long-term maintainability and resilience",
    "Balance delivery velocity with engineering safeguards",
    "Learn from industry case studies and empirical research",
]
OPP_ARGS = [
    "Oppose this proposal based on evidence",
    "Consider long-term maintainability and resilience",
    "Balance delivery velocity with engineering safeguards",
    "Learn from industry case studies and empirical research",
]

topics = []

# ---------------------------------------------------------------------------
# Topic 1: Microservices vs. monoliths for continuous deployment
# ---------------------------------------------------------------------------
topics.append({
    "id": "microservices_vs_monoliths",
    "topic": "Microservices architecture should be preferred over monolithic architecture for continuous deployment",
    "focus_keywords": ["microservices", "monolith", "continuous", "deployment", "architecture"],
    "pro_name": "pro_microservices_vs_monoliths",
    "opp_name": "anti_microservices_vs_monoliths",
    "pro_members": [
        member(
            "Dr. Priya Nair",
            ["PhD in Distributed Systems", "BSc in Computer Science"],
            ["15 years designing cloud-native platforms",
             "Published research on service decomposition and deployment pipelines",
             "Led microservices migrations at large-scale SaaS companies"],
            ["distributed systems", "cloud architecture"],
            "Cloud Platform Architect", "analytical", "evidence-based",
            "research-heavy", ["scalability", "evidence", "team autonomy"],
            "evidence-based", "moderate", "data-driven",
            ["peer-reviewed studies", "production telemetry", "case studies"],
            "contrast trade-offs with deployment metrics", "cloud computing",
            "engineering community", "proposition-supporting"),
        member(
            "Marcus Feld",
            ["MSc in Software Engineering", "BSc in Information Systems"],
            ["12 years in DevOps and site reliability engineering",
             "Built CI/CD pipelines for independently deployable services",
             "Speaker on continuous delivery at industry conferences"],
            ["DevOps", "continuous delivery"],
            "DevOps/SRE Lead", "systematic", "pipeline-focused",
            "framework-based", ["automation", "fast feedback", "reliability"],
            "continuous improvement", "moderate", "metrics-driven",
            ["deployment frequency data", "incident reports", "DORA metrics"],
            "cite independent deployability benefits", "software/DevOps",
            "DevOps community", "proposition-supporting"),
        member(
            "Dr. Kwame Mensah",
            ["PhD in Software Engineering", "BSc in Computer Science"],
            ["13 years researching team topologies and Conway's law",
             "Advised organizations on scaling engineering teams",
             "Published on organizational alignment of service boundaries"],
            ["team topologies", "organizational scaling"],
            "Software Engineering Researcher", "analytical", "evidence-based",
            "research-heavy", ["team autonomy", "scalability", "evidence"],
            "sociotechnical alignment", "moderate", "data-driven",
            ["organizational studies", "case studies", "delivery metrics"],
            "argue service boundaries enable independent teams", "software research",
            "academic community", "proposition-supporting"),
    ],
    "opp_members": [
        member(
            "Dr. James Whitaker",
            ["PhD in Software Architecture", "BSc in Computer Engineering"],
            ["18 years architecting large business systems",
             "Advocate of the modular-monolith approach",
             "Author on architectural complexity and coupling"],
            ["software architecture", "modular design"],
            "Principal Software Architect", "systematic", "structured",
            "framework-based", ["simplicity", "low operational overhead", "consistency"],
            "pragmatic minimalism", "low", "risk-aware",
            ["complexity metrics", "case studies", "operational cost data"],
            "emphasize distributed-systems complexity and failure modes",
            "enterprise software", "architecture community", "opposition-supporting"),
        member(
            "Elena Rossi",
            ["MSc in Computer Science", "BSc in Software Engineering"],
            ["11 years as a backend engineer on monolithic and modular systems",
             "Led teams burned by premature microservice splits",
             "Mentor on pragmatic delivery practices"],
            ["backend engineering", "system maintainability"],
            "Senior Backend Engineer", "practical", "direct",
            "experience-based", ["pragmatism", "developer productivity", "maintainability"],
            "principled pragmatist", "moderate", "experience-driven",
            ["team productivity data", "post-mortems", "case studies"],
            "highlight operational and cognitive overhead", "software",
            "engineering community", "opposition-supporting"),
        member(
            "Tom Bradley",
            ["MSc in Cloud Computing", "BSc in Computer Science"],
            ["10 years in cloud operations and FinOps",
             "Quantified the infrastructure cost of microservice sprawl",
             "Advises on operational cost of distributed systems"],
            ["cloud operations", "cost engineering"],
            "FinOps / Cloud Operations Engineer", "analytical", "cost-aware",
            "framework-based", ["cost-effectiveness", "operational simplicity", "pragmatism"],
            "cost-conscious operations", "low", "cost-benefit-driven",
            ["cost data", "operational metrics", "case studies"],
            "argue operational and infrastructure cost outweighs benefits", "cloud computing",
            "operations community", "opposition-supporting"),
    ],
})

# ---------------------------------------------------------------------------
# Topic 2: Peer review parity for AI-generated code
# ---------------------------------------------------------------------------
topics.append({
    "id": "ai_code_review_parity",
    "topic": "AI-generated code should be subject to the same peer review standards as human-written code",
    "focus_keywords": ["AI-generated", "code", "peer", "review", "parity"],
    "pro_name": "pro_ai_code_review_parity",
    "opp_name": "anti_ai_code_review_parity",
    "pro_members": [
        member(
            "Dr. Sarah Chen",
            ["PhD in Software Quality Engineering", "BSc in Computer Science"],
            ["14 years researching code quality and review effectiveness",
             "Published studies on defect detection in code review",
             "Advisor on engineering quality programs"],
            ["software quality", "code review"],
            "Software Quality Researcher", "analytical", "evidence-based",
            "research-heavy", ["quality", "accountability", "rigor"],
            "evidence-based", "low", "data-driven",
            ["peer-reviewed studies", "defect data", "case studies"],
            "contrast review coverage with defect-escape rates", "software research",
            "academic community", "proposition-supporting"),
        member(
            "David Okafor",
            ["MSc in Software Engineering", "BSc in Computer Engineering"],
            ["13 years leading engineering teams and review processes",
             "Designed code-review guidelines for regulated industries",
             "Speaker on engineering accountability"],
            ["engineering management", "review process"],
            "Engineering Manager", "systematic", "process-focused",
            "framework-based", ["accountability", "consistency", "team ownership"],
            "process integrity", "low", "policy-driven",
            ["process audits", "incident reports", "team metrics"],
            "argue that provenance should not lower scrutiny", "software",
            "engineering community", "proposition-supporting"),
        member(
            "Dr. Hiroshi Yamada",
            ["PhD in Software Security", "BSc in Computer Science"],
            ["15 years in application security research",
             "Studied vulnerability rates in AI-assisted code",
             "Advises secure-development programs"],
            ["application security", "secure development"],
            "Application Security Researcher", "analytical", "risk-focused",
            "research-heavy", ["security-first", "rigor", "accountability"],
            "security-first", "low", "risk-aware",
            ["vulnerability studies", "threat data", "case studies"],
            "argue AI code carries security risk requiring equal review", "software research",
            "security community", "proposition-supporting"),
    ],
    "opp_members": [
        member(
            "Dr. Tom Becker",
            ["PhD in Machine Learning", "BSc in Computer Science"],
            ["12 years building AI developer tooling",
             "Researches automated code verification and assistants",
             "Argues AI code warrants a differentiated review workflow"],
            ["AI tooling", "developer productivity"],
            "AI Tooling Lead", "entrepreneurial", "innovation-focused",
            "innovation-based", ["efficiency", "automation", "developer flow"],
            "automation-first", "high", "opportunity-driven",
            ["tool benchmarks", "productivity studies", "automation metrics"],
            "emphasize automated checks can substitute for parity review", "AI/software",
            "tech industry", "opposition-supporting"),
        member(
            "Aisha Rahman",
            ["MSc in Human-Computer Interaction", "BSc in Software Engineering"],
            ["10 years optimizing developer experience and throughput",
             "Studied review bottlenecks in fast-moving teams",
             "Advocate for proportionate, risk-based review"],
            ["developer experience", "engineering throughput"],
            "Developer Productivity Lead", "practical", "pragmatic",
            "experience-based", ["velocity", "developer autonomy", "pragmatism"],
            "pragmatic efficiency", "moderate-high", "outcome-driven",
            ["throughput metrics", "developer surveys", "case studies"],
            "argue uniform parity creates review bottlenecks", "software",
            "tech industry", "opposition-supporting"),
        member(
            "Lena Schmidt",
            ["MSc in Computer Science", "BSc in Software Engineering"],
            ["11 years maintaining large open-source projects",
             "Triages high volumes of contributions and AI-assisted PRs",
             "Advocate for tiered, trust-based review"],
            ["open-source maintenance", "collaborative development"],
            "Open-Source Maintainer", "practical", "direct",
            "experience-based", ["sustainability", "pragmatism", "community throughput"],
            "pragmatic stewardship", "moderate", "experience-driven",
            ["contribution data", "project metrics", "case studies"],
            "argue parity overwhelms maintainers and slows projects", "open-source software",
            "open-source community", "opposition-supporting"),
    ],
})

# ---------------------------------------------------------------------------
# Topic 3: Technical debt prioritization below coverage thresholds
# ---------------------------------------------------------------------------
topics.append({
    "id": "technical_debt_coverage_threshold",
    "topic": "Technical debt remediation should be prioritized whenever test coverage falls below defined thresholds",
    "focus_keywords": ["technical", "debt", "coverage", "threshold", "prioritization"],
    "pro_name": "pro_technical_debt_coverage_threshold",
    "opp_name": "anti_technical_debt_coverage_threshold",
    "pro_members": [
        member(
            "Dr. Robert Klein",
            ["PhD in Software Maintainability", "BSc in Computer Science"],
            ["16 years researching software maintenance and technical debt",
             "Published on the cost of deferred refactoring",
             "Advisor on engineering health metrics"],
            ["software maintainability", "technical debt"],
            "Software Maintainability Researcher", "analytical", "evidence-based",
            "research-heavy", ["sustainability", "evidence", "long-term value"],
            "evidence-based", "low", "data-driven",
            ["peer-reviewed studies", "defect-density data", "case studies"],
            "link low coverage to defect risk with data", "software research",
            "academic community", "proposition-supporting"),
        member(
            "Nina Petrov",
            ["MSc in Software Engineering", "BSc in Computer Science"],
            ["12 years as a staff engineer leading refactoring initiatives",
             "Recovered legacy systems with poor test coverage",
             "Mentor on sustainable engineering practices"],
            ["refactoring", "test strategy"],
            "Staff Engineer", "systematic", "structured",
            "framework-based", ["code health", "reliability", "discipline"],
            "engineering stewardship", "moderate", "risk-aware",
            ["coverage reports", "post-mortems", "regression data"],
            "show how coverage gaps compound into outages", "software",
            "engineering community", "proposition-supporting"),
        member(
            "Carlos Mendez",
            ["MSc in Computer Science", "BSc in Software Engineering"],
            ["12 years in site reliability engineering",
             "Traced production incidents to under-tested modules",
             "Advocate for reliability-driven engineering investment"],
            ["site reliability", "production stability"],
            "Site Reliability Engineer", "systematic", "incident-focused",
            "framework-based", ["reliability", "accountability", "discipline"],
            "reliability-first", "low", "risk-aware",
            ["incident reports", "reliability metrics", "post-mortems"],
            "tie low-coverage code to recurring production incidents", "software/DevOps",
            "SRE community", "proposition-supporting"),
    ],
    "opp_members": [
        member(
            "Mark Sullivan",
            ["MBA", "BSc in Software Engineering"],
            ["15 years leading product-focused engineering teams",
             "Shipped products under tight market deadlines",
             "Advocate for value-driven prioritization"],
            ["product engineering", "delivery management"],
            "Engineering Lead", "practical", "business-focused",
            "experience-based", ["customer value", "time-to-market", "pragmatism"],
            "value-driven", "moderate-high", "outcome-driven",
            ["business metrics", "customer feedback", "delivery data"],
            "argue debt work should follow business risk, not a metric", "software",
            "product industry", "opposition-supporting"),
        member(
            "Dr. Lisa Wang",
            ["PhD in Empirical Software Engineering", "BSc in Statistics"],
            ["11 years studying software metrics validity",
             "Published critiques of coverage as a quality proxy",
             "Consultant on measurement-driven engineering"],
            ["software metrics", "measurement"],
            "Software Metrics Researcher", "analytical", "skeptical",
            "research-heavy", ["methodological rigor", "evidence", "validity"],
            "measurement skepticism", "moderate", "data-driven",
            ["empirical studies", "statistical analyses", "case studies"],
            "argue coverage thresholds are a weak proxy for risk", "software research",
            "academic community", "opposition-supporting"),
        member(
            "Rachel Kim",
            ["MSc in Computer Science", "BSc in Information Systems"],
            ["13 years as a startup engineering leader and CTO",
             "Balanced survival-mode delivery against engineering health",
             "Advocate for context-driven, lean prioritization"],
            ["startup engineering", "lean delivery"],
            "Startup CTO", "practical", "pragmatic",
            "experience-based", ["pragmatism", "speed", "survival"],
            "lean pragmatism", "high", "outcome-driven",
            ["business outcomes", "delivery data", "case studies"],
            "argue rigid thresholds ignore context and starve product work", "software",
            "startup ecosystem", "opposition-supporting"),
    ],
})

# ---------------------------------------------------------------------------
# Topic 4: Mandatory static analysis and formal verification for safety-critical
# ---------------------------------------------------------------------------
topics.append({
    "id": "formal_verification_safety_critical",
    "topic": "Static analysis and formal verification should be mandatory for safety-critical software",
    "focus_keywords": ["static", "analysis", "formal", "verification", "safety-critical"],
    "pro_name": "pro_formal_verification_safety_critical",
    "opp_name": "anti_formal_verification_safety_critical",
    "pro_members": [
        member(
            "Dr. Heinrich Vogel",
            ["PhD in Formal Methods", "MSc in Computer Science"],
            ["20 years researching formal verification of critical systems",
             "Developed verification tooling used in avionics",
             "Advisor to safety-certification bodies"],
            ["formal methods", "verification"],
            "Formal Methods Researcher", "systematic", "rigorous",
            "framework-based", ["correctness", "safety", "rigor"],
            "correctness-first", "low", "principle-driven",
            ["formal proofs", "verification studies", "safety standards"],
            "cite verified-system success and failure costs", "safety-critical software",
            "academic/aerospace community", "proposition-supporting"),
        member(
            "Maria Santos",
            ["MSc in Safety-Critical Systems Engineering", "BSc in Electrical Engineering"],
            ["17 years engineering medical and aerospace safety systems",
             "Led certification under DO-178C and IEC 62304",
             "Investigated software-related safety incidents"],
            ["safety engineering", "certification"],
            "Safety Systems Engineer", "systematic", "regulatory-focused",
            "framework-based", ["public safety", "accountability", "rigor"],
            "public protection", "low", "regulatory-compliance-driven",
            ["safety standards", "incident investigations", "certification data"],
            "cite catastrophic-failure precedents from other industries",
            "aerospace/medical", "regulatory community", "proposition-supporting"),
        member(
            "Dr. Ingrid Larsson",
            ["PhD in Dependable Systems", "MSc in Computer Engineering"],
            ["16 years developing software safety standards",
             "Contributed to international safety-assurance frameworks",
             "Researches assurance cases for critical software"],
            ["safety standards", "dependable systems"],
            "Safety Standards Researcher", "systematic", "structured",
            "framework-based", ["safety", "accountability", "rigor"],
            "standards-driven assurance", "low", "principle-driven",
            ["safety standards", "assurance cases", "certification data"],
            "argue mandatory verification codifies proven safety practice", "safety-critical software",
            "standards community", "proposition-supporting"),
    ],
    "opp_members": [
        member(
            "Dr. Alan Pierce",
            ["PhD in Systems Engineering", "BSc in Computer Science"],
            ["18 years delivering complex embedded systems",
             "Studies cost-effectiveness of verification techniques",
             "Advocate for risk-proportionate assurance"],
            ["systems engineering", "assurance economics"],
            "Principal Systems Engineer", "analytical", "cost-aware",
            "framework-based", ["feasibility", "cost-effectiveness", "pragmatism"],
            "risk-proportionate assurance", "moderate", "cost-benefit-driven",
            ["cost-benefit analyses", "industry data", "case studies"],
            "argue blanket mandates are infeasible and costly", "embedded systems",
            "engineering community", "opposition-supporting"),
        member(
            "Yuki Tanaka",
            ["MSc in Embedded Software", "BSc in Computer Engineering"],
            ["13 years leading agile embedded software teams",
             "Shipped safety-relevant products under iterative delivery",
             "Advocate for testing plus targeted verification"],
            ["embedded software", "agile delivery"],
            "Embedded Software Lead", "practical", "direct",
            "experience-based", ["adaptability", "delivery velocity", "pragmatism"],
            "agile pragmatism", "moderate", "experience-driven",
            ["delivery metrics", "field data", "case studies"],
            "argue mandatory formal verification slows iteration without proportional gain",
            "embedded software", "engineering community", "opposition-supporting"),
        member(
            "Daniel Cooper",
            ["MSc in Software Engineering", "BSc in Electronics"],
            ["15 years consulting on embedded and industrial software",
             "Assessed verification ROI across smaller suppliers",
             "Advocate for scalable, tool-assisted assurance"],
            ["embedded consulting", "industrial software"],
            "Embedded Systems Consultant", "practical", "cost-aware",
            "experience-based", ["feasibility", "cost-effectiveness", "pragmatism"],
            "scalable pragmatism", "moderate", "cost-benefit-driven",
            ["industry reports", "cost data", "case studies"],
            "argue mandates exclude smaller teams and lack skilled practitioners",
            "embedded software", "industry community", "opposition-supporting"),
    ],
})

# ---------------------------------------------------------------------------
# Topic 5: LLM-based vs. manual exploratory testing in CI/CD
# ---------------------------------------------------------------------------
topics.append({
    "id": "llm_vs_manual_exploratory_testing",
    "topic": "LLM-based exploratory testing should replace manual exploratory testing in CI/CD pipelines",
    "focus_keywords": ["LLM", "exploratory", "testing", "manual", "CI/CD"],
    "pro_name": "pro_llm_vs_manual_exploratory_testing",
    "opp_name": "anti_llm_vs_manual_exploratory_testing",
    "pro_members": [
        member(
            "Dr. Emma Foster",
            ["PhD in Software Testing", "BSc in Computer Science"],
            ["13 years researching automated and AI-driven testing",
             "Published on LLM-based test generation",
             "Advisor on continuous-testing strategy"],
            ["software testing", "AI in testing"],
            "AI Testing Researcher", "analytical", "evidence-based",
            "research-heavy", ["automation", "coverage", "evidence"],
            "evidence-based", "moderate", "data-driven",
            ["peer-reviewed studies", "test-coverage data", "benchmarks"],
            "show LLM agents surface defects at scale and speed", "software research",
            "academic community", "proposition-supporting"),
        member(
            "Raj Patel",
            ["MSc in Software Engineering", "BSc in Information Technology"],
            ["12 years architecting test automation in CI/CD",
             "Integrated AI test agents into delivery pipelines",
             "Speaker on continuous testing"],
            ["test automation", "CI/CD"],
            "Test Automation Architect", "systematic", "pipeline-focused",
            "framework-based", ["automation", "fast feedback", "scalability"],
            "automation-first", "moderate-high", "metrics-driven",
            ["pipeline metrics", "defect-detection data", "benchmarks"],
            "argue automation gives repeatable, scalable exploration", "software/DevOps",
            "DevOps community", "proposition-supporting"),
        member(
            "Dr. Wei Zhang",
            ["PhD in Machine Learning", "BSc in Computer Science"],
            ["11 years building ML systems for software engineering",
             "Developed LLM agents for automated test exploration",
             "Researches reliability of generative testing tools"],
            ["machine learning", "AI test tooling"],
            "ML Engineer (Testing Tools)", "analytical", "innovation-focused",
            "research-heavy", ["automation", "scalability", "evidence"],
            "automation-first", "moderate-high", "data-driven",
            ["model benchmarks", "test-coverage data", "case studies"],
            "argue LLM agents continuously improve and scale beyond humans", "AI/software",
            "ML community", "proposition-supporting"),
    ],
    "opp_members": [
        member(
            "Dr. Karen Mitchell",
            ["PhD in Quality Assurance", "BSc in Cognitive Science"],
            ["16 years researching exploratory testing and tester cognition",
             "Published on human judgment in defect discovery",
             "Advocate for skilled exploratory testing"],
            ["quality assurance", "exploratory testing"],
            "QA Research Lead", "analytical", "evidence-based",
            "research-heavy", ["human judgment", "quality", "rigor"],
            "human-centered quality", "low", "evidence-based",
            ["peer-reviewed studies", "tester observation data", "case studies"],
            "argue LLMs miss context-sensitive and novel defects", "software research",
            "academic community", "opposition-supporting"),
        member(
            "Sergei Ivanov",
            ["MSc in Software Engineering", "BSc in Computer Science"],
            ["14 years as a senior SDET on critical systems",
             "Evaluated LLM testing tools against manual exploration",
             "Skeptic of over-reliance on generative tooling"],
            ["test engineering", "quality assurance"],
            "Senior SDET", "practical", "skeptical",
            "experience-based", ["reliability", "accountability", "rigor"],
            "verification-driven", "low", "risk-aware",
            ["empirical comparisons", "false-positive data", "incident reports"],
            "highlight LLM unreliability, hallucination and oversight cost", "software",
            "engineering community", "opposition-supporting"),
        member(
            "Patricia Nolan",
            ["MSc in Quality Management", "BSc in Computer Science"],
            ["15 years managing QA teams and exploratory test charters",
             "Led human-centered testing for user-facing products",
             "Advocate for tester intuition and domain knowledge"],
            ["QA management", "human factors in testing"],
            "QA Manager", "practical", "narrative",
            "experience-based", ["human judgment", "quality", "user empathy"],
            "human-centered quality", "low", "experience-driven",
            ["tester reports", "user feedback", "case studies"],
            "argue domain intuition and empathy cannot be replaced by LLMs", "software",
            "QA community", "opposition-supporting"),
    ],
})


def build(t, level):
    n = LEVELS[level]
    pro = team(
        t["pro_name"], "proposition",
        "Advocating for: " + t["topic"], "supportive",
        t["focus_keywords"], PRO_ARGS, t["pro_members"][:n])
    opp = team(
        t["opp_name"], "opposition",
        "Opposing: " + t["topic"], "opposing",
        t["focus_keywords"], OPP_ARGS, t["opp_members"][:n])
    return {
        "id": t["id"],
        "topic": t["topic"],
        "max_rounds": level,
        "teams": [pro, opp],
        "audience": AUDIENCE,
        "output_file": "results/se/level_{}/{}.json".format(level, t["id"]),
        "include_user_interaction": False,
    }


for level in LEVELS:
    out_dir = os.path.join(SE_DIR, "level_{}".format(level))
    os.makedirs(out_dir, exist_ok=True)
    for t in topics:
        cfg = build(t, level)
        path = os.path.join(out_dir, t["id"] + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=4)
        print("wrote", path)
print("done")
