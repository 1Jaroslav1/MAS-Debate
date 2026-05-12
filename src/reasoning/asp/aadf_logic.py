AAFD_CORE_LOGIC = r"""
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

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STEP 4. TEAM-SPECIFIC COVERAGE ANALYSIS & NEXT MOVE DECISION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% A subtopic U is covered by team T if any argument from T has U in its computed scope.
covered_by_team(U, T) :- argument(A), team(A, T), scope(A, U).

% A subtopic is uncovered (for the proposition team) if no proposition argument covers it.
uncovered_by_team(U, proposition) :- domain_element(U), not covered_by_team(U, proposition).

% New High-Interest Definition:
% Calculate total interest over all domain elements and count them.
total_interest(Total) :- Total = #sum { I, U : domain_element(U), interest(U, I) }.
count_domains(Count) :- Count = #count { U : domain_element(U) }.
% U is high interest if its interest I multiplied by the number of domains is greater than total interest.
    high_interest(U) :- interest(U, I), count_domains(C), total_interest(Total), I * C > Total.

    % (Optional: You might compute a "strength" measure here.
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

NEW_CORE_LOGIC_PARTIAL = r"""
% =============================================================================
% Goal-Aware Abstract Argumentation Framework with Domains (AAFD)
% Extended ASP Core Logic with Goal-Aware Reasoning
% =============================================================================

% --- Domain, Team, Argument, and Goal Facts ----------------------------------
domain(solar, energy).
domain(grid, energy).
domain(public, social).

team(a1, proposition).
team(a2, proposition).
team(b1, opposition).
team(b2, opposition).

scope(a1, solar).
scope(a2, public).
scope(b1, solar).
scope(b2, grid).

interest(solar, 5).
interest(grid, 4).
interest(public, 3).

goal(cost_reduction, solar, 8).
goal(reliability, grid, 7).
goal(awareness, all, 9).
goal(transparency, public, 3).

% Example attack relations
attack(b1, a1).

% --- Goal Coverage Rules -----------------
{ goal_scope(A, G, D) } :- scope(A, D), goal(G, D, _).
{ goal_scope(A, G, D) } :- scope(A, D), goal(G, all, _).

% --- Conflict Restrictions on Goal Coverage ----------------------------------
:- attack(X, Y), goal_scope(X, G, D), goal_scope(Y, G, D).

% --- Strength Computation -----------------
arg_domain_strength(A, I) :- team(A, proposition), scope(A, D), interest(D, I).

arg_goal_strength(A, Sum) :- team(A, proposition), 
    Sum = #sum{ C, G, D : goal_scope(A, G, D), goal(G, D, C) }.

% Fixed the team_strength rule by removing Type variable which was unused
team_strength(D, S) :- domain(D, _),
    S = #sum{ I, A : scope(A, D), team(A, proposition), interest(D, I) }.

goal_strength(G, D, C) :- goal(G, D, C), #count{ A : goal_scope(A, G, D), team(A, proposition) } >= 1.
goal_strength(G, D, 0) :- goal(G, D, _), #count{ A : goal_scope(A, G, D), team(A, proposition) } = 0.

% --- High-Interest Goals Detection -------------------------------------------
total_listeners(T) :- T = #sum{ C, G, D : goal(G, D, C) }.
goal_count(N) :- N = #count{ G, D : goal(G, D, _) }.
high_interest(G, D) :- goal(G, D, C), total_listeners(T), goal_count(N), C * N > T.

% --- Move Recommendations for Proposition Team ------------------------------
next_move_team(proposition, D, G, introduce_new_argument) :- 
    high_interest(G, D),
    goal(G, D, _),
    not (team(A, proposition), scope(A, D)).

next_move_team(proposition, D, G, strengthen_existing_argument) :- 
    high_interest(G, D),
    goal(G, D, _),
    team(A, proposition), scope(A, D),
    #count{ A : goal_scope(A, G, D), team(A, proposition) } = 0.

#show scope/2.
#show goal_scope/3.
#show team_strength/2.
#show goal_strength/3.
#show next_move_team/4.
"""

CORE_LOGIC_PARTIAL = r"""
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STEP 3. PARTIAL-Acceptance AAFD Logic
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% 1) Generate all possible subtopic assignments to each argument.
{ scope(A,U) : domain_element(U) } :- argument(A).

