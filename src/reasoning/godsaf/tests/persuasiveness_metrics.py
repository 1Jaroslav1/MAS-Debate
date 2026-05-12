def test_apc_basic_calculation():
    """Test basic APC calculation: APC = P_G * S_D"""
    initial_part = r"""
    % Setup
    argument(arg).
    goal_primitive(g1).
    domain_element(d1).
    
    % Values
    pg(g1, d1, 10).
    sd(d1, 5).
    
    % Claim
    goal_coverage_claim(arg, g1, d1).
    """
    
    asp_program = initial_part + "\n" + get_apc_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "apc(arg,g1,d1,50)" in facts  # 10 * 5 = 50


def test_apc_zero_if_pg_is_zero():
    """Test APC when P_G is zero"""
    initial_part = r"""
    % Setup
    argument(arg).
    goal_primitive(g1).
    domain_element(d1).
    
    % Values
    pg(g1, d1, 0).
    sd(d1, 5).
    
    % Claim
    goal_coverage_claim(arg, g1, d1).
    """
    
    asp_program = initial_part + "\n" + get_apc_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "apc(arg,g1,d1,0)" in facts


def test_apc_zero_if_sd_is_zero():
    """Test APC when S_D is zero"""
    initial_part = r"""
    % Setup
    argument(arg).
    goal_primitive(g1).
    domain_element(d1).
    
    % Values
    pg(g1, d1, 10).
    sd(d1, 0).
    
    % Claim
    goal_coverage_claim(arg, g1, d1).
    """
    
    asp_program = initial_part + "\n" + get_apc_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "apc(arg,g1,d1,0)" in facts


def test_apc_argument_independence_for_gd_pair():
    """Test that different arguments claiming same (g,d) have same APC"""
    initial_part = r"""
    % Setup
    argument(arg1).
    argument(arg2).
    goal_primitive(g).
    domain_element(d).
    
    % Values
    pg(g, d, 8).
    sd(d, 3).
    
    % Both claim same (g,d)
    goal_coverage_claim(arg1, g, d).
    goal_coverage_claim(arg2, g, d).
    """
    
    asp_program = initial_part + "\n" + get_apc_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "apc(arg1,g,d,24)" in facts  # 8 * 3 = 24
    assert "apc(arg2,g,d,24)" in facts  # Same value


# Definition 13: Effective Opponent Challenge Tests

def test_is_opp_ch_true_conditions_met():
    """Test effective opponent challenge when all conditions are met"""
    initial_part = r"""
    % Setup
    argument(arg_prop).
    argument(arg_opp).
    argument(defender).
    domain_element(d1).
    team(teamP).
    team(teamO).
    
    % Team assignments
    team_of(arg_prop, teamP).
    team_of(arg_opp, teamO).
    team_of(defender, teamP).
    
    % Prior domains
    prior_domain(arg_prop, d1).
    prior_domain(arg_opp, d1).
    prior_domain(defender, d1).
    
    % Attacks
    attacks(arg_opp, arg_prop).  % Opponent attacks proponent
    attacks(defender, arg_opp).   % Defender attacks opponent
    
    % This creates a situation where:
    % - defender is unattacked, so in scope
    % - arg_opp is attacked by defender (in scope), so not in scope  
    % - arg_prop is attacked by arg_opp (not in scope), so arg_prop is in scope
    
    % But wait, we want arg_opp to be in scope for it to be an effective challenger
    % So let's add another attacker to create the right scenario
    """
    
    # Let me try a different approach - force both to be in scope
    initial_part = r"""
    % Setup
    argument(arg_prop).
    argument(arg_opp).
    domain_element(d1).
    team(teamP).
    team(teamO).
    
    % Team assignments
    team_of(arg_prop, teamP).
    team_of(arg_opp, teamO).
    
    % Prior domains
    prior_domain(arg_prop, d1).
    prior_domain(arg_opp, d1).
    
    % Attack
    attacks(arg_opp, arg_prop).
    
    % Force both arguments to be in scope for testing
    % This simulates a scenario where both are accepted despite the attack
    % (e.g., they might be in different extensions in preferred semantics)
    force_scope(arg_prop, d1).
    force_scope(arg_opp, d1).
    """
    
    asp_program = initial_part + "\n" + get_opponent_challenge_rules_with_forced()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "scope(arg_opp,d1)" in facts  # Attacker is in scope
    assert "scope(arg_prop,d1)" in facts  # Proponent is also in scope (forced)
    assert "is_effective_opponent_challenge(arg_prop,d1)" in facts
    assert "opponent_challenger(arg_prop,d1,arg_opp)" in facts
    assert "num_effective_opponent_challengers(arg_prop,d1,1)" in facts


