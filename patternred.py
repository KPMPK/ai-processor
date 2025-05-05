from f5_ai_gateway_sdk.parameters import Parameters
from f5_ai_gateway_sdk.processor import Processor
from f5_ai_gateway_sdk.processor_routes import ProcessorRoutes
from f5_ai_gateway_sdk.request_input import Message, MessageRole
from f5_ai_gateway_sdk.result import Result
from f5_ai_gateway_sdk.signature import BOTH_SIGNATURE
from f5_ai_gateway_sdk.tags import Tags
from f5_ai_gateway_sdk.type_hints import Metadata
from starlette.applications import Starlette
from pydantic import Field, ConfigDict
from typing import List
import re

DEFAULT_PLACEHOLDER = "*"

class PatternRedactorParameters(Parameters):
    """
    Data class defining the parameters for the Pattern input by user.
    These parameters include a list of pattern, which are use as pattern matching algorithm.

    Attributes:
        rules (List[str]): A list of pattern to be use for matching algorithm.
    """

    model_config = ConfigDict(title="Pattern Redactor parameters")

    rules: List[str] = Field(
        default_factory=lambda: [
            r'(นาย|นาง|นางสาว|นส|เงินเดือน|\.)(?:\s*)(\S+)\s+(\S+)',  # รูปแบบ (จับชื่อ-นามสกุล)
            r'\d{13}',  #  pattern thai national id
            r'\d{1}-\d{4}-\d{5}-\d{2}-\d{1}',# pattern thai national id
            r'\d{3}-\d{3}-\d{4}',  #  pattern Mobile
            r'\d{3}-\d{7}', #  pattern Mobile
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', #  pattern email
        ],
        title="Pattern Redactor",
    )

    debug_echo: bool = Field(
        default=False,
        description="Flag indicating if enable debug-echo to return redacted data",
    )

    placeholder: str = Field(
        default=DEFAULT_PLACEHOLDER,
        description="Placeholder that will be used as replacement for matched pattern",
    )

    reveal_start: int = Field(
        default=2,
        description="Number of characters to keep visible at the start",
    )

    reveal_end: int = Field(
        default=2,
        description="Number of characters to keep visible at the end",
    )

class PatternRedactorProcessor(Processor):
    """
    A simple processor which redact based on matched pattern
    """

    def __init__(self):
        super().__init__(
            name="pattern-redactor",
            version="v1",
            namespace="community",
            signature=BOTH_SIGNATURE,
            parameters_class=PatternRedactorParameters,
        )

    def mask_matches(self, content: str, patterns: list, reveal_start: int, reveal_end: int, placeholder: str) -> str:
        """
        Replace all matches of multiple regex patterns in the content with partial asterisks masking.

        :param content: The input text where the regex will be applied.
        :param patterns: A list of regex patterns to search for.
        :param reveal_start: Number of characters to keep visible at the start.
        :param reveal_end: Number of characters to keep visible at the end.
        :return: The modified text with matches partially replaced by placeholder.
        """
        def partial_mask(match):
            matched_text = match.group()
            length = len(matched_text)

            if length <= reveal_start + reveal_end:
                return placeholder * length  # Fully mask very short matches

            visible_start = matched_text[:reveal_start]  # Keep specified start characters visible
            visible_end = matched_text[-reveal_end:]  # Keep specified end characters visible
            masked_part = placeholder * (length - (reveal_start + reveal_end))  # Mask the middle part

            return visible_start + masked_part + visible_end

        compiled_patterns = [re.compile(pattern) for pattern in patterns]  # Precompile patterns for efficiency

        for pattern in compiled_patterns:
            content = pattern.sub(partial_mask, content)  # Apply partial masking

        return content

    def process(self, prompt, response, metadata, parameters: PatternRedactorParameters, request) -> Result:
        my_tags = Tags()

        user_input = " ".join(message.content for message in prompt.messages if message.role == MessageRole.USER)

        masked_content = self.mask_matches(user_input, parameters.rules, parameters.reveal_start, parameters.reveal_end, parameters.placeholder)

        # For inputStage to mask the prompt
        # Overwrite the user input in prompt.messages
        for message in prompt.messages:
            if message.role == MessageRole.USER:
                message.content = masked_content
                break

        # For responseStage to mask the response
        print(f"Original response content: {response}")
        if response:
            # Extract response content
            response_content = ""
            if response and hasattr(response, "choices"):  # Check if response has 'choices' attribute
                choices = response.choices
                if choices and hasattr(choices[0], "message"):
                    response_content = choices[0].message.content  # Get actual text content
                    print(f"Original response content: {response_content}")
                    masked_response_content = self.mask_matches(response_content, parameters.rules, parameters.reveal_start, parameters.reveal_end, parameters.placeholder)
                    print(f"Masked response content: {masked_response_content}")
            result = Result(modified=True, rejected=False)

            if response is not None:
                for choice in response.choices:
                    choice.message.content = masked_response_content

        my_tags = Tags()
        result = Metadata({"llm_flow": "debug"})

        if parameters.debug_echo and prompt:
            my_tags.add_tag("llm_flow", "debug")
            prompt.messages.append(
                Message(
                    content=masked_content,
                    role=MessageRole.SYSTEM,
                )
            )
            return Result(
                processor_result=result,
                tags=my_tags,
                modified=True,
                modified_prompt=prompt,
            )

        return Result(
            processor_result=result,
            tags=my_tags,
            modified=True,
            modified_prompt=prompt if not response else None,
            modified_response=response,
        )

app = Starlette(
    routes=ProcessorRoutes([PatternRedactorProcessor()]),
)