% 2) Compliant scope:
:- scope(A, U), not domain(A, U).

% 3) Conflict-free:
:- attacks(X, Y), scope(X,U), scope(Y,U).

% 4) We comment out strict admissibility / completeness 
%    so that an argument can keep a subtopic even if it's attacked.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STEP 3.5: Compute Effective Contribution (penalty from attacks)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Let penalty(A,U,P) be the number of opposition arguments that attack A on U.
penalty(A,U,P) :- 
    argument(A), team(A, proposition), domain(A,U),
    P = #count { B : argument(B), team(B,opposition), domain(B,U), attacks(B,A) }.

% If an argument covers U, we define its effective_contribution as interest(U) - penalty(A,U,P).
% This can go negative or zero, but we only sum positive contributions in the next step.
effective_contribution(A,U,EC) :- 
    scope(A,U), interest(U,I), penalty(A,U,P),
    EC = I - P, EC>0.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STEP 4. Coverage & Next Move
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% covered_by_team(U, T) if there's an argument from T whose scope includes U
covered_by_team(U,T) :- argument(A), team(A,T), scope(A,U).

uncovered_by_team(U, proposition) :- domain_element(U), not covered_by_team(U, proposition).

% Dynamically compute "high interest" as interest(U)*count_domains > total_interest
total_interest(S)  :- S = #sum { I, X : domain_element(X), interest(X,I) }.
count_domains(N)   :- N = #count { X : domain_element(X) }.
high_interest(U)   :- interest(U,I), count_domains(N), total_interest(T), I*N > T.

% Team strength is the sum of positive effective_contribution for all proposition arguments that cover U.
team_strength(U, Sum) :-
    domain_element(U),
    Sum = #sum { EC,A : argument(A), team(A,proposition), scope(A,U), effective_contribution(A,U,EC) }.

% (1) If a subtopic is uncovered & high interest => introduce argument
next_move_team(introduce_new_argument, U, proposition) :-
    uncovered_by_team(U, proposition),
    high_interest(U).

% (2) If covered & high_interest & strength < interest => strengthen
next_move_team(strengthen_existing_argument, U, proposition) :-
    covered_by_team(U, proposition), high_interest(U),
    team_strength(U, S), interest(U,I),
    S < I.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STEP 5. OUTPUT
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#show next_move_team/3.
"""

AAFD_CORE_LOGIC_PARTIAL = r"""
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STEP 3. PARTIAL-ACCEPTANCE AAFD LOGIC
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Generate possible subtopic assignments for each argument.
{ scope(A, U) : domain_element(U) } :- argument(A).

% Compliant scope
:- scope(A, U), not domain(A, U).

% We REMOVE conflict-free to allow overlapping coverage.

% We also REMOVE the lines that forbid scope(A, U) if notAcceptable(A, U).
% We keep the definitions so we can measure them, but do not enforce them strictly.
argumentGetsAttackOn(A, U, B) :- domain(A, U), attacks(B, A), domain(B, U).
defendedFrom(A, U, B) :- argumentGetsAttackOn(A, U, B), attacks(C, B), scope(C, U).
notAcceptable(A, U)   :- argumentGetsAttackOn(A, U, B), not defendedFrom(A, U, B).
acceptable(A, U)      :- domain(A, U), not notAcceptable(A, U).

% We remove the lines:
% :- scope(A, U), not acceptable(A, U).
% :- domain(A, U), acceptable(A, U), not scope(A, U).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STEP 3.5: PENALTY & EFFECTIVE CONTRIBUTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% penalty(A,U,P): # of opposition arguments that also have domain(U) and attack(A).
penalty(A, U, P) :- argument(A), team(A, proposition), domain(A,U),
                    P = #count { B : team(B,opposition), domain(B,U), attacks(B,A) }.

% effective_contribution(A,U, EC) if scope(A,U), then EC = interest(U) - penalty(A,U,P) (if >0).
effective_contribution(A,U,EC) :- scope(A,U), interest(U,I), penalty(A,U,P), EC = I - P, EC>0.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STEP 4. TEAM-SPECIFIC COVERAGE & NEXT MOVE
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

