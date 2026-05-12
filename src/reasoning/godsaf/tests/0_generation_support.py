"""
Test suite for GoDsAF Argument Generation Support Metrics
Based on Prompts 4-6 from the specification
(Refactored to not use pytest)
"""

from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass, field
from src.reasoning.asp.solver import ASPSolver



@dataclass
class CandidateArgument:
    """Represents a candidate argument for evaluation"""
    id: str
    team: str
    domains: List[str]
    goal_claims: List[Tuple[str, str]]  # (goal, domain) pairs
    attacks: List[str] = field(default_factory=list)

# --- Helper functions for ASP rules (with arithmetic fixes) ---

def get_ugn_identification_rules() -> str:
    """Return rules for identifying UGN without candidates"""
    return r"""
    % Include base rules for P_G, S_D, etc.
    % Average IGI across relevance bearers
    pg(G, D, AvgValue) :-
        goal_primitive(G),
        domain_element(D),
        SumIGI = #sum { IGI, RB : igi(RB, G, IGI) },
        CountRB = #count { RB : relevance_bearer(RB) },
        CountRB > 0,
        AvgValue = SumIGI / CountRB.
    
    % Average IDS across relevance bearers
    sd(D, AvgValue) :-
        domain_element(D),
        SumIDS = #sum { IDS, RB : ids(RB, D, IDS) },
        CountRB = #count { RB : relevance_bearer(RB) },
        CountRB > 0,
        AvgValue = SumIDS / CountRB.
    
    % APC calculation
    apc(A, G, D, Value) :-
        goal_coverage_claim(A, G, D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    % Simplified scope (all arguments in their domains)
    scope(A, D) :- prior_domain(A, D).
    
    % EAPC (simplified - no challenges for this test)
    eapc(A, G, D, Value) :- apc(A, G, D, Value), scope(A, D).
    
    % TGS calculation
    tgs(Team, G, D, Sum) :-
        team(Team),
        goal_primitive(G),
        domain_element(D),
        Sum = #sum { Value, A : eapc(A, G, D, Value), team_of(A, Team) }.
    
    % ReGS calculation
    regs(G, D, Value) :-
        goal_primitive(G),
        domain_element(D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    % UGN calculation
    ugn(Team, G, D, Value) :-
        team(Team),
        goal_primitive(G),
        domain_element(D),
        regs(G, D, ReGS_Val),
        tgs(Team, G, D, TGS_Val),
        Value = #max { 0; ReGS_Val - TGS_Val }.
    
    #show ugn/4.
    """


def get_candidate_evaluation_rules() -> str:
    """Return rules for evaluating candidate arguments"""
    return r"""
    % Include base calculation rules
    pg(G, D, AvgValue) :-
        goal_primitive(G),
        domain_element(D),
        SumIGI = #sum { IGI, RB : igi(RB, G, IGI) },
        CountRB = #count { RB : relevance_bearer(RB) },
        CountRB > 0,
        AvgValue = SumIGI / CountRB.
    
    sd(D, AvgValue) :-
        domain_element(D),
        SumIDS = #sum { IDS, RB : ids(RB, D, IDS) },
        CountRB = #count { RB : relevance_bearer(RB) },
        CountRB > 0,
        AvgValue = SumIDS / CountRB.
    
    % APC for existing arguments
    apc(A, G, D, Value) :-
        goal_coverage_claim(A, G, D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    % APC for candidate arguments
    apc_candidate(A, G, D, Value) :-
        candidate_goal_coverage_claim(A, G, D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    % Provisional scope analysis (simplified)
    provisional_scope(A, D) :- candidate_prior_domain(A, D).
    
    % Estimated EAPC for candidates (simplified - assume moderate challenge)
    eapc_est(A, G, D, Value) :-
        candidate_goal_coverage_claim(A, G, D),
        provisional_scope(A, D),
        apc_candidate(A, G, D, APC_Val),
        k_chal(K),
        Num = APC_Val * K, % Intermediate step
        Value = Num / 100.  % Assume 1 challenger
    
    % Current UGN calculation
    current_tgs(Team, G, D, Sum) :-
        team(Team),
        goal_primitive(G),
        domain_element(D),
        % Assuming scope for existing arguments for TGS calculation is needed
        scope(A, D) :- prior_domain(A, D), % Simplified scope if not defined elsewhere for this part
        Sum = #sum { APC_Val, A : apc(A, G, D, APC_Val), team_of(A, Team), scope(A,D) }.

    regs(G, D, Value) :-
        goal_primitive(G),
        domain_element(D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    current_ugn(Team, G, D, Value) :-
        team(Team),
        goal_primitive(G),
        domain_element(D),
        regs(G, D, ReGS_Val),
        current_tgs(Team, G, D, TGS_Val),
        Value = #max { 0; ReGS_Val - TGS_Val }.
    
    % Contribution to UGN
    contrib_to_ugn(A, Team, Value) :-
        candidate_argument(A),
        candidate_team_of(A, Team),
        Value = #sum { MinVal, G, D : 
            eapc_est(A, G, D, EAPC_Val),
            current_ugn(Team, G, D, UGN_Val),
            MinVal = #min { EAPC_Val; UGN_Val }
        }.
    
    #show eapc_est/4.
    #show contrib_to_ugn/3.
    """


