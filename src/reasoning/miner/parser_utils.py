"""
Centralized utilities for argument parsing.

Provides consistent formatting and parsing across all architectures.
"""

import logging
from typing import List, Dict, Any, Callable, Optional
from src.reasoning.godsaf.godsaf_service import Domain, Goal
from src.reasoning.miner.argument_miner import Argument, argument_parser_node

logger = logging.getLogger(__name__)


def format_domains_info(
    domains: List[Domain],
    include_salience: bool = True,
    sort_by_salience: bool = True
) -> str:
    """
    Format domains information for parser input.

    Args:
        domains: List of Domain objects
        include_salience: Whether to include salience values
        sort_by_salience: Whether to sort by salience (descending)

    Returns:
        Formatted string with domain information
    """
    if sort_by_salience:
        domains = sorted(domains, key=lambda d: d.salience, reverse=True)

    formatted = []
    for domain in domains:
        if include_salience:
            formatted.append(f"- **{domain.name}**: {domain.description} (salience: {domain.salience})")
        else:
            formatted.append(f"- **{domain.name}**: {domain.description}")

    return "\n".join(formatted)


def format_goals_info(
    goals: List[Goal],
    include_pg_values: bool = True,
    include_domain_descriptions: bool = True,
    sort_by_name: bool = True,
    domain_lookup: Optional[Callable[[str], Optional[Domain]]] = None
) -> str:
    """
    Format goals information for parser input.

    Args:
        goals: List of Goal objects
        include_pg_values: Whether to include PG values
        include_domain_descriptions: Whether to include domain descriptions in PG values
        sort_by_name: Whether to sort by goal name
        domain_lookup: Optional function to look up domain descriptions (domain_id -> Domain)

    Returns:
        Formatted string with goal information
    """
    if sort_by_name:
        goals = sorted(goals, key=lambda g: g.name)

    formatted = []
    for goal in goals:
        goal_line = f"- **{goal.name}**: {goal.description}"

        if include_pg_values and goal.pg_values:
            pg_info = []
            for domain_name, pg_value in sorted(goal.pg_values.items()):
                if include_domain_descriptions and domain_lookup:
                    domain = domain_lookup(domain_name)
                    domain_desc = domain.description if domain else domain_name
                    pg_info.append(f"{domain_name} ({domain_desc}): {pg_value}")
                else:
                    pg_info.append(f"{domain_name}: {pg_value}")

            pg_str = ", ".join(pg_info) if pg_info else "No PG values set"
            goal_line += f"\n  Priority values: {pg_str}"

        formatted.append(goal_line)

    return "\n".join(formatted)


def prepare_parser_input(
    topic: str,
    argument: str,
    domains: List[Domain],
    goals: List[Goal],
    existing_arguments: List[str],
    domain_lookup: Optional[Callable[[str], Optional[Domain]]] = None
) -> Dict[str, Any]:
    """
    Prepare input dictionary for argument_parser_node.

    Args:
        topic: Debate topic
        argument: Argument text to parse
        domains: List of Domain objects
        goals: List of Goal objects
        existing_arguments: List of existing argument names
        domain_lookup: Optional function to look up domain descriptions

    Returns:
        Dictionary ready for parser.invoke()
    """
    return {
        "topic": topic,
        "domains_info": format_domains_info(domains),
        "goals_info": format_goals_info(goals, domain_lookup=domain_lookup),
        "argument": argument,
        "existing_arguments": existing_arguments  # Consistent key name
    }


def parse_argument(
    topic: str,
    argument: str,
    domains: List[Domain],
    goals: List[Goal],
    existing_arguments: List[str],
    domain_lookup: Optional[Callable[[str], Optional[Domain]]] = None
) -> Dict[str, Any]:
    """
    Parse argument text to extract structure (domains, goals, attacks).

    Args:
        topic: Debate topic
        argument: Argument text to parse
        domains: List of Domain objects
        goals: List of Goal objects
        existing_arguments: List of existing argument names
        domain_lookup: Optional function to look up domain descriptions

    Returns:
        Parsed argument structure with keys: name, domains, goals, attacks
    """
    parser = argument_parser_node()
    parser_input = prepare_parser_input(
        topic, argument, domains, goals, existing_arguments, domain_lookup
    )

    logger.debug(f"[PARSER_UTILS] Parsing argument with {len(domains)} domains, {len(goals)} goals")
    parsed_result: Argument = parser.invoke(parser_input)
    logger.debug(f"[PARSER_UTILS] Parsed argument name: {parsed_result.name}")

    return parsed_result
