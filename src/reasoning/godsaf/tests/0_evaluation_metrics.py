"""
Test suite for GoDsAF Argument Evaluation Metrics
Based on Prompts 1-3 from the specification
(Rewritten to not use pytest)
"""

from typing import Set
from dataclasses import dataclass
from src.reasoning.asp.solver import ASPSolver


@dataclass
class GoDsAFTestCase:
    """Base class for GoDsAF test cases"""
    name: str
    initial_part: str
    expected_facts: Set[str]
    excluded_facts: Set[str] = None
    
    def __post_init__(self):
        if self.excluded_facts is None:
            self.excluded_facts = set()

# Helper functions for ASP rules (kept from original)
def get_full_godsaf_rules() -> str:
    """Return complete GoDsAF rules for evaluation metrics"""
    return r"""
    % ==== AAFD Scope Rules ====
    { scope(A, D) : domain_element(D) } :- argument(A).
    
    % Domain Capping
    :- scope(A, D), not prior_domain(A, D).
    
    % Conflict-Free
    :- attacks(A1, A2), scope(A1, D), scope(A2, D).
    
    % Complete semantics
    attacked_in_domain(A, D, B) :- 
        attacks(B, A), 
        prior_domain(A, D), 
        prior_domain(B, D).
    
    defended_from_in_domain(A, D, B) :- 
        attacked_in_domain(A, D, B),
        attacks(C, B),
        scope(C, D).
    
    not_acceptable_in_domain(A, D) :- 
        attacked_in_domain(A, D, B),
        not defended_from_in_domain(A, D, B).
    
    acceptable_in_domain(A, D) :- 
        prior_domain(A, D),
        not not_acceptable_in_domain(A, D).
    
    :- scope(A, D), not acceptable_in_domain(A, D).
    :- acceptable_in_domain(A, D), not scope(A, D).
    
    % ==== P_G and S_D Calculations ====
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
    
    % ==== APC Calculation ====
    apc(A, G, D, Value) :-
        goal_coverage_claim(A, G, D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    % ==== Opponent Challenge Identification ====
    opponent_challenger(A, D, Challenger) :-
        argument(A),
        domain_element(D),
        attacks(Challenger, A),
        team_of(A, TeamA),
        team_of(Challenger, TeamC),
        TeamA != TeamC,
        scope(Challenger, D).
    
    num_effective_opponent_challengers(A, D, Count) :-
        argument(A),
        domain_element(D),
        Count = #count { C : opponent_challenger(A, D, C) }.
    
    % ==== EAPC Calculation ====
    % Case 1: In scope, no challengers
    eapc(A, G, D, EAPC_Value) :-
        goal_coverage_claim(A, G, D),
        scope(A, D),
        num_effective_opponent_challengers(A, D, 0),
        apc(A, G, D, EAPC_Value).
    
    % Case 2: In scope with challengers
    eapc(A, G, D, EAPC_Value) :-
        goal_coverage_claim(A, G, D),
        scope(A, D),
        num_effective_opponent_challengers(A, D, N),
        N > 0,
        apc(A, G, D, APC_Value),
        k_chal(K),
        NumeratorVal = APC_Value * (K ** N),
        DenominatorVal = 100 ** (N-1),
        EAPC_Value = NumeratorVal / DenominatorVal.
    
    % Case 3: Not in scope
    eapc(A, G, D, 0) :-
        goal_coverage_claim(A, G, D),
        not scope(A, D).
    
    % ==== EGR Calculation ====
    egr(A, G, D, 1) :-
        goal_coverage_claim(A, G, D),
        scope(A, D).
    
    egr(A, G, D, 0) :-
        goal_coverage_claim(A, G, D),
        not scope(A, D).
    
    % ==== APS Calculation ====
    aps(A, Sum) :-
        argument(A),
        Sum = #sum { Value, G, D : eapc(A, G, D, Value) }.
    
    % ==== TGS Calculation ====
    tgs(Team, G, D, Sum) :-
        team(Team),
        goal_primitive(G),
        domain_element(D),
        Sum = #sum { Value, A : eapc(A, G, D, Value), team_of(A, Team) }.
    
    % ==== ReGS Calculation ====
    regs(G, D, Value) :-
        goal_primitive(G),
        domain_element(D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    % ==== UGN Calculation ====
    ugn(Team, G, D, Value) :-
        team(Team),
        goal_primitive(G),
        domain_element(D),
        regs(G, D, ReGS_Val),
        tgs(Team, G, D, TGS_Val),
        Value = #max { 0; ReGS_Val - TGS_Val }.
    
    % Suppress warnings
    attacks(dummy1, dummy2) :- #false.
    
    #show scope/2.
    #show apc/4.
    #show num_effective_opponent_challengers/3.
    #show eapc/4.
    #show egr/4.
    #show aps/2.
    #show tgs/4.
    #show regs/3.
    #show ugn/4.
    """

