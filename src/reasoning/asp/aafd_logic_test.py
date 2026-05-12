from solver import ASPSolver
from aadf_logic import AAFD_CORE_LOGIC

def test_no_arguments():
    initial_part = r"""
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % STEP 1. INITIAL FACTS: Topic, Domain Elements, Audience Interest
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    topic(renewable_energy).

    domain_element(solar).
    domain_element(wind).
    domain_element(geo).

    interest(solar, 5).
    interest(wind, 10).
    interest(geo, 1).

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % STEP 2. DEBATE ARGUMENT FACTS
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % No arguments defined in this initial test.
    """
    asp_program = initial_part + "\n" + AAFD_CORE_LOGIC

    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)

    print("Facts:", facts)
    print("Interrupted:", interrupted)
    print("Satisfiable:", satisfiable)
    print()



def test_strength_current_arguments():
    initial_part = r"""
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % STEP 1. INITIAL FACTS: Topic, Domain Elements, Audience Interest
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        topic(renewable_energy).
    
        domain_element(solar).
        domain_element(wind).
        domain_element(geo).
    
        interest(solar, 7).
        interest(wind, 10).
        interest(geo, 3).
    
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % STEP 2. DEBATE ARGUMENT FACTS
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        argument(arg1).
        team(arg1, proposition).
    
        domain(arg1, solar).
        domain(arg1, wind).
    
        % Force arg1 to include both
        scope(arg1, solar).
        scope(arg1, wind).
    
        argument(arg2).
        argument(arg3).
        team(arg2, opposition).
        team(arg3, opposition).
    
        domain(arg2, solar).
        domain(arg3, solar).
    
        attacks(arg2, arg1).
        attacks(arg3, arg1).
    """
    asp_program = initial_part + "\n" + AAFD_CORE_LOGIC_PARTIAL

    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)

    print("Facts:", facts)
    print("Interrupted:", interrupted)
    print("Satisfiable:", satisfiable)
    print()


def test_advanced_debate_next_move():
    initial_part = r"""
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % STEP 1. INITIAL FACTS: Topic, Domain Elements, Audience Interest
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        topic(renewable_energy).

        domain_element(solar).
        domain_element(wind).
        domain_element(geo).

        interest(solar, 5).
        interest(wind, 10).
        interest(geo, 1).

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % STEP 2. DEBATE ARGUMENT FACTS
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        argument(arg1).
        argument(arg2).
        argument(arg3).
        argument(arg4).
        argument(arg5).

        team(arg1, proposition).
        team(arg2, proposition).
        team(arg3, opposition).
        team(arg4, opposition).
        team(arg5, opposition).

        domain(arg1, solar).
        domain(arg1, wind).

        domain(arg2, wind).
        domain(arg2, geo).

        domain(arg3, solar).

        domain(arg4, wind).

        domain(arg5, geo).
        domain(arg5, solar).

        attacks(arg3, arg1).
        attacks(arg4, arg1).
        attacks(arg4, arg2).
        attacks(arg5, arg1).
        attacks(arg5, arg2).
    """

    asp_program = initial_part + "\n" + AAFD_CORE_LOGIC_PARTIAL

    solver = ASPSolver(timeout=20)
    facts, interrupted, satisfiable = solver.solve(asp_program)

    print("Facts:", facts)
    print("Interrupted:", interrupted)
    print("Satisfiable:", satisfiable)
    print()

def test_new_logic():
    asp_program = NEW_CORE_LOGIC_PARTIAL

    solver = ASPSolver(timeout=20)
    facts, interrupted, satisfiable = solver.solve(asp_program)

    print("Facts:", facts)
    print("Interrupted:", interrupted)
    print("Satisfiable:", satisfiable)
    print()

if __name__ == "__main__":
    # test_no_arguments()
    # test_strength_current_arguments()
    # test_advanced_debate_next_move()
    test_new_logic()
