class Trace:
    def __init__(self):
        self.steps: list[dict] = []

    def add_step(self, module: str, prompt: dict, response: dict):
        if not isinstance(prompt, dict):
            prompt = {"value": str(prompt)}
        if not isinstance(response, dict):
            response = {"value": str(response)}

        self.steps.append({
            "module": module,
            "prompt": prompt,
            "response": response,
        })

    # ADD THIS (compatibility with LLModClient)
    def add_llm_step(self, module: str, prompt: dict, response: dict):
        self.add_step(module, prompt, response)