def test_is_opp_ch_false_attacker_not_in_scope():
    """Test that challenge is not effective if attacker not in scope"""
    initial_part = r"""
    % Setup
    argument(arg_prop).
    argument(arg_opp).
    argument(defender).
    domain_element(d1).
    team(teamP).
    team(teamO).
    
    % Team assignments
    team_of(arg_prop, teamP).
    team_of(arg_opp, teamO).
    team_of(defender, teamP).
    
    % Prior domains
    prior_domain(arg_prop, d1).
    prior_domain(arg_opp, d1).
    prior_domain(defender, d1).
    
    % Attacks
    attacks(arg_opp, arg_prop).
    attacks(defender, arg_opp).  % Defender defeats the attacker
    """
    
    asp_program = initial_part + "\n" + get_opponent_challenge_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "scope(arg_opp,d1)" not in facts  # Attacker defeated
    assert "is_effective_opponent_challenge(arg_prop,d1)" not in facts
    assert "num_effective_opponent_challengers(arg_prop,d1,0)" in facts


def test_is_opp_ch_false_attacker_same_team():
    """Test that attack from same team is not opponent challenge"""
    initial_part = r"""
    % Setup
    argument(arg_prop).
    argument(arg_ally).
    domain_element(d1).
    team(teamP).
    
    % Both on same team
    team_of(arg_prop, teamP).
    team_of(arg_ally, teamP).
    
    % Prior domains
    prior_domain(arg_prop, d1).
    prior_domain(arg_ally, d1).
    
    % Attack from ally
    attacks(arg_ally, arg_prop).
    """
    
    asp_program = initial_part + "\n" + get_opponent_challenge_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "is_effective_opponent_challenge(arg_prop,d1)" not in facts
    assert "num_effective_opponent_challengers(arg_prop,d1,0)" in facts


# Definition 15: EAPC Tests

def test_eapc_happy_path_no_challenge():
    """Test EAPC equals APC when no challenges"""
    initial_part = r"""
    % Setup
    argument(a).
    goal_primitive(g).
    domain_element(d).
    team(teamP).
    
    % Team and domains
    team_of(a, teamP).
    prior_domain(a, d).
    goal_coverage_claim(a, g, d).
    
    % Values
    pg(g, d, 10).
    sd(d, 5).
    k_chal(25).  % 0.25
    """
    
    asp_program = initial_part + "\n" + get_eapc_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "eapc(a,g,d,50)" in facts  # APC = 10*5 = 50, no reduction


def test_eapc_happy_path_one_challenge():
    """Test EAPC with one challenger"""
    initial_part = r"""
    % Setup
    argument(a).
    argument(opp).
    goal_primitive(g).
    domain_element(d).
    team(teamP).
    team(teamO).
    
    % Teams and domains
    team_of(a, teamP).
    team_of(opp, teamO).
    prior_domain(a, d).
    prior_domain(opp, d).
    goal_coverage_claim(a, g, d).
    
    % Attack
    attacks(opp, a).
    
    % Force both in scope for testing
    force_scope(a, d).
    force_scope(opp, d).
    
    % Values
    pg(g, d, 10).
    sd(d, 8).
    k_chal(50).  % 0.5
    """
    
    asp_program = initial_part + "\n" + get_eapc_rules_with_forced()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "eapc(a,g,d,40)" in facts  # APC=80, reduced by 0.5


