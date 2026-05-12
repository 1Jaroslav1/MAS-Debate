"""
Test Estimations for Candidate Arguments
Tests for provisional scope, EAPC_est, APS_est, contribution to UGN, DOS, DDS, and delta TGS
"""

from src.reasoning.asp.solver import ASPSolver


# Provisional Scope Predicate Tests

def test_scope_est_cand_accepted_no_local_attackers():
    """Test candidate accepted when no attackers"""
    initial_part = r"""
    % Existing framework
    domain_element(d1).
    
    % Candidate argument
    candidate_argument(a_cand).
    candidate_prior_domain(a_cand, d1).
    
    % No attacks in R_cand
    """
    
    asp_program = initial_part + "\n" + get_scope_est_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "scope_est(a_cand,d1)" in facts


def test_scope_est_cand_not_accepted_effective_local_attacker():
    """Test candidate not accepted when attacked by existing argument in scope"""
    initial_part = r"""
    % Existing framework
    argument(arg_exist).
    domain_element(d1).
    
    % Existing argument is in scope
    prior_domain(arg_exist, d1).
    existing_scope(arg_exist, d1).
    
    % Candidate argument
    candidate_argument(a_cand).
    candidate_prior_domain(a_cand, d1).
    
    % Attack from existing to candidate
    candidate_attacks(arg_exist, a_cand).
    """
    
    asp_program = initial_part + "\n" + get_scope_est_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "scope_est(a_cand,d1)" not in facts


def test_scope_est_cand_accepted_local_defense():
    """Test candidate accepted when defended"""
    initial_part = r"""
    % Existing framework
    argument(arg_exist1).
    argument(arg_exist2).
    domain_element(d1).
    
    % Existing arguments and scopes
    prior_domain(arg_exist1, d1).
    prior_domain(arg_exist2, d1).
    existing_scope(arg_exist1, d1).
    existing_scope(arg_exist2, d1).
    
    % Existing attacks
    attacks(arg_exist2, arg_exist1).
    
    % Candidate argument
    candidate_argument(a_cand).
    candidate_prior_domain(a_cand, d1).
    
    % arg_exist1 attacks candidate, but arg_exist2 defends
    candidate_attacks(arg_exist1, a_cand).
    """
    
    asp_program = initial_part + "\n" + get_scope_est_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "scope_est(a_cand,d1)" in facts  # Defended by arg_exist2


# EAPC_est Tests

def test_eapc_est_happy_path_cand_accepted_no_est_challenge():
    """Test EAPC_est equals APC when candidate accepted with no challenges"""
    initial_part = r"""
    % Setup
    candidate_argument(a_cand).
    goal_primitive(g).
    domain_element(d).
    team(teamP).
    
    % Candidate properties
    candidate_team_of(a_cand, teamP).
    candidate_prior_domain(a_cand, d).
    candidate_goal_coverage_claim(a_cand, g, d).
    
    % Values for APC
    pg(g, d, 10).
    sd(d, 5).
    k_chal(20).
    
    % No attackers - candidate will be accepted
    """
    
    asp_program = initial_part + "\n" + get_eapc_est_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "scope_est(a_cand,d)" in facts
    assert "num_effective_opponent_challengers_est(a_cand,d,0)" in facts
    assert "eapc_est(a_cand,g,d,50)" in facts  # APC = 10*5 = 50


def test_eapc_est_happy_path_cand_accepted_with_est_challenge():
    """Test EAPC_est reduced when candidate faces challenges"""
    initial_part = r"""
    % Existing framework
    argument(arg_opp).
    domain_element(d).
    goal_primitive(g).
    team(teamP).
    team(teamO).
    
    % Existing opponent in scope
    team_of(arg_opp, teamO).
    prior_domain(arg_opp, d).
    existing_scope(arg_opp, d).
    
    % Candidate
    candidate_argument(a_cand).
    candidate_team_of(a_cand, teamP).
    candidate_prior_domain(a_cand, d).
    candidate_goal_coverage_claim(a_cand, g, d).
    
    % Opponent attacks candidate
    candidate_attacks(arg_opp, a_cand).
    
    % Force candidate accepted despite attack (for testing)
    force_scope_est(a_cand, d).
    
    % Values
    pg(g, d, 20).
    sd(d, 4).
    k_chal(50).  % 0.5
    """
    
    asp_program = initial_part + "\n" + get_eapc_est_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "num_effective_opponent_challengers_est(a_cand,d,1)" in facts
    assert "eapc_est(a_cand,g,d,40)" in facts  # APC=80, reduced by 0.5


