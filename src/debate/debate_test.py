from src.debate.debate import create_debate
from src.debate.state import DebateState

# pro team: 2
# opp team: 0

# topic = "Renewable Energy Adoption in Urban Areas: Challenges and Opportunities?"
# topic = "Universal Basic Income: A Pathway to Social Equality?"
topic = "Is climate change primarily a natural phenomenon rather than a result of human activity?"

# audience_members = [
#     {
#         "name": "Sarah Green",
#         "interests": ["Solar Energy", "Sustainable Architecture", "Urban Planning"],
#         "work_experience": ["Renewable Energy Engineer"],
#         "personality": ["Innovative", "Analytical"]
#     },
#     {
#         "name": "Daniel Reed",
#         "interests": ["Wind Power", "Environmental Policy", "Sustainability"],
#         "work_experience": ["Environmental Policy Analyst"],
#         "personality": ["Detail-oriented", "Passionate"]
#     },
#     {
#         "name": "Olivia Patel",
#         "interests": ["Green Technology", "Energy Storage", "Climate Change"],
#         "work_experience": ["R&D Specialist in Renewable Tech"],
#         "personality": ["Curious", "Proactive"]
#     },
#     {
#         "name": "Liam Nguyen",
#         "interests": ["Urban Sustainability", "Smart Cities", "Eco-friendly Design"],
#         "work_experience": ["Urban Planner"],
#         "personality": ["Creative", "Visionary"]
#     },
#     {
#         "name": "Emma Thompson",
#         "interests": ["Sustainable Development", "Policy Reform", "Environmental Justice"],
#         "work_experience": ["Sustainability Consultant"],
#         "personality": ["Empathetic", "Strategic"]
#     },
#     {
#         "name": "Noah Kim",
#         "interests": ["Hydropower", "Energy Efficiency", "Green Innovation"],
#         "work_experience": ["Energy Analyst"],
#         "personality": ["Logical", "Resourceful"]
#     },
#     {
#         "name": "Ava Martinez",
#         "interests": ["Renewable Materials", "Circular Economy", "Sustainable Fashion"],
#         "work_experience": ["Sustainability Researcher"],
#         "personality": ["Innovative", "Environmentally Conscious"]
#     },
#     {
#         "name": "William Scott",
#         "interests": ["Bioenergy", "Waste-to-Energy", "Renewable Resources"],
#         "work_experience": ["Chemical Engineer in Renewable Fuels"],
#         "personality": ["Pragmatic", "Methodical"]
#     },
#     {
#         "name": "Mia Brown",
#         "interests": ["Energy Policy", "Public Transportation", "Green Urbanism"],
#         "work_experience": ["Policy Advisor for Renewable Initiatives"],
#         "personality": ["Persuasive", "Organized"]
#     },
#     {
#         "name": "Ethan Davis",
#         "interests": ["Smart Grid Technology", "Clean Energy", "Future Tech"],
#         "work_experience": ["Technology Consultant in Clean Energy"],
#         "personality": ["Innovative", "Tech-savvy"]
#     }
# ]
#
# # audience_members = [
#     {
#         "name": "Emily Johnson",
#         "interests": ["Literature", "Art", "Cooking"],
#         "work_experience": ["Retail Assistant"],
#         "personality": ["Friendly", "Creative"]
#     },
#     {
#         "name": "Michael Lee",
#         "interests": ["Sports", "Music", "Outdoor Adventures"],
#         "work_experience": ["Sales Representative"],
#         "personality": ["Energetic", "Outgoing"]
#     },
#     {
#         "name": "Sophia Garcia",
#         "interests": ["Fashion", "Travel", "Photography"],
#         "work_experience": ["Fashion Blogger"],
#         "personality": ["Expressive", "Trendsetter"]
#     },
#     {
#         "name": "David Kim",
#         "interests": ["History", "Philosophy", "Chess"],
#         "work_experience": ["Museum Curator"],
#         "personality": ["Analytical", "Thoughtful"]
#     },
#     {
#         "name": "Olivia Brown",
#         "interests": ["Gardening", "Crafting", "Community Events"],
#         "work_experience": ["Community Organizer"],
#         "personality": ["Empathetic", "Organized"]
#     },
#     {
#         "name": "James Wilson",
#         "interests": ["Automotive", "Cooking", "DIY Projects"],
#         "work_experience": ["Automotive Mechanic"],
#         "personality": ["Practical", "Hands-on"]
#     },
#     {
#         "name": "Isabella Martinez",
#         "interests": ["Yoga", "Dance", "Nature"],
#         "work_experience": ["Fitness Instructor"],
#         "personality": ["Calm", "Motivated"]
#     },
#     {
#         "name": "Benjamin Davis",
#         "interests": ["Gaming", "Comics", "Music"],
#         "work_experience": ["Retail Associate"],
#         "personality": ["Creative", "Enthusiastic"]
#     },
#     {
#         "name": "Mia Rodriguez",
#         "interests": ["Theater", "Poetry", "Social Media"],
#         "work_experience": ["Event Coordinator"],
#         "personality": ["Outgoing", "Artistic"]
#     },
#     {
#         "name": "Alexander Walker",
#         "interests": ["Travel", "Culinary Arts", "Photography"],
#         "work_experience": ["Freelance Writer"],
#         "personality": ["Curious", "Adventurous"]
#     }
# ]

