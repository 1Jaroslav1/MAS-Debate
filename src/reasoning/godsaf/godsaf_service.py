from clingo import Control
from typing import List, Dict, Tuple, Optional, Set, Union
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class Domain:
    """Represents a domain in the debate framework"""
    name: str
    description: str
    salience: int
    
    def __str__(self):
        return f"{self.name} ({self.description})"


@dataclass
class Goal:
    """Represents a goal in the debate framework"""
    name: str
    description: str
    pg_values: Dict[str, int] = field(default_factory=dict)  # domain_name -> pg_value
    
    def __str__(self):
        return f"{self.name} ({self.description})"
    
    def add_pg_value(self, domain_name: str, value: int):
        """Add or update PG value for a domain"""
        self.pg_values[domain_name] = value
    
    def get_pg_value(self, domain_name: str) -> Optional[int]:
        """Get PG value for a domain"""
        return self.pg_values.get(domain_name)


@dataclass
class Argument:
    """Represents an argument in the debate"""

    name: str
    text: str
    team: str
    domains: Set[str]
    goals: Dict[str, Set[str]]
    attacks: Set[str] = field(default_factory=set)


@dataclass
class UGNEntry:
    """Unmet Goal Need entry"""

    team: str
    goal: Goal
    domain: Domain
    value: int


@dataclass
class CandidateArgument:
    """Represents a potential new argument to evaluate"""

    name: str
    text: str
    team: str
    domains: Set[str]
    goals: Dict[str, List[str]]
    attacks: Set[str] = field(default_factory=set)


