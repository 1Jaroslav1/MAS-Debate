from solver import ASPSolver


def test_team_assignment():
    """
    Test a team assignment problem where tasks must be assigned to persons.

    The ASP program defines three persons and three tasks. Each task is assigned to exactly one person,
    with the constraint that no person can have more than two tasks.
    """
    asp_program = """
    % Define persons and tasks.
    person(alice; bob; charlie).
    task(t1; t2; t3).

    % Each task is assigned to exactly one person.
    { assign(P, T) : person(P) } = 1 :- task(T).

    % Constraint: Each person can have at most two tasks.
    :- person(P), 3 { assign(P, T) : task(T) }.

    #show assign/2.
    """
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    print("=== Team Assignment Test ===")
    print("Facts:", facts)
    print("Interrupted:", interrupted)
    print("Satisfiable:", satisfiable)
    print()


def test_graph_coloring():
    """
    Test a graph coloring problem for a simple graph.

    The ASP program defines four nodes and three colors. Each node is colored with exactly one color,
    and adjacent nodes (defined by edges) must have different colors.
    """
    asp_program = """
    % Graph Coloring: Define nodes and colors.
    node(1..4).
    color(red; blue; green).

    % Each node gets exactly one color.
    { color(N, C) : color(C) } = 1 :- node(N).

    % Define edges.
    edge(1,2). edge(2,3). edge(3,4). edge(4,1).

    % Constraint: Adjacent nodes must have different colors.
    :- edge(N1,N2), color(N1, C), color(N2, C).

    #show color/2.
    """
    asp_program = """
        product_request(apple, 3).

        % guess selection of products
        {select(P,W,Q',S) : Q' = 1..@min(Q,R), S = Q-Q'} <= 1 :-
          product_request(P,R),
          product_price(P,W,PP),
          warehouse(W),
          warehouse_shipping_cost(W,C),
          product_in_warehouse(P,W,Q).
        
        % select the correct amount of products
        :- product_request(P,R), #sum{Q,W : select(P,W,Q,_)} != R.
        
        % minimize shipping cost
        :~ warehouse_shipping_cost(W,C),
          warehouse_free_shipping(W,T),
          select(_,W,Q,_), Q > 0,
          #sum{Q' * Price,P : select(P,W,Q',_), product_price(P,W,Price)} < T.
          [C@3, W]
        
        #show select/4.
        """
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)
    print("=== Graph Coloring Test ===")
    print("Facts:", facts)
    print("Interrupted:", interrupted)
    print("Satisfiable:", satisfiable)
    print()


