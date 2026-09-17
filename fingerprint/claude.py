from fingerprint.configurable import ConfigurableDetector
class ClaudeDetector(ConfigurableDetector):
    def __init__(self, signatures: list[dict]) -> None: super().__init__("claude", signatures)

