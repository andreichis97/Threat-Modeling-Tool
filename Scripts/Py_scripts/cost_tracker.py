class CostTracker:
    def __init__(self, input_price_per_1k=0.002, output_price_per_1k=0.008):
        # Set these to your actual GPT-4.1 pricing
        self.input_price_per_1k = input_price_per_1k
        self.output_price_per_1k = output_price_per_1k
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.calls = []

    def track(self, usage, label=""):
        output_tokens = getattr(usage, "completion_tokens", 0) or 0
        self.total_input_tokens += usage.prompt_tokens
        self.total_output_tokens += output_tokens
        self.calls.append({
            "label": label,
            "input_tokens": usage.prompt_tokens,
            "output_tokens": output_tokens
        })

    @property
    def total_cost(self):
        input_cost = (self.total_input_tokens / 1000) * self.input_price_per_1k
        output_cost = (self.total_output_tokens / 1000) * self.output_price_per_1k
        return input_cost + output_cost

    def summary(self):
        print(f"{'Label':<40} {'Input':>8} {'Output':>8}")
        print("-" * 60)
        for c in self.calls:
            print(f"{c['label']:<40} {c['input_tokens']:>8} {c['output_tokens']:>8}")
        print("-" * 60)
        print(f"{'TOTAL':<40} {self.total_input_tokens:>8} {self.total_output_tokens:>8}")
        print(f"Estimated cost: ${self.total_cost:.6f}")