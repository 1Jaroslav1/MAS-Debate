from src.tutor.tutor import creat_tutor
from src.tutor.state import TutorState

tutor_state: TutorState = {
    "topic": "All people should have the right to own guns.",
    "user_arguments": [
        {
          "speaker": {
            "name": "Diana",
            "expertise": "Innovation & Technology",
            "description": "A technology entrepreneur who believes that heavy regulation stifles innovation and that market-driven solutions yield the best outcomes."
          },
          "team_role": "OPPOSING",
          "text": "The right to own guns is not merely a question of personal freedom; it is a fundamental aspect of our identity as responsible individuals and innovators in society. As a technology entrepreneur, I assert that gun ownership, like many freedoms, comes with the vital responsibility to ensure safety—not just for ourselves, but for our communities at large.\n\nThe argument for the right to own guns becomes particularly compelling when we explore the advancements in gun safety technology. Innovations such as smart guns and biometric locks are specifically designed to prevent unauthorized use, thereby enhancing public safety while preserving our right to bear arms. Research from the Centers for Disease Control and Prevention indicates that states with higher rates of gun ownership often report lower crime rates, especially when ownership is coupled with education and responsible practices. This data suggests that educated firearm owners employing advanced safety technologies contribute to safer communities.\n\nNonetheless, I recognize the valid concerns surrounding gun violence and the potential misuse of firearms. It is imperative to address these concerns directly. Comprehensive data demonstrates that responsible gun ownership, combined with thorough education and technological advancements, can significantly reduce crime rates. The focus of our discussion should not be on imposing restrictions on ownership but on promoting responsible use and education. By empowering individuals with knowledge and the latest safety technologies, we can mitigate the risks associated with gun ownership effectively.\n\nImagine a future in which gun ownership is not merely a right but a serious responsibility—one where technological innovations enhance our safety rather than threaten it. This vision is not a distant dream; it is an achievable goal that requires collaboration among regulators, technology developers, and responsible gun owners. By fostering an environment that embraces innovation in safety technology and prioritizes personal responsibility, we can cultivate a society where the right to own guns coexists harmoniously with the imperative for safety.\n\nIn conclusion, the right to own guns should be upheld, not only as a fundamental freedom but also as an opportunity for innovation in safety practices. We must welcome the role of technology in enhancing safety, advocate for responsible ownership, and engage in constructive dialogues about the implications of gun ownership in our communities. Let us not allow fear to overshadow our rights; instead, let us champion the responsible use of firearms and the innovative technologies that can facilitate safe practices."
        },
        {
          "speaker": {
            "name": "Edward",
            "expertise": "Economics",
            "description": "An economist specializing in tech markets who argues that overregulation could hurt economic growth and limit global competitiveness."
          },
          "team_role": "OPPOSING",
          "text": "The right to own firearms is an essential element of personal freedom and community responsibility, intricately linked to our identity as innovative individuals. As an economist with expertise in tech markets, I contend that responsible gun ownership not only empowers individuals but also fosters a safer society.\n\nConsider the advancements in gun safety technology — innovations such as smart guns and biometric locks are designed to prevent unauthorized use while simultaneously honoring our rights. These technologies have the potential to markedly reduce accidents and misuse, demonstrating that gun ownership can coexist harmoniously with a commitment to safety. A study conducted by the National Institute of Justice reveals a noteworthy correlation: states with higher rates of gun ownership often experience lower crime rates, especially when ownership is paired with education and responsible practices. This suggests that informed firearm owners, equipped with advanced safety measures, can significantly contribute to the well-being of their communities.\n\nHowever, it is crucial to acknowledge the legitimate concerns surrounding gun violence. The emotional impact of gun violence resonates deeply within our society, and dismissing these fears would undermine the ongoing dialogue. Instead, we should examine successful educational programs that promote gun safety and responsible ownership. For example, the Eddie Eagle GunSafe Program has effectively reduced accidents among children and has been widely adopted across various states.\n\nImagine a future where gun ownership is not merely a right but a solemn responsibility, enhanced by the latest technologies that prioritize safety rather than compromise it. This vision is not a distant aspiration; it is attainable through collaboration among regulators, technology developers, and responsible gun owners. By creating an environment that champions innovation and prioritizes education, we can cultivate a society where the right to own guns harmonizes with the imperative for safety.\n\nIn conclusion, upholding the right to own firearms transcends the preservation of personal freedoms; it represents an opportunity to embrace innovation in safety practices. We must advocate for responsible ownership, support rigorous educational initiatives, and engage in constructive discussions regarding the implications of gun ownership in our communities. Let us not permit fear to overshadow our rights; instead, let us illuminate the responsible use of firearms and the innovative technologies that can facilitate safe practices. By doing so, we can establish a balanced approach that respects both our freedoms and our collective safety."
        },
        {
          "speaker": {
            "name": "Fiona",
            "expertise": "Software Development",
            "description": "A lead software engineer and advocate for open-source innovation, stressing that flexible frameworks rather than strict rules drive technological progress."
          },
          "team_role": "OPPOSING",
          "text": "The right to own guns is not merely a fundamental freedom; it embodies a significant responsibility that can enhance community safety through personal accountability and technological innovation. As a lead software engineer and advocate for open-source solutions, I assert that just as we embrace advancements in technology across various fields, we must also evolve our approach to gun ownership by prioritizing safety alongside liberty.\n\nOne of the most compelling facets of responsible gun ownership is the integration of advanced safety technologies. Innovations such as smart guns, which can only be fired by authorized users, and biometric locks that prevent unauthorized access, significantly mitigate the risks of accidents and misuse. A report from the National Institute of Justice indicates that states with comprehensive gun safety education and higher rates of responsible ownership tend to experience lower crime rates. This correlation underscores the notion that educated firearm owners, armed with the latest safety technologies, contribute positively to their communities.\n\nHowever, we must not overlook the profound emotional and societal ramifications of gun violence. A poignant example is the story of a mother who tragically lost her child to accidental gunfire. This heartbreaking incident highlights the urgent need for rigorous safety education and responsible ownership. Acknowledging this emotional weight is essential in our discussions. Rather than advocating for sweeping restrictions on gun ownership, we should focus on education and technology as pivotal solutions. Programs like the Eddie Eagle GunSafe Program have proven effective in reducing firearm accidents among children, demonstrating the power of safety education.\n\nImagine a society where gun ownership is viewed as a serious responsibility, supported by innovations that enhance safety. This vision can be realized through collaboration among technology developers, regulators, and conscientious gun owners. By cultivating an environment that champions safety innovation and emphasizes education, we can establish a balanced approach that respects our freedoms while actively promoting public safety.\n\nIn conclusion, the right to own firearms offers an opportunity to weave personal liberty with community responsibility. We must champion comprehensive education initiatives that prioritize safety and the responsible use of firearms, while concurrently embracing innovative technologies that facilitate safer practices. Let us rise above fear; together, we can illuminate the path towards responsible gun ownership and the progressive technologies that will safeguard our communities."
        }
    ],
    "opponent_arguments": [
        {
          "speaker": {
            "name": "Alice",
            "expertise": "Artificial Intelligence",
            "description": "An AI specialist with deep expertise in machine learning, neural networks, and natural language processing. Advocates for strong oversight to ensure AI is developed responsibly."
          },
          "team_role": "PROPOSING",
          "text": "In contemporary society, the debate surrounding the right to own guns often pivots on the principles of personal freedom, safety, and community responsibility. As an AI specialist with a profound understanding of technology and ethics, I contend that advocating for responsible gun ownership transcends mere rights; it is about harnessing technological advancements to bolster safety and accountability.\n\nFirstly, it is essential to recognize that the right to bear arms is a fundamental liberty enshrined in our Constitution, embodying the values of individual autonomy and self-defense. This right is paramount for personal protection; numerous studies indicate that individuals who possess firearms for self-defense frequently report heightened feelings of safety within their homes and communities. Moreover, responsible gun ownership cultivates a sense of community responsibility, as many gun owners actively participate in local safety initiatives, fostering a culture of awareness and education regarding safe handling practices.\n\nFurthermore, technological innovations in gun safety are transforming the landscape of gun ownership. Developments such as smart guns, which can only be discharged by authorized users, and biometric locks that provide additional security measures exemplify how technology can enhance responsible ownership while addressing safety concerns. These innovations empower gun owners to take proactive measures to prevent misuse, ultimately contributing to a reduction in gun violence incidents.\n\nHowever, it is critical to acknowledge the complexities surrounding gun violence and the legitimate concerns voiced by advocates for stricter regulations. The alarming prevalence of gun-related incidents indeed prompts inquiries about the equilibrium between individual rights and public safety. Yet, substantial evidence suggests that education and training significantly diminish the risks associated with accidental shootings and misuse. In fact, states implementing comprehensive gun education programs consistently report lower rates of gun-related accidents and crimes.\n\nResponding to the concerns of those advocating for more stringent regulations does not necessitate a compromise on the right to own guns; rather, it demands a balanced approach. We can champion responsible gun ownership while simultaneously advocating for innovative safety measures and educational initiatives that mitigate firearm-related risks. Community-based programs emphasizing responsible ownership and safe storage practices can nurture a culture of safety without infringing upon individual rights.\n\nIn conclusion, the right to own guns must be preserved, but it should also adapt to societal needs and technological advancements. By leveraging the power of education and innovation, we can forge a safer environment that respects individual freedoms while addressing concerns about gun violence. Ultimately, responsible gun ownership is a collective responsibility that can enhance safety and promote community well-being."
        },
        {
          "speaker": {
            "name": "Bob",
            "expertise": "Ethics & Policy",
            "description": "A seasoned policy advisor with extensive experience in technology ethics, arguing that strict regulations are necessary to safeguard societal well-being."
          },
          "team_role": "PROPOSING",
          "text": "In the ongoing discourse regarding gun ownership rights, we find ourselves navigating a complex interplay between individual freedoms and societal safety. As an expert in ethics and policy, I contend that the right to own guns is indeed a fundamental element of our constitutional freedoms. However, it is imperative that we approach this issue with a sense of responsibility and a commitment to innovation.\n\nThe right to bear arms serves not only as a legal provision but as a vital component of personal autonomy and self-defense. According to a Gallup poll, over 60% of Americans report feeling safer when they own a firearm, underscoring the psychological comfort that gun possession can provide. Moreover, responsible gun owners frequently take proactive roles in their communities, participating in initiatives that promote safe handling and awareness practices, thereby contributing to overall public safety.\n\nTechnological advancements present us with new opportunities to enhance gun safety. Innovations such as smart guns and biometric locks exemplify how we can leverage technology to foster responsible ownership. A study from the National Institute of Justice indicates that states adopting smart gun technologies have witnessed a significant reduction in accidental discharges, demonstrating a dual benefit: protecting individual rights while addressing concerns about gun violence by preventing unauthorized use.\n\nWhile it is crucial to acknowledge the legitimate concerns of those advocating for stricter gun regulations, we must also recognize the importance of education and training in mitigating risks. Research from Johns Hopkins University reveals that comprehensive gun safety education can dramatically lower the incidence of accidental shootings and firearm misuse. Notably, states implementing such educational programs have experienced up to a 30% reduction in gun-related accidents.\n\nAddressing counterarguments is essential. Promoting responsible gun ownership does not equate to ignoring the realities of gun violence. Instead, it advocates for a balanced approach that emphasizes education, community involvement, and innovative technological solutions. By fostering a culture of responsible ownership through community-based initiatives and safety programs, we can cultivate an environment where individual rights and public safety coexist harmoniously.\n\nIn conclusion, while we advocate for the right to own guns, we must equally commit to responsibility and innovation. By embracing technological advancements and prioritizing education, we can uphold our constitutional freedoms while addressing the pressing concerns surrounding gun violence. Ultimately, responsible gun ownership is not just an individual right; it embodies a collective responsibility that enhances the safety and well-being of our communities."
        },
        {
          "speaker": {
            "name": "Charlie",
            "expertise": "Public Safety",
            "description": "An expert in cybersecurity and AI safety, emphasizing the need for clear regulations to prevent potential harms from unchecked AI applications."
          },
          "team_role": "PROPOSING",
          "text": "In contemporary society, the debate over the right to bear arms evokes profound emotions and spirited discussions. As a public safety expert with a focus on technology, I assert that responsible gun ownership is not merely a constitutional right but a necessary component of personal autonomy, community safety, and technological progress. This perspective arises from the understanding that while individual freedoms are vital, they must be wielded with a commitment to responsibility and an awareness of their broader implications.\n\nThe right to own a firearm is a fundamental freedom enshrined in the Constitution, embodying the values of personal autonomy and self-defense. A Gallup poll reveals that over 60% of Americans feel safer when owning a firearm, underscoring the psychological assurance that comes with the ability to protect oneself and loved ones. Furthermore, many responsible gun owners actively participate in their communities through safety initiatives and educational programs that promote responsible firearm handling, thereby enhancing overall public safety.\n\nTechnological advancements have paved the way for significant improvements in gun safety. Innovations such as smart guns—designed to be fired only by authorized users—and biometric locks that secure firearms exemplify a proactive approach to responsible ownership. Research from the National Institute of Justice indicates that states implementing smart gun technologies have experienced notable reductions in accidental discharges. These advancements not only safeguard individual rights but also tackle pressing issues of gun violence and unauthorized access, illustrating the potential of technology as a crucial ally in this discourse.\n\nNevertheless, it is essential to acknowledge the legitimate concerns regarding gun violence. Recognizing these concerns does not undermine the case for responsible gun ownership; rather, it fortifies it. A study from Johns Hopkins University shows that comprehensive gun safety education can significantly reduce the frequency of accidental shootings and firearm misuse. States with such educational programs have reported reductions of up to 30% in gun-related accidents. By fostering education and community engagement, we cultivate a culture of responsible ownership that honors individual rights while prioritizing public safety.\n\nTo address the reservations of those advocating for stricter regulations, we must advocate for a balanced approach that underscores education, community involvement, and technological solutions. This discussion is not about dismissing the realities of gun violence; it is about creating an environment where individual rights and public safety can coexist harmoniously. By supporting community-based initiatives and safety programs, we can enhance responsible ownership and mitigate the risks associated with firearms.\n\nIn conclusion, while we champion the right to own firearms, we must equally commit to responsibility and innovation. By embracing technological advancements and prioritizing education, we can uphold our constitutional freedoms while addressing the urgent concerns surrounding gun violence. Ultimately, responsible gun ownership represents a collective responsibility that enhances the safety and well-being of our communities, ensuring that individual liberties are exercised with care and respect for the greater good."
        }
    ],
    "audience_profile": {
        "audience_members": [
            {
              "name": "Alice",
              "interests": [
                "technology",
                "innovation"
              ],
              "work_experience": [
                "software engineer"
              ],
              "personality": [
                "analytical",
                "curious"
              ]
            },
            {
              "name": "Bob",
              "interests": [
                "finance",
                "economics"
              ],
              "work_experience": [
                "banker"
              ],
              "personality": [
                "pragmatic",
                "cautious"
              ]
            },
            {
              "name": "Charlie",
              "interests": [
                "arts",
                "culture"
              ],
              "work_experience": [
                "artist"
              ],
              "personality": [
                "creative",
                "open-minded"
              ]
            },
            {
              "name": "Dana",
              "interests": [
                "science",
                "research"
              ],
              "work_experience": [
                "researcher"
              ],
              "personality": [
                "observant",
                "inquisitive"
              ]
            },
            {
              "name": "Eric",
              "interests": [
                "politics",
                "social justice"
              ],
              "work_experience": [
                "activist"
              ],
              "personality": [
                "passionate",
                "determined"
              ]
            },
            {
              "name": "Fiona",
              "interests": [
                "literature",
                "writing"
              ],
              "work_experience": [
                "editor"
              ],
              "personality": [
                "thoughtful",
                "articulate"
              ]
            },
            {
              "name": "George",
              "interests": [
                "history",
                "philosophy"
              ],
              "work_experience": [
                "historian"
              ],
              "personality": [
                "reflective",
                "intellectual"
              ]
            },
            {
              "name": "Hannah",
              "interests": [
                "environment",
                "sustainability"
              ],
              "work_experience": [
                "environmental scientist"
              ],
              "personality": [
                "empathetic",
                "practical"
              ]
            },
            {
              "name": "Ian",
              "interests": [
                "sports",
                "fitness"
              ],
              "work_experience": [
                "personal trainer"
              ],
              "personality": [
                "energetic",
                "disciplined"
              ]
            },
            {
              "name": "Jessica",
              "interests": [
                "music",
                "performing arts"
              ],
              "work_experience": [
                "musician"
              ],
              "personality": [
                "expressive",
                "passionate"
              ]
            },
            {
              "name": "Kevin",
              "interests": [
                "gaming",
                "technology"
              ],
              "work_experience": [
                "game developer"
              ],
              "personality": [
                "innovative",
                "strategic"
              ]
            },
            {
              "name": "Laura",
              "interests": [
                "travel",
                "culture"
              ],
              "work_experience": [
                "travel blogger"
              ],
              "personality": [
                "adventurous",
                "curious"
              ]
            },
            {
              "name": "Michael",
              "interests": [
                "politics",
                "debate"
              ],
              "work_experience": [
                "political analyst"
              ],
              "personality": [
                "assertive",
                "analytical"
              ]
            },
            {
              "name": "Natalie",
              "interests": [
                "fashion",
                "design"
              ],
              "work_experience": [
                "fashion designer"
              ],
              "personality": [
                "creative",
                "stylish"
              ]
            },
            {
              "name": "Oliver",
              "interests": [
                "engineering",
                "innovation"
              ],
              "work_experience": [
                "mechanical engineer"
              ],
              "personality": [
                "logical",
                "practical"
              ]
            },
            {
              "name": "Patricia",
              "interests": [
                "health",
                "nutrition"
              ],
              "work_experience": [
                "dietitian"
              ],
              "personality": [
                "compassionate",
                "methodical"
              ]
            },
            {
              "name": "Quentin",
              "interests": [
                "cinema",
                "film"
              ],
              "work_experience": [
                "film critic"
              ],
              "personality": [
                "observant",
                "expressive"
              ]
            },
            {
              "name": "Rachel",
              "interests": [
                "psychology",
                "human behavior"
              ],
              "work_experience": [
                "therapist"
              ],
              "personality": [
                "empathetic",
                "insightful"
              ]
            },
            {
              "name": "Samuel",
              "interests": [
                "technology",
                "cybersecurity"
              ],
              "work_experience": [
                "cybersecurity expert"
              ],
              "personality": [
                "cautious",
                "detail-oriented"
              ]
            },
            {
              "name": "Teresa",
              "interests": [
                "education",
                "learning"
              ],
              "work_experience": [
                "teacher"
              ],
              "personality": [
                "patient",
                "nurturing"
              ]
            },
            {
              "name": "Ulysses",
              "interests": [
                "literature",
                "poetry"
              ],
              "work_experience": [
                "writer"
              ],
              "personality": [
                "imaginative",
                "reflective"
              ]
            },
            {
              "name": "Victoria",
              "interests": [
                "politics",
                "activism"
              ],
              "work_experience": [
                "community organizer"
              ],
              "personality": [
                "driven",
                "empathetic"
              ]
            },
            {
              "name": "William",
              "interests": [
                "business",
                "entrepreneurship"
              ],
              "work_experience": [
                "startup founder"
              ],
              "personality": [
                "ambitious",
                "innovative"
              ]
            },
            {
              "name": "Xander",
              "interests": [
                "science",
                "technology"
              ],
              "work_experience": [
                "data scientist"
              ],
              "personality": [
                "analytical",
                "curious"
              ]
            },
            {
              "name": "Yvonne",
              "interests": [
                "art",
                "design"
              ],
              "work_experience": [
                "graphic designer"
              ],
              "personality": [
                "creative",
                "detail-oriented"
              ]
            },
            {
              "name": "Zachary",
              "interests": [
                "sports",
                "business"
              ],
              "work_experience": [
                "sports manager"
              ],
              "personality": [
                "competitive",
                "driven"
              ]
            },
            {
              "name": "Amara",
              "interests": [
                "social media",
                "marketing"
              ],
              "work_experience": [
                "digital marketer"
              ],
              "personality": [
                "innovative",
                "charismatic"
              ]
            },
            {
              "name": "Benedict",
              "interests": [
                "cooking",
                "culinary arts"
              ],
              "work_experience": [
                "chef"
              ],
              "personality": [
                "creative",
                "passionate"
              ]
            },
            {
              "name": "Cassandra",
              "interests": [
                "yoga",
                "meditation"
              ],
              "work_experience": [
                "yoga instructor"
              ],
              "personality": [
                "calm",
                "mindful"
              ]
            },
            {
              "name": "Dimitri",
              "interests": [
                "travel",
                "adventure"
              ],
              "work_experience": [
                "travel agent"
              ],
              "personality": [
                "sociable",
                "adventurous"
              ]
            }
          ],
    },
    "relevance_analysis": {},
    "evidence_support_analysis": {},
    "emotional_appeal_analysis": {},
    "style_clarity_analysis": {},
    "complex_feedback": {}
}

tutor_workflow = creat_tutor()
tutor = tutor_workflow.compile()

tutor.get_graph().draw_mermaid_png(output_file_path="tutor.png")

result = tutor.invoke(tutor_state)
print(result)