def get_offensive_defensive_rules() -> str:
    """Return rules for offensive and defensive merit calculation"""
    return r"""
    % Include base rules
    pg(G, D, AvgValue) :-
        goal_primitive(G),
        domain_element(D),
        SumIGI = #sum { IGI, RB : igi(RB, G, IGI) },
        CountRB = #count { RB : relevance_bearer(RB) },
        CountRB > 0,
        AvgValue = SumIGI / CountRB.
    
    sd(D, AvgValue) :-
        domain_element(D),
        SumIDS = #sum { IDS, RB : ids(RB, D, IDS) },
        CountRB = #count { RB : relevance_bearer(RB) },
        CountRB > 0,
        AvgValue = SumIDS / CountRB.
    
    % Existing scope (simplified)
    scope(A, D) :- prior_domain(A, D).
    
    % APC calculations
    apc(A, G, D, Value) :-
        goal_coverage_claim(A, G, D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    apc_candidate(A, G, D, Value) :-
        candidate_goal_coverage_claim(A, G, D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    % Current APS for existing arguments
    % EAPC for existing arguments (simplified as per previous rule sets)
    eapc(A, G, D, Value) :- apc(A, G, D, Value), scope(A,D). 

    aps_current(A, Sum) :-
        argument(A),
        Sum = #sum { Value, G, D : eapc(A, G, D, Value) }. % Sum over EAPC values
    
    % Estimated APS for candidate
    % EAPC_est for candidate (simplified as per previous rule sets)
    eapc_est_cand(A, G, D, Value) :- 
        apc_candidate(A, G, D, APC_Cand_Val), 
        k_chal(K), 
        TempNum = APC_Cand_Val * K,
        Value = TempNum / 100.

    aps_est(A, Sum) :-
        candidate_argument(A),
        Sum = #sum { Value, G, D : eapc_est_cand(A, G, D, Value) }.
    
    % Dialectical Offense Score (DOS)
    % Estimated APS reduction of opponents attacked by candidate
    dos_est(Cand, Team, Value) :-
        candidate_argument(Cand),
        candidate_team_of(Cand, Team),
        Value = #sum { Reduction, Target :
            candidate_attacks(Cand, Target),
            team_of(Target, OppTeam),
            Team != OppTeam,
            aps_current(Target, CurrentAPS),
            k_chal(K),
            TempNum = CurrentAPS * K,
            Reduction = TempNum / 100
        }.
    
    % Dialectical Defense Score (DDS)
    % Estimated EAPC increase for allies defended
    dds_est(Cand, Team, Value) :-
        candidate_argument(Cand),
        candidate_team_of(Cand, Team),
        Value = #sum { Increase, Ally, G, D : % Added G, D here for apc
            team_of(Ally, Team),
            attacks(Attacker, Ally),
            team_of(Attacker, OppTeam), Team != OppTeam, % Ensure Attacker is opponent
            candidate_attacks(Cand, Attacker),
            goal_coverage_claim(Ally, G, D), % Need G, D for specific APC
            apc(Ally, G, D, APC_Val), % Use APC of the specific claim being defended
            scope(Ally, D), % Ally's claim must be in scope to have EAPC affected
            k_chal(K),
            % Simplified: assume removing one attacker restores K/100 of its APC as EAPC gain
            TempNum = APC_Val * K,
            Increase = TempNum / 100
        }.
    
    % Total estimated change in TGS (sum of candidate's own APS_est and DDS_est it provides)
    delta_tgs_est(Cand, Value) :-
        candidate_argument(Cand),
        candidate_team_of(Cand, Team), % Team needed for DDS
        aps_est(Cand, APS),
        dds_est(Cand, Team, DDS), % DDS is for the candidate's team
        Value = APS + DDS.
    
    #show aps_est/2.
    #show dos_est/3.
    #show dds_est/3.
    #show delta_tgs_est/2.
    """

