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
    goal_claims: List[Tuple[str, str]]
    attacks: List[str] = field(default_factory=list)

# --- Helper functions for ASP rules (with arithmetic fixes) ---

def get_ugn_identification_rules() -> str:
    """Return rules for identifying UGN without candidates"""
    return r"""
    pg(G, D, AvgValue) :-
        goal_primitive(G), domain_element(D),
        SumIGI = #sum { IGI, RB : igi(RB, G, IGI) },
        CountRB = #count { RB : relevance_bearer(RB) }, CountRB > 0,
        AvgValue = SumIGI / CountRB.
    sd(D, AvgValue) :-
        domain_element(D),
        SumIDS = #sum { IDS, RB : ids(RB, D, IDS) },
        CountRB = #count { RB : relevance_bearer(RB) }, CountRB > 0,
        AvgValue = SumIDS / CountRB.
    apc(A, G, D, Value) :-
        goal_coverage_claim(A, G, D), pg(G, D, PG_Val), sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    scope(A, D) :- prior_domain(A, D).
    eapc(A, G, D, Value) :- apc(A, G, D, Value), scope(A, D).
    tgs(Team, G, D, Sum) :-
        team(Team), goal_primitive(G), domain_element(D),
        Sum = #sum { Value, A : eapc(A, G, D, Value), team_of(A, Team) }.
    regs(G, D, Value) :-
        goal_primitive(G), domain_element(D),
        pg(G, D, PG_Val), sd(D, SD_Val), Value = PG_Val * SD_Val.
    temp_ugn_diff(Team, G, D, (ReGS_Val - TGS_Val)) :-
        team(Team), goal_primitive(G), domain_element(D),
        regs(G, D, ReGS_Val), tgs(Team, G, D, TGS_Val).
    ugn(Team, G, D, Diff) :- temp_ugn_diff(Team, G, D, Diff), Diff >= 0.
    ugn(Team, G, D, 0)    :- temp_ugn_diff(Team, G, D, Diff), Diff < 0.
    #show ugn/4.
    """

def get_candidate_evaluation_rules() -> str:
    """Return rules for evaluating candidate arguments"""
    return r"""
    pg(G, D, AvgValue) :-
        goal_primitive(G), domain_element(D),
        SumIGI = #sum { IGI, RB : igi(RB, G, IGI) },
        CountRB = #count { RB : relevance_bearer(RB) }, CountRB > 0,
        AvgValue = SumIGI / CountRB.
    sd(D, AvgValue) :-
        domain_element(D),
        SumIDS = #sum { IDS, RB : ids(RB, D, IDS) },
        CountRB = #count { RB : relevance_bearer(RB) }, CountRB > 0,
        AvgValue = SumIDS / CountRB.
    apc(A, G, D, Value) :- % For existing args
        goal_coverage_claim(A, G, D), pg(G, D, PG_Val), sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    apc_candidate(A, G, D, Value) :- % For candidate args
        candidate_goal_coverage_claim(A, G, D), pg(G, D, PG_Val), sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    scope(A, D) :- prior_domain(A, D). 
    provisional_scope(A, D) :- candidate_prior_domain(A, D).
    eapc_est(A, G, D, Value) :-
        candidate_goal_coverage_claim(A, G, D), provisional_scope(A, D),
        apc_candidate(A, G, D, APC_Val), k_chal(K),
        Num = APC_Val * K, Value = Num / 100.
    current_tgs(Team, G, D, Sum) :-
        team(Team), goal_primitive(G), domain_element(D),
        Sum = #sum { APC_Val_Sum, Arg : apc(Arg, G, D, APC_Val_Sum), team_of(Arg, Team), scope(Arg,D) }.
    regs(G, D, Value) :-
        goal_primitive(G), domain_element(D),
        pg(G, D, PG_Val), sd(D, SD_Val), Value = PG_Val * SD_Val.
    temp_current_ugn_diff(Team, G, D, (ReGS_Val - TGS_Val)) :-
        team(Team), goal_primitive(G), domain_element(D),
        regs(G, D, ReGS_Val), current_tgs(Team, G, D, TGS_Val).
    current_ugn(Team, G, D, Diff) :- temp_current_ugn_diff(Team, G, D, Diff), Diff >= 0.
    current_ugn(Team, G, D, 0)    :- temp_current_ugn_diff(Team, G, D, Diff), Diff < 0.
    
    % Fixed contribution to UGN calculation
    contrib_to_ugn(A, Team, Value) :-
        candidate_argument(A), 
        candidate_team_of(A, Team),
        Value = #sum { CalculatedMinValue, G, D : 
                        eapc_est(A, G, D, EAPC_Val),
                        current_ugn(Team, G, D, UGN_Val),
                        CalculatedMinValue = min(EAPC_Val, UGN_Val) % Poprawione użycie funkcji min()
                   }.
    
    #show eapc_est/4.
    #show contrib_to_ugn/3.
    """