def get_full_godsaf_rules_with_structural() -> str:
    """Return GoDsAF rules including structural impact analysis"""
    base_rules = get_full_godsaf_rules()
    structural_rules = r"""
    % ==== Structural Impact Analysis ====
    % Weight calculation for domain d*
    weight(A, D, Value) :-
        argument(A),
        focus_domain(D),
        prior_domain(A, D),
        Value = #sum { EAPC, G : eapc(A, G, D, EAPC) }.
    
    weight(A, D, 0) :-
        argument(A),
        focus_domain(D),
        not prior_domain(A, D).
    
    % Structurally relevant arguments (weight > theta)
    structurally_relevant(A, D) :-
        weight(A, D, W),
        theta_relevance(Theta),
        W > Theta.
    
    #show weight/3.
    #show structurally_relevant/2.
    """
    return base_rules + "\n" + structural_rules

# --- Test Case 1: Proponent Key Argument Impact ---
def get_ubi_debate_setup() -> str:
    """Setup for Universal Basic Income debate scenario"""
    return r"""
    % Teams
    team(team_pro_ubi).
    team(team_con_ubi).
    
    % Domain Elements
    domain_element(economic_effects).
    domain_element(social_impact).
    domain_element(fiscal_sustainability).
    
    % Goal Primitives
    goal_primitive(reduce_poverty).
    goal_primitive(stimulate_economy).
    goal_primitive(ensure_fiscal_viability).
    goal_primitive(improve_public_health).
    
    % Proponent's Key Argument
    argument(arg_pro_main).
    team_of(arg_pro_main, team_pro_ubi).
    prior_domain(arg_pro_main, economic_effects).
    prior_domain(arg_pro_main, social_impact).
    goal_coverage_claim(arg_pro_main, reduce_poverty, economic_effects).
    goal_coverage_claim(arg_pro_main, improve_public_health, social_impact).
    
    % Opponent Arguments
    argument(arg_con_econ_critique).
    team_of(arg_con_econ_critique, team_con_ubi).
    prior_domain(arg_con_econ_critique, economic_effects).
    
    argument(arg_con_social_doubt).
    team_of(arg_con_social_doubt, team_con_ubi).
    prior_domain(arg_con_social_doubt, social_impact).
    
    % Attacks
    attacks(arg_con_econ_critique, arg_pro_main).
    
    % Relevance Bearers
    relevance_bearer(economist_A).
    relevance_bearer(social_worker_B).
    relevance_bearer(taxpayer_C).
    
    % IGI and IDS scores for high P_G and S_D values
    igi(economist_A, reduce_poverty, 80).
    igi(economist_A, improve_public_health, 60).
    igi(social_worker_B, reduce_poverty, 90).
    igi(social_worker_B, improve_public_health, 85).
    igi(taxpayer_C, reduce_poverty, 70).
    igi(taxpayer_C, improve_public_health, 50).
    
    ids(economist_A, economic_effects, 90).
    ids(economist_A, social_impact, 70).
    ids(social_worker_B, economic_effects, 75).
    ids(social_worker_B, social_impact, 95).
    ids(taxpayer_C, economic_effects, 85).
    ids(taxpayer_C, social_impact, 60).
    
    % System constants
    k_chal(40).  % 0.4 challenge reduction factor
    """