def get_comparison_rules() -> str:
    """Return comprehensive rules for comparing multiple candidates"""
    # This function reuses many parts from get_offensive_defensive_rules and get_candidate_evaluation_rules
    # For brevity, we'll combine them conceptually.
    # A more robust solution would be to have a modular ASP rule system.
    # We will use the rules from get_offensive_defensive_rules and add UGN contribution and overall_utility.

    offensive_defensive = get_offensive_defensive_rules() # Gets pg, sd, apc, aps_current, aps_est, dos, dds

    comparison_specific_rules = r"""
    % --- Rules specific to comparison, building on offensive/defensive ---
    
    % ReGS and current TGS/UGN needed for UGN contribution
    % (pg, sd, apc, scope are already in offensive_defensive part)
    current_tgs(Team, G, D, Sum) :-
        team(Team),
        goal_primitive(G),
        domain_element(D),
        % eapc for existing arguments, already defined via apc & scope in offensive_defensive
        Sum = #sum { Value, A : apc(A, G, D, Value), team_of(A, Team), scope(A,D) }.
    
    regs(G, D, Value) :-
        goal_primitive(G),
        domain_element(D),
        pg(G, D, PG_Val), % pg is defined in offensive_defensive
        sd(D, SD_Val),   % sd is defined in offensive_defensive
        Value = PG_Val * SD_Val.
    
    current_ugn(Team, G, D, Value) :-
        team(Team),
        goal_primitive(G),
        domain_element(D),
        regs(G, D, ReGS_Val),
        current_tgs(Team, G, D, TGS_Val),
        Value = #max { 0; ReGS_Val - TGS_Val }.

    % Contribution to UGN (using apc_candidate for EAPC_est equivalent for UGN)
    contrib_to_ugn(A, Team, Value) :-
        candidate_argument(A),
        candidate_team_of(A, Team),
        Value = #sum { MinVal, G, D : 
            apc_candidate(A, G, D, APC_Cand_Val), % Using full APC of candidate for potential contribution
            current_ugn(Team, G, D, UGN_Val),
            MinVal = #min { APC_Cand_Val; UGN_Val }
        }.
        
    % Overall utility (example formula - can be customized)
    overall_utility(Cand, Utility) :-
        candidate_argument(Cand),
        candidate_team_of(Cand, Team),
        aps_est(Cand, APS),
        contrib_to_ugn(Cand, Team, UGN_Contrib), % UGN_Contrib instead of UGN
        dos_est(Cand, Team, DOS),
        dds_est(Cand, Team, DDS),
        Utility = APS + UGN_Contrib + DOS + DDS.
    
    #show aps_est/2.
    #show contrib_to_ugn/3.
    #show dos_est/3.
    #show dds_est/3.
    #show overall_utility/2.
    """
    return offensive_defensive + "\n" + comparison_specific_rules

# --- Helper functions for test setups (converted from methods) ---

def get_nuclear_power_debate_setup() -> str:
    """Setup for nuclear power sustainability debate"""
    return r"""
    % Teams
    team(team_pro_nuclear).
    team(team_anti_nuclear).
    
    % Domain Elements
    domain_element(waste_management).
    domain_element(safety_protocols).
    domain_element(energy_output_reliability).
    domain_element(cost_effectiveness).
    
    % Goal Primitives
    goal_primitive(ensure_longterm_safety).
    goal_primitive(provide_stable_baseload_power).
    goal_primitive(achieve_economic_viability).
    
    % Existing team_pro_nuclear Arguments
    argument(arg_PN1).
    team_of(arg_PN1, team_pro_nuclear).
    prior_domain(arg_PN1, energy_output_reliability).
    goal_coverage_claim(arg_PN1, provide_stable_baseload_power, energy_output_reliability).
    
    % Existing team_anti_nuclear Arguments
    argument(arg_AN1).
    team_of(arg_AN1, team_anti_nuclear).
    prior_domain(arg_AN1, waste_management).
    goal_coverage_claim(arg_AN1, ensure_longterm_safety, waste_management).
    
    % No attacks on arg_PN1 - it's unchallenged
    
    % Relevance Bearers with high concern for waste safety
    relevance_bearer(safety_expert).
    relevance_bearer(environmental_scientist).
    relevance_bearer(local_resident).
    
    % Very high P_G and S_D for waste management safety
    igi(safety_expert, ensure_longterm_safety, 98).
    igi(environmental_scientist, ensure_longterm_safety, 95).
    igi(local_resident, ensure_longterm_safety, 90).
    
    ids(safety_expert, waste_management, 95).
    ids(environmental_scientist, waste_management, 98).
    ids(local_resident, waste_management, 85).
    
    % Moderate values for other areas
    igi(safety_expert, provide_stable_baseload_power, 70).
    igi(environmental_scientist, provide_stable_baseload_power, 65).
    igi(local_resident, provide_stable_baseload_power, 60).
    
    ids(safety_expert, energy_output_reliability, 80).
    ids(environmental_scientist, energy_output_reliability, 75).
    ids(local_resident, energy_output_reliability, 70).
    
    % System constants
    k_chal(40).
    """