def get_offensive_defensive_rules() -> str:
    return r"""
    pg(G, D, AvgValue) :-
        goal_primitive(G), domain_element(D),
        SumIGI = #sum { IGI, RB : igi(RB, G, IGI) },
        CountRB = #count { RB : relevance_bearer(RB) }, CountRB > 0,
        AvgValue = SumIGI / CountRB.
    sd(D, AvgValue) :-
        domain_element(D),
        SumIDS = #sum { IDS, RB : ids(RB, D, IDS) },
        CountRB = #count { RB : relevance_bearer(RB) }, CountRB > 0,
        AvgValue = SumIDS / CountRB.
    scope(A, D) :- prior_domain(A, D).
    apc(A, G, D, Value) :-
        goal_coverage_claim(A, G, D), pg(G, D, PG_Val), sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    apc_candidate(A, G, D, Value) :-
        candidate_goal_coverage_claim(A, G, D), pg(G, D, PG_Val), sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    eapc(A, G, D, APC_Val) :- 
        apc(A, G, D, APC_Val), scope(A,D).
    aps_current(A, Sum) :-
        argument(A), Sum = #sum { Value, G, D : eapc(A, G, D, Value) }.
    eapc_est_cand(A, G, D, Value) :- 
        apc_candidate(A, G, D, APC_Cand_Val), k_chal(K), 
        TempNum = APC_Cand_Val * K, Value = TempNum / 100.
    aps_est(A, Sum) :-
        candidate_argument(A), Sum = #sum { Value, G, D : eapc_est_cand(A, G, D, Value) }.
    dos_est(Cand, Team, Value) :-
        candidate_argument(Cand), candidate_team_of(Cand, Team),
        Value = #sum { Reduction, Target :
            candidate_attacks(Cand, Target), team_of(Target, OppTeam), Team != OppTeam,
            aps_current(Target, CurrentAPS), k_chal(K),
            TempNum = CurrentAPS * K, Reduction = TempNum / 100 }.
    dds_est(Cand, Team, Value) :-
        candidate_argument(Cand), candidate_team_of(Cand, Team),
        Value = #sum { Increase, Ally, G, D : 
            team_of(Ally, Team), attacks(Attacker, Ally),
            team_of(Attacker, OppTeam), Team != OppTeam, 
            candidate_attacks(Cand, Attacker),
            goal_coverage_claim(Ally, G, D), apc(Ally, G, D, APC_Val), scope(Ally, D), 
            k_chal(K), TempNum = APC_Val * K, Increase = TempNum / 100 }.
    delta_tgs_est(Cand, Value) :-
        candidate_argument(Cand), candidate_team_of(Cand, Team), 
        aps_est(Cand, APS), dds_est(Cand, Team, DDS), Value = APS + DDS.
    #show aps_est/2. #show dos_est/3. #show dds_est/3. #show delta_tgs_est/2.
    """