audience_members = [
    {
        "name": "Alice",
        "interests": ["technology", "innovation"],
        "work_experience": ["software engineer"],
        "personality": ["analytical", "curious"]
    },
    {
        "name": "Bob",
        "interests": ["finance", "economics"],
        "work_experience": ["banker"],
        "personality": ["pragmatic", "cautious"]
    },
    {
        "name": "Charlie",
        "interests": ["arts", "culture"],
        "work_experience": ["artist"],
        "personality": ["creative", "open-minded"]
    },
    {
        "name": "Dana",
        "interests": ["science", "research"],
        "work_experience": ["researcher"],
        "personality": ["observant", "inquisitive"]
    },
    {
        "name": "Eric",
        "interests": ["politics", "social justice"],
        "work_experience": ["activist"],
        "personality": ["passionate", "determined"]
    },
    {
        "name": "Fiona",
        "interests": ["literature", "writing"],
        "work_experience": ["editor"],
        "personality": ["thoughtful", "articulate"]
    },
    {
        "name": "George",
        "interests": ["history", "philosophy"],
        "work_experience": ["historian"],
        "personality": ["reflective", "intellectual"]
    },
    {
        "name": "Hannah",
        "interests": ["environment", "sustainability"],
        "work_experience": ["environmental scientist"],
        "personality": ["empathetic", "practical"]
    },
    {
        "name": "Ian",
        "interests": ["sports", "fitness"],
        "work_experience": ["personal trainer"],
        "personality": ["energetic", "disciplined"]
    },
    {
        "name": "Jessica",
        "interests": ["music", "performing arts"],
        "work_experience": ["musician"],
        "personality": ["expressive", "passionate"]
    },
    {
        "name": "Kevin",
        "interests": ["gaming", "technology"],
        "work_experience": ["game developer"],
        "personality": ["innovative", "strategic"]
    },
    {
        "name": "Laura",
        "interests": ["travel", "culture"],
        "work_experience": ["travel blogger"],
        "personality": ["adventurous", "curious"]
    },
    {
        "name": "Michael",
        "interests": ["politics", "debate"],
        "work_experience": ["political analyst"],
        "personality": ["assertive", "analytical"]
    },
    {
        "name": "Natalie",
        "interests": ["fashion", "design"],
        "work_experience": ["fashion designer"],
        "personality": ["creative", "stylish"]
    },
    {
        "name": "Oliver",
        "interests": ["engineering", "innovation"],
        "work_experience": ["mechanical engineer"],
        "personality": ["logical", "practical"]
    },
    {
        "name": "Patricia",
        "interests": ["health", "nutrition"],
        "work_experience": ["dietitian"],
        "personality": ["compassionate", "methodical"]
    },
    {
        "name": "Quentin",
        "interests": ["cinema", "film"],
        "work_experience": ["film critic"],
        "personality": ["observant", "expressive"]
    },
    {
        "name": "Rachel",
        "interests": ["psychology", "human behavior"],
        "work_experience": ["therapist"],
        "personality": ["empathetic", "insightful"]
    },
    {
        "name": "Samuel",
        "interests": ["technology", "cybersecurity"],
        "work_experience": ["cybersecurity expert"],
        "personality": ["cautious", "detail-oriented"]
    },
    {
        "name": "Teresa",
        "interests": ["education", "learning"],
        "work_experience": ["teacher"],
        "personality": ["patient", "nurturing"]
    },
    {
        "name": "Ulysses",
        "interests": ["literature", "poetry"],
        "work_experience": ["writer"],
        "personality": ["imaginative", "reflective"]
    },
    {
        "name": "Victoria",
        "interests": ["politics", "activism"],
        "work_experience": ["community organizer"],
        "personality": ["driven", "empathetic"]
    },
    {
        "name": "William",
        "interests": ["business", "entrepreneurship"],
        "work_experience": ["startup founder"],
        "personality": ["ambitious", "innovative"]
    },
    {
        "name": "Xander",
        "interests": ["science", "technology"],
        "work_experience": ["data scientist"],
        "personality": ["analytical", "curious"]
    },
    {
        "name": "Yvonne",
        "interests": ["art", "design"],
        "work_experience": ["graphic designer"],
        "personality": ["creative", "detail-oriented"]
    },
    {
        "name": "Zachary",
        "interests": ["sports", "business"],
        "work_experience": ["sports manager"],
        "personality": ["competitive", "driven"]
    },
    {
        "name": "Amara",
        "interests": ["social media", "marketing"],
        "work_experience": ["digital marketer"],
        "personality": ["innovative", "charismatic"]
    },
    {
        "name": "Benedict",
        "interests": ["cooking", "culinary arts"],
        "work_experience": ["chef"],
        "personality": ["creative", "passionate"]
    },
    {
        "name": "Cassandra",
        "interests": ["yoga", "meditation"],
        "work_experience": ["yoga instructor"],
        "personality": ["calm", "mindful"]
    },
    {
        "name": "Dimitri",
        "interests": ["travel", "adventure"],
        "work_experience": ["travel agent"],
        "personality": ["sociable", "adventurous"]
    }
]

