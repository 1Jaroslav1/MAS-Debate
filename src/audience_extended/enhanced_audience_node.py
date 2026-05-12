"""
Enhanced audience system that properly determines debate winners
Uses comparative evaluation and argument quality assessment
"""
from typing import List, Dict, Any, Tuple
from src.debate_extended.state import DebateState
from src.reasoning.godsaf.godsaf_service import GoDsAFService
from src.audience_extended.audience_node import ListenerProfile
from src.hub import gpt_4o_mini
from src.utils import ParallelExecutor, ParallelExecutionConfig
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate


class TeamPerformance(BaseModel):
    """Individual team performance evaluation"""
    team_name: str = Field(description="Name of the team")
    argument_quality_score: float = Field(description="Quality of arguments (0-100)", ge=0, le=100)
    evidence_strength_score: float = Field(description="Strength of evidence (0-100)", ge=0, le=100)
    persuasiveness_score: float = Field(description="Persuasiveness (0-100)", ge=0, le=100)
    logical_coherence_score: float = Field(description="Logical coherence (0-100)", ge=0, le=100)
    overall_score: float = Field(description="Overall team performance (0-100)", ge=0, le=100)
    strengths: List[str] = Field(description="Key strengths of this team's arguments")
    weaknesses: List[str] = Field(description="Key weaknesses of this team's arguments")
    best_argument: str = Field(description="The team's strongest argument")
    worst_argument: str = Field(description="The team's weakest argument")


class ComparativeEvaluation(BaseModel):
    """Comparative evaluation between teams"""
    team_performances: List[TeamPerformance] = Field(description="Performance evaluation for each team")
    winning_team: str = Field(description="Name of the winning team")
    margin_of_victory: float = Field(description="Score difference between winner and runner-up")
    key_differentiators: List[str] = Field(description="What made the winner stand out")
    swing_voters: List[str] = Field(description="Listeners who changed their vote")
    vote_breakdown: Dict[str, int] = Field(description="Final vote count per team")

class InterestPair(BaseModel):
    """Domain-goal interest pair chosen from existing AF ids"""
    domain_id: str = Field(description="Domain id from available domains (e.g., 'd_ops')")
    goal_id: str = Field(description="Goal id from available goals (e.g., 'g_safety')")


class InitialEvaluation(BaseModel):
    """Initial evaluation by listener before debate"""
    team_preference: str = Field(description="Team name that the listener initially leans toward")
    confidence_level: str = Field(description="Confidence level: high, medium, or low")
    reasoning: str = Field(description="Detailed explanation of the reasoning")
    key_factors: List[str] = Field(description="Key factors that influenced the initial lean")
    interest_pairs: List[InterestPair] = Field(description="List of domain-goal id pairs relevant to this listener")


class ListenerVote(BaseModel):
    """Individual listener vote with detailed reasoning"""
    decision: str = Field(description="Decision: team name that won their vote")
    confidence: float = Field(description="Confidence in decision (0-100)", ge=0, le=100)
    reasoning: str = Field(description="Detailed reasoning for the decision")
    key_factors: List[str] = Field(description="Key factors that influenced the decision")