def test_eapc_est_error_path_cand_not_accepted_est():
    """Test EAPC_est is zero when candidate not accepted"""
    initial_part = r"""
    % Existing framework
    argument(arg_strong).
    domain_element(d).
    goal_primitive(g).
    team(teamP).
    team(teamO).
    
    % Strong opponent in scope
    team_of(arg_strong, teamO).
    prior_domain(arg_strong, d).
    existing_scope(arg_strong, d).
    
    % Candidate
    candidate_argument(a_cand).
    candidate_team_of(a_cand, teamP).
    candidate_prior_domain(a_cand, d).
    candidate_goal_coverage_claim(a_cand, g, d).
    
    % Strong attack with no defense
    candidate_attacks(arg_strong, a_cand).
    
    % Values
    pg(g, d, 15).
    sd(d, 2).
    k_chal(10).
    """
    
    asp_program = initial_part + "\n" + get_eapc_est_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "scope_est(a_cand,d)" not in facts
    assert "eapc_est(a_cand,g,d,0)" in facts


# APS_est Tests

def test_aps_est_single_eapc_est_contribution():
    """Test APS_est with single EAPC_est contribution"""
    initial_part = r"""
    % Setup
    candidate_argument(a_cand).
    goal_primitive(g1).
    domain_element(d1).
    
    % Manual EAPC_est for testing
    manual_eapc_est(a_cand, g1, d1, 75).
    """
    
    asp_program = initial_part + "\n" + get_aps_est_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "aps_est(a_cand,75)" in facts


def test_aps_est_multiple_eapc_est_contributions():
    """Test APS_est with multiple EAPC_est contributions"""
    initial_part = r"""
    % Setup
    candidate_argument(a_cand).
    goal_primitive(g1).
    goal_primitive(g2).
    domain_element(d1).
    domain_element(d2).
    
    % Manual EAPC_est values
    manual_eapc_est(a_cand, g1, d1, 40).
    manual_eapc_est(a_cand, g2, d2, 35).
    """
    
    asp_program = initial_part + "\n" + get_aps_est_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "aps_est(a_cand,75)" in facts  # 40 + 35


# Contribution to UGN Tests

def test_contrib_ugn_cand_fills_part_of_need():
    """Test contribution when candidate partially fills need"""
    initial_part = r"""
    % Setup
    candidate_argument(a_cand).
    goal_primitive(g).
    domain_element(d).
    team(teamP).
    
    % Manual values
    manual_eapc_est(a_cand, g, d, 50).
    manual_ugn(teamP, g, d, 80).
    
    % Candidate claims
    candidate_goal_coverage_claim(a_cand, g, d).
    """
    
    asp_program = initial_part + "\n" + get_contrib_ugn_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    # Contribution should be min(50, 80) = 50
    assert "contrib_to_ugn_single(a_cand,g,d,teamP,50)" in facts


def test_contrib_ugn_cand_exceeds_need():
    """Test contribution when candidate exceeds need"""
    initial_part = r"""
    % Setup
    candidate_argument(a_cand).
    goal_primitive(g).
    domain_element(d).
    team(teamP).
    
    % Manual values
    manual_eapc_est(a_cand, g, d, 100).
    manual_ugn(teamP, g, d, 30).
    
    % Candidate claims
    candidate_goal_coverage_claim(a_cand, g, d).
    """
    
    asp_program = initial_part + "\n" + get_contrib_ugn_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    # Contribution should be min(100, 30) = 30
    assert "contrib_to_ugn_single(a_cand,g,d,teamP,30)" in facts


def test_contrib_ugn_summation_over_multiple_gd_pairs():
    """Test total contribution across multiple goal-domain pairs"""
    initial_part = r"""
    % Setup
    candidate_argument(a_cand).
    goal_primitive(g1).
    goal_primitive(g2).
    domain_element(d1).
    domain_element(d2).
    team(teamP).
    
    % Manual values
    manual_eapc_est(a_cand, g1, d1, 40).
    manual_eapc_est(a_cand, g2, d2, 60).
    manual_ugn(teamP, g1, d1, 50).  % Will contribute 40
    manual_ugn(teamP, g2, d2, 30).  % Will contribute 30
    
    % Candidate claims
    candidate_goal_coverage_claim(a_cand, g1, d1).
    candidate_goal_coverage_claim(a_cand, g2, d2).
    """
    
    asp_program = initial_part + "\n" + get_contrib_ugn_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "contrib_to_ugn(a_cand,teamP,70)" in facts  # 40 + 30


# Delta TGS Tests

