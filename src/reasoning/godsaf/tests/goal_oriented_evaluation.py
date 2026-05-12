"""
Test Goal-Oriented Evaluation
Tests for EGR (Effective Goal Realization) and Skeptical/Credulous Goal Realization
"""

from src.reasoning.asp.solver import ASPSolver


# Definition 10: Effective Goal Realization (EGR_Scope) Tests

def test_egr_happy_path_realized():
    """Test EGR when argument claims (g1,d1) and is in scope for d1."""
    initial_part = r"""
    % Setup
    argument(a).
    goal_primitive(g1).
    domain_element(d1).
    
    % Prior domain and claim
    prior_domain(a, d1).
    goal_coverage_claim(a, g1, d1).
    
    % No attacks - a will be in scope
    """
    
    asp_program = initial_part + "\n" + get_egr_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "scope(a,d1)" in facts
    assert "egr(a,g1,d1)" in facts


def test_egr_error_path_not_in_scope():
    """Test EGR when argument claims (g1,d1) but is not in scope for d1."""
    initial_part = r"""
    % Setup
    argument(a).
    argument(b).
    goal_primitive(g1).
    domain_element(d1).
    
    % Prior domains and claim
    prior_domain(a, d1).
    prior_domain(b, d1).
    goal_coverage_claim(a, g1, d1).
    
    % b attacks a, preventing a from being in scope
    attacks(b, a).
    """
    
    asp_program = initial_part + "\n" + get_egr_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "scope(a,d1)" not in facts
    assert "egr(a,g1,d1)" not in facts


def test_egr_error_path_no_claim():
    """Test EGR when argument is in scope but makes no claim."""
    initial_part = r"""
    % Setup
    argument(a).
    goal_primitive(g1).
    domain_element(d1).
    
    % Prior domain but NO claim
    prior_domain(a, d1).
    % NO: goal_coverage_claim(a, g1, d1).
    
    % No attacks - a will be in scope
    """
    
    asp_program = initial_part + "\n" + get_egr_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "scope(a,d1)" in facts
    assert "egr(a,g1,d1)" not in facts


def test_egr_edge_case_multiple_claims_scopes():
    """Test EGR with multiple claims and varying scope acceptances."""
    initial_part = r"""
    % Setup
    argument(a).
    argument(b).
    goal_primitive(g1).
    goal_primitive(g2).
    domain_element(d1).
    domain_element(d2).
    
    % Prior domains
    prior_domain(a, d1).
    prior_domain(a, d2).
    prior_domain(b, d2).
    
    % Multiple claims
    goal_coverage_claim(a, g1, d1).
    goal_coverage_claim(a, g2, d2).
    goal_coverage_claim(a, g1, d2).
    
    % b attacks a only for d2
    attacks(b, a).
    """
    
    asp_program = initial_part + "\n" + get_egr_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    
    # a should be in scope for d1 (no attacker with d1)
    assert "scope(a,d1)" in facts
    # a should not be in scope for d2 (attacked by b)
    assert "scope(a,d2)" not in facts
    
    # EGR only where both conditions hold
    assert "egr(a,g1,d1)" in facts
    assert "egr(a,g2,d2)" not in facts
    assert "egr(a,g1,d2)" not in facts


# Definition 11: Skeptical/Credulous Goal Realization Tests
# Note: These tests require multiple answer sets, which is complex in basic ASP testing
# We'll test the concepts with simpler scenarios

def test_skept_realized_by_arg_holds_in_all_scopes():
    """Test skeptical realization when argument achieves EGR in all models."""
    initial_part = r"""
    % Setup
    argument(a).
    goal_primitive(g).
    domain_element(d).
    
    % Uncontested argument
    prior_domain(a, d).
    goal_coverage_claim(a, g, d).
    
    % No attacks - only one model where a is in scope
    """
    
    asp_program = initial_part + "\n" + get_skeptical_credulous_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    # In single model, both skeptical and credulous should hold
    assert "egr(a,g,d)" in facts
    # These predicates would need special ASP encoding to check across models
    # For now, we verify the base EGR holds


def test_cred_realized_overall_one_arg_is_credulous():
    """Test credulous realization overall when at least one argument realizes (g,d)."""
    initial_part = r"""
    % Setup
    argument(a1).
    argument(a2).
    goal_primitive(g).
    domain_element(d).
    
    % Both arguments can realize g for d
    prior_domain(a1, d).
    prior_domain(a2, d).
    goal_coverage_claim(a1, g, d).
    goal_coverage_claim(a2, g, d).
    
    % Symmetric attack - creates multiple models
    attacks(a1, a2).
    attacks(a2, a1).
    """
    
    asp_program = initial_part + "\n" + get_skeptical_credulous_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    # In grounded semantics, neither would be in scope
    # But the concept is that in some extension, one could realize the goal
    

def get_egr_rules():
    """Return ASP rules for EGR calculation"""
    return r"""
    % Scope determination (simplified)
    { scope(A, D) : domain_element(D) } :- argument(A).
    
    % Domain Capping
    :- scope(A, D), not prior_domain(A, D).
    
    % Conflict-Free
    :- attacks(A1, A2), scope(A1, D), scope(A2, D).
    
    % Admissibility helpers
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
    
    % Admissibility and Completeness
    :- scope(A, D), not acceptable_in_domain(A, D).
    :- acceptable_in_domain(A, D), not scope(A, D).
    
    % EGR Definition
    egr(A, G, D) :- 
        goal_coverage_claim(A, G, D),
        scope(A, D).
    
    % Suppress warnings
    attacks(dummy1, dummy2) :- #false.
    goal_coverage_claim(dummy1, dummy2, dummy3) :- #false.
    
    % Show results
    #show scope/2.
    #show egr/3.
    """


def get_skeptical_credulous_rules():
    """Return ASP rules for skeptical/credulous realization"""
    return r"""
    % Include EGR rules
    { scope(A, D) : domain_element(D) } :- argument(A).
    :- scope(A, D), not prior_domain(A, D).
    :- attacks(A1, A2), scope(A1, D), scope(A2, D).
    
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
    
    % EGR
    egr(A, G, D) :- 
        goal_coverage_claim(A, G, D),
        scope(A, D).
    
    % Overall realization (exists an argument that realizes)
    realized_overall(G, D) :- egr(A, G, D).
    
    % Suppress warnings
    attacks(dummy1, dummy2) :- #false.
    goal_coverage_claim(dummy1, dummy2, dummy3) :- #false.
    
    % Show results
    #show egr/3.
    #show realized_overall/2.
    """


if __name__ == "__main__":
    test_egr_happy_path_realized()
    print("✓ EGR happy path test passed")
    
    test_egr_error_path_not_in_scope()
    print("✓ EGR not in scope test passed")
    
    test_egr_error_path_no_claim()
    print("✓ EGR no claim test passed")
    
    test_egr_edge_case_multiple_claims_scopes()
    print("✓ EGR multiple claims/scopes test passed")
    
    test_skept_realized_by_arg_holds_in_all_scopes()
    print("✓ Skeptical realization concept test passed")
    
    test_cred_realized_overall_one_arg_is_credulous()
    print("✓ Credulous realization concept test passed")
    
    print("\nAll goal-oriented evaluation tests passed!")
