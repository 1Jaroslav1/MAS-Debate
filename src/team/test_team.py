from typing_extensions import List
from src.team.state import TeamState
from src.model.model import TeamRole
from src.audience import AudienceMember
from team import create_team_workflow

members = [
        {
            "name": "Alice",
            "expertise": "Artificial Intelligence",
            "description": "An AI specialist with deep expertise in machine learning, neural networks, and natural language processing."
        },
        {
            "name": "Bob",
            "expertise": "Conservation",
            "description": "A seasoned conservator who values traditional methods and proven techniques, with decades of experience."
        },
        {
            "name": "Charlie",
            "expertise": "Economics",
            "description": "A dynamic young economics student with fresh insights on market trends and innovative financial analysis."
        }
    ]


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


team_state: TeamState = {
    "topic": "Should artificial intelligence have legal rights and responsibilities, similar to humans and corporations?",
    "team_role": TeamRole.PROPOSING,
    "members": members,
    "transcript": [],
    "audience_profile": {
        "audience_members": audience_members
    }
}

team_workflow = create_team_workflow(members)
team = team_workflow.compile()

team.get_graph().draw_mermaid_png(output_file_path ="team.png")

events = team.stream(team_state, stream_mode="values")

for event in events:
    print(event)