def get_comparison_rules() -> str:
    offensive_defensive_rules_str = get_offensive_defensive_rules()
    comparison_specific_rules = r"""
    provisional_scope(A, D) :- candidate_prior_domain(A, D). % Dodane dla jasności, jeśli jest potrzebne
    current_tgs(Team, G, D, Sum) :- 
        team(Team), goal_primitive(G), domain_element(D),
        Sum = #sum { Value, A : eapc(A, G, D, Value), team_of(A, Team) }. 
    regs(G, D, Value) :- 
        goal_primitive(G), domain_element(D),
        pg(G, D, PG_Val), sd(D, SD_Val), Value = PG_Val * SD_Val. 
    temp_comp_ugn_diff(Team, G, D, (ReGS_Val - TGS_Val)) :-
        team(Team), goal_primitive(G), domain_element(D),
        regs(G, D, ReGS_Val), current_tgs(Team, G, D, TGS_Val).
    current_ugn(Team, G, D, Diff) :- temp_comp_ugn_diff(Team, G, D, Diff), Diff >= 0.
    current_ugn(Team, G, D, 0)    :- temp_comp_ugn_diff(Team, G, D, Diff), Diff < 0.

    % Fixed contribution to UGN calculation for comparison
    contrib_to_ugn(A, Team, Value) :-
        candidate_argument(A), 
        candidate_team_of(A, Team),
        Value = #sum { CalculatedMinValue, G, D : 
                        apc_candidate(A, G, D, APC_Cand_Val), 
                        provisional_scope(A, D), % Warunek, aby uwzględnić tylko roszczenia w scope kandydata
                        current_ugn(Team, G, D, UGN_Val),
                        CalculatedMinValue = min(APC_Cand_Val, UGN_Val) % Poprawione użycie funkcji min()
                   }.
        
    overall_utility(Cand, Utility) :-
        candidate_argument(Cand), candidate_team_of(Cand, Team),
        aps_est(Cand, APS), contrib_to_ugn(Cand, Team, UGN_Contrib), 
        dos_est(Cand, Team, DOS), dds_est(Cand, Team, DDS),
        Utility = APS + UGN_Contrib + DOS + DDS.
    #show contrib_to_ugn/3. #show overall_utility/2. 
    """
    return offensive_defensive_rules_str + "\n" + comparison_specific_rules

# --- Helper functions for test setups ---
def get_nuclear_power_debate_setup() -> str:
    return r"""% Teams
    team(team_pro_nuclear). team(team_anti_nuclear).
    % Domain Elements
    domain_element(waste_management). domain_element(safety_protocols).
    domain_element(energy_output_reliability). domain_element(cost_effectiveness).
    % Goal Primitives
    goal_primitive(ensure_longterm_safety). goal_primitive(provide_stable_baseload_power).
    goal_primitive(achieve_economic_viability).
    % Existing team_pro_nuclear Arguments
    argument(arg_PN1). team_of(arg_PN1, team_pro_nuclear).
    prior_domain(arg_PN1, energy_output_reliability).
    goal_coverage_claim(arg_PN1, provide_stable_baseload_power, energy_output_reliability).
    % Existing team_anti_nuclear Arguments
    argument(arg_AN1). team_of(arg_AN1, team_anti_nuclear).
    prior_domain(arg_AN1, waste_management).
    goal_coverage_claim(arg_AN1, ensure_longterm_safety, waste_management).
    % Relevance Bearers
    relevance_bearer(safety_expert). relevance_bearer(environmental_scientist). relevance_bearer(local_resident).
    % IGI and IDS
    igi(safety_expert, ensure_longterm_safety, 98). igi(environmental_scientist, ensure_longterm_safety, 95). igi(local_resident, ensure_longterm_safety, 90).
    ids(safety_expert, waste_management, 95). ids(environmental_scientist, waste_management, 98). ids(local_resident, waste_management, 85).
    igi(safety_expert, provide_stable_baseload_power, 70). igi(environmental_scientist, provide_stable_baseload_power, 65). igi(local_resident, provide_stable_baseload_power, 60).
    ids(safety_expert, energy_output_reliability, 80). ids(environmental_scientist, energy_output_reliability, 75). ids(local_resident, energy_output_reliability, 70).
    % System constants
    k_chal(40)."""