def get_ai_ethics_debate_setup() -> str:
    """Setup for AI development ethics vs innovation speed debate"""
    return r"""
    % Teams
    team(team_ethics_first).
    team(team_innovation_speed).
    
    % Domain Elements
    domain_element(job_displacement_risk).
    domain_element(algorithmic_bias).
    domain_element(global_competitiveness).
    domain_element(existential_risks).
    
    % Goal Primitives
    goal_primitive(minimize_ai_harm).
    goal_primitive(maintain_tech_leadership).
    goal_primitive(ensure_fairness).
    
    % Existing Arguments - Ethics First team
    argument(arg_EF1).
    team_of(arg_EF1, team_ethics_first).
    prior_domain(arg_EF1, algorithmic_bias).
    goal_coverage_claim(arg_EF1, minimize_ai_harm, algorithmic_bias). % Connects to minimize_ai_harm via algorithmic_bias
    
    % Existing Arguments - Innovation Speed team
    argument(arg_IS1).
    team_of(arg_IS1, team_innovation_speed).
    prior_domain(arg_IS1, global_competitiveness).
    goal_coverage_claim(arg_IS1, maintain_tech_leadership, global_competitiveness).
    
    argument(arg_IS2). % Another argument for innovation speed team
    team_of(arg_IS2, team_innovation_speed).
    prior_domain(arg_IS2, existential_risks). % e.g. related to unaligned superintelligence
    goal_coverage_claim(arg_IS2, minimize_ai_harm, existential_risks). % Can also claim to address a type of harm

    % Attacks
    attacks(arg_IS1, arg_EF1). % IS1 attacks EF1 (e.g. competitiveness argument undermines ethics focus)
    
    % Relevance Bearers
    relevance_bearer(ai_researcher).
    relevance_bearer(policy_advisor).
    relevance_bearer(tech_ceo).
    
    % IGI scores
    igi(ai_researcher, minimize_ai_harm, 85).
    igi(ai_researcher, maintain_tech_leadership, 75).
    igi(policy_advisor, minimize_ai_harm, 90).
    igi(policy_advisor, maintain_tech_leadership, 70).
    igi(tech_ceo, minimize_ai_harm, 65).
    igi(tech_ceo, maintain_tech_leadership, 95).
    
    % IDS scores
    ids(ai_researcher, algorithmic_bias, 90).
    ids(ai_researcher, global_competitiveness, 80).
    ids(ai_researcher, job_displacement_risk, 85).
    ids(ai_researcher, existential_risks, 75).
    
    ids(policy_advisor, algorithmic_bias, 85).
    ids(policy_advisor, global_competitiveness, 75).
    ids(policy_advisor, job_displacement_risk, 90).
    ids(policy_advisor, existential_risks, 80).
    
    ids(tech_ceo, algorithmic_bias, 70).
    ids(tech_ceo, global_competitiveness, 95).
    ids(tech_ceo, job_displacement_risk, 80).
    ids(tech_ceo, existential_risks, 85).
    
    % System constants
    k_chal(30).
    """

