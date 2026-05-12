from typing import List, Dict, Any, Optional
from src.debate_extended.state import DebateState
from src.reasoning.godsaf.godsaf_service import GoDsAFService
from src.hub import gpt_4o_mini
from src.utils import ParallelExecutor, ParallelExecutionConfig
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate


class ListenerProfile(BaseModel):
    name: str = Field(description="Listener name/identifier")
    education: List[str] = Field(description="Educational background (degrees, institutions)")
    experience: List[str] = Field(description="Professional experience areas")
    expertise_domains: List[str] = Field(description="Areas of knowledge/expertise")
    current_role: str = Field(description="Current professional role")
    thinking_style: str = Field(description="Analytical/intuitive/systematic/creative")
    communication_style: str = Field(description="Direct/diplomatic/academic/conversational")
    argumentation_preference: str = Field(description="Evidence-heavy/story-driven/logical/emotional")
    core_values: List[str] = Field(description="Fundamental values that guide decision-making")
    philosophical_stance: str = Field(description="General worldview or philosophical approach")
    risk_tolerance: str = Field(description="Conservative/moderate/aggressive")
    decision_making_style: str = Field(description="Quick/deliberate/consensus-seeking/data-driven")
    preferred_evidence_types: List[str] = Field(description="Research/case studies/expert opinions/statistics")
    typical_counterargument_approach: str = Field(description="How they typically evaluate opposing views")
    industry_background: Optional[str] = Field(default=None, description="Primary industry experience")
    cultural_background: Optional[str] = Field(default=None, description="Cultural influences on perspective")
    notable_biases: List[str] = Field(default=[], description="Known cognitive biases or perspectives"
)

class ListenerVote(BaseModel):
    decision: str = Field(description="Decision: either 'agree' or 'disagree'.")
    reasoning: str = Field(description="Brief reasoning for the decision based on profile.")


class DomainMapping(BaseModel):
    domain_id: str = Field(description="Unique domain identifier (e.g., 'd_technology')")
    domain_name: str = Field(description="Human-readable domain name")
    domain_description: str = Field(description="Detailed description of the domain")
    salience: int = Field(description="Importance score (1-100)", ge=1, le=100)
    relevance_reason: str = Field(description="Why this domain is relevant to the audience")


class GoalMapping(BaseModel):
    goal_id: str = Field(description="Unique goal identifier (e.g., 'g_safety')")
    goal_name: str = Field(description="Human-readable goal name")
    goal_description: str = Field(description="Detailed description of the goal")
    relevance_reason: str = Field(description="Why this goal is relevant to the audience")


class AudienceMappingOutput(BaseModel):
    domains: List[DomainMapping] = Field(description="List of relevant domains for this audience")
    goals: List[GoalMapping] = Field(description="List of relevant goals for this audience")