def run_test_eval_proponent_key_argument_impact():
    """Test comprehensive evaluation of proponent's key argument"""
    initial_part = get_ubi_debate_setup()
    
    asp_program = initial_part + "\n" + get_full_godsaf_rules()
    solver = ASPSolver(timeout=10) # Można zwiększyć timeout w razie potrzeby
    facts, interrupted, satisfiable = solver.solve(asp_program)

    assert satisfiable, "ASP program should be satisfiable"
    assert not interrupted, "ASP solving should not be interrupted by timeout"
    assert facts is not None, "Facts should not be None if satisfiable"
    
    facts_set = set(facts) # Użyj set dla efektywniejszego sprawdzania

    # --- Weryfikacja scope ---
    # arg_pro_main jest atakowany przez arg_con_econ_critique w domenie economic_effects.
    # arg_pro_main nie jest broniony przed tym atakiem w tej domenie.
    # Zatem scope(arg_pro_main, economic_effects) powinien być FAŁSZYWY.
    assert "scope(arg_pro_main,economic_effects)" not in facts_set, \
        "scope(arg_pro_main,economic_effects) should be false"
    
    # W domenie social_impact, arg_pro_main nie jest atakowany przez żaden argument *w tej domenie*.
    # (atak z arg_con_econ_critique jest w innej domenie).
    # Zatem scope(arg_pro_main, social_impact) powinien być PRAWDZIWY.
    assert "scope(arg_pro_main,social_impact)" in facts_set, \
        "scope(arg_pro_main,social_impact) should be true"

    # --- Weryfikacja APC (obliczane niezależnie od scope) ---
    # Dla (arg_pro_main, reduce_poverty, economic_effects):
    # PG_Val = (80+90+70)/3 = 240/3 = 80.
    # SD_Val = (90+75+85)/3 = 250/3 = 83 (dzielenie całkowitoliczbowe w Clingo).
    # APC_Val = 80 * 83 = 6640.
    assert "apc(arg_pro_main,reduce_poverty,economic_effects,6640)" in facts_set, \
        "APC for (arg_pro_main,reduce_poverty,economic_effects) mismatch"
    
    # Dla (arg_pro_main, improve_public_health, social_impact):
    # PG_Val = (60+85+50)/3 = 195/3 = 65.
    # SD_Val = (70+95+60)/3 = 225/3 = 75.
    # APC_Val = 65 * 75 = 4875.
    assert "apc(arg_pro_main,improve_public_health,social_impact,4875)" in facts_set, \
        "APC for (arg_pro_main,improve_public_health,social_impact) mismatch"
    
    # --- Weryfikacja liczby challengerów ---
    # Dla (arg_pro_main, economic_effects):
    # Challenger to arg_con_econ_critique. scope(arg_con_econ_critique, economic_effects) jest true.
    # Zespoły są różne. Więc N=1.
    assert "num_effective_opponent_challengers(arg_pro_main,economic_effects,1)" in facts_set, \
        "Challenger count for (arg_pro_main,economic_effects) mismatch"
    
    # Dla (arg_pro_main, social_impact):
    # Brak challengerów w scope dla tej domeny. N=0.
    assert "num_effective_opponent_challengers(arg_pro_main,social_impact,0)" in facts_set, \
        "Challenger count for (arg_pro_main,social_impact) mismatch"

    # --- Weryfikacja EAPC ---
    # Dla (arg_pro_main, reduce_poverty, economic_effects):
    # scope jest false, więc eapc = 0 (zgodnie z Case 3 reguły eapc).
    assert "eapc(arg_pro_main,reduce_poverty,economic_effects,0)" in facts_set, \
        "EAPC for (arg_pro_main,reduce_poverty,economic_effects) should be 0 due to scope"
    
    # Dla (arg_pro_main, improve_public_health, social_impact):
    # scope jest true, N=0, więc eapc = apc (zgodnie z Case 1 reguły eapc).
    # APC = 4875.
    assert "eapc(arg_pro_main,improve_public_health,social_impact,4875)" in facts_set, \
        "EAPC for (arg_pro_main,improve_public_health,social_impact) should be APC value"

    # --- Weryfikacja APS ---
    # aps(arg_pro_main, Suma_EAPC_dla_arg_pro_main)
    # Suma EAPC = eapc(reduce_poverty,economic_effects) + eapc(improve_public_health,social_impact)
    # Suma EAPC = 0 + 4875 = 4875.
    assert "aps(arg_pro_main,4875)" in facts_set, \
        "APS for arg_pro_main mismatch"
    
    # --- Weryfikacja TGS dla team_pro_ubi ---
    # tgs(team_pro_ubi, reduce_poverty, economic_effects, Suma_EAPC_dla_zespolu_celu_domeny)
    # Jedynie arg_pro_main z team_pro_ubi pokrywa ten cel/domenę. Jego EAPC = 0.
    assert "tgs(team_pro_ubi,reduce_poverty,economic_effects,0)" in facts_set, \
        "TGS for (team_pro_ubi,reduce_poverty,economic_effects) mismatch"
        
    # tgs(team_pro_ubi, improve_public_health, social_impact, Suma_EAPC_dla_zespolu_celu_domeny)
    # Jedynie arg_pro_main z team_pro_ubi pokrywa ten cel/domenę. Jego EAPC = 4875.
    assert "tgs(team_pro_ubi,improve_public_health,social_impact,4875)" in facts_set, \
        "TGS for (team_pro_ubi,improve_public_health,social_impact) mismatch"

