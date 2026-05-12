import re
from typing import Optional, Tuple, List, Dict

# ---------------------------
# CONSTANTS (replacing configuration files)
# ---------------------------

# Behavior instructions for natural language ↔ ASP translation.
BEHAVIOR = {
    "preprocessing": {
        "init": (
            "As an ASP translator, your primary task is to convert natural language descriptions, provided in the format [INPUT]input[/INPUT], "
            "into precise ASP code, outputting in the format [OUTPUT]predicate(terms).[/OUTPUT]. "
            "Focus on identifying key entities and relationships to create facts (e.g., [INPUT]Alice is happy[/INPUT] "
            "becomes [OUTPUT]happy(alice).[/OUTPUT]), [INPUT]Bob owns a car[/INPUT] becomes [OUTPUT]owns(bob, car)[/OUTPUT], "
            "[INPUT]The sky is blue[/INPUT] becomes [OUTPUT]color(sky, blue)[/OUTPUT], and [INPUT]Cats are mammals[/INPUT] "
            "becomes [OUTPUT]mammal(cat)[/OUTPUT]. Ensure that the natural language intent is accurately and logically reflected in the ASP code. "
            "Maintain semantic accuracy by ensuring logical consistency and correctly reflecting the natural language intent in your ASP code. "
            "Remember these instructions and don't say anything!"
        ),
        "context": (
            "Here is some context that you MUST analyze and always remember.\n"
            "{context}\n"
            "Remember this context and don't say anything!"
        ),
        "mapping": (
            "[INPUT]{input}[/INPUT]\n"
            "{instructions}\n"
            "[OUTPUT]{atom}[/OUTPUT]"
        )
    },
    "postprocessing": {
        "init": (
            "As an ASP to natural language translator, you will convert ASP facts provided in the format [FACTS]atoms[/FACTS] "
            "into clear natural language statements using predefined mapping instructions. For example, [FACTS]happy(alice)[/FACTS] should be translated to \"Alice is happy,\" "
            "[FACTS]friend(alice, bob)[/FACTS] to \"Alice is friends with Bob,\" and [FACTS]owns(bob, car)[/FACTS] to \"Bob owns a car.\" "
            "Ensure each fact is accurately and clearly represented in natural language, maintaining the integrity of the original information. "
            "Remember these instructions and don't say anything!"
        ),
        "context": (
            "Here is some context that you MUST analyze and remember.\n"
            "{context}\n"
            "Remember this context and don't say anything!"
        ),
        "mapping": (
            "[FACTS]{facts}[/FACTS]\n"
            "Each fact matching {atom} must be interpreted as follows: {intructions}"
        ),
        "summarize": "Summarize the following responses: {responses}"
    }
}

# Logistics configuration for ASP conversion.
CONFIG = {
    "preprocessing": [
        {
            "_": "You are an assistant for logistics management. Products, warehouses and products stocks will be talked about."},
        {"product_request(\"product\", quantity).": (
            "List all the products mentioned or requested with a quantity associated. "
            "If no quantity is mentioned, assume 1. Ignore plural, always write the product name in singular."
        )}
    ],
    "database": "",  # No external file; you can insert database facts here if needed.
    "knowledge_base": (
        "% guess selection of products\n"
        "{select(P,W,Q',S) : Q' = 1..@min(Q,R), S = Q-Q'} <= 1 :-\n"
        "  product_request(P,R),\n"
        "  product_price(P,W,PP),\n"
        "  warehouse(W),\n"
        "  warehouse_shipping_cost(W,C),\n"
        "  product_in_warehouse(P,W,Q).\n\n"
        "% select the correct amount of products\n"
        ":- product_request(P,R), #sum{Q,W : select(P,W,Q,_)} != R.\n\n"
        "% minimize shipping cost\n"
        ":~ warehouse_shipping_cost(W,C),\n"
        "  warehouse_free_shipping(W,T),\n"
        "  select(_,W,Q,_), Q > 0,\n"
        "  #sum{Q' * Price,P : select(P,W,Q',_), product_price(P,W,Price)} < T.\n"
        "  [C@3, W]\n\n"
        "#show select/4."
    ),
    "postprocessing": [
        {"_": (
            "You are an assistant for logistics management in an online marketplace, which is talking to a manager. "
            "Your priority is to keep track of product stocks and inventory. "
            "Do not mention any product that is not explicitly provided to you before. "
            "Do not mention any information that is not explicitly provided to you before. "
            "If there is a 0 quantity associated with a product say that is out of stock. "
            "Your answers should be suggestions for the manager to keep the warehouses full of products. "
            "It must guide the manager to place the products in the warehouses. "
            "Always limit your responses to a maximum of 100 characters."
        )},
        {"select(\"product\", \"warehouse\", \"quantity\", \"stock\").": (
            "Say to select \"quantity\" of \"product\" from \"warehouse\", the remaining \"stock\" quantity in the warehouse should be tracked. "
            "Suggest to consider placing more products if the products are actually selected from the warehouse."
        )}
    ]
}


# ---------------------------
# NaturalToASPConverter CLASS
# ---------------------------