def test_debate_next_move():
    """
    Test debate scenario where arguments from our proposition team and the opposition are provided.

    The ASP program defines:
      - A debate topic "renewable_energy" with three subtopics.
      - Audience interests for each subtopic.
      - Two proposition arguments and three opposition arguments with their intended domains.
      - Attack relations where opposition arguments attack our team’s arguments.
      - Simulated final scopes after attacks.

    Coverage analysis then checks which subtopics are not covered by our proposition team.
    In this scenario, our team loses coverage on "solar" (which is high interest) so the next move is to introduce
    a new argument on "solar".
    """
    asp_program = """
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % STEP 1. INITIAL FACTS: Topic, Domain Elements, Audience Interest
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    % Overall debate topic.
    topic(renewable_energy).

    % Domain elements (subtopics).
    domain_element(solar).
    domain_element(wind).
    domain_element(geo).

    % Audience interest for each domain element.
    interest(solar, 5).
    interest(wind, 10).
    interest(geo, 1).

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % STEP 2. DEBATE ARGUMENT FACTS
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    % Define arguments.
    argument(arg1).  % Proposition argument 1
    argument(arg2).  % Proposition argument 2
    argument(arg3).  % Opposition argument 3
    argument(arg4).  % Opposition argument 4
    argument(arg5).  % Opposition argument 5

    % Define team affiliation.
    team(arg1, proposition).
    team(arg2, proposition).
    team(arg3, opposition).
    team(arg4, opposition).
    team(arg5, opposition).

    % Intended domain assignments for proposition arguments.
    domain(arg1, solar).
    domain(arg1, wind).

    domain(arg2, wind).
    domain(arg2, geo).

    % Intended domain assignments for opposition arguments.
    domain(arg3, solar).

    domain(arg4, wind).

    domain(arg5, geo).
    domain(arg5, solar).

    % Attack relations: Opposition attacks our arguments.
    attacks(arg3, arg1).  % arg3 attacks arg1 on solar.
    attacks(arg4, arg2).  % arg4 attacks arg2 on wind.
    attacks(arg5, arg1).  % arg5 attacks arg1 on wind.

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % STEP 3. SIMULATED SCOPE ASSIGNMENTS (POST-ATTACK STATE)
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    % For proposition arguments: simulate that arg1 loses solar (attacked) and only covers wind,
    % and arg2 loses wind (attacked) and only covers geo.
    scope(arg1, wind).
    scope(arg2, geo).

    % Opposition arguments keep their intended domains.
    scope(arg3, solar).
    scope(arg4, wind).
    scope(arg5, solar).
    scope(arg5, geo).

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % STEP 4. TEAM-SPECIFIC COVERAGE ANALYSIS
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    % A subtopic U is covered by team T if any argument from team T has U in its scope.
    covered_by_team(U, T) :- argument(A), team(A, T), scope(A, U).

    % A subtopic U is uncovered by team proposition if it is defined but not covered by any proposition argument.
    uncovered_by_team(U, proposition) :- domain_element(U), not covered_by_team(U, proposition).

    % Define high interest as any subtopic with interest >= 5.
    high_interest(U) :- interest(U, I), I >= 5.

    % For the proposition team, they need a new argument on U if U is uncovered and U is high interest.
    need_new_argument_team(U, proposition) :- uncovered_by_team(U, proposition), high_interest(U).

    % Next move for the proposition team: introduce a new argument on subtopic U.
    next_move_team(introduce_new_argument, U, proposition) :- need_new_argument_team(U, proposition).

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % STEP 5. OUTPUT DIRECTIVES
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    #show next_move_team/3.
    """
    # Create an instance of the ASP solver (using a hypothetical ASPSolver interface)
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)

    print("=== Debate Next Move Test ===")
    print("Facts:", facts)
    print("Interrupted:", interrupted)
    print("Satisfiable:", satisfiable)
    print()


def test_advanced_debate_next_move():
    asp_program = r"""
    topic(renewable_energy).

    domain_element(solar).
    domain_element(wind).
    domain_element(geo).

    interest(solar, 5).
    interest(wind, 10).
    interest(geo, 1).

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

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    attack_count(A, U, Count) :- 
        team(A, proposition), 
        domain(A, U), 
        Count = #count { B : argument(B), team(B, opposition), domain(B, U) }.

    % An argument A effectively accepts subtopic U with effective acceptance EA if:
    % EA = interest(U) - (number of opposition arguments covering U), and EA must be positive.
    effective_acceptance(A, U, EA) :- 
        attack_count(A, U, Count), 
        interest(U, I), 
        EA = I - Count, 
        EA > 0.

    % Define the computed scope for argument A as those subtopics for which it has effective acceptance.
    scope(A, U) :- effective_acceptance(A, U, _).

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    accepted(A, U, EA) :- effective_acceptance(A, U, EA).

    lost(A, U, I) :- domain(A, U), interest(U, I), not effective_acceptance(A, U, _).

    total_accepted(A, Sum) :- Sum = #sum { EA, U : accepted(A, U, EA) }.

    total_lost(A, Sum) :- Sum = #sum { I, U : lost(A, U, I) }.

    arg_strength(A, Strength) :- total_accepted(A, TA), total_lost(A, TL), Strength = TA - TL.

    covered_by_team(U, proposition) :- argument(A), team(A, proposition), effective_acceptance(A, U, _).

    uncovered_by_team(U, proposition) :- domain_element(U), not covered_by_team(U, proposition).

    high_interest(U) :- interest(U, I), I >= 5.

    team_strength(U, Sum) :- 
         Sum = #sum { S, A : team(A, proposition), effective_acceptance(A, U, S) }.

    next_move_team(introduce_new_argument, U, proposition) :- 
         uncovered_by_team(U, proposition), high_interest(U).


    next_move_team(strengthen_existing_argument, U, proposition) :- 
         covered_by_team(U, proposition), high_interest(U), 
         team_strength(U, TS), interest(U, I), TS < I.

    #show next_move_team/3.
    """
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)

    print("Facts:", facts)
    print("Interrupted:", interrupted)
    print("Satisfiable:", satisfiable)
    print()