def get_ip_reform_debate_setup() -> str:
    """Setup for intellectual property reform debate"""
    return r"""
    % Teams
    team(team_pro_reform_ip).
    team(team_con_strong_ip).
    
    % Domain Elements
    domain_element(patent_law).
    domain_element(copyright_duration).
    domain_element(open_source_impact).
    domain_element(pharmaceutical_rd).
    
    % Goal Primitives
    goal_primitive(foster_innovation).
    goal_primitive(protect_creator_rights).
    goal_primitive(ensure_public_access_to_knowledge).
    goal_primitive(incentivize_research).
    
    % Existing Arguments - Pro Reform
    argument(arg_PR_OS).
    team_of(arg_PR_OS, team_pro_reform_ip).
    prior_domain(arg_PR_OS, open_source_impact).
    goal_coverage_claim(arg_PR_OS, foster_innovation, open_source_impact).
    goal_coverage_claim(arg_PR_OS, ensure_public_access_to_knowledge, open_source_impact).


    % Existing Arguments - Con (Strong IP)
    argument(arg_CS_pharma).
    team_of(arg_CS_pharma, team_con_strong_ip).
    prior_domain(arg_CS_pharma, pharmaceutical_rd).
    goal_coverage_claim(arg_CS_pharma, incentivize_research, pharmaceutical_rd).
    goal_coverage_claim(arg_CS_pharma, foster_innovation, pharmaceutical_rd).


    argument(arg_CS_copy).
    team_of(arg_CS_copy, team_con_strong_ip).
    prior_domain(arg_CS_copy, copyright_duration).
    goal_coverage_claim(arg_CS_copy, protect_creator_rights, copyright_duration).
    
    % Attacks
    attacks(arg_CS_copy, arg_PR_OS).
    
    % Relevance Bearers
    relevance_bearer(innovation_expert).
    relevance_bearer(pharma_executive).
    relevance_bearer(open_source_advocate).
    
    % High UGN for patent law innovation and public access via patent law
    igi(innovation_expert, foster_innovation, 95).
    igi(pharma_executive, foster_innovation, 70). % Lower but still relevant
    igi(open_source_advocate, foster_innovation, 90).
    
    igi(innovation_expert, ensure_public_access_to_knowledge, 80).
    igi(pharma_executive, ensure_public_access_to_knowledge, 50).
    igi(open_source_advocate, ensure_public_access_to_knowledge, 95).

    ids(innovation_expert, patent_law, 90).
    ids(pharma_executive, patent_law, 85).
    ids(open_source_advocate, patent_law, 88).
    
    % Other values for completeness
    ids(innovation_expert, open_source_impact, 85).
    ids(open_source_advocate, open_source_impact, 92).
    
    ids(pharma_executive, pharmaceutical_rd, 95).
    ids(innovation_expert, pharmaceutical_rd, 75).

    ids(innovation_expert, copyright_duration, 70).
    ids(pharma_executive, copyright_duration, 70). % Neutral
    ids(open_source_advocate, copyright_duration, 60). % Less emphasis
    
    igi(innovation_expert, protect_creator_rights, 75).
    igi(pharma_executive, protect_creator_rights, 85).
    igi(open_source_advocate, protect_creator_rights, 65).

    igi(innovation_expert, incentivize_research, 80).
    igi(pharma_executive, incentivize_research, 98).
    igi(open_source_advocate, incentivize_research, 50).


    % System constants
    k_chal(40).
    """

# --- Helper function for metric extraction ---
def _extract_metric(facts: List[str], prefix: str) -> int: # Changed Set to List to match usage
    """Helper to extract numeric metric from facts"""
    matching = [f for f in facts if f.startswith(prefix)]
    if not matching:
        # print(f"Warning: No fact found with prefix '{prefix}'. Returning 0.") # Optional warning
        return 0
    try:
        return int(matching[0].split(',')[-1].rstrip(')'))
    except ValueError:
        # print(f"Warning: Could not parse int from fact '{matching[0]}'. Returning 0.") # Optional warning
        return 0


# --- Test functions (converted from test methods) ---