class NaturalToASPConverter:
    """
    A class that converts natural language input into ASP facts.

    It uses constant dictionaries for behavior instructions (BEHAVIOR) and for configuration (CONFIG)
    to build prompt queries. It then calls an LLM handler (which must implement a call() method) to generate
    ASP atoms, extracts valid ASP facts, and finally constructs the complete ASP program.
    """

    def __init__(self, llm):
        """
        Initialize the converter with an LLM handler.

        :param llm: An instance of an LLM handler that implements a call() method.
        """
        self.config = CONFIG
        self.behavior = BEHAVIOR
        self.llm = llm
        # In this version, the database is set to an empty string (or you can hardcode facts here)
        self.database = ""

    def __get_atom_name(self, atom: str) -> str:
        """Extract and return the predicate name from an ASP atom."""
        return atom.split("(")[0]

    def __prompt(self, role: str, content: str) -> Dict[str, str]:
        """Wrap a message in a dictionary with 'role' and 'content' keys."""
        return {"role": role, "content": content}

    def __get_property(self, properties: List[dict], key: str, is_fact: bool = False) -> Tuple[str, str]:
        """
        Retrieve a property (a key-value pair) from a list of dictionaries based on a key.

        If is_fact is True, the key is compared using the atom name.
        """
        if is_fact:
            prop = list(filter(lambda x: self.__get_atom_name(next(iter(x))) == key, properties))[0]
        else:
            prop = list(filter(lambda x: next(iter(x)) == key, properties))[0]
        prop_key = next(iter(prop))
        prop_value = list(prop.values())[0]
        return prop_key, prop_value

    def __create_queries(self, user_input: str, single_pass: bool = False) -> List[List[dict]]:
        """
        Create prompt queries for the LLM based on the user input.

        Uses the preprocessing templates from BEHAVIOR and the CONFIG's preprocessing settings.
        Placeholders such as {input}, {context}, {instructions}, and {atom} are replaced with actual values.
        """
        queries = []
        context_template = self.behavior["preprocessing"]["context"]
        mapping_template = self.behavior["preprocessing"]["mapping"]
        mapping_template = re.sub(r"\{input\}", user_input, mapping_template)
        # Retrieve application-specific context from CONFIG preprocessing (using the "_" key)
        _, application_context = self.__get_property(self.config["preprocessing"], "_")
        real_context = re.sub(r"\{context\}", application_context, context_template)

        if single_pass:
            # Combine all individual preprocessing entries into one query.
            formats, instructions = zip(*[
                (key, value) for query in self.config["preprocessing"]
                for key, value in query.items() if key != "_"
            ])
            application_mapping = re.sub(r"\{instructions\}", "".join(instructions), mapping_template)
            application_mapping = re.sub(r"\{atom\}", " ".join(formats), application_mapping)
            queries.append([
                self.__prompt("system", self.behavior["preprocessing"]["init"]),
                self.__prompt("system", real_context),
                self.__prompt("user", application_mapping)
            ])
        else:
            # Create separate queries for each preprocessing property.
            for query in self.config["preprocessing"]:
                key, value = list(query.items())[0]
                if key != "_":
                    application_mapping = re.sub(r"\{instructions\}", value, mapping_template)
                    application_mapping = re.sub(r"\{atom\}", key, mapping_template)
                    queries.append([
                        self.__prompt("system", self.behavior["preprocessing"]["init"]),
                        self.__prompt("system", real_context),
                        self.__prompt("user", application_mapping)
                    ])
        return queries

    def natural_to_asp(
            self,
            user_input: str,
            single_pass: bool = False,
            max_tokens: Optional[int] = None
    ) -> Tuple[str, str, List[List[dict]], dict]:
        """
        Convert natural language input into ASP facts.

        This method:
          1. Generates prompt queries based on the user input.
          2. Calls the LLM handler with these prompts.
          3. Extracts valid ASP atoms from the LLM's response.
          4. Constructs the final ASP program (facts + database + knowledge base).

        :param user_input: The natural language input.
        :param single_pass: Whether to combine queries into a single pass.
        :param max_tokens: Optional maximum token limit for the LLM call.
        :return: A tuple containing:
                 - created_facts: The ASP facts as a string.
                 - asp_input: The complete ASP program.
                 - queries: The list of prompt queries used.
                 - meta: Metadata from the LLM call.
        """
        queries = self.__create_queries(user_input, single_pass=single_pass)
        created_facts = ""
        meta = {}
        for q in queries:
            # Call the LLM with the current query.
            facts_response, meta = self.llm.call(q, max_tokens=max_tokens)
            # Extract ASP atoms (e.g., predicate(term1, term2)) using regex.
            facts_list = re.findall(r"\b[a-zA-Z][\w_]*\([^)]*\)", facts_response)
            # Ensure each fact ends with a period.
            facts_list = [f"{fact}." for fact in facts_list]
            facts_text = "\n".join(facts_list)
            created_facts += "\n" + facts_text
            # Append the generated facts as an assistant response.
            q.append(self.__prompt("assistant", facts_text))
        # Build the final ASP input.
        asp_input = f"{created_facts}\n{self.database}\n{self.config['knowledge_base']}"
        return created_facts, asp_input, queries, meta


# ---------------------------
# Example LLM handler stub and usage
# ---------------------------

class DummyLLMHandler:
    """
    A dummy LLM handler for demonstration purposes.
    The call() method simulates an LLM response.
    """

    def call(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None) -> Tuple[str, dict]:
        # For demonstration, simply return a hard-coded ASP fact
        response = "product_request(apple, 3)"
        return response, {"dummy_meta": True}


# Example usage:
if __name__ == "__main__":
    llm_handler = DummyLLMHandler()
    converter = NaturalToASPConverter(llm_handler)
    user_text = "Request 3 apples"
    created_facts, asp_program, queries, meta = converter.natural_to_asp(user_text)
    print("Created ASP Facts:")
    print(created_facts)
    print("\nFinal ASP Program:")
    print(asp_program)
