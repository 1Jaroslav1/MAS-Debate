"""
Test Component 1: Foundational Elements Setup
Covers: U_D, U_G, A, R, D_π, C, U_RB, U_Act, U_Team, Members, TeamOf, IGI, IDS, and the derivation of P_G, S_D
"""

from src.reasoning.asp.solver import ASPSolver

def test_foundational_minimal():
    """
    Test the framework's ability to initialize with the most basic, minimal set of entities
    and correctly derive initial aggregate values (P_G, S_D) from singular audience inputs.
    This covers the 'empty' or 'starting state' use case for the foundational data structures.
    """
    initial_part = r"""
    % Domain Elements (U_D) 
    domain_element(climate_change).
    
    % Goal Primitives (U_G)
    goal_primitive(reduce_carbon_footprint).
    
    % Arguments (A is empty in this minimal setup)
    
    % Attacks (R is empty)
    
    % Relevance Bearers (U_RB)
    relevance_bearer(environmentalist_A).
    
    % Primitive Actors (U_Act)
    primitive_actor(expert_X).
    
    % Teams (U_Team)
    team(pro_environment).
    team_composition(pro_environment, expert_X).
    
    % Individual Goal Interest (IGI)
    igi(environmentalist_A, reduce_carbon_footprint, climate_change, 1).
    
    % Individual Domain Salience (IDS)
    ids(environmentalist_A, climate_change, 1).
    """
    
    asp_program = initial_part + "\n" + get_foundational_asp_rules()
    
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable, "The minimal foundational setup should be satisfiable"
    assert not interrupted, "Solver should not be interrupted for minimal setup"
    
    # Verify derived values
    assert "pg(reduce_carbon_footprint,climate_change,1)" in facts
    assert "sd(climate_change,1)" in facts
    
    # Verify all basic entities are present
    assert "domain_element(climate_change)" in facts
    assert "goal_primitive(reduce_carbon_footprint)" in facts
    assert "relevance_bearer(environmentalist_A)" in facts
    assert "primitive_actor(expert_X)" in facts
    assert "team(pro_environment)" in facts


def test_foundational_multiple_elements():
    """
    Test the correct representation and interaction of a typical, moderately complex debate setup.
    Key use cases include handling multiple arguments with claims and attacks, multiple relevance
    bearers with graded interests/saliences, and the accurate aggregation of these into P_G and S_D values.
    """
    initial_part = r"""
    % Domain Elements (U_D)
    domain_element(urban_planning).
    domain_element(public_transport).
    
    % Goal Primitives (U_G)
    goal_primitive(increase_sustainability).
    goal_primitive(improve_accessibility).
    
    % Arguments (A)
    argument(arg_sustain).
    argument(arg_access).
    argument(arg_counter).
    
    % Teams (U_Team)
    team(city_planners).
    team(transport_critics).
    
    % Primitive Actors (U_Act)
    primitive_actor(planner1).
    primitive_actor(critic1).
    
    % Team Composition (Members)
    team_composition(city_planners, planner1).
    team_composition(transport_critics, critic1).
    
    % Team Assignment (TeamOf)
    team_of(arg_sustain, city_planners).
    team_of(arg_access, city_planners).
    team_of(arg_counter, transport_critics).
    
    % Prior Domain Assignment (D_π)
    prior_domain(arg_sustain, urban_planning).
    prior_domain(arg_access, public_transport).
    prior_domain(arg_counter, urban_planning).
    
    % Goal Coverage Claim (C)
    goal_coverage_claim(arg_sustain, increase_sustainability, urban_planning).
    goal_coverage_claim(arg_access, improve_accessibility, public_transport).
    
    % Attack Relation (R)
    attacks(arg_counter, arg_sustain).
    
    % Relevance Bearers (U_RB)
    relevance_bearer(citizen_jane).
    relevance_bearer(commuter_john).
    
    % IGI
    igi(citizen_jane, increase_sustainability, urban_planning, 3).
    igi(commuter_john, improve_accessibility, public_transport, 5).
    igi(citizen_jane, improve_accessibility, public_transport, 2).
    
    % IDS
    ids(citizen_jane, urban_planning, 4).
    ids(commuter_john, public_transport, 5).
    ids(citizen_jane, public_transport, 3).
    """
    
    asp_program = initial_part + "\n" + get_foundational_asp_rules()
    
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable, "The multiple elements setup should be satisfiable"
    assert not interrupted, "Solver should not be interrupted"
    
    # Verify P_G aggregation
    assert "pg(increase_sustainability,urban_planning,3)" in facts
    assert "pg(improve_accessibility,public_transport,7)" in facts  # 5 + 2
    
    # Verify S_D aggregation
    assert "sd(urban_planning,4)" in facts
    assert "sd(public_transport,8)" in facts  # 5 + 3
    
    # Verify attack relation
    assert "attacks(arg_counter,arg_sustain)" in facts
    
    # Verify team assignments
    assert "team_of(arg_sustain,city_planners)" in facts
    assert "team_of(arg_counter,transport_critics)" in facts