class GoDsAFService:
    """Enhanced GoDsAF Service with Domain and Goal classes"""

    # Embedded rules as a constant
    RULES = """
% ===== STRENGTH CALCULATION =====
apc(A, G, D, Value) :- 
    goal_coverage_claim(A, G, D),
    pg_value(G, D, PG),
    sd_value(D, SD),
    Value = PG * SD.

arg_strength(A, D, TotalStr) :-
    argument(A),
    domain_element(D),
    prior_domain(A, D),
    TotalStr = #sum { APC, G : apc(A, G, D, APC) }.

arg_strength(A, D, 0) :-
    argument(A),
    domain_element(D),
    not prior_domain(A, D).

% ===== STRENGTH-BASED DEFEAT =====
defeat(A1, A2, D) :-
    attacks(A1, A2),
    prior_domain(A1, D),
    prior_domain(A2, D),
    arg_strength(A1, D, Str1),
    arg_strength(A2, D, Str2),
    Str1 > Str2.

% ===== SCOPE DETERMINATION =====
{ scope(A, D) } :- prior_domain(A, D).

undefended(A, D) :-
    defeat(B, A, D),
    not defeated_in_scope(B, D).

defeated_in_scope(B, D) :-
    defeat(C, B, D),
    scope(C, D).

:- scope(A, D), undefended(A, D).
:- prior_domain(A, D), not undefended(A, D), not scope(A, D).

% ===== EFFECTIVE CHALLENGERS =====
effective_challenger(Target, Challenger, D) :-
    scope(Target, D),
    scope(Challenger, D),
    attacks(Challenger, Target),
    team_of(Target, T1),
    team_of(Challenger, T2),
    T1 != T2.

num_challengers(A, N) :-
    argument(A),
    N = #count { C, D : effective_challenger(A, C, D) }.

% ===== APS CALCULATION =====
aps_for_domain(A, D, APS) :-
    scope(A, D),
    arg_strength(A, D, Str),
    num_challengers(A, 0),
    APS = Str.

aps_for_domain(A, D, APS) :-
    scope(A, D),
    arg_strength(A, D, Str),
    num_challengers(A, 1),
    APS = (Str * 40) / 100.

aps_for_domain(A, D, APS) :-
    scope(A, D),
    arg_strength(A, D, Str),
    num_challengers(A, N),
    N > 1,
    APS = (Str * 16) / 100.

total_aps(A, Total) :-
    argument(A),
    Total = #sum { APS, D : aps_for_domain(A, D, APS) }.

total_aps(A, 0) :-
    argument(A),
    not scope(A, _).

% ===== TEAM METRICS =====
eapc(A, G, D, EAPC) :-
    goal_coverage_claim(A, G, D),
    scope(A, D),
    apc(A, G, D, APCVal),
    num_challengers(A, 0),
    EAPC = APCVal.

eapc(A, G, D, EAPC) :-
    goal_coverage_claim(A, G, D),
    scope(A, D),
    apc(A, G, D, APCVal),
    num_challengers(A, N),
    N > 0,
    EAPC = (APCVal * 40) / 100.

eapc(A, G, D, 0) :-
    goal_coverage_claim(A, G, D),
    not scope(A, D).

tgs(Team, G, D, Sum) :-
    team(Team),
    goal_primitive(G),
    domain_element(D),
    Sum = #sum { EAPC, A : eapc(A, G, D, EAPC), team_of(A, Team) }.

regs(G, D, Value) :-
    pg_value(G, D, PG),
    sd_value(D, SD),
    Value = PG * SD.

ugn(Team, G, D, Need) :-
    team(Team),
    goal_primitive(G),
    domain_element(D),
    regs(G, D, ReGS),
    tgs(Team, G, D, TGS),
    Need = ReGS - TGS,
    Need > 0.

ugn(Team, G, D, 0) :-
    team(Team),
    goal_primitive(G),
    domain_element(D),
    regs(G, D, ReGS),
    tgs(Team, G, D, TGS),
    ReGS <= TGS.
"""

    def __init__(self):
        self.teams: Set[str] = set()
        self.arguments: Dict[str, Argument] = {}
        self.domains: Dict[str, Domain] = {}
        self.goals: Dict[str, Goal] = {}
        self.current_candidate_id: str = None
        self.candidate_arguments: Dict[str, CandidateArgument] = {}
        self._reset_control()

    def _reset_control(self):
        """Reset the Clingo control"""
        self.ctl = Control(arguments=[], logger=None, message_limit=0)
        self.ctl.add("base", [], self.RULES)
        self._add_all_facts()

    def _add_all_facts(self):
        """Add all facts to control"""
        facts_string = self._generate_all_facts()
        if facts_string:
            self.ctl.add("base", [], facts_string)

    def _generate_all_facts(self) -> str:
        """Generate all facts as a string"""
        facts = []

        # Teams
        for team in sorted(self.teams):
            facts.append(f"team({team}).")

        # Domains
        for domain_name in sorted(self.domains.keys()):
            domain = self.domains[domain_name]
            facts.append(f"domain_element({domain.name}).")
            facts.append(f"sd_value({domain.name}, {domain.salience}).")

        # Goals
        for goal_name in sorted(self.goals.keys()):
            goal = self.goals[goal_name]
            facts.append(f"goal_primitive({goal.name}).")
            
            # Add PG values for this goal
            for domain_name, value in sorted(goal.pg_values.items()):
                facts.append(f"pg_value({goal.name}, {domain_name}, {value}).")

        # Arguments
        for arg_name in sorted(self.arguments.keys()):
            arg = self.arguments[arg_name]
            facts.append(f"argument({arg_name}).")
            facts.append(f"team_of({arg_name}, {arg.team}).")

            for domain in sorted(arg.domains):
                facts.append(f"prior_domain({arg_name}, {domain}).")

            for goal, domains in sorted(arg.goals.items()):
                for domain in sorted(domains):
                    facts.append(f"goal_coverage_claim({arg_name}, {goal}, {domain}).")

            for target in sorted(arg.attacks):
                facts.append(f"attacks({arg_name}, {target}).")

        return "\n".join(facts)

    def _sanitize_identifier(self, identifier: str) -> str:
        """Sanitize identifier to be safe for ASP parsing"""
        if not identifier:
            return "empty"
        
        # Remove or replace problematic characters
        sanitized = identifier
        
        # Replace spaces and special characters with underscores
        sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in sanitized)
        
        # Ensure it starts with a letter or underscore
        if sanitized and not (sanitized[0].isalpha() or sanitized[0] == '_'):
            sanitized = 'id_' + sanitized
        
        # Ensure it's not empty after sanitization
        if not sanitized:
            sanitized = 'empty_id'
        
        # Limit length to prevent issues
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        
        return sanitized

    def add_team(self, team_name: str):
        """Add a new team"""
        self.teams.add(team_name)
        self.ctl.add("base", [], f"team({team_name}).")

    def add_domain(self, domain_name: str, description: str, salience: int):
        """Add a domain with description and salience"""
        domain = Domain(name=domain_name, description=description, salience=salience)
        self.domains[domain_name] = domain
        
        self.ctl.add("base", [], f"domain_element({domain_name}).")
        self.ctl.add("base", [], f"sd_value({domain_name}, {salience}).")

    def add_goal(self, goal_name: str, description: str, pg_values: Optional[Dict[str, int]] = None):
        """Add a goal with description and optional PG values"""
        goal = Goal(name=goal_name, description=description, pg_values=pg_values or {})
        self.goals[goal_name] = goal
        
        self.ctl.add("base", [], f"goal_primitive({goal_name}).")
        
        # Add PG values if provided
        if pg_values:
            for domain_name, value in pg_values.items():
                self.ctl.add("base", [], f"pg_value({goal_name}, {domain_name}, {value}).")

    def update_goal_pg_value(self, goal_name: str, domain_name: str, value: int):
        """Update or add a PG value for a goal in a specific domain"""
        if goal_name not in self.goals:
            raise ValueError(f"Goal {goal_name} not found")
        if domain_name not in self.domains:
            raise ValueError(f"Domain {domain_name} not found")
            
        self.goals[goal_name].add_pg_value(domain_name, value)
        self.ctl.add("base", [], f"pg_value({goal_name}, {domain_name}, {value}).")

    def get_domain(self, domain_name: str) -> Optional[Domain]:
        """Get domain object by name"""
        return self.domains.get(domain_name)

    def get_goal(self, goal_name: str) -> Optional[Goal]:
        """Get goal object by name"""
        return self.goals.get(goal_name)

    def list_domains(self) -> List[Domain]:
        """Get all domains as a list"""
        return list(self.domains.values())

    def list_goals(self) -> List[Goal]:
        """Get all goals as a list"""
        return list(self.goals.values())
    
    def list_team_names(self) -> List[str]:
        return list(self.teams)

    def add_argument(
        self,
        argument_name: str,
        team_of: str,
        domains: List[str],
        goals: Dict[str, List[str]],
        attacks: Optional[List[str]] = None,
        text: str = ""
    ):
        """Add an argument"""
        if team_of not in self.teams:
            self.add_team(team_of)

        # Validate domains exist
        for domain_name in domains:
            if domain_name not in self.domains:
                raise ValueError(f"Domain {domain_name} not found. Add it first using add_domain().")

        # Validate goals exist
        for goal_name in goals.keys():
            if goal_name not in self.goals:
                raise ValueError(f"Goal {goal_name} not found. Add it first using add_goal().")

        arg = Argument(
            name=argument_name,
            text=text,
            team=team_of,
            domains=set(domains),
            goals={g: set(ds) for g, ds in goals.items()},
            attacks=set(attacks) if attacks else set(),
        )
        self.arguments[argument_name] = arg

        # Add facts
        self.ctl.add("base", [], f"argument({argument_name}).")
        self.ctl.add("base", [], f"team_of({argument_name}, {team_of}).")

        for domain in domains:
            self.ctl.add("base", [], f"prior_domain({argument_name}, {domain}).")

        for goal, claim_domains in goals.items():
            for domain in claim_domains:
                self.ctl.add(
                    "base",
                    [],
                    f"goal_coverage_claim({argument_name}, {goal}, {domain}).",
                )

        if attacks:
            for target in attacks:
                self.ctl.add("base", [], f"attacks({argument_name}, {target}).")

    def add_attack(self, attacker_name: str, target_name: str):
        """Add attack relation"""
        if attacker_name in self.arguments:
            self.arguments[attacker_name].attacks.add(target_name)
        self.ctl.add("base", [], f"attacks({attacker_name}, {target_name}).")

    def solve(self) -> Dict:
        """Solve and return results"""
        self.ctl.ground([("base", [])])

        results = {
            "scope": defaultdict(list),
            "ugn": [],
            "aps": {},
            "arg_strengths": defaultdict(dict),
            "defeats": [],
            # Team Goal Strength per (goal, domain)
            "tgs": defaultdict(dict),
            # Effective APC per (argument, goal, domain)
            "eapc": defaultdict(dict),
        }

        with self.ctl.solve(yield_=True) as handle:
            for model in handle:
                for atom in model.symbols(atoms=True):
                    if atom.name == "scope" and len(atom.arguments) == 2:
                        arg = str(atom.arguments[0])
                        domain = str(atom.arguments[1])
                        results["scope"][arg].append(domain)

                    elif atom.name == "ugn" and len(atom.arguments) == 4:
                        goal_name = str(atom.arguments[1])
                        domain_name = str(atom.arguments[2])
                        
                        # Look up the actual objects
                        goal_obj = self.goals.get(goal_name)
                        domain_obj = self.domains.get(domain_name)
                        
                        # Only create UGNEntry if both objects exist
                        if goal_obj and domain_obj:
                            results["ugn"].append(
                                UGNEntry(
                                    str(atom.arguments[0]),  # team
                                    goal_obj,                # goal object
                                    domain_obj,              # domain object
                                    atom.arguments[3].number, # value
                                )
                            )

                    elif atom.name == "total_aps" and len(atom.arguments) == 2:
                        results["aps"][str(atom.arguments[0])] = atom.arguments[
                            1
                        ].number

                    elif atom.name == "arg_strength" and len(atom.arguments) == 3:
                        arg = str(atom.arguments[0])
                        domain = str(atom.arguments[1])
                        results["arg_strengths"][arg][domain] = atom.arguments[2].number

                    elif atom.name == "defeat" and len(atom.arguments) == 3:
                        results["defeats"].append(
                            (
                                str(atom.arguments[0]),
                                str(atom.arguments[1]),
                                str(atom.arguments[2]),
                            )
                        )
                    elif atom.name == "tgs" and len(atom.arguments) == 4:
                        team_name = str(atom.arguments[0])
                        goal_name = str(atom.arguments[1])
                        domain_name = str(atom.arguments[2])
                        value = atom.arguments[3].number
                        results["tgs"][team_name][(goal_name, domain_name)] = value
                    elif atom.name == "eapc" and len(atom.arguments) == 4:
                        arg_name = str(atom.arguments[0])
                        goal_name = str(atom.arguments[1])
                        domain_name = str(atom.arguments[2])
                        value = atom.arguments[3].number
                        results["eapc"][arg_name][(goal_name, domain_name)] = value
                break

        return results

    def get_ugn_for_team(self, team_name: str) -> List[UGNEntry]:
        """Get sorted UGN for team"""
        results = self.solve()
        team_ugns = [u for u in results["ugn"] if u.team == team_name]
        return sorted(team_ugns, key=lambda x: x.value, reverse=True)

    def evaluate_new_argument(self, candidate: CandidateArgument) -> Dict:
        """Legacy method - use evaluate_candidate_argument instead"""
        temp_id = f"temp_{candidate.name}"
        self.set_candidate_argument(temp_id, candidate)
        result = self.evaluate_candidate_argument(temp_id)
        self.remove_candidate_argument(temp_id)
        return result

    def evaluate_candidate_argument(self, candidate_id: str) -> Dict:
        """
        Evaluate a candidate argument without affecting the main framework.
        
        Creates a temporary framework including the candidate and returns evaluation.
        """
        if candidate_id not in self.candidate_arguments:
            raise ValueError(f"Candidate {candidate_id} not found")

        candidate = self.candidate_arguments[candidate_id]
        
        # Create temporary control with all facts plus candidate
        temp_ctl = Control(arguments=[], logger=None, message_limit=0)
        temp_ctl.add("base", [], self.RULES)

        # Add all current facts
        current_facts = self._generate_all_facts()
        if current_facts:
            try:
                temp_ctl.add("base", [], current_facts)
            except RuntimeError as e:
                if "parsing failed" in str(e):
                    print(f"Warning: Failed to add current facts to temporary control. Skipping evaluation.")
                    return {"estimated_aps": 0, "defeats": []}
                else:
                    raise

        # Add candidate facts
        candidate_facts = self._generate_candidate_facts(candidate)
        temp_ctl.add("base", [], candidate_facts)

        # Ground and solve
        temp_ctl.ground([("base", [])])

        evaluation = {"estimated_aps": 0, "defeats": []}

        with temp_ctl.solve(yield_=True) as handle:
            for model in handle:
                for atom in model.symbols(atoms=True):
                    if atom.name == "total_aps" and len(atom.arguments) == 2:
                        if str(atom.arguments[0]) == candidate.name:
                            evaluation["estimated_aps"] = atom.arguments[1].number

                    elif atom.name == "defeat" and len(atom.arguments) == 3:
                        if str(atom.arguments[0]) == candidate.name:
                            evaluation["defeats"].append(
                                (str(atom.arguments[1]), str(atom.arguments[2]))
                            )
                break

        return evaluation

    def _generate_candidate_facts(self, candidate: CandidateArgument) -> str:
        """Generate facts for a candidate argument with sanitized identifiers"""
        facts = []
        
        facts.append(f"argument({candidate.name}).")
        facts.append(f"team_of({candidate.name}, {candidate.team}).")

        for domain in sorted(candidate.domains):
            facts.append(f"prior_domain({candidate.name}, {domain}).")

        for goal, domains in sorted(candidate.goals.items()):
            for domain in sorted(domains):
                facts.append(f"goal_coverage_claim({candidate.name}, {goal}, {domain}).")

        for target in sorted(candidate.attacks):
            facts.append(f"attacks({candidate.name}, {target}).")

        return "\n".join(facts)

    def apply_candidate_argument(self) -> bool:
        """
        Apply a candidate argument to the main framework.
        
        Converts candidate to committed argument and removes from candidates.
        """

        candidate = self.candidate_arguments[self.current_candidate_id]

        # Ensure the argument name is ASP-safe
        candidate.name = self._sanitize_identifier(candidate.name)
        
        if candidate.name in self.arguments:
            # Use a simple counter-based approach that's ASP-safe
            counter = 1
            original_name = candidate.name
            while candidate.name in self.arguments:
                candidate.name = f"{original_name}_{counter}"
                counter += 1

        committed_arg = Argument(
            name=candidate.name,
            text=candidate.text,
            team=candidate.team,
            domains=candidate.domains,
            goals={g: set(ds) for g, ds in candidate.goals.items()},
            attacks=candidate.attacks
        )

        self.arguments[candidate.name] = committed_arg

        self._reset_control()

        del self.candidate_arguments[self.current_candidate_id]
        self.current_candidate_id = None

        # Record a lightweight snapshot for external services
        try:
            if hasattr(self, "_on_argument_committed") and callable(self._on_argument_committed):
                self._on_argument_committed({
                    "argument_name": committed_arg.name,
                    "team": committed_arg.team,
                    "domains": sorted(list(committed_arg.domains)),
                    "goals": {k: sorted(list(v)) for k, v in committed_arg.goals.items()},
                    "attacks": sorted(list(committed_arg.attacks)),
                    "text": committed_arg.text,
                })
        except Exception as e:
            import traceback
            print(f"⚠️  WARNING: Failed to execute _on_argument_committed hook for argument {committed_arg.name}")
            print(f"   Error: {e}")
            print(f"   This means the argument was committed to GoDsAF but may not be logged in results.")
            traceback.print_exc()

        return True

    def _add_argument_facts(self, arg: Argument):
        """Add facts for a committed argument to the control"""
        facts = []
        
        facts.append(f"argument({arg.name}).")
        facts.append(f"team_of({arg.name}, {arg.team}).")

        for domain in sorted(arg.domains):
            facts.append(f"prior_domain({arg.name}, {domain}).")

        for goal, domains in sorted(arg.goals.items()):
            for domain in sorted(domains):
                facts.append(f"goal_coverage_claim({arg.name}, {goal}, {domain}).")

        for target in sorted(arg.attacks):
            facts.append(f"attacks({arg.name}, {target}).")

        if facts:
            self._add_facts_with_retry("\n".join(facts))

    def get_argument_names(self):
        return self.arguments.keys()
    
    def get_arguments_by_team(self, team: str) -> List[Argument]:
        """Get all arguments for a specific team"""
        team_arguments = []
        for _, argument in self.arguments.items():
            if argument.team == team:
                team_arguments.append(argument)
        return team_arguments
    
    def get_argument_test_by_team(self, team: str, domains: List[str], goals: List[str]) -> List[str]:
        """Get all arguments for a specific team"""
        team_arguments = []
        for _, argument in self.arguments.items():
            if (
                argument.team == team
                and any(domain in argument.domains for domain in domains)
                and any(goal in argument.goals for goal in goals)
            ):
                team_arguments.append(argument.text)
        return team_arguments
    
    def set_candidate_argument(self, candidate_id: str, candidate: CandidateArgument):
        """Store or update a candidate argument"""
        self.current_candidate_id = candidate_id
        self.candidate_arguments[candidate_id] = candidate

    def get_current_candidate_argument(self) -> Optional[CandidateArgument]:
        """Retrieve a current candidate argument"""
        return self.candidate_arguments.get(self.current_candidate_id)

    def remove_candidate_argument(self, candidate_id: str) -> bool:
        """Remove a candidate argument"""
        if candidate_id in self.candidate_arguments:
            del self.candidate_arguments[candidate_id]
            return True
        return False
    
    def list_candidate_arguments(self) -> List[str]:
        """List all candidate argument IDs"""
        return list(self.candidate_arguments.keys())

    def print_debate_state(self):
        """Print current state with enhanced domain and goal information"""
        results = self.solve()

        print("\n=== DEBATE STATE ===")
        print(f"Teams: {', '.join(sorted(self.teams))}")
        
        print("\n=== DOMAINS ===")
        for domain in sorted(self.domains.values(), key=lambda d: d.name):
            print(f"  {domain.name}: {domain.description} (salience: {domain.salience})")
        
        print("\n=== GOALS ===")
        for goal in sorted(self.goals.values(), key=lambda g: g.name):
            print(f"  {goal.name}: {goal.description}")
            if goal.pg_values:
                for domain_name, pg_value in sorted(goal.pg_values.items()):
                    domain_desc = self.domains[domain_name].description if domain_name in self.domains else domain_name
                    print(f"    -> {domain_name} ({domain_desc}): PG = {pg_value}")

        print("\n=== ARGUMENTS ===")
        for arg_name, arg in sorted(self.arguments.items()):
            print(f"\n{arg_name} (Team {arg.team}):")
            if arg.text:
                print(f"  Text: {arg.text}")
            
            domain_descs = []
            for domain_name in sorted(arg.domains):
                if domain_name in self.domains:
                    domain_descs.append(f"{domain_name} ({self.domains[domain_name].description})")
                else:
                    domain_descs.append(domain_name)
            print(f"  Domains: {', '.join(domain_descs)}")
            print(f"  Scope: {', '.join(results['scope'].get(arg_name, []))}")
            print(f"  APS: {results['aps'].get(arg_name, 0)}")
            if arg.attacks:
                print(f"  Attacks: {', '.join(sorted(arg.attacks))}")

        if self.candidate_arguments:
            print("\n=== CANDIDATE ARGUMENTS ===")
            for cid, candidate in sorted(self.candidate_arguments.items()):
                print(f"\n[{cid}] {candidate.name} (Team {candidate.team}):")
                if candidate.text:
                    print(f"  Text: {candidate.text}")
                
                domain_descs = []
                for domain_name in sorted(candidate.domains):
                    if domain_name in self.domains:
                        domain_descs.append(f"{domain_name} ({self.domains[domain_name].description})")
                    else:
                        domain_descs.append(domain_name)
                print(f"  Domains: {', '.join(domain_descs)}")
                if candidate.attacks:
                    print(f"  Proposed Attacks: {', '.join(sorted(candidate.attacks))}")

        print("\n=== DEFEATS ===")
        for attacker, target, domain in results["defeats"]:
            domain_desc = self.domains[domain].description if domain in self.domains else domain
            print(f"{attacker} defeats {target} in {domain} ({domain_desc})")

        print("\n=== UNMET GOAL NEEDS ===")
        for team in sorted(self.teams):
            print(f"\nTeam {team}:")
            ugns = self.get_ugn_for_team(team)
            for ugn in ugns[:5]:
                print(f"  {ugn.goal.name} ({ugn.goal.description}) in {ugn.domain.name} ({ugn.domain.description}): {ugn.value}")