covered_by_team(U, proposition) :- argument(A), team(A, proposition), scope(A,U).
uncovered_by_team(U, proposition) :- domain_element(U), not covered_by_team(U, proposition).

% high_interest: dynamic average logic
total_interest(S) :- S = #sum { I, D : domain_element(D), interest(D,I) }.
count_domains(N)  :- N = #count { D : domain_element(D) }.
high_interest(U)  :- interest(U,I), count_domains(N), total_interest(T), I*N > T.

team_strength(U,Sum) :-
    domain_element(U),
    Sum = #sum { EC,A : argument(A), team(A, proposition), scope(A,U), effective_contribution(A,U,EC) }.

% (1) uncovered & high_interest => introduce
next_move_team(introduce_new_argument, U, proposition) :-
    uncovered_by_team(U, proposition),
    high_interest(U).

% (2) covered & high_interest & strength < interest => strengthen
next_move_team(strengthen_existing_argument, U, proposition) :-
    covered_by_team(U, proposition), high_interest(U),
    team_strength(U,TS), interest(U,I),
    TS < I.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STEP 5. OUTPUT
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#show next_move_team/3.
"""

# AAFD_CORE_LOGIC = r"""
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# % STEP 3. PURE AAFD: COMPUTE SCOPES
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
# % Generate all possible assignments of subtopics to each argument.
# { scope(A, U) : domain_element(U) } :- argument(A).
#
# % Compliant scope: An argument may only cover elements in its intended domain.
# :- scope(A, U), not domain(A, U).
#
# % Conflict-free scope: Two arguments that attack each other may not share the same subtopic.
# :- attacks(A1, A2), scope(A1, U), scope(A2, U).
#
# % Admissibility:
# argumentGetsAttackOn(A, U, B) :- domain(A, U), attacks(B, A), domain(B, U).
# defendedFrom(A, U, B) :- argumentGetsAttackOn(A, U, B), attacks(C, B), scope(C, U).
# notAcceptable(A, U) :- argumentGetsAttackOn(A, U, B), not defendedFrom(A, U, B).
# acceptable(A, U) :- domain(A, U), not notAcceptable(A, U).
# :- scope(A, U), not acceptable(A, U).
#
# % Completeness: If a subtopic is acceptable for an argument, it must be included in its scope.
# :- domain(A, U), acceptable(A, U), not scope(A, U).
#
# % (Optional) Grounded, Preferred, and Stable scopes could be defined here;
# % for our purposes we assume that the above constraints yield the "final" (e.g. grounded) scope.
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# % STEP 4. TEAM-SPECIFIC COVERAGE ANALYSIS & NEXT MOVE DECISION
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
# % A subtopic U is covered by team T if any argument from T has U in its computed scope.
# covered_by_team(U, T) :- argument(A), team(A, T), scope(A, U).
#
# % A subtopic is uncovered (for the proposition team) if no proposition argument covers it.
# uncovered_by_team(U, proposition) :- domain_element(U), not covered_by_team(U, proposition).
#
# % Define high interest as any subtopic with interest >= 5.
# high_interest(U) :- interest(U, I), I >= 5.
#
# % (Optional: You might compute a "strength" measure here.
# % For example, one simple measure is to sum the interests of subtopics covered by a proposition argument.)
# team_strength(U, Sum) :- domain_element(U),
#          Sum = #sum { I, A : argument(A), team(A, proposition), scope(A, U), interest(U, I) }.
#
# % Next move decision using pure AAFD computed scopes:
# % (1) If a high-interest subtopic is uncovered by the proposition team, introduce a new argument.
# next_move_team(introduce_new_argument, U, proposition) :-
#          uncovered_by_team(U, proposition), high_interest(U).
#
# % (2) If a high-interest subtopic is covered but the aggregated team strength is lower than the audience interest,
# % then the move is to strengthen the existing argument.
# next_move_team(strengthen_existing_argument, U, proposition) :-
#          covered_by_team(U, proposition), high_interest(U),
#          team_strength(U, TS), interest(U, I), TS < I.
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# % STEP 5. OUTPUT DIRECTIVES
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
# #show next_move_team/3.
# """
