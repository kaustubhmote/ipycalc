from IPython.terminal.prompts import Prompts
from pygments.token import Token


class LoadingPrompt(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [(Token.OutPrompt, "‣ ")]

    def out_prompt_tokens(self, cli=None):
        return [(Token.OutPrompt, "= ")]


class ReadyPrompt(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [(Token.Prompt, "‣ ")]

    def out_prompt_tokens(self, cli=None):
        return [(Token.OutPrompt, "= ")]


def set_prompt(ipython, ready: bool) -> None:
    prompt_class = ReadyPrompt if ready else LoadingPrompt
    ipython.prompts = prompt_class(ipython)

