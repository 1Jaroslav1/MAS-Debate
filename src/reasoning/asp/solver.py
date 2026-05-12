import logging
from clingo import Control

logger = logging.getLogger("ASPSolver")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class ASPContext:
    @staticmethod
    def min(a, b):
        return a if a < b else b


class ASPSolver:
    def __init__(self, arguments=None, timeout=2, context=ASPContext):
        """
        Initialize the ASP solver with optional arguments, a timeout, and a grounding context.

        :param arguments: List of command-line arguments for Clingo.
        :param timeout: Time (in seconds) to wait for the solver.
        :param context: A context class to extend the grounding process with extra functions.
        """
        if arguments is None:
            arguments = ["--opt-strategy=usc,k,0,5", "--opt-usc-shrink=rgs"]
        self.arguments = arguments
        self.timeout = timeout
        self.context = context

    def solve(self, program: str):
        """
        Solve the given ASP program and return the resulting facts along with solver status.

        :param program: A string representing the ASP program.
        :return: A tuple containing:
                 - facts: A list of strings, each a fact from the solution.
                 - interrupted: A boolean flag indicating if the solving was interrupted.
                 - satisfiable: A boolean flag indicating if the program is satisfiable.
        """
        models = []

        def on_model(model):
            logger.debug("Found model: %s", model)
            atoms = [str(atom) for atom in model.symbols(shown=True)]
            models.append(atoms)

        try:
            ctl = Control(self.arguments, logger=logger.debug)
            ctl.add("base", [], program)
            ctl.ground([("base", [])], context=self.context)
            logger.info("ASP program grounded successfully.")

            with ctl.solve(on_model=on_model, async_=True) as handle:
                logger.info("Solving ASP program with a timeout of %s seconds.", self.timeout)
                handle.wait(self.timeout)
                handle.cancel()
                final_handle = handle.get()
                logger.info("Solver execution completed.")

            atoms = models[0] if models else []
            logger.info("Extracted facts: %s", atoms)

            return atoms, final_handle.interrupted, final_handle.satisfiable

        except Exception as error:
            logger.error("An error occurred during solving: %s", error)
            raise