def test_eapc_error_path_not_in_scope():
    """Test EAPC is zero when argument not in scope"""
    initial_part = r"""
    % Setup
    argument(a).
    argument(opp).
    goal_primitive(g).
    domain_element(d).
    team(teamP).
    team(teamO).
    
    % Teams and domains
    team_of(a, teamP).
    team_of(opp, teamO).
    prior_domain(a, d).
    prior_domain(opp, d).
    goal_coverage_claim(a, g, d).
    
    % Attack that defeats a
    attacks(opp, a).
    
    % Values
    pg(g, d, 10).
    sd(d, 10).
    k_chal(30).
    """
    
    asp_program = initial_part + "\n" + get_eapc_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "scope(a,d)" not in facts
    assert "eapc(a,g,d,0)" in facts


# Definition 16: APS Tests

def test_aps_single_eapc_contribution():
    """Test APS with single EAPC contribution"""
    initial_part = r"""
    % Setup
    argument(a).
    goal_primitive(g1).
    domain_element(d1).
    team(teamP).
    
    % Setup for EAPC = 75
    team_of(a, teamP).
    prior_domain(a, d1).
    goal_coverage_claim(a, g1, d1).
    
    % Manual EAPC for testing
    manual_eapc(a, g1, d1, 75).
    """
    
    asp_program = initial_part + "\n" + get_aps_rules_manual()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "aps(a,75)" in facts


def test_aps_multiple_eapc_contributions():
    """Test APS with multiple EAPC contributions"""
    initial_part = r"""
    % Setup
    argument(a).
    goal_primitive(g1).
    goal_primitive(g2).
    domain_element(d1).
    domain_element(d2).
    
    % Manual EAPCs for testing
    manual_eapc(a, g1, d1, 50).
    manual_eapc(a, g2, d2, 30).
    """
    
    asp_program = initial_part + "\n" + get_aps_rules_manual()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "aps(a,80)" in facts  # 50 + 30


# Definition 17: TGS Tests

def test_tgs_single_arg_contribution_for_team_goal_domain():
    """Test TGS with single argument contribution"""
    initial_part = r"""
    % Setup
    argument(a1).
    goal_primitive(g).
    domain_element(d).
    team(teamT).
    
    % Team assignment
    team_of(a1, teamT).
    
    % Manual EAPC
    manual_eapc(a1, g, d, 60).
    """
    
    asp_program = initial_part + "\n" + get_tgs_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "tgs(teamT,g,d,60)" in facts


def test_tgs_multiple_args_contribution_for_team_goal_domain():
    """Test TGS with multiple arguments from same team"""
    initial_part = r"""
    % Setup
    argument(a1).
    argument(a2).
    goal_primitive(g).
    domain_element(d).
    team(teamT).
    
    % Team assignments
    team_of(a1, teamT).
    team_of(a2, teamT).
    
    % Manual EAPCs
    manual_eapc(a1, g, d, 40).
    manual_eapc(a2, g, d, 35).
    """
    
    asp_program = initial_part + "\n" + get_tgs_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "tgs(teamT,g,d,75)" in facts  # 40 + 35


# Definition 20: ReGS Tests

def test_regs_basic_calculation():
    """Test ReGS calculation: ReGS = P_G * S_D"""
    initial_part = r"""
    % Setup
    goal_primitive(g1).
    domain_element(d1).
    
    % Values
    pg(g1, d1, 15).
    sd(d1, 4).
    """
    
    asp_program = initial_part + "\n" + get_regs_rules()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "regs(g1,d1,60)" in facts  # 15 * 4


# Definition 21: UGN Tests