def test_foundational_complex_claims_teams():
    """
    Test the framework's capacity to manage more intricate scenarios, such as multiple actors per team,
    arguments from different teams making similar or conflicting claims, and diverse audience valuations
    affecting P_G and S_D aggregation. This tests the robustness of foundational data handling in complex situations.
    """
    initial_part = r"""
    % Domain Elements (U_D)
    domain_element(renewable_tech).
    domain_element(economic_impact).
    
    % Goal Primitives (U_G)
    goal_primitive(achieve_energy_independence).
    goal_primitive(ensure_affordability).
    
    % Arguments
    argument(arg_solar_pro).
    argument(arg_wind_pro).
    argument(arg_fossil_lobby).
    
    % Primitive Actors (U_Act)
    primitive_actor(solar_expert).
    primitive_actor(wind_analyst).
    primitive_actor(econ_consultant).
    primitive_actor(lobbyist).
    
    % Teams
    team(green_initiative).
    team(economic_stability_front).
    
    % Team Composition
    team_composition(green_initiative, solar_expert).
    team_composition(green_initiative, wind_analyst).
    team_composition(economic_stability_front, econ_consultant).
    team_composition(economic_stability_front, lobbyist).
    
    % Team Assignment
    team_of(arg_solar_pro, green_initiative).
    team_of(arg_wind_pro, green_initiative).
    team_of(arg_fossil_lobby, economic_stability_front).
    
    % Prior Domain Assignment (D_π)
    prior_domain(arg_solar_pro, renewable_tech).
    prior_domain(arg_solar_pro, economic_impact).
    prior_domain(arg_wind_pro, renewable_tech).
    prior_domain(arg_fossil_lobby, economic_impact).
    
    % Goal Coverage Claims (C)
    goal_coverage_claim(arg_solar_pro, achieve_energy_independence, renewable_tech).
    goal_coverage_claim(arg_solar_pro, ensure_affordability, economic_impact).
    goal_coverage_claim(arg_wind_pro, achieve_energy_independence, renewable_tech).
    goal_coverage_claim(arg_fossil_lobby, ensure_affordability, economic_impact).
    
    % Attacks
    attacks(arg_fossil_lobby, arg_solar_pro).
    attacks(arg_fossil_lobby, arg_wind_pro).
    
    % Relevance Bearers (U_RB)
    relevance_bearer(consumer_watchdog).
    relevance_bearer(industry_rep).
    
    % IGI - Varied and potentially conflicting interests
    igi(consumer_watchdog, achieve_energy_independence, renewable_tech, 4).
    igi(consumer_watchdog, ensure_affordability, economic_impact, 5).
    igi(consumer_watchdog, ensure_affordability, renewable_tech, 2).
    igi(industry_rep, achieve_energy_independence, renewable_tech, 3).
    igi(industry_rep, ensure_affordability, economic_impact, 4).
    igi(industry_rep, achieve_energy_independence, economic_impact, 1).
    
    % IDS - Diverse saliences
    ids(consumer_watchdog, renewable_tech, 5).
    ids(consumer_watchdog, economic_impact, 4).
    ids(industry_rep, renewable_tech, 3).
    ids(industry_rep, economic_impact, 5).
    """
    
    asp_program = initial_part + "\n" + get_foundational_asp_rules()
    
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    
    assert satisfiable, "The complex claims and teams setup should be satisfiable"
    assert not interrupted, "Solver should not be interrupted"
    
    # Verify P_G aggregation with multiple bearers and interests
    assert "pg(achieve_energy_independence,renewable_tech,7)" in facts  # 4 + 3
    assert "pg(ensure_affordability,economic_impact,9)" in facts  # 5 + 4
    assert "pg(ensure_affordability,renewable_tech,2)" in facts
    assert "pg(achieve_energy_independence,economic_impact,1)" in facts
    
    # Verify S_D aggregation
    assert "sd(renewable_tech,8)" in facts  # 5 + 3
    assert "sd(economic_impact,9)" in facts  # 4 + 5
    
    # Verify multiple team members
    team_members = [f for f in facts if f.startswith("team_composition(green_initiative")]
    assert len(team_members) == 2
    
    # Verify overlapping claims from same team
    solar_claims = [f for f in facts if f.startswith("goal_coverage_claim(arg_solar_pro")]
    assert len(solar_claims) == 2
    
    # Verify attacks from different teams
    assert "attacks(arg_fossil_lobby,arg_solar_pro)" in facts
    assert "attacks(arg_fossil_lobby,arg_wind_pro)" in facts


def get_foundational_asp_rules():
    """
    Return the ASP rules for computing P_G and S_D from IGI and IDS
    """
    return r"""
    % Compute Goal Profile (P_G) - aggregating IGI across relevance bearers
    pg(G, D, Sum) :- 
        goal_primitive(G), 
        domain_element(D),
        Sum = #sum { Interest, RB : igi(RB, G, D, Interest), relevance_bearer(RB) }.
    
    % Compute Domain Salience (S_D) - aggregating IDS across relevance bearers
    sd(D, Sum) :- 
        domain_element(D),
        Sum = #sum { Salience, RB : ids(RB, D, Salience), relevance_bearer(RB) }.
    
    % Show all facts for verification
    #show domain_element/1.
    #show goal_primitive/1.
    #show argument/1.
    #show attacks/2.
    #show relevance_bearer/1.
    #show primitive_actor/1.
    #show team/1.
    #show team_composition/2.
    #show team_of/2.
    #show prior_domain/2.
    #show goal_coverage_claim/3.
    #show igi/4.
    #show ids/3.
    #show pg/3.
    #show sd/2.
    """


if __name__ == "__main__":
    test_foundational_minimal()
    print("✓ Minimal foundational setup test passed")
    
    test_foundational_multiple_elements()
    print("✓ Multiple elements test passed")
    
    test_foundational_complex_claims_teams()
    print("✓ Complex claims and teams test passed")
    
    print("\nAll Component 1 tests passed!")