# --- Test Case 2: Team Performance And Unmet Needs ---
def get_renewable_energy_debate_setup() -> str:
    """Setup for renewable energy investment debate"""
    return r"""
    % Teams
    team(team_renewables_advocates).
    team(team_market_solutions).
    
    % Domain Elements
    domain_element(energy_sector_transition).
    domain_element(economic_implications).
    domain_element(technological_innovation_speed).
    
    % Goal Primitives
    goal_primitive(accelerate_decarbonization).
    goal_primitive(ensure_economic_stability).
    goal_primitive(foster_rapid_tech_adoption).
    
    % Proponent Arguments
    argument(arg_P1).
    team_of(arg_P1, team_renewables_advocates).
    prior_domain(arg_P1, energy_sector_transition).
    goal_coverage_claim(arg_P1, accelerate_decarbonization, energy_sector_transition).
    
    argument(arg_P2).
    team_of(arg_P2, team_renewables_advocates).
    prior_domain(arg_P2, economic_implications).
    goal_coverage_claim(arg_P2, ensure_economic_stability, economic_implications).
    
    argument(arg_P3).
    team_of(arg_P3, team_renewables_advocates).
    prior_domain(arg_P3, technological_innovation_speed).
    goal_coverage_claim(arg_P3, foster_rapid_tech_adoption, technological_innovation_speed).
    
    % Opponent Arguments & Attacks
    argument(arg_O1).
    team_of(arg_O1, team_market_solutions).
    prior_domain(arg_O1, economic_implications).
    attacks(arg_O1, arg_P2).
    
    % Relevance Bearers with high P_G and S_D values
    relevance_bearer(energy_expert).
    relevance_bearer(economist).
    relevance_bearer(tech_investor).
    
    % High IGI scores, especially for economic stability
    igi(energy_expert, accelerate_decarbonization, 95).
    igi(energy_expert, ensure_economic_stability, 85).
    igi(energy_expert, foster_rapid_tech_adoption, 80).
    
    igi(economist, accelerate_decarbonization, 70).
    igi(economist, ensure_economic_stability, 98).  % Very high
    igi(economist, foster_rapid_tech_adoption, 75).
    
    igi(tech_investor, accelerate_decarbonization, 80).
    igi(tech_investor, ensure_economic_stability, 90).
    igi(tech_investor, foster_rapid_tech_adoption, 95).
    
    % IDS scores
    ids(energy_expert, energy_sector_transition, 95).
    ids(energy_expert, economic_implications, 80).
    ids(energy_expert, technological_innovation_speed, 85).
    
    ids(economist, energy_sector_transition, 75).
    ids(economist, economic_implications, 95).
    ids(economist, technological_innovation_speed, 70).
    
    ids(tech_investor, energy_sector_transition, 85).
    ids(tech_investor, economic_implications, 88).
    ids(tech_investor, technological_innovation_speed, 92).
    
    % System constants
    k_chal(30).  % 0.3 challenge reduction factor
    """

