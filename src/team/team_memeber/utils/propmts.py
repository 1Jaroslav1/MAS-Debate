TEXT_2_ASP_PROMPT = """
**Task:**  
Convert natural language facts into ASP knowledge facts.

**Format:**  
Each fact should be represented as:  
```
knowledge(domain, atomic_fact).
```
- **domain:** One of the provided domains.
- **atomic_fact:** A concise, standalone statement extracted from the input text.

**Input:**  
Domains:

Text containing statements:

**Instructions:**  
- Parse the input text and extract atomic facts related to each domain.
- If a sentence contains multiple facts for a domain, output each as a separate ASP fact.
- If a sentence mentions multiple domains, generate a separate fact for each domain mentioned.
- Only include facts relevant to the provided domains.
- Ensure each output ends with a period.

**Example 1:**  
*Domains:* solar, wind, geo  
*Input Text:* "Solar energy is cheap and efficient, whereas wind energy is expensive."  
*Expected Output:*  
```
knowledge(solar, solar energy is cheap).
knowledge(solar, solar energy is efficient).
knowledge(wind, wind energy is expensive).
```

**Example 2:**  
*Domains:* solar, wind, geo  
*Input Text:* "Geothermal energy is reliable, but solar energy depends on the weather."  
*Expected Output:*  
```
knowledge(geo, geothermal energy is reliable).
knowledge(solar, solar energy depends on the weather).
```
"""