def test_delta_tgs_basic_sum():
    """Test delta TGS as sum of APS_est and DDS_est"""
    initial_part = r"""
    % Setup
    candidate_argument(a_cand).
    team(teamP).
    
    % Manual values
    manual_aps_est(a_cand, 100).
    manual_dds_est(a_cand, teamP, 50).
    """
    
    asp_program = initial_part + "\n" + get_delta_tgs_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "delta_tgs_est(a_cand,teamP,150)" in facts


def test_delta_tgs_only_aps_est_no_dds_est():
    """Test delta TGS with only APS contribution"""
    initial_part = r"""
    % Setup
    candidate_argument(a_cand).
    team(teamP).
    
    % Manual values
    manual_aps_est(a_cand, 70).
    manual_dds_est(a_cand, teamP, 0).
    """
    
    asp_program = initial_part + "\n" + get_delta_tgs_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "delta_tgs_est(a_cand,teamP,70)" in facts


# Helper rule functions

def get_scope_est_rules():
    """Return rules for provisional scope estimation"""
    return r"""
    % Existing scope
    scope(A, D) :- existing_scope(A, D).
    
    % Candidate attacked in domain
    candidate_attacked_in_domain(Cand, D, Attacker) :-
        candidate_argument(Cand),
        candidate_prior_domain(Cand, D),
        candidate_attacks(Attacker, Cand),
        prior_domain(Attacker, D),
        scope(Attacker, D).
    
    % Candidate defended
    candidate_defended_from(Cand, D, Attacker) :-
        candidate_attacked_in_domain(Cand, D, Attacker),
        argument(Defender),
        attacks(Defender, Attacker),
        scope(Defender, D).
    
    % Candidate not acceptable
    candidate_not_acceptable(Cand, D) :-
        candidate_attacked_in_domain(Cand, D, Attacker),
        not candidate_defended_from(Cand, D, Attacker).
    
    % Estimated scope
    scope_est(Cand, D) :-
        candidate_argument(Cand),
        candidate_prior_domain(Cand, D),
        not candidate_not_acceptable(Cand, D).
    
    % Suppress warnings
    attacks(dummy1, dummy2) :- #false.
    candidate_attacks(dummy1, dummy2) :- #false.
    
    #show scope_est/2.
    """


def get_eapc_est_rules():
    """Return rules for EAPC estimation"""
    return r"""
    % Include scope estimation
    scope(A, D) :- existing_scope(A, D).
    
    % Forced scope_est for testing
    scope_est(Cand, D) :- force_scope_est(Cand, D).
    
    % Default scope_est calculation
    candidate_attacked_in_domain(Cand, D, Attacker) :-
        candidate_argument(Cand),
        candidate_prior_domain(Cand, D),
        candidate_attacks(Attacker, Cand),
        prior_domain(Attacker, D),
        scope(Attacker, D),
        not force_scope_est(Cand, D).
    
    candidate_defended_from(Cand, D, Attacker) :-
        candidate_attacked_in_domain(Cand, D, Attacker),
        argument(Defender),
        attacks(Defender, Attacker),
        scope(Defender, D).
    
    candidate_not_acceptable(Cand, D) :-
        candidate_attacked_in_domain(Cand, D, Attacker),
        not candidate_defended_from(Cand, D, Attacker).
    
    scope_est(Cand, D) :-
        candidate_argument(Cand),
        candidate_prior_domain(Cand, D),
        not candidate_not_acceptable(Cand, D),
        not force_scope_est(Cand, D).
    
    % APC for candidate
    apc_candidate(Cand, G, D, Value) :-
        candidate_goal_coverage_claim(Cand, G, D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    % Estimated opponent challengers
    est_opponent_challenger(Cand, D, Challenger) :-
        candidate_argument(Cand),
        domain_element(D),
        candidate_attacks(Challenger, Cand),
        candidate_team_of(Cand, TeamCand),
        team_of(Challenger, TeamChallenger),
        TeamCand != TeamChallenger,
        scope(Challenger, D).
    
    num_effective_opponent_challengers_est(Cand, D, Count) :-
        candidate_argument(Cand),
        domain_element(D),
        Count = #count { C : est_opponent_challenger(Cand, D, C) }.
    
    % EAPC_est calculation
    eapc_est(Cand, G, D, Value) :-
        candidate_goal_coverage_claim(Cand, G, D),
        scope_est(Cand, D),
        num_effective_opponent_challengers_est(Cand, D, 0),
        apc_candidate(Cand, G, D, Value).
    
    eapc_est(Cand, G, D, Value) :-
        candidate_goal_coverage_claim(Cand, G, D),
        scope_est(Cand, D),
        num_effective_opponent_challengers_est(Cand, D, N),
        N > 0,
        apc_candidate(Cand, G, D, APC_Val),
        k_chal(K),
        Reduction = (K ** N) / (100 ** N),
        Value = (APC_Val * Reduction).
    
    eapc_est(Cand, G, D, 0) :-
        candidate_goal_coverage_claim(Cand, G, D),
        not scope_est(Cand, D).
    
    % Suppress warnings
    attacks(dummy1, dummy2) :- #false.
    candidate_attacks(dummy1, dummy2) :- #false.
    
    #show scope_est/2.
    #show num_effective_opponent_challengers_est/3.
    #show eapc_est/4.
    """


