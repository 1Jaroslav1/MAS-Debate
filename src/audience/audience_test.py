from audience import create_audience
from typing_extensions import List
from src.audience.state import AudienceState
from src.model.model import AudienceMember

audience_state: AudienceState = {
    "topic": "All workers deserve equal pay for equal work.",
    "transcript": [],

    "initial_scores": [],
    "final_scores": []
}

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

audience_workflow = create_audience("init", audience_members)
audience = audience_workflow.compile()
audience.get_graph().draw_mermaid_png(output_file_path="audience.png")

result = audience.invoke(audience_state)
print(result)