def get_ai_ethics_debate_setup() -> str:
    return r"""% Teams
    team(team_ethics_first). team(team_innovation_speed).
    % Domain Elements
    domain_element(job_displacement_risk). domain_element(algorithmic_bias).
    domain_element(global_competitiveness). domain_element(existential_risks).
    % Goal Primitives
    goal_primitive(minimize_ai_harm). goal_primitive(maintain_tech_leadership). goal_primitive(ensure_fairness).
    % Existing Arguments - Ethics First team
    argument(arg_EF1). team_of(arg_EF1, team_ethics_first).
    prior_domain(arg_EF1, algorithmic_bias).
    goal_coverage_claim(arg_EF1, minimize_ai_harm, algorithmic_bias).
    % Existing Arguments - Innovation Speed team
    argument(arg_IS1). team_of(arg_IS1, team_innovation_speed).
    prior_domain(arg_IS1, global_competitiveness).
    goal_coverage_claim(arg_IS1, maintain_tech_leadership, global_competitiveness).
    argument(arg_IS2). team_of(arg_IS2, team_innovation_speed).
    prior_domain(arg_IS2, existential_risks).
    goal_coverage_claim(arg_IS2, minimize_ai_harm, existential_risks).
    % Attacks
    attacks(arg_IS1, arg_EF1).
    % Relevance Bearers
    relevance_bearer(ai_researcher). relevance_bearer(policy_advisor). relevance_bearer(tech_ceo).
    % IGI scores
    igi(ai_researcher, minimize_ai_harm, 85). igi(ai_researcher, maintain_tech_leadership, 75).
    igi(policy_advisor, minimize_ai_harm, 90). igi(policy_advisor, maintain_tech_leadership, 70).
    igi(tech_ceo, minimize_ai_harm, 65). igi(tech_ceo, maintain_tech_leadership, 95).
    % IDS scores
    ids(ai_researcher, algorithmic_bias, 90). ids(ai_researcher, global_competitiveness, 80). ids(ai_researcher, job_displacement_risk, 85). ids(ai_researcher, existential_risks, 75).
    ids(policy_advisor, algorithmic_bias, 85). ids(policy_advisor, global_competitiveness, 75). ids(policy_advisor, job_displacement_risk, 90). ids(policy_advisor, existential_risks, 80).
    ids(tech_ceo, algorithmic_bias, 70). ids(tech_ceo, global_competitiveness, 95). ids(tech_ceo, job_displacement_risk, 80). ids(tech_ceo, existential_risks, 85).
    % System constants
    k_chal(30)."""