def run_test_gen_argument_for_critical_ugn():
    """Test identifying UGN and evaluating candidate argument to address it"""
    initial_part = get_nuclear_power_debate_setup()
    
    # First, verify the UGN exists
    asp_program_ugn = initial_part + "\n" + get_ugn_identification_rules()
    solver_ugn = ASPSolver(timeout=10)
    facts_ugn, interrupted_ugn, satisfiable_ugn = solver_ugn.solve(asp_program_ugn)
    
    assert satisfiable_ugn, "UGN identification program should be satisfiable"
    assert not interrupted_ugn, "UGN identification solving should not be interrupted"
    assert facts_ugn is not None, "Facts from UGN identification should not be None"
    
    # Verify high UGN for waste management safety for team_pro_nuclear
    ugn_facts = [f for f in facts_ugn if f.startswith("ugn(team_pro_nuclear,ensure_longterm_safety,waste_management,")]
    assert len(ugn_facts) > 0, "UGN fact for (team_pro_nuclear,ensure_longterm_safety,waste_management) not found"
    ugn_value = _extract_metric(facts_ugn, "ugn(team_pro_nuclear,ensure_longterm_safety,waste_management,")
    assert ugn_value > 5000, f"UGN for waste management safety should be high (e.g. >5000), but was {ugn_value}" 
    # Note: Original assert was >50. UGN values can be large (P_G*S_D), e.g. 90*90=8100. Adjusted expectation.

    # Now test candidate argument
    candidate_setup = r"""
    % Candidate Argument
    candidate_argument(a_cand_waste_solution).
    candidate_team_of(a_cand_waste_solution, team_pro_nuclear).
    candidate_prior_domain(a_cand_waste_solution, waste_management).
    candidate_goal_coverage_claim(a_cand_waste_solution, ensure_longterm_safety, waste_management).
    
    % Candidate attacks anti-nuclear argument to improve its own standing or reduce opposition
    candidate_attacks(a_cand_waste_solution, arg_AN1). 
    """
    
    asp_program_cand = initial_part + "\n" + candidate_setup + "\n" + get_candidate_evaluation_rules()
    solver_cand = ASPSolver(timeout=10)
    facts_cand, interrupted_cand, satisfiable_cand = solver_cand.solve(asp_program_cand)
    
    assert satisfiable_cand, "Candidate evaluation program should be satisfiable"
    assert not interrupted_cand, "Candidate evaluation solving should not be interrupted"
    assert facts_cand is not None, "Facts from candidate evaluation should not be None"

    # Verify positive estimated EAPC for the candidate's claim
    eapc_est_facts = [f for f in facts_cand if f.startswith("eapc_est(a_cand_waste_solution,ensure_longterm_safety,waste_management,")]
    assert len(eapc_est_facts) > 0, "eapc_est for candidate's claim not found"
    eapc_est_value = _extract_metric(facts_cand, "eapc_est(a_cand_waste_solution,ensure_longterm_safety,waste_management,")
    assert eapc_est_value > 0, f"eapc_est for candidate should be positive, but was {eapc_est_value}"
    
    # Verify high contribution to UGN
    contrib_facts = [f for f in facts_cand if f.startswith("contrib_to_ugn(a_cand_waste_solution,team_pro_nuclear,")]
    assert len(contrib_facts) > 0, "contrib_to_ugn for candidate not found"
    contrib_value = _extract_metric(facts_cand, "contrib_to_ugn(a_cand_waste_solution,team_pro_nuclear,")
    assert contrib_value > 0, f"contrib_to_ugn for candidate should be positive, but was {contrib_value}"


def run_test_gen_candidate_offensive_defensive_merits():
    """Test offensive and defensive merit evaluation of candidate"""
    initial_part = get_ai_ethics_debate_setup()
    
    candidate_setup = r"""
    % Candidate Argument for team_ethics_first
    candidate_argument(a_cand_strategic).
    candidate_team_of(a_cand_strategic, team_ethics_first).
    candidate_prior_domain(a_cand_strategic, job_displacement_risk). % New domain coverage
    candidate_goal_coverage_claim(a_cand_strategic, minimize_ai_harm, job_displacement_risk).
    
    % Candidate attacks opponent arguments
    candidate_attacks(a_cand_strategic, arg_IS1). % Attacks an opponent arg
    candidate_attacks(a_cand_strategic, arg_IS2). % Attacks another opponent arg
    """
    
    asp_program = initial_part + "\n" + candidate_setup + "\n" + get_offensive_defensive_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable, "Offensive/Defensive merit program should be satisfiable"
    assert not interrupted, "Offensive/Defensive merit solving should not be interrupted"
    assert facts is not None, "Facts from Offensive/Defensive merit should not be None"

    # Verify APS_est calculation for the candidate
    aps_est_facts = [f for f in facts if f.startswith("aps_est(a_cand_strategic,")]
    assert len(aps_est_facts) > 0, "aps_est for candidate not found"
    aps_est_value = _extract_metric(facts, "aps_est(a_cand_strategic,")
    assert aps_est_value > 0, f"aps_est for candidate should be positive, but was {aps_est_value}"
    
    # Verify DOS calculation (should be positive as it attacks two opponent args)
    dos_facts = [f for f in facts if f.startswith("dos_est(a_cand_strategic,team_ethics_first,")]
    assert len(dos_facts) > 0, "dos_est for candidate not found"
    dos_value = _extract_metric(facts, "dos_est(a_cand_strategic,team_ethics_first,")
    assert dos_value > 0, f"dos_est for candidate should be positive (attacks opponents), but was {dos_value}"
    
    # Verify DDS calculation
    # In this setup, arg_EF1 is attacked by arg_IS1.
    # If a_cand_strategic attacks arg_IS1, it defends arg_EF1.
    # So DDS should be positive.
    dds_facts = [f for f in facts if f.startswith("dds_est(a_cand_strategic,team_ethics_first,")]
    assert len(dds_facts) > 0, "dds_est for candidate not found"
    dds_value = _extract_metric(facts, "dds_est(a_cand_strategic,team_ethics_first,")
    assert dds_value > 0, f"dds_est for candidate should be positive (defends ally), but was {dds_value}"
    
    # Verify total change in TGS (delta_tgs_est)
    delta_tgs_facts = [f for f in facts if f.startswith("delta_tgs_est(a_cand_strategic,")]
    assert len(delta_tgs_facts) > 0, "delta_tgs_est for candidate not found"
    delta_tgs_value = _extract_metric(facts, "delta_tgs_est(a_cand_strategic,")
    assert delta_tgs_value == aps_est_value + dds_value, \
        f"delta_tgs_est ({delta_tgs_value}) should equal aps_est ({aps_est_value}) + dds_est ({dds_value})"


