from IPython.terminal.prompts import Prompts
from pygments.token import Token
from IPython import get_ipython


class PromptBeforeImports(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [(Token.OutPrompt, "‣ ")]

    def out_prompt_tokens(self, cli=None):
        return [(Token.OutPrompt, "= ")]



class PromptAfterImports(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [(Token.Prompt, "‣ ")]

    def out_prompt_tokens(self, cli=None):
        return [(Token.OutPrompt, "= ")]



def set_prompt(name):
    ip = get_ipython()

    if name == "before":
        ip.prompts = PromptBeforeImports(ip)

    if name == "after":
        ip.prompts = PromptAfterImports(ip)