class Listener:
    def __init__(self, profile: ListenerProfile):
        self.profile = profile
        
    def make_initial_vote(self, topic: str) -> Dict[str, str]:
        prompt = PromptTemplate(
            template="""
            You are a listener participating in a debate. You must answer EXACTLY as your profile defines - this is critical for accuracy and authenticity.

            CRITICAL INSTRUCTIONS:
            - Answer with the HIGHEST PRECISION based on your specific profile characteristics
            - Your decision must align with your education, experience, values, and background
            - Consider how someone with YOUR EXACT profile would realistically think about this topic
            - Do NOT give generic or neutral responses - be specific to YOUR profile

            Your Detailed Profile:
            - Name: {name}
            - Education: {education}
            - Professional Experience: {experience}
            - Areas of Expertise: {expertise_domains}
            - Core Values & Principles: {core_values}
            - Philosophical Stance: {philosophical_stance}
            - Risk Tolerance: {risk_tolerance}
            - Decision Making Style: {decision_making_style}
            - Industry Background: {industry_background}
            - Cultural Background: {cultural_background}
            
            Debate Topic: {topic}
            
            Based on YOUR SPECIFIC background, values, expertise, and worldview, do you initially "agree" or "disagree" with this statement?
            
            REMEMBER: Answer as this specific person would, with the highest precision to their profile. Your reasoning should directly reference specific aspects of your profile that influence this decision.
            """,
            input_variables=["name", "education", "experience", "expertise_domains", 
                           "core_values", "philosophical_stance", "risk_tolerance",
                           "decision_making_style", "industry_background", 
                           "cultural_background", "topic"]
        )
        
        chain = prompt | gpt_4o_mini.with_structured_output(ListenerVote)
        result = chain.invoke({
            "name": self.profile.name,
            "education": ", ".join(self.profile.education),
            "experience": ", ".join(self.profile.experience),
            "expertise_domains": ", ".join(self.profile.expertise_domains),
            "core_values": ", ".join(self.profile.core_values),
            "philosophical_stance": self.profile.philosophical_stance,
            "risk_tolerance": self.profile.risk_tolerance,
            "decision_making_style": self.profile.decision_making_style,
            "industry_background": self.profile.industry_background or "None",
            "cultural_background": self.profile.cultural_background or "None",
            "topic": topic
        })
        
        return {
            "name": self.profile.name,
            "decision": result.decision,
            "reasoning": result.reasoning
        }
    
    def make_final_vote(self, topic: str, debate_transcript: str) -> Dict[str, str]:
        prompt = PromptTemplate(
            template="""
            You are a listener who has carefully followed the entire debate. You must make your final decision with the HIGHEST PRECISION based on your specific profile.

            CRITICAL INSTRUCTIONS:
            - Answer EXACTLY as your profile defines - this is essential for authenticity
            - Your decision must be TRUE to your education, experience, values, and expertise
            - Consider how someone with YOUR EXACT background would evaluate these arguments
            - Weight evidence types based on YOUR preferences and expertise
            - Let your industry/cultural background significantly influence your perspective
            - Do NOT give generic responses - be specific to YOUR unique profile

            Your Detailed Profile:
            - Name: {name}
            - Education: {education}
            - Professional Experience: {experience}
            - Areas of Expertise: {expertise_domains}
            - Core Values & Principles: {core_values}
            - Philosophical Stance: {philosophical_stance}
            - Risk Tolerance: {risk_tolerance}
            - Decision Making Style: {decision_making_style}
            - Preferred Evidence Types: {preferred_evidence_types}
            - Industry Background: {industry_background}
            - Cultural Background: {cultural_background}
            
            Debate Topic: {topic}
            
            Complete Debate Transcript:
            {debate_transcript}
            
            Now, having heard all arguments, do you "agree" or "disagree" with the statement?
            
            EVALUATION CRITERIA (based on YOUR profile):
            - Which arguments align with YOUR specific values and expertise?
            - What evidence types presented match YOUR preferences? (Give these more weight)
            - How does YOUR industry/cultural background shape your interpretation?
            - What would someone with YOUR exact education and experience conclude?
            
            Your final decision must be authentic to who YOU are as defined by your profile. Reference specific aspects of your background that influenced your decision.
            """,
            input_variables=["name", "education", "experience", "expertise_domains", "core_values", "philosophical_stance", "risk_tolerance","decision_making_style", "preferred_evidence_types","industry_background", "cultural_background", "topic", "debate_transcript"]
        )
        
        chain = prompt | gpt_4o_mini.with_structured_output(ListenerVote)
        result = chain.invoke({
            "name": self.profile.name,
            "education": ", ".join(self.profile.education),
            "experience": ", ".join(self.profile.experience),
            "expertise_domains": ", ".join(self.profile.expertise_domains),
            "core_values": ", ".join(self.profile.core_values),
            "philosophical_stance": self.profile.philosophical_stance,
            "risk_tolerance": self.profile.risk_tolerance,
            "decision_making_style": self.profile.decision_making_style,
            "preferred_evidence_types": ", ".join(self.profile.preferred_evidence_types),
            "industry_background": self.profile.industry_background or "None",
            "cultural_background": self.profile.cultural_background or "None",
            "topic": topic,
            "debate_transcript": debate_transcript
        })
        
        return {
            "name": self.profile.name,
            "decision": result.decision,
            "reasoning": result.reasoning
        }