class EnhancedListener:
    """Enhanced listener with comparative evaluation capabilities"""
    
    def __init__(self, profile: ListenerProfile):
        self.profile = profile
        self.initial_lean = None  # Will be set after initial evaluation
        
    def make_initial_evaluation(
        self,
        topic: str,
        teams: List[str],
        available_pairs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Make initial evaluation based on topic and team positions"""
        prompt = PromptTemplate(
            template="""
            You are a listener participating in a debate. Real people with similar backgrounds often hold different opinions on controversial topics due to personal experiences, values prioritization, and individual reasoning.
            Your Profile:
            - Name: {name}
            - Education: {education}
            - Experience: {experience}
            - Expertise: {expertise_domains}
            - Values: {core_values}
            - Philosophical Stance: {philosophical_stance}
            - Risk Tolerance: {risk_tolerance}
            - Decision Making Style: {decision_making_style}
            - Industry Background: {industry_background}
            
            Debate Topic: {topic}
            Teams: {teams}

            AVAILABLE DOMAIN-GOAL PAIRS (use only these ids when selecting):
            {pairs}
            
            CRITICAL INSTRUCTIONS:
            - Your profile suggests tendencies, not predetermined positions
            - Consider multiple valid perspectives, including those that might conflict with your initial instincts
            - Acknowledge uncertainty, internal conflicts, or mixed feelings where appropriate
            - Remember that controversial topics generate diverse opinions even among people with similar backgrounds
            
            TASKS:
            1) Based on your profile, state which team's position you initially lean toward and why.
            2) Select 1-6 domain-goal pairs that best reflect what aspects you will focus on during the debate.
               - IMPORTANT: Use ONLY domain_id and goal_id from the provided lists.
               - Choose pairs that align with your profile's expertise and values.
            """,
            input_variables=["name", "education", "experience", "expertise_domains", 
                           "core_values", "philosophical_stance", "risk_tolerance",
                           "decision_making_style", "industry_background", "topic", "teams",
                           "pairs"]
        )
        
        chain = prompt | gpt_4o_mini.with_structured_output(InitialEvaluation)
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
            "topic": topic,
            "teams": ", ".join(teams),
            "pairs": "\n".join([
                f"- domain_id={p['domain_id']}, goal_id={p['goal_id']} — domain: {p['domain_description']}; goal: {p['goal_description']}" 
                for p in available_pairs
            ])
        })
        
        # Store the structured result
        self.initial_lean = {
            "team_preference": result.team_preference,
            "confidence_level": result.confidence_level,
            "reasoning": result.reasoning,
            "key_factors": result.key_factors
        }
        
        return {
            "name": self.profile.name,
            "initial_lean": self.initial_lean,
            "interest_pairs": [{"domain_id": p.domain_id, "goal_id": p.goal_id} for p in result.interest_pairs]
        }
    
    def make_final_vote(self, topic: str, debate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make final vote after evaluating all team arguments"""
        
        # Extract team arguments and performance data
        team_arguments = debate_data.get("team_arguments", {})
        # team_performances = debate_data.get("team_performances", {})
        
        prompt = PromptTemplate(
            template="""
            You are a listener who has carefully followed the entire debate. You must determine which team performed better based on argument quality, not just your personal bias.

            Your Profile:
            - Name: {name}
            - Education: {education}
            - Experience: {experience}
            - Expertise: {expertise_domains}
            - Values: {core_values}
            - Preferred Evidence Types: {preferred_evidence_types}
            - Decision Making Style: {decision_making_style}
            
            Debate Topic: {topic}
            
            Team Arguments:
            {team_data}
            
            EVALUATION CRITERIA (be objective):
            1. ARGUMENT QUALITY: Which team presented stronger, more logical arguments?
            2. EVIDENCE STRENGTH: Which team provided better evidence that matches your preferred types?
            3. PERSUASIVENESS: Which team was more convincing overall?
            4. LOGICAL COHERENCE: Which team's reasoning was more sound?
            5. COUNTERARGUMENT HANDLING: Which team better addressed opposing views?
            
            IMPORTANT: You must vote for the team that performed BETTER in the debate, not necessarily the team you personally agree with. Be objective and fair.
            
            Consider:
            - Which team's arguments were more compelling?
            - Which team provided stronger evidence?
            - Which team handled counterarguments better?
            - Which team's logic was more sound?
            
            Vote for the team that won the debate based on performance, not personal preference.
            """,
            input_variables=["name", "education", "experience", "expertise_domains", 
                           "core_values", "preferred_evidence_types", "decision_making_style",
                           "topic", "team_data"]
        )
        
        # Format team data for the prompt
        team_data_text = ""
        for team_name, args in team_arguments.items():
            team_data_text += f"\n{team_name.upper()}:\n"
            if args and len(args) > 0 and not args[0].startswith("No arguments found"):
                team_data_text += f"Arguments:\n"
                for i, arg in enumerate(args, 1):
                    team_data_text += f"  {i}. {arg}\n"
            else:
                team_data_text += f"Arguments: No specific arguments found for this team\n"

        chain = prompt | gpt_4o_mini.with_structured_output(ListenerVote)
        result = chain.invoke({
            "name": self.profile.name,
            "education": ", ".join(self.profile.education),
            "experience": ", ".join(self.profile.experience),
            "expertise_domains": ", ".join(self.profile.expertise_domains),
            "core_values": ", ".join(self.profile.core_values),
            "preferred_evidence_types": ", ".join(self.profile.preferred_evidence_types),
            "decision_making_style": self.profile.decision_making_style,
            "topic": topic,
            "team_data": team_data_text
        })
        
        return {
            "name": self.profile.name,
            "decision": result.decision,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "key_factors": result.key_factors,
            "team_comparison": result.team_comparison
        }