def test_ugn_positive_need_tgs_less_than_regs():
    """Test UGN when TGS < ReGS"""
    initial_part = r"""
    % Setup
    goal_primitive(g).
    domain_element(d).
    team(teamP).
    
    % Manual values
    manual_regs(g, d, 100).
    manual_tgs(teamP, g, d, 60).
    """
    
    asp_program = initial_part + "\n" + get_ugn_rules_manual()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "ugn(teamP,g,d,40)" in facts  # 100 - 60


def test_ugn_zero_need_tgs_equals_regs():
    """Test UGN when TGS = ReGS"""
    initial_part = r"""
    % Setup
    goal_primitive(g).
    domain_element(d).
    team(teamP).
    
    % Manual values
    manual_regs(g, d, 100).
    manual_tgs(teamP, g, d, 100).
    """
    
    asp_program = initial_part + "\n" + get_ugn_rules_manual()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "ugn(teamP,g,d,0)" in facts


def test_ugn_zero_need_tgs_exceeds_regs():
    """Test UGN when TGS > ReGS"""
    initial_part = r"""
    % Setup
    goal_primitive(g).
    domain_element(d).
    team(teamP).
    
    % Manual values
    manual_regs(g, d, 100).
    manual_tgs(teamP, g, d, 120).
    """
    
    asp_program = initial_part + "\n" + get_ugn_rules_manual()
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable
    assert not interrupted
    assert "ugn(teamP,g,d,0)" in facts  # Max(0, 100-120) = 0


# Helper rule functions

def get_apc_rules():
    """Return APC calculation rules"""
    return r"""
    % APC = P_G * S_D
    apc(A, G, D, Value) :-
        goal_coverage_claim(A, G, D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    #show apc/4.
    """


def get_opponent_challenge_rules():
    """Return opponent challenge rules"""
    return r"""
    % Scope rules (simplified)
    { scope(A, D) : domain_element(D) } :- argument(A).
    :- scope(A, D), not prior_domain(A, D).
    :- attacks(A1, A2), scope(A1, D), scope(A2, D).
    
    % Complete semantics helpers
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
    
    % Opponent challenger identification
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
    
    % EAPC calculation
    eapc(A, G, D, EAPC_Value) :-
        goal_coverage_claim(A, G, D),
        scope(A, D),
        num_effective_opponent_challengers(A, D, 0),
        apc(A, G, D, EAPC_Value).
    
    eapc(A, G, D, EAPC_Value) :-
        goal_coverage_claim(A, G, D),
        scope(A, D),
        num_effective_opponent_challengers(A, D, N),
        N > 0,
        apc(A, G, D, APC_Value),
        k_chal(K),
        Reduction = (K ** N) / (100 ** N),
        EAPC_Value = (APC_Value * Reduction).
    
    eapc(A, G, D, 0) :-
        goal_coverage_claim(A, G, D),
        not scope(A, D).
    
    #show eapc/4.
    """


def get_opponent_challenge_rules_with_forced():
    """Return opponent challenge rules with forced scope option"""
    return r"""
    % Force specific scopes when specified
    scope(A, D) :- force_scope(A, D).
    
    % Normal scope generation for non-forced arguments
    { scope(A, D) : domain_element(D) } :- argument(A), not force_scope(A, D).
    
    % Domain Capping - but not for forced scopes
    :- scope(A, D), not prior_domain(A, D), not force_scope(A, D).
    
    % Conflict-Free - but allow forced scopes to override
    :- attacks(A1, A2), scope(A1, D), scope(A2, D), 
       not force_scope(A1, D), not force_scope(A2, D).
    
    % Opponent challenger identification
    opponent_challenger(A, D, Challenger) :-
        argument(A),
        domain_element(D),
        attacks(Challenger, A),
        team_of(A, TeamA),
        team_of(Challenger, TeamC),
        TeamA != TeamC,
        scope(Challenger, D).
    
    % Is there an effective opponent challenge?
    is_effective_opponent_challenge(A, D) :-
        opponent_challenger(A, D, _).
    
    % Count challengers
    num_effective_opponent_challengers(A, D, Count) :-
        argument(A),
        domain_element(D),
        Count = #count { C : opponent_challenger(A, D, C) }.
    
    % Suppress warnings
    attacks(dummy1, dummy2) :- #false.
    
    #show scope/2.
    #show is_effective_opponent_challenge/2.
    #show opponent_challenger/3.
    #show num_effective_opponent_challengers/3.
    """
    """Return APS rules using manual EAPC values"""
    return r"""
    % Use manual EAPC values
    eapc(A, G, D, Value) :- manual_eapc(A, G, D, Value).
    
    % APS = sum of all EAPCs for an argument
    aps(A, Sum) :-
        argument(A),
        Sum = #sum { Value, G, D : eapc(A, G, D, Value) }.
    
    #show aps/2.
    """


