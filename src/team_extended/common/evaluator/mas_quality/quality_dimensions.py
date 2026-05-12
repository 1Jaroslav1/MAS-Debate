QUALITY_DIMENSIONS = {
    "cogency": {
        "definition": "An argument is cogent if it has acceptable premises that are relevant to its conclusion and that are sufficient to draw the conclusion.",
        "subdimensions": [
            "local_acceptability",
            "local_relevance",
            "local_sufficiency",
        ],
        "scoring_guide": "Score 1: Major logical flaws, unsupported claims, or irrelevant premises. Score 2: Some logical support but with gaps or questionable premises. Score 3: Strong logical structure with well-supported, relevant premises leading clearly to the conclusion.",
        "examples": {
            "high": "Smoking causes lung cancer (established medical fact). My grandfather smoked for 40 years and died of lung cancer. Therefore, smoking significantly increases the risk of fatal lung disease. [Score: 3 - Uses accepted medical knowledge, relevant personal example, sufficient for conclusion]",
            "medium": "Smoking is unhealthy according to doctors. Many people who smoke get sick. We should probably discourage smoking in public. [Score: 2 - Generally acceptable premises but lacks specific evidence, conclusion somewhat follows but could be stronger]",
            "low": "Some people say smoking is bad. My friend's mom doesn't like it. So nobody should ever smoke. [Score: 1 - Vague premises, weak relevance, insufficient support for broad conclusion]",
        },
    },
    "local_acceptability": {
        "definition": "A premise of an argument is acceptable if it is rationally worthy of being believed to be true.",
        "focus": "truth_value",
        "scoring_guide": "Score 1: False claims, conspiracy theories, or completely unsupported assertions. Score 2: Plausible but unverified claims or common beliefs without strong evidence. Score 3: Well-established facts, credible sources, or verifiable evidence.",
        "examples": {
            "high": "According to NASA's climate data, global temperatures have risen 1.1°C since 1880, with the warmest years on record occurring in the last decade. [Score: 3 - Cites authoritative source with specific, verifiable data]",
            "medium": "Many scientists believe climate change is a serious problem affecting weather patterns worldwide. [Score: 2 - Generally accurate but vague, lacks specific sources or data]",
            "low": "Everyone knows that the weather has been crazy lately because of chemtrails. [Score: 1 - Relies on conspiracy theory, no credible evidence]",
        },
    },
    "local_relevance": {
        "definition": "A premise of an argument is relevant if it contributes to the acceptance or rejection of the argument's conclusion.",
        "focus": "premise_support",
        "scoring_guide": "Score 1: Premises have no logical connection to the conclusion. Score 2: Premises have some connection but are indirect or only partially support the conclusion. Score 3: Premises directly and clearly support or challenge the conclusion.",
        "examples": {
            "high": "To argue for renewable energy investment: Solar panel costs have decreased 89% in the last decade, making them economically competitive with fossil fuels. [Score: 3 - Directly addresses economic viability, key concern for investment]",
            "medium": "To argue for renewable energy investment: Many countries are interested in environmental protection and reducing pollution. [Score: 2 - Related to topic but doesn't directly address investment rationale]",
            "low": "To argue for renewable energy investment: My cousin recently painted his house green. [Score: 1 - No logical connection to renewable energy investment]",
        },
    },
    "local_sufficiency": {
        "definition": "An argument's premises are sufficient if, together, they give enough support to make it rational to draw its conclusion.",
        "focus": "collective_support",
        "scoring_guide": "Score 1: Single weak premise or anecdote used to support broad conclusion. Score 2: Some supporting evidence but gaps remain, conclusion partially justified. Score 3: Multiple strong premises that collectively justify the conclusion without significant gaps.",
        "examples": {
            "high": "Universities should increase mental health resources because: (1) Student mental health issues have increased 135% over 8 years, (2) Current counseling centers have 3-week wait times, (3) Academic performance correlates strongly with mental health support access. [Score: 3 - Multiple strong premises that together justify the conclusion]",
            "medium": "Universities should increase mental health resources because many students report feeling stressed and counseling centers are often busy. [Score: 2 - Valid concerns raised but lacks specific data, only partially supports the need for increased resources]",
            "low": "We should ban all social media because one teenager felt sad after using Instagram. [Score: 1 - Single anecdote insufficient for sweeping policy conclusion]",
        },
    },
    "effectiveness": {
        "definition": "Argumentation is effective if it persuades the target audience of the author's stance on the issue.",
        "subdimensions": [
            "credibility",
            "emotional_appeal",
            "clarity",
            "appropriateness",
            "arrangement",
        ],
        "scoring_guide": "Score 1: Unlikely to persuade anyone, lacks basic persuasive elements. Score 2: May persuade some but has weaknesses in credibility, emotion, or clarity. Score 3: Highly persuasive with strong ethos, appropriate pathos, and clear logos.",
        "examples": {
            "high": "As a pediatrician with 20 years experience, I've seen how childhood vaccines have eliminated diseases that once killed thousands. When I see a healthy child in my office, I think of the polio wards my mentor described - row after row of iron lungs. That's why I recommend following the CDC vaccination schedule. [Score: 3 - Combines expertise, emotion, and clear recommendation]",
            "medium": "Vaccines have been proven safe by many studies. They protect children from dangerous diseases. Parents should vaccinate their children according to medical guidelines. [Score: 2 - Factually sound but lacks personal connection and emotional resonance]",
            "low": "Vaccines are good I guess. Scientists say so. You should probably get them or whatever. [Score: 1 - Lacks conviction, authority, and persuasive elements]",
        },
    },
    "credibility": {
        "definition": "Argumentation creates credibility if it conveys arguments in a way that makes the author worthy of credence.",
        "focus": "author_trustworthiness",
        "scoring_guide": "Score 1: No credibility established, dubious sources, clear bias. Score 2: Some credibility but lacks expertise or relies on general knowledge. Score 3: Strong credibility through expertise, experience, or authoritative sources.",
        "examples": {
            "high": "As the former Director of the National Hurricane Center, I analyzed 40 years of storm data. The frequency of Category 4+ hurricanes has doubled since 1980, consistent with climate model predictions I helped develop at MIT. [Score: 3 - Establishes relevant expertise and methodology]",
            "medium": "I've been following hurricane news for years and noticed they seem to be getting stronger. Government data supports this trend. [Score: 2 - Shows interest and some knowledge but lacks professional expertise]",
            "low": "I read on a blog somewhere that hurricanes are getting worse. Trust me, I know about weather - I watch the news sometimes. [Score: 1 - No credentials, vague sources, weak claim to authority]",
        },
    },
    "emotional_appeal": {
        "definition": "Argumentation makes a successful emotional appeal if it creates emotions that make the audience more open to the arguments.",
        "focus": "pathos",
        "scoring_guide": "Score 1: No emotional connection or inappropriate/manipulative emotions. Score 2: Some emotional appeal but generic or not well integrated. Score 3: Appropriate, genuine emotional connection that enhances the argument.",
        "examples": {
            "high": "Imagine your child struggling to breathe during an asthma attack, triggered by polluted air. This isn't hypothetical - 1 in 12 children suffer from asthma, and air quality directly impacts their daily lives. Supporting clean air regulations means protecting the children we love. [Score: 3 - Appropriate emotional connection to policy issue]",
            "medium": "Air pollution is concerning because it affects people's health, especially children and the elderly. We should care about clean air for future generations. [Score: 2 - Mentions emotional stakes but in abstract terms]",
            "low": "Air pollution will DESTROY EVERYTHING!!! EVERYONE WILL DIE HORRIBLE DEATHS!!! BE TERRIFIED!!! [Score: 1 - Excessive fear-mongering, manipulative rather than persuasive]",
        },
    },
    "clarity": {
        "definition": "Argumentation has clear style if it uses correct and unambiguous language and avoids unnecessary complexity.",
        "focus": "linguistic_clarity",
        "scoring_guide": "Score 1: Confusing, ambiguous, or unnecessarily complex language. Score 2: Generally clear but some vague terms or minor organizational issues. Score 3: Crystal clear language, well-organized thoughts, accessible to target audience.",
        "examples": {
            "high": "Raising the minimum wage to $15/hour would affect 32 million workers. This means: (1) Increased purchasing power for low-income families, (2) Potential job losses in price-sensitive industries, (3) Reduced government spending on welfare programs. Each factor requires careful consideration. [Score: 3 - Clear structure, specific numbers, accessible language]",
            "medium": "Increasing the minimum wage would help many workers afford basic necessities, though some economists worry about potential negative effects on employment. [Score: 2 - Clear main point but lacks specifics and detailed structure]",
            "low": "The fiduciary ramifications of wage floor modulations create a paradigmatic shift in labor market equilibria, necessitating a reconceptualization of the employer-employee dialectic within late-stage capitalism. [Score: 1 - Unnecessarily complex, jargon-heavy, unclear message]",
        },
    },
    "appropriateness": {
        "definition": "Argumentation has appropriate style if the language supports credibility and emotions and is proportional to the issue.",
        "focus": "style_fit",
        "scoring_guide": "Score 1: Tone completely mismatched to audience or issue severity. Score 2: Generally appropriate but some language choices don't fit context. Score 3: Perfect tone and style match for the audience and issue.",
        "examples": {
            "high": "For a city council meeting on park funding: 'Our community's children deserve safe, well-maintained places to play. The proposed 2% budget allocation would repair playground equipment and add lighting, making our parks accessible to all families.' [Score: 3 - Professional yet accessible tone appropriate for civic forum]",
            "medium": "For a city council meeting on park funding: 'Parks are really important for kids and families. We need to spend more money to fix them up because some equipment is broken.' [Score: 2 - Message is appropriate but language is too casual for formal setting]",
            "low": "For a scientific conference: 'Dude, this quantum stuff is like, totally mind-blowing! It's super weird how particles can be in two places at once - it's like magic or something!' [Score: 1 - Overly casual tone inappropriate for academic setting]",
        },
    },
    "arrangement": {
        "definition": "Argumentation is arranged properly if it presents the issue, arguments, and conclusion in the right order.",
        "focus": "structure",
        "scoring_guide": "Score 1: Chaotic organization, conclusion before evidence, unclear flow. Score 2: Basic organization present but some ideas out of order or transitions missing. Score 3: Logical flow from introduction through evidence to conclusion.",
        "examples": {
            "high": "First, let me explain why traffic congestion costs our city $2.3 billion annually. Second, I'll show how dedicated bus lanes reduced commute times 40% in similar cities. Finally, I'll detail the specific routes where this solution would have maximum impact. Therefore, we should implement dedicated bus lanes on these three corridors. [Score: 3 - Clear problem-solution-application structure]",
            "medium": "Traffic is a big problem in our city. Other cities have used bus lanes successfully. We should try bus lanes on Main Street and First Avenue. This would help reduce congestion. [Score: 2 - Basic structure but jumps too quickly to solution, lacks smooth transitions]",
            "low": "Bus lanes are good. Oh, I forgot to mention traffic is bad. Seattle did something. We need change. Also, cars pollute. In conclusion, I started by saying buses. [Score: 1 - Disorganized, conclusion before premises, unclear flow]",
        },
    },
    "reasonableness": {
        "definition": "Argumentation is reasonable if it contributes to the issue's resolution in a sufficient way acceptable to the audience.",
        "subdimensions": [
            "global_acceptability",
            "global_relevance",
            "global_sufficiency",
        ],
        "scoring_guide": "Score 1: Dismissive of other views, doesn't advance discussion. Score 2: Acknowledges some complexity but limited in addressing opposing views. Score 3: Thoughtfully considers multiple perspectives and advances resolution.",
        "examples": {
            "high": "While both sides have valid concerns about GMO labeling, a compromise would require clear labeling of genetically modified ingredients while avoiding alarming language. This respects consumer choice, addresses transparency concerns, and maintains scientific accuracy without stigmatizing biotechnology. [Score: 3 - Acknowledges all perspectives, offers practical resolution]",
            "medium": "GMO labeling is a complex issue. Consumers want transparency while scientists worry about misunderstanding. We should find a middle ground that provides information without causing unnecessary fear. [Score: 2 - Recognizes complexity but lacks specific solution]",
            "low": "Anyone who disagrees with mandatory GMO labeling is obviously paid by Monsanto and wants to poison children. There's no room for discussion. [Score: 1 - Dismissive of opposing views, doesn't advance resolution]",
        },
    },
    "global_acceptability": {
        "definition": "Argumentation is acceptable if the audience accepts both the stated arguments and the way they are stated.",
        "focus": "audience_acceptance",
        "scoring_guide": "Score 1: Alienates significant portions of audience, uses divisive language. Score 2: Acceptable to some but may exclude or offend others unintentionally. Score 3: Inclusive language and framing that respects diverse audience perspectives.",
        "examples": {
            "high": "To a diverse community group: While we may have different political views, we all want safe neighborhoods for our families. Crime statistics show that both increased police presence AND community programs reduce crime. Let's fund both approaches based on what works, not ideology. [Score: 3 - Acknowledges diverse audience, finds common ground]",
            "medium": "To a diverse community group: Crime is a problem we need to address. Most people agree that we need better policing and prevention programs. Let's increase the public safety budget. [Score: 2 - Generally acceptable but doesn't explicitly acknowledge different viewpoints]",
            "low": "To a mixed-income audience: If you don't support this tax increase, you obviously hate poor people and want them to suffer. Only heartless rich people would oppose this. [Score: 1 - Alienates part of audience, assumes bad faith]",
        },
    },
    "global_relevance": {
        "definition": "Argumentation is relevant if it contributes to the issue's resolution by stating arguments that help reach a conclusion.",
        "focus": "resolution_contribution",
        "scoring_guide": "Score 1: Off-topic tangents that don't address the core issue. Score 2: Addresses the issue but misses key aspects or focuses on peripheral concerns. Score 3: Directly addresses core issue with arguments that advance toward resolution.",
        "examples": {
            "high": "Regarding downtown parking shortage: Analysis shows 73% of spots are used by employees, not customers. Implementing 2-hour limits during business hours would increase customer access while encouraging employees to use the underutilized park-and-ride lots. This directly addresses the core issue. [Score: 3 - Identifies root cause, proposes specific solution]",
            "medium": "Regarding downtown parking shortage: Parking is difficult downtown. We could add more parking meters or build a new garage. Public transportation improvements might also help. [Score: 2 - Relevant suggestions but lacks analysis of root cause]",
            "low": "Regarding downtown parking shortage: Parking is a problem everywhere in America. Cities were built for cars. My grandmother doesn't drive. We should think about climate change. [Score: 1 - Tangential observations that don't advance resolution]",
        },
    },
    "global_sufficiency": {
        "definition": "Argumentation is sufficient if it adequately rebuts anticipated counter-arguments.",
        "focus": "rebuttal_completeness",
        "scoring_guide": "Score 1: Ignores obvious objections entirely. Score 2: Acknowledges some counterarguments but doesn't fully address them. Score 3: Anticipates and thoroughly addresses major objections.",
        "examples": {
            "high": "School uniforms should be required. Critics worry about cost, but our proposal includes a voucher program for low-income families. Concerns about self-expression are addressed by allowing accessories and after-school clothing choices. Studies from 64 schools show uniforms don't suppress creativity when implemented with student input. [Score: 3 - Anticipates and addresses major objections]",
            "medium": "School uniforms should be required because they reduce bullying and improve focus. Yes, they cost money, but parents save on regular clothes. Some say uniforms limit expression, but school is for learning, not fashion. [Score: 2 - Mentions counterarguments but addresses them superficially]",
            "low": "School uniforms are good because they look nice. That's all that matters. [Score: 1 - Ignores obvious counterarguments about cost, expression, effectiveness]",
        },
    },
    "overall_quality": {
        "definition": "The holistic quality of the argument considering all dimensions.",
        "focus": "aggregate_assessment",
        "scoring_guide": "Score 1: Fails on multiple dimensions, unconvincing and poorly constructed. Score 2: Adequate on most dimensions but has notable weaknesses. Score 3: Strong across all major dimensions, compelling and well-crafted.",
        "examples": {
            "high": "The death penalty should be abolished. First, DNA evidence has exonerated 185 death row inmates since 1973, proving our justice system makes fatal errors. Second, it costs taxpayers $2.3 million more per case than life imprisonment. Third, it fails as a deterrent - murder rates are actually higher in death penalty states. Finally, state-sanctioned killing violates the human dignity principles our democracy was founded on. While victims deserve justice, irreversible punishments in an imperfect system ultimately undermine the justice we seek. [Score: 3 - Strong logic, clear structure, addresses counterarguments, appropriate tone]",
            "medium": "The death penalty should be abolished because innocent people might be executed and it's expensive. Many countries have already banned it. Life in prison is a serious punishment too. We should join other nations in ending capital punishment. [Score: 2 - Valid points but lacks depth, evidence, and sophisticated argumentation]",
            "low": "Death penalty bad. Some innocent people died probably. It's mean. We shouldn't kill. [Score: 1 - Lacks development, evidence, structure, and persuasive elements]",
        },
    },
}