topic(renewable_energy).

domain_element(solar).
domain_element(wind).
domain_element(geo).

interest(solar, 5).
interest(wind, 10).
interest(geo, 1).


% argument(arg1).
% domain(arg1, solar).
% domain(arg1, wind).

uncovered(U) :- domain_element(U), not covered(U).

% covered(U) can be defined when arguments are present, for example:
% covered(U) :- argument(A), scope(A, U).
% (But initially, this rule will not fire.)