def get_aps_est_rules():
    """Return rules for APS estimation"""
    return r"""
    % Use manual EAPC_est values
    eapc_est(Cand, G, D, Value) :- manual_eapc_est(Cand, G, D, Value).
    
    % APS_est = sum of all EAPC_est
    aps_est(Cand, Sum) :-
        candidate_argument(Cand),
        Sum = #sum { Value, G, D : eapc_est(Cand, G, D, Value) }.
    
    #show aps_est/2.
    """


def get_contrib_ugn_rules():
    """Return rules for contribution to UGN"""
    return r"""
    % Use manual values
    eapc_est(Cand, G, D, Value) :- manual_eapc_est(Cand, G, D, Value).
    ugn(Team, G, D, Value) :- manual_ugn(Team, G, D, Value).
    
    % Single contribution = min(eapc_est, ugn)
    contrib_to_ugn_single(Cand, G, D, Team, Contrib) :-
        candidate_goal_coverage_claim(Cand, G, D),
        eapc_est(Cand, G, D, EAPC_Val),
        ugn(Team, G, D, UGN_Val),
        Contrib = #min { EAPC_Val; UGN_Val }.
    
    % Total contribution
    contrib_to_ugn(Cand, Team, Total) :-
        candidate_argument(Cand),
        team(Team),
        Total = #sum { Contrib, G, D : contrib_to_ugn_single(Cand, G, D, Team, Contrib) }.
    
    #show contrib_to_ugn_single/5.
    #show contrib_to_ugn/3.
    """


def get_delta_tgs_rules():
    """Return rules for delta TGS estimation"""
    return r"""
    % Use manual values
    aps_est(Cand, Value) :- manual_aps_est(Cand, Value).
    dds_est(Cand, Team, Value) :- manual_dds_est(Cand, Team, Value).
    
    % Delta TGS = APS_est + DDS_est
    delta_tgs_est(Cand, Team, Value) :-
        candidate_argument(Cand),
        team(Team),
        aps_est(Cand, APS_Val),
        dds_est(Cand, Team, DDS_Val),
        Value = APS_Val + DDS_Val.
    
    #show delta_tgs_est/3.
    """


if __name__ == "__main__":
    # Scope estimation tests
    test_scope_est_cand_accepted_no_local_attackers()
    print("✓ Scope_est accepted no attackers test passed")
    
    test_scope_est_cand_not_accepted_effective_local_attacker()
    print("✓ Scope_est not accepted with attacker test passed")
    
    test_scope_est_cand_accepted_local_defense()
    print("✓ Scope_est accepted with defense test passed")
    
    # EAPC_est tests
    test_eapc_est_happy_path_cand_accepted_no_est_challenge()
    print("✓ EAPC_est no challenge test passed")
    
    test_eapc_est_happy_path_cand_accepted_with_est_challenge()
    print("✓ EAPC_est with challenge test passed")
    
    test_eapc_est_error_path_cand_not_accepted_est()
    print("✓ EAPC_est not accepted test passed")
    
    # APS_est tests
    test_aps_est_single_eapc_est_contribution()
    print("✓ APS_est single contribution test passed")
    
    test_aps_est_multiple_eapc_est_contributions()
    print("✓ APS_est multiple contributions test passed")
    
    # Contribution to UGN tests
    test_contrib_ugn_cand_fills_part_of_need()
    print("✓ Contribution to UGN partial fill test passed")
    
    test_contrib_ugn_cand_exceeds_need()
    print("✓ Contribution to UGN exceeds need test passed")
    
    test_contrib_ugn_summation_over_multiple_gd_pairs()
    print("✓ Contribution to UGN summation test passed")
    
    # Delta TGS tests
    test_delta_tgs_basic_sum()
    print("✓ Delta TGS basic sum test passed")
    
    test_delta_tgs_only_aps_est_no_dds_est()
    print("✓ Delta TGS only APS test passed")
    
    print("\nAll candidate estimation tests passed!")