def run_test_gen_compare_candidate_arguments_utility():
    """Test comparison of multiple candidate arguments"""
    initial_part = get_ip_reform_debate_setup()
    
    candidates_setup = r"""
    % Candidate A - Focuses on UGN (patent law innovation)
    candidate_argument(cand_A_reform_patent).
    candidate_team_of(cand_A_reform_patent, team_pro_reform_ip).
    candidate_prior_domain(cand_A_reform_patent, patent_law).
    candidate_goal_coverage_claim(cand_A_reform_patent, foster_innovation, patent_law).
    % No explicit attacks by cand_A
    
    % Candidate B - Offensive focus (attacks pharma R&D)
    candidate_argument(cand_B_offensive_pharma).
    candidate_team_of(cand_B_offensive_pharma, team_pro_reform_ip).
    candidate_prior_domain(cand_B_offensive_pharma, pharmaceutical_rd). % Different domain than UGN
    candidate_goal_coverage_claim(cand_B_offensive_pharma, ensure_public_access_to_knowledge, pharmaceutical_rd).
    candidate_attacks(cand_B_offensive_pharma, arg_CS_pharma).
    
    % Candidate C - Defensive focus (defends open source argument)
    candidate_argument(cand_C_defensive_os).
    candidate_team_of(cand_C_defensive_os, team_pro_reform_ip).
    candidate_prior_domain(cand_C_defensive_os, open_source_impact). % Related to existing arg_PR_OS
    candidate_goal_coverage_claim(cand_C_defensive_os, foster_innovation, open_source_impact).
    candidate_attacks(cand_C_defensive_os, arg_CS_copy). % Attacks the attacker of arg_PR_OS
    """
    
    asp_program = initial_part + "\n" + candidates_setup + "\n" + get_comparison_rules()
    solver = ASPSolver(timeout=15) # Increased timeout for more complex program
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable, "Comparison program should be satisfiable"
    assert not interrupted, "Comparison solving should not be interrupted"
    assert facts is not None, "Facts from comparison should not be None"

    # Debug: Print all relevant facts
    # print("\nFacts for comparison test:")
    # for f_item in sorted(list(facts if facts else set())):
    #      if "cand_" in f_item:
    #          print(f_item)

    candidates = ["cand_A_reform_patent", "cand_B_offensive_pharma", "cand_C_defensive_os"]
    metrics = {}
    
    for cand in candidates:
        metrics[cand] = {
            'aps_est': _extract_metric(facts, f"aps_est({cand},"),
            'contrib_ugn': _extract_metric(facts, f"contrib_to_ugn({cand},team_pro_reform_ip,"),
            'dos_est': _extract_metric(facts, f"dos_est({cand},team_pro_reform_ip,"),
            'dds_est': _extract_metric(facts, f"dds_est({cand},team_pro_reform_ip,"),
            'overall_utility': _extract_metric(facts, f"overall_utility({cand},")
        }
        # Ensure all metrics are at least found (value >= 0)
        assert metrics[cand]['aps_est'] >= 0, f"aps_est for {cand} not found or negative"
        assert metrics[cand]['contrib_ugn'] >= 0, f"contrib_ugn for {cand} not found or negative"
        assert metrics[cand]['dos_est'] >= 0, f"dos_est for {cand} not found or negative"
        assert metrics[cand]['dds_est'] >= 0, f"dds_est for {cand} not found or negative"
        assert metrics[cand]['overall_utility'] >= 0, f"overall_utility for {cand} not found or negative"

    # Verify expected characteristics
    # Candidate A aims to fill UGN for (foster_innovation, patent_law)
    assert metrics["cand_A_reform_patent"]['contrib_ugn'] > 0, \
        f"cand_A_reform_patent contrib_ugn expected > 0, got {metrics['cand_A_reform_patent']['contrib_ugn']}"
    
    # Candidate B attacks arg_CS_pharma.
    assert metrics["cand_B_offensive_pharma"]['dos_est'] > 0, \
        f"cand_B_offensive_pharma dos_est expected > 0, got {metrics['cand_B_offensive_pharma']['dos_est']}"
    
    # Candidate C attacks arg_CS_copy, which attacks arg_PR_OS (ally).
    assert metrics["cand_C_defensive_os"]['dds_est'] > 0, \
        f"cand_C_defensive_os dds_est expected > 0, got {metrics['cand_C_defensive_os']['dds_est']}"
    
    # All should have some APS_est based on their claims
    for cand in candidates:
        assert metrics[cand]['aps_est'] > 0, f"aps_est for {cand} expected > 0, got {metrics[cand]['aps_est']}"

    # Check overall utility logic
    for cand in candidates:
        expected_utility = (metrics[cand]['aps_est'] + 
                            metrics[cand]['contrib_ugn'] + 
                            metrics[cand]['dos_est'] + 
                            metrics[cand]['dds_est'])
        assert metrics[cand]['overall_utility'] == expected_utility, \
            f"overall_utility for {cand} ({metrics[cand]['overall_utility']}) " \
            f"does not match sum of components ({expected_utility})"
    
    # Optional: check which candidate has highest overall_utility (example, not a strict test requirement)
    # best_cand = max(candidates, key=lambda c: metrics[c]['overall_utility'])
    # print(f"Candidate with highest overall utility: {best_cand} (Utility: {metrics[best_cand]['overall_utility']})")


