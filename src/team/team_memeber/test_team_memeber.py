from typing_extensions import List
from team_member import create_team_member_workflow
from state import TeamMemberState
from src.model.model import TeamRole
from src.audience import AudienceMember

team_member_1 = create_team_member_workflow()

audience_members: List[AudienceMember] = [
    {
        "name": "Alice",
        "interests": ["technology", "innovation"],
        "work_experience": ["software engineer"],
        "personality": ["analytical"]
    },
    {
        "name": "Bob",
        "interests": ["finance", "economics"],
        "work_experience": ["banker"],
        "personality": ["conservative"]
    },
    {
        "name": "Charlie",
        "interests": ["arts", "culture"],
        "work_experience": ["artist"],
        "personality": ["creative"]
    },
    {
        "name": "Dana",
        "interests": ["science", "research"],
        "work_experience": ["researcher"],
        "personality": ["curious"]
    },
    {
        "name": "Eric",
        "interests": ["All people should earn the same amount of moneys", "politics", "all people are equal"],
        "work_experience": ["post"],
        "personality": ["passionate communist"]
    }
]

team_member_state: TeamMemberState = {
    "topic": "Should artificial intelligence have legal rights and responsibilities, similar to humans and corporations?",
    "team_role": TeamRole.PROPOSING,
    "person": {
        "name": "Dr. Alex Carter",
        "expertise": "AI Ethics and Law",
        "description": "A leading expert in artificial intelligence regulations, focusing on the intersection of ethics, law, and AI development."
    },
    "transcript": [],
    "team_arguments": [],
    "opponent_arguments": [],
    "audience_profile": {
        "audience_members": audience_members,
    },
    "analysis": {},
    "retrieved_data": {},
    "argument": {},
    "lexicon_adjustment": {},
    "evaluation": {},
    "iteration_number": 0
}

team_member_graph_1 = team_member_1.compile()
team_member_graph_1.get_graph().draw_mermaid_png(output_file_path ="team_member_graph_1.png")


events = team_member_graph_1.stream(team_member_state, stream_mode="values")

for event in events:
    print(event)
