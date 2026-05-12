from src.model.model import AudienceProfile


def summarize_audience_profile(profile: AudienceProfile) -> str:
    lines = []
    for idx, member in enumerate(profile["audience_members"], start=1):
        lines.append(f"Audience Member {idx}:")
        lines.append(f"  - Name: {member['name']}")
        lines.append(f"  - Interests: {', '.join(member['interests'])}")
        lines.append(f"  - Work Experience: {', '.join(member['work_experience'])}")
        lines.append(f"  - Personality: {', '.join(member['personality'])}")
        lines.append("")
    return "\n".join(lines)