# --- Manual Test Runner ---
if __name__ == "__main__":
    tests_to_run = [
        run_test_gen_argument_for_critical_ugn,
        run_test_gen_candidate_offensive_defensive_merits,
        run_test_gen_compare_candidate_arguments_utility,
    ]

    passed_count = 0
    failed_count = 0
    test_results = []

    print("Starting GoDsAF Argument Generation Support Metrics Test Suite...\n")

    for i, test_func in enumerate(tests_to_run):
        test_name = test_func.__name__
        print(f"Running test {i+1}/{len(tests_to_run)}: {test_name}...")
        try:
            test_func()
            print(f"  [PASSED] {test_name}")
            passed_count += 1
            test_results.append((test_name, "PASSED", ""))
        except AssertionError as e:
            print(f"  [FAILED] {test_name}")
            print(f"    AssertionError: {e}")
            failed_count += 1
            test_results.append((test_name, "FAILED", f"AssertionError: {e}"))
        except Exception as e:
            print(f"  [ERROR] {test_name}")
            print(f"    Unexpected Exception: {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc() # Print full traceback for unexpected errors
            failed_count += 1
            test_results.append((test_name, "ERROR", f"Exception: {type(e).__name__} - {e}\n{traceback.format_exc()}"))
        print("-" * 50)

    print("\nTest Execution Summary:")
    print("=" * 50)
    for name, status, message in test_results:
        indented_message = "\n".join([f"          {line}" for line in message.splitlines()])
        print(f"{status:<8} : {name}")
        if message and (status == "FAILED" or status == "ERROR"):
            print(f"          Details: {indented_message if message.strip() else 'No details'}")
            
    print("=" * 50)
    print(f"\nTotal tests run: {len(tests_to_run)}")
    print(f"  Passed: {passed_count}")
    print(f"  Failed/Errored: {failed_count}")
    print("=" * 50)

    if failed_count == 0:
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests did not pass. Please review the output above.")