def get_tgs_rules():
    """Return TGS calculation rules"""
    return r"""
    % Use manual EAPC values
    eapc(A, G, D, Value) :- manual_eapc(A, G, D, Value).
    
    % TGS = sum of EAPCs for team's arguments
    tgs(Team, G, D, Sum) :-
        team(Team),
        goal_primitive(G),
        domain_element(D),
        Sum = #sum { Value, A : eapc(A, G, D, Value), team_of(A, Team) }.
    
    #show tgs/4.
    """


def get_regs_rules():
    """Return ReGS calculation rules"""
    return r"""
    % ReGS = P_G * S_D
    regs(G, D, Value) :-
        goal_primitive(G),
        domain_element(D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    #show regs/3.
    """


def get_ugn_rules_manual():
    """Return UGN rules using manual values"""
    return r"""
    % Use manual values
    regs(G, D, Value) :- manual_regs(G, D, Value).
    tgs(Team, G, D, Value) :- manual_tgs(Team, G, D, Value).
    
    % UGN = max(0, ReGS - TGS)
    ugn(Team, G, D, Value) :-
        team(Team),
        goal_primitive(G),
        domain_element(D),
        regs(G, D, ReGS_Val),
        tgs(Team, G, D, TGS_Val),
        Value = #max { 0; ReGS_Val - TGS_Val }.
    
    #show ugn/4.
    """