if __name__ == "__main__":
    af = GoDsAFService()

    # Add teams
    af.add_team("tl")
    af.add_team("tws")

    # Add domains with descriptions
    af.add_domain("d_culture", "Organizational Culture", 25)
    af.add_domain("d_ops", "Operations", 80)

    # Add goals with descriptions and PG values
    af.add_goal("g_innovation", "Innovation and Creativity", {
        "d_culture": 10, 
        "d_ops": 30
    })
    af.add_goal("g_retention", "Employee Retention", {
        "d_culture": 15, 
        "d_ops": 55
    })

    # Add arguments
    af.add_argument(
        "a_regulate_ai",
        "tl",
        ["d_culture", "d_ops"],
        {"g_innovation": ["d_ops"], "g_retention": ["d_ops"]},
        [],
        "AI regulation will improve operations and retention"
    )
    af.add_argument(
        "a_regulate_ai_2",
        "tl",
        ["d_culture", "d_ops"],
        {"g_innovation": ["d_culture"], "g_retention": ["d_culture"]},
        [],
        "AI regulation will enhance cultural innovation and retention"
    )

    af.print_debate_state()

    # Demonstrate new functionality
    print("\n=== DOMAIN AND GOAL LOOKUP ===")
    culture_domain = af.get_domain("d_culture")
    if culture_domain:
        print(f"Culture Domain: {culture_domain}")
    
    innovation_goal = af.get_goal("g_innovation")
    if innovation_goal:
        print(f"Innovation Goal: {innovation_goal}")
        print(f"PG value for culture: {innovation_goal.get_pg_value('d_culture')}")

    # Update a goal's PG value
    print("\n=== UPDATING PG VALUE ===")
    af.update_goal_pg_value("g_innovation", "d_culture", 20)
    print(f"Updated PG value for innovation in culture: {innovation_goal.get_pg_value('d_culture')}")