def get_ip_reform_debate_setup() -> str:
    return r"""% Teams
    team(team_pro_reform_ip). team(team_con_strong_ip).
    % Domain Elements
    domain_element(patent_law). domain_element(copyright_duration).
    domain_element(open_source_impact). domain_element(pharmaceutical_rd).
    % Goal Primitives
    goal_primitive(foster_innovation). goal_primitive(protect_creator_rights).
    goal_primitive(ensure_public_access_to_knowledge). goal_primitive(incentivize_research).
    % Existing Arguments - Pro Reform
    argument(arg_PR_OS). team_of(arg_PR_OS, team_pro_reform_ip).
    prior_domain(arg_PR_OS, open_source_impact).
    goal_coverage_claim(arg_PR_OS, foster_innovation, open_source_impact).
    goal_coverage_claim(arg_PR_OS, ensure_public_access_to_knowledge, open_source_impact).
    % Existing Arguments - Con (Strong IP)
    argument(arg_CS_pharma). team_of(arg_CS_pharma, team_con_strong_ip).
    prior_domain(arg_CS_pharma, pharmaceutical_rd).
    goal_coverage_claim(arg_CS_pharma, incentivize_research, pharmaceutical_rd).
    goal_coverage_claim(arg_CS_pharma, foster_innovation, pharmaceutical_rd).
    argument(arg_CS_copy). team_of(arg_CS_copy, team_con_strong_ip).
    prior_domain(arg_CS_copy, copyright_duration).
    goal_coverage_claim(arg_CS_copy, protect_creator_rights, copyright_duration).
    % Attacks
    attacks(arg_CS_copy, arg_PR_OS).
    % Relevance Bearers
    relevance_bearer(innovation_expert). relevance_bearer(pharma_executive). relevance_bearer(open_source_advocate).
    % IGI and IDS values
    igi(innovation_expert, foster_innovation, 95). igi(pharma_executive, foster_innovation, 70). igi(open_source_advocate, foster_innovation, 90).
    igi(innovation_expert, ensure_public_access_to_knowledge, 80). igi(pharma_executive, ensure_public_access_to_knowledge, 50). igi(open_source_advocate, ensure_public_access_to_knowledge, 95).
    ids(innovation_expert, patent_law, 90). ids(pharma_executive, patent_law, 85). ids(open_source_advocate, patent_law, 88).
    ids(innovation_expert, open_source_impact, 85). ids(open_source_advocate, open_source_impact, 92). 
    ids(pharma_executive, pharmaceutical_rd, 95). ids(innovation_expert, pharmaceutical_rd, 75). ids(open_source_advocate, pharmaceutical_rd, 60).
    ids(innovation_expert, copyright_duration, 70). ids(pharma_executive, copyright_duration, 70). ids(open_source_advocate, copyright_duration, 60).
    igi(innovation_expert, protect_creator_rights, 75). igi(pharma_executive, protect_creator_rights, 85). igi(open_source_advocate, protect_creator_rights, 65).
    igi(innovation_expert, incentivize_research, 80). igi(pharma_executive, incentivize_research, 98). igi(open_source_advocate, incentivize_research, 50).
    % System constants
    k_chal(40)."""

# --- Helper function for metric extraction ---
def _extract_metric(facts: List[str], prefix: str) -> int:
    matching = [f for f in facts if f.startswith(prefix)]
    if not matching: return 0
    try: return int(matching[0].split(',')[-1].rstrip(')'))
    except ValueError: return 0

# --- Test functions ---
def run_test_gen_argument_for_critical_ugn():
    initial_part = get_nuclear_power_debate_setup()
    asp_program_ugn = initial_part + "\n" + get_ugn_identification_rules()
    solver_ugn = ASPSolver(timeout=10)
    facts_ugn, interrupted_ugn, satisfiable_ugn = solver_ugn.solve(asp_program_ugn)
    
    assert satisfiable_ugn, "UGN id program failed"
    assert not interrupted_ugn, "UGN id interrupted"
    assert facts_ugn is not None, "UGN id no facts"
    
    ugn_value = _extract_metric(facts_ugn, "ugn(team_pro_nuclear,ensure_longterm_safety,waste_management,")
    assert ugn_value == 8648, f"UGN expected 8648, got {ugn_value}" 

    candidate_setup = r"""
    candidate_argument(a_cand_waste_solution). candidate_team_of(a_cand_waste_solution, team_pro_nuclear).
    candidate_prior_domain(a_cand_waste_solution, waste_management).
    candidate_goal_coverage_claim(a_cand_waste_solution, ensure_longterm_safety, waste_management).
    candidate_attacks(a_cand_waste_solution, arg_AN1)."""
    asp_program_cand = initial_part + "\n" + candidate_setup + "\n" + get_candidate_evaluation_rules()
    solver_cand = ASPSolver(timeout=10)
    facts_cand, interrupted_cand, satisfiable_cand = solver_cand.solve(asp_program_cand)
    
    assert satisfiable_cand, "Candidate eval program failed"
    assert not interrupted_cand, "Candidate eval interrupted"
    assert facts_cand is not None, "Candidate eval no facts"

    eapc_est_value = _extract_metric(facts_cand, "eapc_est(a_cand_waste_solution,ensure_longterm_safety,waste_management,")
    print(eapc_est_value)
    assert eapc_est_value == 3459, f"eapc_est expected 3459, got {eapc_est_value}"
    
    contrib_value = _extract_metric(facts_cand, "contrib_to_ugn(a_cand_waste_solution,team_pro_nuclear,")
    print(contrib_value)
    assert contrib_value == 3459, f"contrib_to_ugn expected 3459, got {contrib_value}"

