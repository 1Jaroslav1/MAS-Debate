import json
from typing import Dict, Any

from src.debate_extended.config.debate_builder import DebateBuilder
from src.debate_extended.config.model import AudienceConfig, DebateConfig, MemberConfig, TeamConfig

from src.debate_extended.debate import create_enhanced_debate_workflow


class DebateConfigLoader:
    @staticmethod
    def load_from_file(config_path: str) -> DebateConfig:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return DebateConfigLoader._parse_config(config_data)
    
    @staticmethod
    def load_from_dict(config_data: Dict[str, Any]) -> DebateConfig:
        return DebateConfigLoader._parse_config(config_data)
    
    @staticmethod
    def _parse_config(config_data: Dict[str, Any]) -> DebateConfig:
        teams = []
        for team_data in config_data.get('teams', []):
            members = []
            for member_data in team_data.get('members', []):
                members.append(MemberConfig(**member_data))
            
            team_config = TeamConfig(
                team_name=team_data['team_name'],
                team_type=team_data['team_type'],
                perspective_description=team_data['perspective_description'],
                priority_aspects=team_data['priority_aspects'],
                evidence_preferences=team_data['evidence_preferences'],
                counterargument_strategy=team_data['counterargument_strategy'],
                rhetorical_emphasis=team_data['rhetorical_emphasis'],
                focus_keywords=team_data['focus_keywords'],
                avoid_keywords=team_data['avoid_keywords'],
                viewpoint_orientation=team_data['viewpoint_orientation'],
                interests_and_concerns=team_data['interests_and_concerns'],
                typical_arguments=team_data['typical_arguments'],
                members=members,
                architecture=team_data.get('architecture', 'godsaf')
            )
            teams.append(team_config)
        
        audience_data = config_data.get('audience', {})
        audience_config = AudienceConfig(
            listeners=audience_data.get('custom_listeners'),
            max_domains=audience_data.get('max_domains', 6),
            max_goals=audience_data.get('max_goals', 6)
        )
        
        return DebateConfig(
            id=config_data.get('id'),
            topic=config_data['topic'],
            max_rounds=config_data.get('max_rounds', 3),
            teams=teams,
            audience=audience_config,
            output_file=config_data.get('output_file', 'debate_results.json'),
            include_user_interaction=config_data.get('include_user_interaction', False),
            user_team_name=config_data.get('user_team_name', 't_user'),
            team_llm_model=config_data.get('team_llm_model')
        )


def create_debate_from_config(config_path: str) -> Dict[str, Any]:
    config = DebateConfigLoader.load_from_file(config_path)
    
    builder = DebateBuilder(config)
    
    teams = [builder.create_team(team_config) for team_config in config.teams]
    
    audience_node = builder.create_audience()
    
    initial_state = builder.create_initial_state(teams)
    
    workflow = create_enhanced_debate_workflow(teams, audience_node, builder.is_user_interaction_enabled())
    
    print(f"📝 Topic: {config.topic}")
    print(f"👥 Teams: {[team['team_name'] for team in teams]}")
    
    print(f"🎭 Standard Audience: {len(initial_state.get('audience_initial_votes', []))} listeners")
    print(f"🔄 Max rounds: {config.max_rounds}")
    print("\n" + "="*80 + "\n")
    
    try:
        final_state = workflow.invoke(initial_state)
        results_service = final_state.get("results_service")
        if results_service:
            results = results_service.build_results(final_state)
        else:
            results = final_state
    except RuntimeError as e:
        if "parsing failed" in str(e) or "grounding stopped because of errors" in str(e):
            print(f"Warning: Debate workflow failed due to parsing/grounding error. Returning partial results. Error: {e}")
            results = {
                "topic": config.topic,
                "teams": [team['team_name'] for team in teams],
                "rounds_completed": 0,
                "audience_initial_votes": initial_state.get("audience_initial_votes", []),
                "audience_final_votes": initial_state.get("audience_initial_votes", []),  # Use initial as final
                "argument_log": initial_state.get("argument_log", []),
                "tgs_snapshots": initial_state.get("tgs_snapshots", []),
                "error": f"Parsing/grounding error: {e}"
            }
        else:
            raise
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR: Unexpected error in debate workflow")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        print(f"\n📍 Full traceback:")
        traceback.print_exc()
        print("\n" + "="*80)

        results = {
            "topic": config.topic,
            "teams": [team['team_name'] for team in teams],
            "rounds_completed": 0,
            "audience_initial_votes": initial_state.get("audience_initial_votes", []),
            "audience_final_votes": initial_state.get("audience_initial_votes", []),
            "argument_log": initial_state.get("argument_log", []),
            "tgs_snapshots": initial_state.get("tgs_snapshots", []),
            "error": f"Unexpected error: {e}",
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }

    if builder.config.id and isinstance(results, dict):
        results["config_id"] = builder.config.id
    builder.save_results(results)
    
    return results