def test_advanced_debate_next_move_2():
    asp_program = r"""
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

argument(arg1).  % Proposition argument 1
argument(arg2).  % Proposition argument 2
argument(arg3).  % Opposition argument 3
argument(arg4).  % Opposition argument 4
argument(arg5).  % Opposition argument 5

team(arg1, proposition).
team(arg2, proposition).
team(arg3, opposition).
team(arg4, opposition).
team(arg5, opposition).

% Intended domain assignments:
domain(arg1, solar).
domain(arg1, wind).

domain(arg2, wind).
domain(arg2, geo).

domain(arg3, solar).

domain(arg4, wind).

domain(arg5, geo).
domain(arg5, solar).

% Attack relations (each opposition argument attacks any proposition argument sharing a subtopic):
attacks(arg3, arg1).
attacks(arg4, arg1).
attacks(arg4, arg2).
attacks(arg5, arg1).
attacks(arg5, arg2).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STEP 3. PURE AAFD: COMPUTE SCOPES
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Generate all possible assignments of subtopics to each argument.
{ scope(A, U) : domain_element(U) } :- argument(A).

% Compliant scope: An argument may only cover elements in its intended domain.
:- scope(A, U), not domain(A, U).

% Conflict-free scope: Two arguments that attack each other may not share the same subtopic.
:- attacks(A1, A2), scope(A1, U), scope(A2, U).

% Admissibility:
argumentGetsAttackOn(A, U, B) :- domain(A, U), attacks(B, A), domain(B, U).
defendedFrom(A, U, B) :- argumentGetsAttackOn(A, U, B), attacks(C, B), scope(C, U).
notAcceptable(A, U) :- argumentGetsAttackOn(A, U, B), not defendedFrom(A, U, B).
acceptable(A, U) :- domain(A, U), not notAcceptable(A, U).
:- scope(A, U), not acceptable(A, U).

% Completeness: If a subtopic is acceptable for an argument, it must be included in its scope.
:- domain(A, U), acceptable(A, U), not scope(A, U).

% (Optional) Grounded, Preferred, and Stable scopes could be defined here;
% for our purposes we assume that the above constraints yield the “final” (e.g. grounded) scope.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STEP 4. TEAM-SPECIFIC COVERAGE ANALYSIS & NEXT MOVE DECISION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% A subtopic U is covered by team T if any argument from T has U in its computed scope.
covered_by_team(U, T) :- argument(A), team(A, T), scope(A, U).

% A subtopic is uncovered (for the proposition team) if no proposition argument covers it.
uncovered_by_team(U, proposition) :- domain_element(U), not covered_by_team(U, proposition).

% Define high interest as any subtopic with interest >= 5.
high_interest(U) :- interest(U, I), I >= 5.

% (Optional: You might compute a “strength” measure here.
% For example, one simple measure is to sum the interests of subtopics covered by a proposition argument.)
team_strength(U, Sum) :- domain_element(U), 
         Sum = #sum { I, A : argument(A), team(A, proposition), scope(A, U), interest(U, I) }.

% Next move decision using pure AAFD computed scopes:
% (1) If a high-interest subtopic is uncovered by the proposition team, introduce a new argument.
next_move_team(introduce_new_argument, U, proposition) :- 
         uncovered_by_team(U, proposition), high_interest(U).

% (2) If a high-interest subtopic is covered but the aggregated team strength is lower than the audience interest,
% then the move is to strengthen the existing argument.
next_move_team(strengthen_existing_argument, U, proposition) :- 
         covered_by_team(U, proposition), high_interest(U), 
         team_strength(U, TS), interest(U, I), TS < I.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STEP 5. OUTPUT DIRECTIVES
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#show next_move_team/3.
    """
    solver = ASPSolver(timeout=10)
    facts, interrupted, satisfiable = solver.solve(asp_program)

    print("Facts:", facts)
    print("Interrupted:", interrupted)
    print("Satisfiable:", satisfiable)
    print()


if __name__ == "__main__":
    # test_team_assignment()
    # test_graph_coloring()
    test_debate_next_move()
    test_advanced_debate_next_move_2()