def run_test_gen_candidate_offensive_defensive_merits():
    initial_part = get_ai_ethics_debate_setup()
    candidate_setup = r"""
    candidate_argument(a_cand_strategic). candidate_team_of(a_cand_strategic, team_ethics_first).
    candidate_prior_domain(a_cand_strategic, job_displacement_risk). 
    candidate_goal_coverage_claim(a_cand_strategic, minimize_ai_harm, job_displacement_risk).
    candidate_attacks(a_cand_strategic, arg_IS1). candidate_attacks(a_cand_strategic, arg_IS2)."""
    asp_program = initial_part + "\n" + candidate_setup + "\n" + get_offensive_defensive_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable, "Off/Def program failed"
    assert not interrupted, "Off/Def interrupted"
    assert facts is not None, "Off/Def no facts"

    aps_est_value = _extract_metric(facts, "aps_est(a_cand_strategic,")
    assert aps_est_value == 2040, f"aps_est expected 2040, got {aps_est_value}" 
    
    dos_value = _extract_metric(facts, "dos_est(a_cand_strategic,team_ethics_first,")
    assert dos_value == 3912, f"dos_est expected 3912, got {dos_value}"
    
    dds_value = _extract_metric(facts, "dds_est(a_cand_strategic,team_ethics_first,")
    assert dds_value == 1944, f"dds_est expected 1944, got {dds_value}"
    
    delta_tgs_value = _extract_metric(facts, "delta_tgs_est(a_cand_strategic,")
    assert delta_tgs_value == 3984, \
        f"delta_tgs_est ({delta_tgs_value}) expected 3984 (aps_est:{aps_est_value} + dds_est:{dds_value})"