class AudienceNode:
    """
    Audience node containing multiple listener agents.
    
    Performance Optimizations:
    - Parallel initial voting with batching (10 concurrent, 0.5s delay between batches)
    - Parallel final voting with batching (10 concurrent, 0.5s delay between batches)
    - Uses ParallelExecutor for efficient API utilization
    """
    
    def __init__(self, listeners: List[Listener]):
        self.listeners = listeners
    
    def initial_voting_node(self, state: DebateState) -> DebateState:
        print(f"🎭 Audience initial voting on: {state['topic']}")

        def make_initial_vote(listener: 'Listener') -> Dict[str, Any]:
            return listener.make_initial_vote(state["topic"])

        config = ParallelExecutionConfig(
            max_concurrent=5,
            batch_delay=2.0,  # Increased delay between batches
            retry_attempts=5,  # More retry attempts for rate limits
            retry_delay=10.0,  # Longer initial retry delay
            show_progress=False
        )
        executor = ParallelExecutor(config)

        initial_votes = executor.run(
            items=self.listeners,
            func=make_initial_vote
        )

        valid_votes = []
        for vote in initial_votes:
            if isinstance(vote, Exception):
                print(f"  ❌ Error in vote: {vote}")
                continue
            valid_votes.append(vote)
            print(f"  📊 {vote['name']}: {vote['decision']} - {vote['reasoning'][:100]}...")

        # Count initial votes
        initial_vote_counts: Dict[str, int] = {}
        for vote in valid_votes:
            initial_vote_counts[vote["decision"]] = initial_vote_counts.get(vote["decision"], 0) + 1

        # Determine initial winning team
        if initial_vote_counts:
            initial_winning_team = max(initial_vote_counts.items(), key=lambda x: x[1])[0]
            vote_margins = sorted(initial_vote_counts.items(), key=lambda x: x[1], reverse=True)
            initial_margin = vote_margins[0][1] - vote_margins[1][1] if len(vote_margins) >= 2 else vote_margins[0][1]
        else:
            initial_winning_team = None
            initial_margin = None

        state["audience_initial_votes"] = valid_votes
        state["initial_vote_counts"] = initial_vote_counts
        state["initial_winning_team"] = initial_winning_team
        state["initial_margin_of_victory"] = initial_margin

        return state
    
    def final_voting_node(self, state: DebateState) -> DebateState:
        print(f"🎭 Audience final voting after debate")
        
        debate_transcript = self._get_debate_transcript(state["af"])
        
        def make_final_vote(listener: 'Listener') -> Dict[str, Any]:
            return listener.make_final_vote(state["topic"], debate_transcript)

        config = ParallelExecutionConfig(
            max_concurrent=5,  # Reduced concurrency to avoid rate limits
            batch_delay=2.0,  # Increased delay between batches
            retry_attempts=5,  # More retry attempts for rate limits
            retry_delay=10.0,  # Longer initial retry delay
            show_progress=False
        )
        executor = ParallelExecutor(config)
        
        final_votes = executor.run(
            items=self.listeners,
            func=make_final_vote
        )

        valid_votes = []
        for vote in final_votes:
            if isinstance(vote, Exception):
                print(f"  ❌ Error in vote: {vote}")
                continue
            valid_votes.append(vote)
            print(f"  📊 {vote['name']}: {vote['decision']} - {vote['reasoning'][:100]}...")

        final_votes = valid_votes

        # Count final votes
        final_vote_counts: Dict[str, int] = {}
        for vote in final_votes:
            final_vote_counts[vote["decision"]] = final_vote_counts.get(vote["decision"], 0) + 1

        final_winning_team = max(final_vote_counts.items(), key=lambda x: x[1])[0]
        vote_margins = sorted(final_vote_counts.items(), key=lambda x: x[1], reverse=True)
        final_margin = vote_margins[0][1] - vote_margins[1][1] if len(vote_margins) >= 2 else vote_margins[0][1]
        final_vote_changes = self.analyze_vote_changes(state, final_votes)

        state["audience_final_votes"] = valid_votes
        state["final_vote_counts"] = final_vote_counts
        state["final_winning_team"] = final_winning_team
        state["final_margin_of_victory"] = final_margin
        state["final_vote_changes"] = final_vote_changes

        return state
    
    def analyze_vote_changes(self, state: DebateState, final_votes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze changes between initial and final votes"""
        initial_votes = state.get("audience_initial_votes", [])

        initial_vote_lookup = {vote["name"]: vote["decision"] for vote in initial_votes}
        
        unchanged_votes = []
        changed_votes = []
        vote_swings = {}  # Track which teams gained/lost votes
        
        for final_vote in final_votes:
            name = final_vote["name"]
            final_decision = final_vote["decision"]
            initial_decision = initial_vote_lookup.get(name, "unknown")
            
            if initial_decision == final_decision:
                unchanged_votes.append({
                    "name": name,
                    "decision": final_decision,
                    "confidence": final_vote.get("confidence", 0)
                })
            else:
                changed_votes.append({
                    "name": name,
                    "initial_decision": initial_decision,
                    "final_decision": final_decision,
                    "confidence": final_vote.get("confidence", 0),
                    "reasoning": final_vote.get("reasoning", "")
                })
                
                # Track vote swings
                if initial_decision != "unknown":
                    if initial_decision not in vote_swings:
                        vote_swings[initial_decision] = {"lost": 0, "gained": 0}
                    if final_decision not in vote_swings:
                        vote_swings[final_decision] = {"lost": 0, "gained": 0}
                    
                    vote_swings[initial_decision]["lost"] += 1
                    vote_swings[final_decision]["gained"] += 1
        
        # Calculate net changes per team
        net_changes = {}
        for team in vote_swings:
            net_changes[team] = vote_swings[team]["gained"] - vote_swings[team]["lost"]
        
        return {
            "unchanged_votes": unchanged_votes,
            "changed_votes": changed_votes,
            "vote_swings": vote_swings,
            "net_changes": net_changes,
            "total_changes": len(changed_votes),
            "change_percentage": (len(changed_votes) / len(final_votes)) * 100 if final_votes else 0
        }
    
    def _get_debate_transcript(self, af_service: GoDsAFService) -> str:
        try:
            arguments_info = []
            for _, arg in af_service.arguments.items():
                arguments_info.append(f"Argument by {arg.team}: {arg.text}")
            
            if arguments_info:
                return "\n".join(arguments_info)
            else:
                return "No debate transcript available yet."
        except Exception as e:
            print(f"Warning: Could not retrieve debate transcript: {e}")
            return "Debate transcript unavailable."

def generate_audience_mapping(listeners: List[Listener], max_domains: int = 6, max_goals: int = 6) -> AudienceMappingOutput:
    """Use LLM to generate domains and goals based on audience profiles
    
    Args:
        listeners: List of listener objects
        max_domains: Maximum number of domains to generate (default: 6)
        max_goals: Maximum number of goals to generate (default: 6)
    """
    
    audience_summary = []
    for listener in listeners:
        profile_summary = f"""
        {listener.profile.name}:
        - Education: {', '.join(listener.profile.education)}
        - Experience: {', '.join(listener.profile.experience)}
        - Expertise: {', '.join(listener.profile.expertise_domains)}
        - Values: {', '.join(listener.profile.core_values)}
        - Philosophical Stance: {listener.profile.philosophical_stance}
        - Industry: {listener.profile.industry_background or 'N/A'}
        - Decision Style: {listener.profile.decision_making_style}
        """
        audience_summary.append(profile_summary.strip())
    
    audience_text = "\n\n".join(audience_summary)
    
    prompt = PromptTemplate(
        template="""
        You are an expert analyst tasked with identifying the most relevant domains and goals for a debate framework based on the audience composition.

        Audience Profiles:
        {audience_profiles}

        Based on these audience profiles, identify the most relevant domains and goals that would be important for structuring a debate analysis.

        DOMAINS should represent key areas of knowledge, expertise, or impact that are relevant to this audience. Each domain should:
        - Have a unique identifier starting with 'd_' (e.g., 'd_technology', 'd_healthcare')
        - Have a clear, descriptive name
        - Have a detailed description explaining what it covers
        - Have a salience score (1-100) indicating its importance to this audience
        - Include reasoning for why it's relevant to this specific audience

        GOALS should represent objectives, values, or outcomes that this audience would care about. Each goal should:
        - Have a unique identifier starting with 'g_' (e.g., 'g_safety', 'g_innovation')
        - Have a clear, descriptive name  
        - Have a detailed description explaining what it represents
        - Include reasoning for why it's relevant to this specific audience

        Generate exactly {max_domains} domains and {max_goals} goals that best represent the interests, expertise, and values of this audience.
        """,
        input_variables=["audience_profiles", "max_domains", "max_goals"]
    )
    
    chain = prompt | gpt_4o_mini.with_structured_output(AudienceMappingOutput)
    result = chain.invoke({
        "audience_profiles": audience_text,
        "max_domains": max_domains,
        "max_goals": max_goals
    })
    
    return result


def map_audience_to_domains_goals(listeners: List[Listener], af_service: GoDsAFService, max_domains: int = 6, max_goals: int = 6):
    """Map audience listener profiles to relevant domains and goals using LLM analysis
    
    Args:
        listeners: List of listener objects
        af_service: GoDsAF service instance
        max_domains: Maximum number of domains to generate (default: 6)
        max_goals: Maximum number of goals to generate (default: 6)
    """
    
    print("🤖 Generating domains and goals based on audience profiles...")
    print(f"   Max domains: {max_domains}, Max goals: {max_goals}")
    
    mapping_result = generate_audience_mapping(listeners, max_domains, max_goals)
    
    print("\n📂 Adding domains:")
    for domain in mapping_result.domains:
        af_service.add_domain(domain.domain_id, domain.domain_description, domain.salience)
        print(f"  {domain.domain_name}: {domain.domain_description} (salience: {domain.salience})")
        print(f"    Reason: {domain.relevance_reason}")
    
    print("\n🎯 Adding goals:")
    for goal in mapping_result.goals:
        # Create PG values for each goal across all domains
        pg_values = {}
        for domain in mapping_result.domains:
            # Assign PG values based on semantic relevance
            # This could be enhanced with more sophisticated matching
            base_value = 35
            # Add variation based on goal-domain combination
            variation = hash(goal.goal_id + domain.domain_id) % 30  # 0-29
            pg_values[domain.domain_id] = base_value + variation  # 35-64 range
        
        af_service.add_goal(goal.goal_id, goal.goal_description, pg_values)
        print(f"  {goal.goal_name}: {goal.goal_description}")
        print(f"    Reason: {goal.relevance_reason}")
    
    print(f"\n✅ Added {len(mapping_result.domains)} domains and {len(mapping_result.goals)} goals")
