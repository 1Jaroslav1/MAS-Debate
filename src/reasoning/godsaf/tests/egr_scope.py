"""
Test Component 3: Effective Goal Realization (EGR_Scope)
Tests the conditions under which arguments effectively realize goals in specific domains
"""

from src.reasoning.asp.solver import ASPSolver


def test_egr_successful_realization():
    """
    Test the primary success condition for EGR: an argument makes a claim for a goal in a domain,
    and it is accepted (in scope) for that domain. This is the core 'argument achieves its stated aim' use case.
    """
    initial_part = r"""
    % Domain Elements (U_D)
    domain_element(market_strategy).
    
    % Goal Primitives (U_G)
    goal_primitive(increase_share).
    
    % Argument
    argument(strat_A).
    
    % Prior Domain Assignment (D_pi)
    prior_domain(strat_A, market_strategy).
    
    % Goal Coverage Claim (C)
    goal_coverage_claim(strat_A, increase_share, market_strategy).
    
    % Team assignment (required for complete setup)
    team(marketing_team).
    team_of(strat_A, marketing_team).
    """
    
    asp_program = initial_part + "\n" + get_egr_rules_with_scope()
    
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable, "The successful EGR realization setup should be satisfiable"
    assert not interrupted, "Solver should not be interrupted"
    
    # Verify strat_A is in scope for market_strategy (no attacks, so it should be accepted)
    assert "scope(strat_A,market_strategy)" in facts
    
    # Verify EGR is achieved
    assert "egr_scope(strat_A,increase_share,market_strategy)" in facts


def test_egr_failure_not_in_scope():
    """
    Test that EGR fails if the argument, despite its claim, is not accepted (in scope) for the
    relevant domain. This covers the crucial 'claim made but argument defeated' use case.
    """
    initial_part = r"""
    % Domain Elements (U_D)
    domain_element(d_report).
    
    % Goal Primitives (U_G)
    goal_primitive(g_accuracy).
    
    % Arguments
    argument(arg_report).
    argument(arg_critique).
    
    % Prior Domain Assignment (D_pi)
    prior_domain(arg_report, d_report).
    prior_domain(arg_critique, d_report).
    
    % Goal Coverage Claim (C)
    goal_coverage_claim(arg_report, g_accuracy, d_report).
    
    % Attacks
    attacks(arg_critique, arg_report).
    
    % Teams
    team(report_team).
    team(critique_team).
    team_of(arg_report, report_team).
    team_of(arg_critique, critique_team).
    """
    
    asp_program = initial_part + "\n" + get_egr_rules_with_scope()
    
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable, "The EGR failure due to not in scope setup should be satisfiable"
    assert not interrupted, "Solver should not be interrupted"
    
    # Verify arg_critique is in scope for d_report (unchallenged)
    assert "scope(arg_critique,d_report)" in facts
    
    # Verify arg_report is NOT in scope for d_report (attacked by arg_critique)
    assert "scope(arg_report,d_report)" not in facts
    
    # Verify EGR is NOT achieved (since arg_report is not in scope)
    assert "egr_scope(arg_report,g_accuracy,d_report)" not in facts


def test_egr_failure_no_claim_made():
    """
    Test that EGR fails if the argument does not explicitly claim to cover the goal in the
    specific domain, even if the argument is accepted for that domain. This covers the
    'argument accepted but no relevant teleological claim' use case.
    """
    initial_part = r"""
    % Domain Elements (U_D)
    domain_element(d_tech).
    
    % Goal Primitives (U_G)
    goal_primitive(g_innovate).
    
    % Argument
    argument(arg_idea).
    
    % Prior Domain Assignment (D_pi)
    prior_domain(arg_idea, d_tech).
    
    % Crucially, NO goal_coverage_claim is defined
    % goal_coverage_claim(arg_idea, g_innovate, d_tech). % INTENTIONALLY OMITTED
    
    % Team
    team(innovation_team).
    team_of(arg_idea, innovation_team).
    """
    
    asp_program = initial_part + "\n" + get_egr_rules_with_scope()
    
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable, "The EGR failure due to no claim setup should be satisfiable"
    assert not interrupted, "Solver should not be interrupted"
    
    # Verify arg_idea is in scope for d_tech (no attacks, so it should be accepted)
    assert "scope(arg_idea,d_tech)" in facts
    
    # Verify NO goal_coverage_claim exists
    gcc_facts = [f for f in facts if f.startswith("goal_coverage_claim(arg_idea")]
    assert len(gcc_facts) == 0, "No goal coverage claims should exist for arg_idea"
    
    # Verify EGR is NOT achieved (no claim made)
    assert "egr_scope(arg_idea,g_innovate,d_tech)" not in facts


def get_egr_rules_with_scope():
    """
    Return ASP rules for computing scopes and EGR
    """
    return r"""
    % AAFD Scope Determination (simplified complete semantics)
    { scope(A, D) : domain_element(D) } :- argument(A).
    
    % Domain Capping
    :- scope(A, D), not prior_domain(A, D).
    
    % Conflict-Free
    :- attacks(A1, A2), scope(A1, D), scope(A2, D).
    
    % Admissibility helpers
    % Only define these rules when attacks exist
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
    
    % Admissibility constraint
    :- scope(A, D), not acceptable_in_domain(A, D).
    
    % Completeness
    :- acceptable_in_domain(A, D), not scope(A, D).
    
    % EGR (Effective Goal Realization) Rules
    % An argument A effectively realizes goal G for domain D if:
    % 1. A claims to cover G for D (goal_coverage_claim)
    % 2. A is in scope for D
    egr_scope(A, G, D) :- 
        goal_coverage_claim(A, G, D),
        scope(A, D).
    
    % Suppress warnings by defining atoms that might not have facts
    % These are optional - only used if they appear in facts
    attacks(dummy1, dummy2) :- #false.
    goal_coverage_claim(dummy1, dummy2, dummy3) :- #false.
    
    % Suppress warnings by defining atoms that might not have facts
    % These are optional - only used if they appear in facts
    attacks(dummy1, dummy2) :- #false.
    goal_coverage_claim(dummy1, dummy2, dummy3) :- #false.
    
    % Show results
    #show scope/2.
    #show egr_scope/3.
    #show goal_coverage_claim/3.
    """


if __name__ == "__main__":
    test_egr_successful_realization()
    print("✓ Successful EGR realization test passed")
    
    test_egr_failure_not_in_scope()
    print("✓ EGR failure due to not in scope test passed")
    
    test_egr_failure_no_claim_made()
    print("✓ EGR failure due to no claim test passed")
    
    print("\nAll Component 3 tests passed!")