def run_test_gen_compare_candidate_arguments_utility():
    initial_part = get_ip_reform_debate_setup()
    candidates_setup = r"""
    candidate_argument(cand_A_reform_patent). candidate_team_of(cand_A_reform_patent, team_pro_reform_ip).
    candidate_prior_domain(cand_A_reform_patent, patent_law).
    candidate_goal_coverage_claim(cand_A_reform_patent, foster_innovation, patent_law).
    candidate_argument(cand_B_offensive_pharma). candidate_team_of(cand_B_offensive_pharma, team_pro_reform_ip).
    candidate_prior_domain(cand_B_offensive_pharma, pharmaceutical_rd).
    candidate_goal_coverage_claim(cand_B_offensive_pharma, ensure_public_access_to_knowledge, pharmaceutical_rd).
    candidate_attacks(cand_B_offensive_pharma, arg_CS_pharma).
    candidate_argument(cand_C_defensive_os). candidate_team_of(cand_C_defensive_os, team_pro_reform_ip).
    candidate_prior_domain(cand_C_defensive_os, open_source_impact). 
    candidate_goal_coverage_claim(cand_C_defensive_os, foster_innovation, open_source_impact).
    candidate_attacks(cand_C_defensive_os, arg_CS_copy)."""
    asp_program = initial_part + "\n" + candidates_setup + "\n" + get_comparison_rules()
    solver = ASPSolver(timeout=15)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable, "Comparison program failed"
    assert not interrupted, "Comparison interrupted"
    assert facts is not None, "Comparison no facts"

    metrics = {}
    candidates = ["cand_A_reform_patent", "cand_B_offensive_pharma", "cand_C_defensive_os"]
    for cand in candidates:
        metrics[cand] = {
            'aps_est': _extract_metric(facts, f"aps_est({cand},"),
            'contrib_ugn': _extract_metric(facts, f"contrib_to_ugn({cand},team_pro_reform_ip,"),
            'dos_est': _extract_metric(facts, f"dos_est({cand},team_pro_reform_ip,"),
            'dds_est': _extract_metric(facts, f"dds_est({cand},team_pro_reform_ip,"),
            'overall_utility': _extract_metric(facts, f"overall_utility({cand},")
        }

    # Asercje dla wartości z logów i przewidywanych po poprawkach ASP
    assert metrics["cand_A_reform_patent"]['aps_est'] == 2958, f"cand_A aps_est mismatch: expected 2958, got {metrics['cand_A_reform_patent']['aps_est']}"
    assert metrics["cand_B_offensive_pharma"]['aps_est'] == 2280, f"cand_B aps_est mismatch: expected 2280, got {metrics['cand_B_offensive_pharma']['aps_est']}" 
    assert metrics["cand_C_defensive_os"]['aps_est'] == 2006, f"cand_C aps_est mismatch: expected 2006, got {metrics['cand_C_defensive_os']['aps_est']}"

    assert metrics["cand_A_reform_patent"]['dos_est'] == 0, f"cand_A dos_est mismatch"
    assert metrics["cand_B_offensive_pharma"]['dos_est'] == 4894, f"cand_B dos_est mismatch" 
    assert metrics["cand_C_defensive_os"]['dos_est'] == 1980, f"cand_C dos_est mismatch"

    assert metrics["cand_A_reform_patent"]['dds_est'] == 0, f"cand_A dds_est mismatch"
    assert metrics["cand_B_offensive_pharma"]['dds_est'] == 0, f"cand_B dds_est mismatch"
    assert metrics["cand_C_defensive_os"]['dds_est'] == 3776, f"cand_C dds_est mismatch"
    
    assert metrics["cand_A_reform_patent"]['contrib_ugn'] == 7395, \
        f"cand_A contrib_ugn expected 7395, got {metrics['cand_A_reform_patent']['contrib_ugn']}"
    assert metrics["cand_B_offensive_pharma"]['contrib_ugn'] == 5700, \
        f"cand_B contrib_ugn expected 5700, got {metrics['cand_B_offensive_pharma']['contrib_ugn']}"
    assert metrics["cand_C_defensive_os"]['contrib_ugn'] == 0, \
        f"cand_C contrib_ugn expected 0, got {metrics['cand_C_defensive_os']['contrib_ugn']}"

    # Przeliczenie oczekiwanych wartości overall_utility na podstawie poprawionych contrib_ugn
    metrics["cand_A_reform_patent"]['expected_overall_utility'] = 2958 + 7395 + 0 + 0 # = 10353
    metrics["cand_B_offensive_pharma"]['expected_overall_utility'] = 2280 + 5700 + 4894 + 0 # = 12874
    metrics["cand_C_defensive_os"]['expected_overall_utility'] = 2006 + 0 + 1980 + 3776 # = 7762

    for cand in candidates:
        current_utility = metrics[cand]['overall_utility']
        expected_utility = metrics[cand]['expected_overall_utility']
        assert current_utility == expected_utility, \
            f"overall_utility for {cand} ({current_utility}) " \
            f"does not match sum of components ({expected_utility})"

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
            traceback.print_exc() 
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