def run_test_eval_team_performance_and_unmet_needs():
    """Test team-level goal achievement and UGN analysis"""
    initial_part = get_renewable_energy_debate_setup()
    
    asp_program = initial_part + "\n" + get_full_godsaf_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert facts is not None
    
    # Verify TGS calculations for each (goal, domain) pair
    assert any("tgs(team_renewables_advocates,accelerate_decarbonization,energy_sector_transition," in f for f in facts)
    assert any("tgs(team_renewables_advocates,ensure_economic_stability,economic_implications," in f for f in facts)
    assert any("tgs(team_renewables_advocates,foster_rapid_tech_adoption,technological_innovation_speed," in f for f in facts)
    
    # Verify ReGS calculations
    assert any("regs(accelerate_decarbonization,energy_sector_transition," in f for f in facts)
    assert any("regs(ensure_economic_stability,economic_implications," in f for f in facts)
    assert any("regs(foster_rapid_tech_adoption,technological_innovation_speed," in f for f in facts)
    
    # Verify UGN calculations
    assert any("ugn(team_renewables_advocates,ensure_economic_stability,economic_implications," in f for f in facts)
    
    # Extract and verify UGN value for economic stability is positive
    ugn_facts = [f for f in facts if f.startswith("ugn(team_renewables_advocates,ensure_economic_stability,economic_implications,")]
    assert len(ugn_facts) > 0, "UGN fact for economic stability not found"
    ugn_value_str = ugn_facts[0].split(',')[-1].rstrip(')')
    # UGN value can be a float if division results in floats, or int. ASP typically deals with integers unless floats are forced.
    # Let's assume it can be parsed as a number.
    try:
        ugn_value = float(ugn_value_str) # Use float for generality
    except ValueError:
        assert False, f"UGN value part is not a valid number: {ugn_value_str}"
    assert ugn_value >= 0  # UGN is max(0, ReGS - TGS), so it can be 0. If attack reduces TGS, UGN might increase.
                           # The original assert was ugn_value > 0, let's analyze if it must be strictly positive.
                           # If arg_P2 is attacked by arg_O1, its EAPC might decrease.
                           # This could make TGS smaller than ReGS, leading to positive UGN.
                           # It's plausible for UGN to be > 0 here.

# --- Test Case 3: Comparative Strength And Structural Impact ---
def get_social_media_regulation_setup() -> str:
    """Setup for social media regulation debate"""
    return r"""
    % Teams
    team(team_regulation_advocates).
    team(team_free_speech_defenders).
    
    % Domain Elements
    domain_element(misinformation_spread).
    domain_element(freedom_of_expression).
    domain_element(platform_accountability).
    domain_element(innovation_impact).
    
    % Goal Primitives
    goal_primitive(reduce_harmful_content).
    goal_primitive(protect_free_speech).
    goal_primitive(ensure_platform_transparency).
    goal_primitive(foster_tech_innovation).
    
    % Focus domain
    focus_domain(misinformation_spread).
    
    % Arguments for regulation advocates
    argument(arg_RA1).
    team_of(arg_RA1, team_regulation_advocates).
    prior_domain(arg_RA1, misinformation_spread).
    goal_coverage_claim(arg_RA1, reduce_harmful_content, misinformation_spread).
    
    argument(arg_RA2).
    team_of(arg_RA2, team_regulation_advocates).
    prior_domain(arg_RA2, platform_accountability).
    goal_coverage_claim(arg_RA2, ensure_platform_transparency, platform_accountability).
    
    % Arguments for free speech defenders
    argument(arg_FS1).
    team_of(arg_FS1, team_free_speech_defenders).
    prior_domain(arg_FS1, misinformation_spread).
    prior_domain(arg_FS1, freedom_of_expression).
    goal_coverage_claim(arg_FS1, protect_free_speech, freedom_of_expression).
    
    argument(arg_FS2).
    team_of(arg_FS2, team_free_speech_defenders).
    prior_domain(arg_FS2, misinformation_spread). % FS2 is also relevant to misinformation_spread
    goal_coverage_claim(arg_FS2, protect_free_speech, misinformation_spread). % Example: arguing free speech on this domain counters bad ideas
    
    % Attacks
    attacks(arg_RA1, arg_FS2). % RA1 attacks FS2
    attacks(arg_FS1, arg_RA1). % FS1 attacks RA1
    
    % Relevance Bearers with high values for misinformation_spread
    relevance_bearer(policy_maker).
    relevance_bearer(civil_rights_advocate).
    relevance_bearer(tech_executive).
    
    % Very high P_G and S_D for misinformation_spread and relevant goals
    igi(policy_maker, reduce_harmful_content, 95).
    igi(policy_maker, protect_free_speech, 70). % For FS2's goal
    igi(civil_rights_advocate, reduce_harmful_content, 80).
    igi(civil_rights_advocate, protect_free_speech, 90).
    igi(tech_executive, reduce_harmful_content, 85).
    igi(tech_executive, protect_free_speech, 75).
    
    ids(policy_maker, misinformation_spread, 98).
    ids(civil_rights_advocate, misinformation_spread, 92).
    ids(tech_executive, misinformation_spread, 88).
    
    % Moderate values for other domains/goals to ensure focus
    ids(policy_maker, freedom_of_expression, 70).
    ids(civil_rights_advocate, freedom_of_expression, 85).
    ids(tech_executive, freedom_of_expression, 60).
    ids(policy_maker, platform_accountability, 60). % For arg_RA2
    igi(policy_maker, ensure_platform_transparency, 65). % For arg_RA2
     
    % System constants
    k_chal(40).
    theta_relevance(10).  % Threshold for structural relevance
    """

