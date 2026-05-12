from src.reasoning.asp.solver import ASPSolver

GODSAF_EXAMPLE = """
% ===== GoDsAF Framework - Practical Integer Version =====
% This version uses integer arithmetic to avoid Clingo's floating-point limitations

% ===== CONSTANTS AND SCALING =====
% We scale all values by 100 to work with integers
#const scale = 100.
#const k_chal_scaled = 40.  % 0.4 * 100

% ===== FACTS (scaled by 100) =====

% Teams
team(tl).
team(tws).

% Arguments
argument(a_culture).   team_of(a_culture, tl).
argument(a_innovation). team_of(a_innovation, tl).
argument(a_tools).     team_of(a_tools, tl).
argument(a_talent).    team_of(a_talent, tws).
argument(a_burnout).   team_of(a_burnout, tws).

% Domains and Goals
domain_element(d_culture).
domain_element(d_ops).
goal_primitive(g_innovation).
goal_primitive(g_retention).

% Prior domains
prior_domain(a_culture, d_culture).
prior_domain(a_innovation, d_ops).
prior_domain(a_tools, d_ops).
prior_domain(a_talent, d_culture).
prior_domain(a_burnout, d_ops).

% Goal coverage claims
goal_coverage_claim(a_culture, g_innovation, d_culture).
goal_coverage_claim(a_culture, g_retention, d_culture).
goal_coverage_claim(a_innovation, g_innovation, d_ops).
goal_coverage_claim(a_tools, g_innovation, d_ops).
goal_coverage_claim(a_talent, g_retention, d_culture).
goal_coverage_claim(a_burnout, g_retention, d_ops).

% Attacks
attacks(a_talent, a_culture).
attacks(a_burnout, a_innovation).
attacks(a_tools, a_burnout).

% P_G and S_D values (already represent counts, so no scaling needed)
pg_value(g_innovation, d_culture, 10).
pg_value(g_innovation, d_ops, 30).
pg_value(g_retention, d_culture, 15).
pg_value(g_retention, d_ops, 55).

sd_value(d_culture, 25).
sd_value(d_ops, 80).

% ===== STRENGTH CALCULATION =====

% APC = P_G * S_D
apc(A, G, D, Value) :- 
    goal_coverage_claim(A, G, D),
    pg_value(G, D, PG),
    sd_value(D, SD),
    Value = PG * SD.

% Total argument strength in domain
arg_strength(A, D, TotalStr) :-
    argument(A),
    domain_element(D),
    prior_domain(A, D),
    TotalStr = #sum { APC, G : apc(A, G, D, APC) }.

% ===== STRENGTH-BASED DEFEAT =====

defeat(A1, A2, D) :-
    attacks(A1, A2),
    prior_domain(A1, D),
    prior_domain(A2, D),
    arg_strength(A1, D, Str1),
    arg_strength(A2, D, Str2),
    Str1 > Str2.

% ===== SCOPE DETERMINATION =====

% Generate scopes
{ scope(A, D) } :- prior_domain(A, D).

% Compute undefended arguments
undefended(A, D) :-
    defeat(B, A, D),
    not defeated_in_scope(B, D).

defeated_in_scope(B, D) :-
    defeat(C, B, D),
    scope(C, D).

% Grounded semantics constraints
:- scope(A, D), undefended(A, D).
:- prior_domain(A, D), not undefended(A, D), not scope(A, D).

% ===== EFFECTIVE CHALLENGERS =====

% Count challengers from opposing teams that are in scope
effective_challenger(Target, Challenger, D) :-
    scope(Target, D),
    scope(Challenger, D),
    attacks(Challenger, Target),
    team_of(Target, T1),
    team_of(Challenger, T2),
    T1 != T2.

num_challengers(A, N) :-
    argument(A),
    N = #count { C, D : effective_challenger(A, C, D) }.

% ===== APS CALCULATION WITH INTEGER ARITHMETIC =====

% For N=0: APS = Strength
% For N=1: APS = Strength * 40 / 100
% For N=2: APS = Strength * 16 / 100
% etc.

aps_for_domain(A, D, APS) :-
    scope(A, D),
    arg_strength(A, D, Str),
    num_challengers(A, 0),
    APS = Str.

aps_for_domain(A, D, APS) :-
    scope(A, D),
    arg_strength(A, D, Str),
    num_challengers(A, 1),
    APS = (Str * k_chal_scaled) / scale.

aps_for_domain(A, D, APS) :-
    scope(A, D),
    arg_strength(A, D, Str),
    num_challengers(A, 2),
    APS = (Str * k_chal_scaled * k_chal_scaled) / (scale * scale).

% Total APS across all domains
total_aps(A, Total) :-
    argument(A),
    Total = #sum { APS, D : aps_for_domain(A, D, APS) }.

% ===== TEAM METRICS =====

% EAPC for each goal claim
eapc(A, G, D, EAPC) :-
    goal_coverage_claim(A, G, D),
    scope(A, D),
    apc(A, G, D, APCVal),
    num_challengers(A, N),
    N = 0,
    EAPC = APCVal.

eapc(A, G, D, EAPC) :-
    goal_coverage_claim(A, G, D),
    scope(A, D),
    apc(A, G, D, APCVal),
    num_challengers(A, 1),
    EAPC = (APCVal * k_chal_scaled) / scale.

eapc(A, G, D, 0) :-
    goal_coverage_claim(A, G, D),
    not scope(A, D).

% Team Goal Strength
tgs(Team, G, D, Sum) :-
    team(Team),
    goal_primitive(G),
    domain_element(D),
    Sum = #sum { EAPC, A : eapc(A, G, D, EAPC), team_of(A, Team) }.

% Required Goal Strength
regs(G, D, Value) :-
    pg_value(G, D, PG),
    sd_value(D, SD),
    Value = PG * SD.

% Unmet Goal Need
ugn(Team, G, D, Need) :-
    team(Team),
    goal_primitive(G),
    domain_element(D),
    regs(G, D, ReGS),
    tgs(Team, G, D, TGS),
    Need = ReGS - TGS,
    Need > 0.

ugn(Team, G, D, 0) :-
    team(Team),
    goal_primitive(G),
    domain_element(D),
    regs(G, D, ReGS),
    tgs(Team, G, D, TGS),
    ReGS <= TGS.

% ===== OUTPUT =====

output_scope(A, D, "IN") :- scope(A, D).
output_scope(A, D, "OUT") :- prior_domain(A, D), not scope(A, D).

output_defeat(Attacker, Target, Domain, Str1, Str2) :-
    defeat(Attacker, Target, Domain),
    arg_strength(Attacker, Domain, Str1),
    arg_strength(Target, Domain, Str2).

#show output_scope/3.
#show output_defeat/5.
#show arg_strength/3.
#show num_challengers/2.
#show total_aps/2.
#show tgs/4.
#show ugn/4.

% Debug outputs
% #show apc/4.
% #show eapc/4.
% #show effective_challenger/3.
"""

def run_test_gen_argument_for_critical_ugn():
    solver = ASPSolver(timeout=10)
    answer = solver.solve(GODSAF_EXAMPLE)
    print(answer)

run_test_gen_argument_for_critical_ugn()
    