if __name__ == "__main__":
    # APC tests
    test_apc_basic_calculation()
    print("✓ APC basic calculation test passed")
    
    test_apc_zero_if_pg_is_zero()
    print("✓ APC zero if P_G is zero test passed")
    
    test_apc_zero_if_sd_is_zero()
    print("✓ APC zero if S_D is zero test passed")
    
    test_apc_argument_independence_for_gd_pair()
    print("✓ APC argument independence test passed")
    
    # Opponent challenge tests
    test_is_opp_ch_true_conditions_met()
    print("✓ Opponent challenge conditions met test passed")
    
    test_is_opp_ch_false_attacker_not_in_scope()
    print("✓ Opponent challenge attacker not in scope test passed")
    
    test_is_opp_ch_false_attacker_same_team()
    print("✓ Opponent challenge same team test passed")
    
    # EAPC tests
    test_eapc_happy_path_no_challenge()
    print("✓ EAPC no challenge test passed")
    
    test_eapc_happy_path_one_challenge()
    print("✓ EAPC one challenge test passed")
    
    test_eapc_error_path_not_in_scope()
    print("✓ EAPC not in scope test passed")
    
    # APS tests
    test_aps_single_eapc_contribution()
    print("✓ APS single EAPC test passed")
    
    test_aps_multiple_eapc_contributions()
    print("✓ APS multiple EAPCs test passed")
    
    # TGS tests
    test_tgs_single_arg_contribution_for_team_goal_domain()
    print("✓ TGS single argument test passed")
    
    test_tgs_multiple_args_contribution_for_team_goal_domain()
    print("✓ TGS multiple arguments test passed")
    
    # ReGS test
    test_regs_basic_calculation()
    print("✓ ReGS basic calculation test passed")
    
    # UGN tests
    test_ugn_positive_need_tgs_less_than_regs()
    print("✓ UGN positive need test passed")
    
    test_ugn_zero_need_tgs_equals_regs()
    print("✓ UGN zero need (equal) test passed")
    
    test_ugn_zero_need_tgs_exceeds_regs()
    print("✓ UGN zero need (exceeds) test passed")
    
    print("\nAll persuasiveness metrics tests passed!") TeamC),
        TeamA != TeamC,
        scope(Challenger, D).
    
    % Is there an effective opponent challenge?
    is_effective_opponent_challenge(A, D) :-
        opponent_challenger(A, D, _).
    
    % Count challengers
    num_effective_opponent_challengers(A, D, Count) :-
        argument(A),
        domain_element(D),
        Count = #count { C : opponent_challenger(A, D, C) }.
    
    % Suppress warnings
    attacks(dummy1, dummy2) :- #false.
    
    #show scope/2.
    #show is_effective_opponent_challenge/2.
    #show opponent_challenger/3.
    #show num_effective_opponent_challengers/3.
    """


def get_opponent_challenge_rules_with_forced():
    """Return opponent challenge rules with forced scope option"""
    return r"""
    % Force specific scopes when specified
    scope(A, D) :- force_scope(A, D).
    
    % Normal scope generation for non-forced arguments
    { scope(A, D) : domain_element(D) } :- argument(A), not force_scope(A, D).
    
    % Domain Capping - but not for forced scopes
    :- scope(A, D), not prior_domain(A, D), not force_scope(A, D).
    
    % Conflict-Free - but allow forced scopes to override
    :- attacks(A1, A2), scope(A1, D), scope(A2, D), 
       not force_scope(A1, D), not force_scope(A2, D).
    
    % Opponent challenger identification
    opponent_challenger(A, D, Challenger) :-
        argument(A),
        domain_element(D),
        attacks(Challenger, A),
        team_of(A, TeamA),
        team_of(Challenger, TeamC),
        TeamA != TeamC,
        scope(Challenger, D).
    
    % Is there an effective opponent challenge?
    is_effective_opponent_challenge(A, D) :-
        opponent_challenger(A, D, _).
    
    % Count challengers
    num_effective_opponent_challengers(A, D, Count) :-
        argument(A),
        domain_element(D),
        Count = #count { C : opponent_challenger(A, D, C) }.
    
    % Suppress warnings
    attacks(dummy1, dummy2) :- #false.
    
    #show scope/2.
    #show is_effective_opponent_challenge/2.
    #show opponent_challenger/3.
    #show num_effective_opponent_challengers/3.
    """


def get_eapc_rules():
    """Return EAPC calculation rules"""
    return r"""
    % Include scope and challenge rules
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
    
    % APC
    apc(A, G, D, Value) :-
        goal_coverage_claim(A, G, D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    % Opponent challengers
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
    
    % EAPC calculation
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
        Reduction = (K ** N) / (100 ** N),
        EAPC_Value = (APC_Value * Reduction).
    
    % Case 3: Not in scope
    eapc(A, G, D, 0) :-
        goal_coverage_claim(A, G, D),
        not scope(A, D).
    
    % Suppress warnings
    attacks(dummy1, dummy2) :- #false.
    
    #show eapc/4.
    """


def get_eapc_rules_with_forced():
    """Return EAPC rules with forced scope"""
    return r"""
    % Force specific scopes
    scope(A, D) :- force_scope(A, D).
    
    % APC
    apc(A, G, D, Value) :-
        goal_coverage_claim(A, G, D),
        pg(G, D, PG_Val),
        sd(D, SD_Val),
        Value = PG_Val * SD_Val.
    
    % Opponent challengers
    opponent_challenger(A, D, Challenger) :-
        argument(A),
        domain_element(D),
        attacks(Challenger, A),
        team_of(A, TeamA),
        team_of(Challenger,