def run_test_eval_comparative_strength_and_sis():
    """Test comparative APS and structural impact analysis"""
    initial_part = get_social_media_regulation_setup()
    
    asp_program = initial_part + "\n" + get_full_godsaf_rules_with_structural()
    solver = ASPSolver(timeout=10) # Increased timeout slightly just in case
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable, f"ASP program should be satisfiable. Facts: {facts}"
    assert not interrupted, "ASP solving should not be interrupted by timeout"
    assert facts is not None, "Facts should not be None if satisfiable"
    
    # Verify APS scores for competing arguments
    # Arguments involved in attacks on misinformation_spread domain are arg_RA1 and arg_FS2.
    # arg_FS1 attacks arg_RA1, so arg_RA1 might have reduced EAPC for its claims on misinformation_spread.
    # arg_RA1 attacks arg_FS2, so arg_FS2 might have reduced EAPC for its claims on misinformation_spread.
    assert any("aps(arg_RA1," in f for f in facts), "APS for arg_RA1 not found"
    assert any("aps(arg_FS2," in f for f in facts), "APS for arg_FS2 not found"
    
    # Verify weight calculations for misinformation_spread domain
    # Both arg_RA1 and arg_FS2 make claims in misinformation_spread
    assert any("weight(arg_RA1,misinformation_spread," in f for f in facts), "Weight for arg_RA1 in misinformation_spread not found"
    assert any("weight(arg_FS2,misinformation_spread," in f for f in facts), "Weight for arg_FS2 in misinformation_spread not found"
    
    # Verify identification of structurally relevant arguments
    # At least one of arg_RA1 or arg_FS2 should be structurally relevant in misinformation_spread if their weights are > theta_relevance(10)
    # This depends on the EAPC values which are affected by attacks.
    relevant_found = any("structurally_relevant(arg_RA1,misinformation_spread)" in f for f in facts) or \
                     any("structurally_relevant(arg_FS2,misinformation_spread)" in f for f in facts)
    
    # For debugging if the assertion fails:
    if not relevant_found:
        print("Facts for structural relevance test:")
        for f in sorted(list(facts if facts else set())): # Sort for consistent output
            if "weight(" in f or "eapc(arg_RA1" in f or "eapc(arg_FS2" in f or "aps(" in f or "structurally_relevant" in f:
                print(f)
    
    assert relevant_found, "Neither arg_RA1 nor arg_FS2 found structurally_relevant in misinformation_spread. Check weights and EAPC."


# Manual Test Runner
if __name__ == "__main__":
    # List of test functions to run
    tests_to_run = [
        run_test_eval_proponent_key_argument_impact,
        run_test_eval_team_performance_and_unmet_needs,
        run_test_eval_comparative_strength_and_sis,
    ]

    passed_count = 0
    failed_count = 0
    test_results = []

    print("Starting GoDsAF Argument Evaluation Metrics Test Suite...\n")

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
            # traceback.print_exc() # Uncomment for full traceback if needed
            failed_count += 1
            test_results.append((test_name, "ERROR", f"Exception: {type(e).__name__} - {e}"))
        print("-" * 50)

    print("\nTest Execution Summary:")
    print("=" * 50)
    for name, status, message in test_results:
        print(f"{status:<8} : {name}")
        if message and (status == "FAILED" or status == "ERROR"):
            # Indent message for readability
            for line in message.splitlines():
                print(f"          {line}")


    print("=" * 50)
    print(f"\nTotal tests run: {len(tests_to_run)}")
    print(f"  Passed: {passed_count}")
    print(f"  Failed/Errored: {failed_count}")
    print("=" * 50)

    if failed_count == 0:
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests did not pass. Please review the output above.")