class EnhancedAudienceNode:
    """
    Enhanced audience node with comparative evaluation and winner determination.
    
    Performance Optimizations:
    - Parallel listener initial evaluations with batching (10 concurrent, 0.5s delay between batches)
    - Parallel listener final votes with batching (10 concurrent, 0.5s delay between batches)
    - Parallel team performance evaluations (all teams concurrently)
    - Uses asyncio.gather for efficient API utilization
    
    Methods:
    - initial_evaluation_node: Parallel initial audience evaluation
    - final_listeners_voting_node: Parallel final voting using listener evaluations
    - final_voting_node: Final voting using GoDsAF coverage (alternative approach)
    """
    
    def __init__(self, listeners: List[EnhancedListener]):
        self.listeners = listeners
    
    def initial_evaluation_node(self, state: DebateState) -> DebateState:
        """Conduct initial evaluation by all listeners in parallel"""
        print(f"🎭 Audience initial evaluation on: {state['topic']}")
        
        team_names = [team["team_name"] for team in state["teams"]]
        
        # Build available domain/goal lists from AF for LLM selection
        af: GoDsAFService = state["af"]
        # Build all available domain-goal pairs from AF goals' pg_values
        available_pairs: List[Dict[str, Any]] = []
        for goal in af.list_goals():
            for domain_id, _ in (goal.pg_values or {}).items():
                if domain_id in af.domains:
                    domain = af.domains[domain_id]
                    available_pairs.append({
                        "domain_id": domain_id,
                        "goal_id": goal.name,
                        "domain_description": domain.description,
                        "goal_description": goal.description
                    })

        # Define evaluation function
        def evaluate_listener(listener: 'EnhancedListener') -> Dict[str, Any]:
            return listener.make_initial_evaluation(state["topic"], team_names, available_pairs)

        # Use parallel executor with aggressive retry for rate limits
        config = ParallelExecutionConfig(
            max_concurrent=5,  # Reduced concurrency to avoid rate limits
            batch_delay=2.0,  # Increased delay between batches
            retry_attempts=5,  # More retry attempts
            retry_delay=10.0,  # Longer initial retry delay for rate limits
            show_progress=False  # We'll print our own progress
        )
        executor = ParallelExecutor(config)
        
        # Run evaluations in parallel
        initial_evaluations = executor.run(
            items=self.listeners,
            func=evaluate_listener
        )
        
        # Process results
        listener_interest_pairs: Dict[str, List[Tuple[str, str]]] = {}
        for evaluation in initial_evaluations:
            if isinstance(evaluation, Exception):
                print(f"  ❌ Error evaluating listener: {evaluation}")
                continue
                
            pairs = [(p["domain_id"], p["goal_id"]) for p in evaluation.get("interest_pairs", [])]
            listener_interest_pairs[evaluation['name']] = pairs
            
            # Print result
            initial_lean_info = evaluation['initial_lean']
            if isinstance(initial_lean_info, dict):
                team_pref = initial_lean_info.get('team_preference', 'unknown')
                confidence = initial_lean_info.get('confidence_level', 'unknown')
                print(f"  📊 {evaluation['name']}: {team_pref} (confidence: {confidence})")
            else:
                print(f"  📊 {evaluation['name']}: {str(initial_lean_info)[:100]}...")
        
        # Filter out exceptions
        initial_evaluations = [e for e in initial_evaluations if not isinstance(e, Exception)]
        
        state["audience_initial_evaluations"] = initial_evaluations
        state["listener_interest_pairs"] = listener_interest_pairs
        return state
    
    def initial_voting_node(self, state: DebateState) -> DebateState:
        """Alias for initial_evaluation_node for compatibility with debate workflow"""
        # Run the enhanced initial evaluation
        state = self.initial_evaluation_node(state)
        
        # Convert enhanced evaluations to standard vote format for compatibility
        if "audience_initial_evaluations" in state:
            initial_votes = []
            initial_vote_counts = {}
            
            for evaluation in state["audience_initial_evaluations"]:
                # Get the team preference from structured initial lean
                team_preference = evaluation["initial_lean"]["team_preference"]
                
                # Convert initial lean to a simple vote format
                vote = {
                    "name": evaluation["name"],
                    "decision": team_preference,  # Use actual team preference
                    "reasoning": evaluation["initial_lean"]["reasoning"],
                    "confidence_level": evaluation["initial_lean"]["confidence_level"],
                    "key_factors": evaluation["initial_lean"]["key_factors"]
                }
                initial_votes.append(vote)
                
                # Count votes per team
                initial_vote_counts[team_preference] = initial_vote_counts.get(team_preference, 0) + 1
            
            # Determine initial winning team
            if initial_vote_counts:
                initial_winning_team = max(initial_vote_counts.items(), key=lambda x: x[1])[0]
                vote_margins = sorted(initial_vote_counts.items(), key=lambda x: x[1], reverse=True)
                initial_margin = vote_margins[0][1] - vote_margins[1][1] if len(vote_margins) >= 2 else vote_margins[0][1]
            else:
                initial_winning_team = None
                initial_margin = None

            state["audience_initial_votes"] = initial_votes
            state["initial_vote_counts"] = initial_vote_counts
            state["initial_winning_team"] = initial_winning_team
            state["initial_margin_of_victory"] = initial_margin

            # Display initial vote summary
            print(f"\n📊 INITIAL VOTE SUMMARY:")
            for team, count in initial_vote_counts.items():
                print(f"   {team}: {count} votes")
            print(f"   Total listeners: {len(initial_votes)}")
            if initial_winning_team:
                print(f"   Initial winner: {initial_winning_team} (margin: {initial_margin})")

        return state
    
    def extract_team_arguments(self, state: DebateState) -> Dict[str, List[str]]:
        """Extract arguments from each team for evaluation"""
        team_arguments = {}
        
        for team in state["teams"]:
            team_name = team["team_name"]
            arguments = []
            
            team_args = state["af"].get_arguments_by_team(team_name)
            print(f"  📝 Found {len(team_args)} arguments for {team_name}")
            for arg in team_args:
                arguments.append(arg.text)
                print(f"    - {arg.text[:100]}...")
            team_arguments[team_name] = arguments
        
        return team_arguments
    
    def final_listeners_voting_node(self, state: DebateState) -> DebateState:
        """Conduct final voting using listeners' make_final_vote in parallel"""
        print(f"🎭 Audience final voting using listener evaluations")
        
        # Extract team arguments for voting
        team_arguments = self.extract_team_arguments(state)
        debate_data = {"team_arguments": team_arguments}
        
        # Define vote function
        def make_vote(listener: 'EnhancedListener') -> Dict[str, Any]:
            return listener.make_final_vote(state["topic"], debate_data)

        # Use parallel executor with aggressive retry for rate limits
        config = ParallelExecutionConfig(
            max_concurrent=5,  # Reduced concurrency to avoid rate limits
            batch_delay=2.0,  # Increased delay between batches
            retry_attempts=5,  # More retry attempts
            retry_delay=10.0,  # Longer initial retry delay for rate limits
            show_progress=False  # We'll print our own progress
        )
        executor = ParallelExecutor(config)
        
        # Run votes in parallel
        final_votes = executor.run(
            items=self.listeners,
            func=make_vote
        )
        
        # Process results and print
        valid_votes = []
        for vote in final_votes:
            if isinstance(vote, Exception):
                print(f"  ❌ Error in vote: {vote}")
                continue
            valid_votes.append(vote)
            print(f"  📊 {vote['name']}: {vote['decision']} (confidence: {vote.get('confidence', 'N/A')})")
        
        final_votes = valid_votes

        # Count final votes
        final_vote_counts: Dict[str, int] = {}
        for vote in final_votes:
            final_vote_counts[vote["decision"]] = final_vote_counts.get(vote["decision"], 0) + 1

        # Determine winner
        final_winning_team = max(final_vote_counts.items(), key=lambda x: x[1])[0]
        vote_margins = sorted(final_vote_counts.items(), key=lambda x: x[1], reverse=True)
        final_margin = vote_margins[0][1] - vote_margins[1][1] if len(vote_margins) >= 2 else vote_margins[0][1]

        # Analyze vote changes
        final_vote_changes = self.analyze_vote_changes(state, final_votes)

        # Update state with prefixed fields
        state["audience_final_votes"] = [{"name": v["name"], "decision": v["decision"], "reasoning": v["reasoning"]} for v in final_votes]
        state["audience_final_votes_enhanced"] = final_votes
        state["final_vote_counts"] = final_vote_counts
        state["final_winning_team"] = final_winning_team
        state["final_margin_of_victory"] = final_margin
        state["final_vote_changes"] = final_vote_changes

        print(f"\n🏆 FINAL RESULTS:")
        print(f"   Winner: {final_winning_team} ({final_vote_counts[final_winning_team]} votes)")
        print(f"   Vote breakdown: {final_vote_counts}")
        print(f"   Margin of victory: {final_margin} votes")
        self.display_vote_changes(final_vote_changes)
        
        print("GoDsAF coverage:")
        # self.final_voting_node(state)

        return state
    
    def final_voting_node(self, state: DebateState) -> DebateState:
        """Conduct final voting using GoDsAF coverage across listener domain-goal interests"""
        print(f"🎭 Audience final voting using GoDsAF coverage")

        af: GoDsAFService = state["af"]
        # Solve once to get team coverage metrics per (goal, domain)
        godsaf_results = af.solve()
        tgs = godsaf_results.get("tgs", {})  # team -> {(goal, domain): value}

        # Build listener interests as pairs (domain, goal) from saved initial evaluations
        listener_interests: Dict[str, List[Tuple[str, str]]] = {}
        for evaluation in state.get("audience_initial_evaluations", []):
            name = evaluation.get("name")
            pairs_raw = evaluation.get("interest_pairs", []) or []
            pairs: List[Tuple[str, str]] = []
            for p in pairs_raw:
                d_id = p.get("domain_id")
                g_id = p.get("goal_id")
                if d_id and g_id:
                    pairs.append((d_id, g_id))
            if name:
                listener_interests[name] = pairs

        # For each listener, vote for team with higher cumulative TGS across their pairs
        final_votes = []
        teams = [team["team_name"] for team in state["teams"]]
        for listener in self.listeners:
            name = listener.profile.name
            pairs = listener_interests.get(name, [])
            team_scores: Dict[str, int] = {t: 0 for t in teams}
            for team_name in teams:
                per_team = tgs.get(team_name, {})
                score_sum = 0
                for (d_id, g_id) in pairs:
                    score_sum += per_team.get((g_id, d_id), 0)
                team_scores[team_name] = score_sum

            # Choose team with max score; break ties by larger global total over all pairs
            decision = max(team_scores.items(), key=lambda x: x[1])[0]
            confidence = 100.0 if sum(team_scores.values()) == 0 else (
                (team_scores[decision] / (sum(team_scores.values()) or 1)) * 100.0
            )
            final_votes.append({
                "name": name,
                "decision": decision,
                "confidence": confidence,
                "reasoning": f"Based on GoDsAF TGS over listener domain-goal interests: {pairs}",
                "key_factors": [f"{d}-{g}" for (d, g) in pairs],
                "team_comparison": str(team_scores)
            })

        final_vote_counts: Dict[str, int] = {}
        for vote in final_votes:
            final_vote_counts[vote["decision"]] = final_vote_counts.get(vote["decision"], 0) + 1

        final_winning_team = max(final_vote_counts.items(), key=lambda x: x[1])[0]
        vote_margins = sorted(final_vote_counts.items(), key=lambda x: x[1], reverse=True)
        final_margin = vote_margins[0][1] - vote_margins[1][1] if len(vote_margins) >= 2 else vote_margins[0][1]

        final_vote_changes = self.analyze_vote_changes(state, final_votes)

        print(f"\n🏆 FINAL RESULTS:")
        print(f"   Winner: {final_winning_team} ({final_vote_counts[final_winning_team]} votes)")
        print(f"   Vote breakdown: {final_vote_counts}")
        print(f"   Margin of victory: {final_margin} votes")
        self.display_vote_changes(final_vote_changes)

        # return state
    
    def analyze_vote_changes(self, state: DebateState, final_votes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze changes between initial and final votes"""
        initial_votes = state.get("audience_initial_votes", [])

        # Create lookup for initial votes by name
        initial_vote_lookup = {vote["name"]: vote["decision"] for vote in initial_votes}
        
        # Track changes
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
    
    def display_vote_changes(self, vote_changes: Dict[str, Any]) -> None:
        """Display detailed vote change analysis"""
        print(f"\n🔄 VOTE CHANGE ANALYSIS:")
        print(f"   Total listeners who changed their vote: {vote_changes['total_changes']}")
        print(f"   Change percentage: {vote_changes['change_percentage']:.1f}%")
        
        if vote_changes['changed_votes']:
            print(f"\n📝 INDIVIDUAL VOTE CHANGES:")
            for change in vote_changes['changed_votes']:
                print(f"   {change['name']}: {change['initial_decision']} → {change['final_decision']} (confidence: {change['confidence']:.1f}%)")
        
        if vote_changes['net_changes']:
            print(f"\n📊 NET VOTE CHANGES BY TEAM:")
            for team, net_change in vote_changes['net_changes'].items():
                if net_change != 0:
                    direction = "gained" if net_change > 0 else "lost"
                    print(f"   {team}: {direction} {abs(net_change)} votes")
        
        if vote_changes['unchanged_votes']:
            print(f"\n✅ UNCHANGED VOTES: {len(vote_changes['unchanged_votes'])} listeners")
            # Show a few examples
            examples = vote_changes['unchanged_votes'][:3]
            for vote in examples:
                print(f"   {vote['name']}: {vote['decision']} (confidence: {vote['confidence']:.1f}%)")
            if len(vote_changes['unchanged_votes']) > 3:
                print(f"   ... and {len(vote_changes['unchanged_votes']) - 3} more")


def create_enhanced_audience_node(listeners: List[EnhancedListener]) -> EnhancedAudienceNode:
    """Factory function to create enhanced audience node"""
    return EnhancedAudienceNode(listeners)


def create_enhanced_sample_listeners(topic: str) -> List[EnhancedListener]:
    """Create enhanced sample listeners with diverse profiles"""
    
    listener_profiles = [
        ListenerProfile(
            name="Dr. Sarah Chen",
            education=["PhD in Computer Science from MIT", "MS in Ethics from Stanford"],
            experience=["10 years AI research", "5 years tech policy consulting"],
            expertise_domains=["machine learning", "AI ethics", "technology policy"],
            current_role="AI Ethics Researcher",
            thinking_style="analytical",
            communication_style="academic",
            argumentation_preference="evidence-heavy",
            core_values=["scientific integrity", "responsible innovation"],
            philosophical_stance="pragmatic technologist",
            risk_tolerance="conservative",
            decision_making_style="data-driven",
            preferred_evidence_types=["peer-reviewed research", "empirical studies"],
            typical_counterargument_approach="systematic analysis",
            industry_background="technology research",
            cultural_background="academic STEM environment",
            notable_biases=["pro-research bias"]
        ),
        
        ListenerProfile(
            name="Marcus Williams",
            education=["MBA from Wharton", "BS in Economics"],
            experience=["15 years venture capital", "startup founder"],
            expertise_domains=["business strategy", "market dynamics", "innovation management"],
            current_role="Venture Capital Partner",
            thinking_style="strategic",
            communication_style="direct",
            argumentation_preference="case-study-based",
            core_values=["economic growth", "innovation", "market efficiency"],
            philosophical_stance="free market advocate",
            risk_tolerance="aggressive",
            decision_making_style="quick",
            preferred_evidence_types=["market data", "business case studies"],
            typical_counterargument_approach="present alternative business models",
            industry_background="venture capital",
            cultural_background="business/entrepreneurial environment",
            notable_biases=["market-solution preference"]
        ),
        
        ListenerProfile(
            name="Dr. Aisha Patel",
            education=["MD from Johns Hopkins", "MPH in Public Health"],
            experience=["12 years clinical practice", "public health policy work"],
            expertise_domains=["clinical medicine", "public health", "healthcare policy"],
            current_role="Physician and Public Health Advocate",
            thinking_style="systematic",
            communication_style="empathetic",
            argumentation_preference="patient-centered",
            core_values=["patient safety", "healthcare equity", "evidence-based medicine"],
            philosophical_stance="public health focused",
            risk_tolerance="conservative",
            decision_making_style="deliberate",
            preferred_evidence_types=["clinical trials", "epidemiological studies"],
            typical_counterargument_approach="focus on patient safety",
            industry_background="healthcare",
            cultural_background="medical and public service environment",
            notable_biases=["patient-first perspective"]
        )
    ]
    
    return [EnhancedListener(profile) for profile in listener_profiles]