# pro_team_members = [
#     {
#         "name": "Emily Turner",
#         "expertise": "Environmental Engineering",
#         "description": "A leading environmental engineer with extensive experience in sustainable urban planning, advocating for renewable energy integration to transform city infrastructures."
#     },
#     {
#         "name": "Marcus Green",
#         "expertise": "Urban Sociology",
#         "description": "An urban sociologist who examines how renewable energy initiatives can improve urban living conditions and community well-being through innovative policy design."
#     },
#     {
#         "name": "Linda Cheng",
#         "expertise": "Renewable Energy Finance",
#         "description": "A financial analyst specializing in renewable energy investments, emphasizing the long-term economic benefits and market potential of urban renewable projects."
#     }
# ]
#
# opp_team_members = [
#     {
#         "name": "David Reynolds",
#         "expertise": "Infrastructure Economics",
#         "description": "An economist focused on urban infrastructure costs, raising concerns about the financial feasibility and return on investment of integrating renewable energy in dense urban areas."
#     },
#     {
#         "name": "Sophie Martin",
#         "expertise": "Political Science",
#         "description": "A political analyst who critically examines the regulatory and policy hurdles that complicate the widespread adoption of renewable energy in urban settings."
#     },
#     {
#         "name": "Brian Walker",
#         "expertise": "Energy Systems Reliability",
#         "description": "An engineer specializing in grid reliability and energy systems management, skeptical about the technical challenges and stability of renewable energy sources in crowded urban environments."
#     }
# ]

# pro_team_members = [
#     {
#         "name": "Dr. Maria Lopez",
#         "expertise": "Social Policy",
#         "description": "A renowned social policy expert advocating that Universal Basic Income can significantly reduce poverty and foster social equality through a robust safety net."
#     },
#     {
#         "name": "John Smith",
#         "expertise": "Economic Sociology",
#         "description": "An economic sociologist who researches societal impacts of income redistribution, arguing that UBI stabilizes communities and empowers citizens."
#     },
#     {
#         "name": "Angela Kim",
#         "expertise": "Public Administration",
#         "description": "A public administrator with hands-on experience in pilot UBI programs, emphasizing its potential to streamline government support and improve quality of life."
#     }
# ]
#
# opp_team_members = [
#     {
#         "name": "Robert Johnson",
#         "expertise": "Macroeconomics",
#         "description": "A macroeconomist who challenges the fiscal sustainability of UBI, warning of potential inflationary pressures and budget deficits."
#     },
#     {
#         "name": "Sarah Thompson",
#         "expertise": "Labor Economics",
#         "description": "A labor economist concerned that UBI could disincentivize work, negatively affecting productivity and labor market participation."
#     },
#     {
#         "name": "Michael Green",
#         "expertise": "Political Philosophy",
#         "description": "A political theorist who argues that UBI might erode the traditional work ethic and social contract, potentially leading to dependency and reduced civic engagement."
#     }
# ]

pro_team_members = [
    {
        "name": "Dr. Alan Carter",
        "expertise": "Climatology (Skeptical)",
        "description": "A climatologist who argues that natural cycles have always driven climate fluctuations, downplaying the role of human activity in current trends."
    },
    {
        "name": "Jessica Nguyen",
        "expertise": "Environmental History",
        "description": "An environmental historian who emphasizes past natural climate variations, suggesting that the current changes are part of long-term natural cycles."
    },
    {
        "name": "Markus Feldman",
        "expertise": "Earth Systems Science",
        "description": "An earth systems scientist who questions modern climate models, asserting that natural variability is the dominant factor behind climate change."
    }
]

opp_team_members = [
    {
        "name": "Dr. Rebecca Li",
        "expertise": "Climate Science",
        "description": "A leading climate scientist presenting robust evidence that human activities are the primary drivers of current climate change."
    },
    {
        "name": "Carlos Ramirez",
        "expertise": "Environmental Policy",
        "description": "An environmental policy expert who argues for immediate action based on overwhelming scientific consensus about human-induced climate change."
    },
    {
        "name": "Samantha Jones",
        "expertise": "Sustainable Development",
        "description": "A sustainable development advocate emphasizing the urgent need for policy intervention to mitigate the human impact on the climate."
    }
]

debate_state: DebateState = {
    "topic": topic,
    "initial_scores": [],
    "final_scores": [],
    "transcript": [],
    "round": 0,
    "audience_members": audience_members,
    "proposing_members": pro_team_members,
    "opposing_members": opp_team_members
}

debate_workflow = create_debate()
debate = debate_workflow.compile()

events = debate.stream(debate_state, stream_mode="values")

for event in events:
    print(event)
