import asyncio
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import traceback
from typing import Callable, Awaitable
from fastapi import APIRouter, WebSocket
import openai
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
from codegen.utils import extract_html_content
from config import (
    ANTHROPIC_API_KEY,
    GEMINI_API_KEY,
    IS_PROD,
    NUM_VARIANTS,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    REPLICATE_API_KEY,
    SHOULD_MOCK_AI_RESPONSE,
)
from custom_types import InputMode
from llm import (
    Completion,
    Llm,
    OPENAI_MODELS,
    ANTHROPIC_MODELS,
    GEMINI_MODELS,
)
from models import (
    stream_claude_response,
    stream_claude_response_native,
    stream_openai_response,
    stream_gemini_response,
)
from fs_logging.core import write_logs
from mock_llm import mock_completion
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    List,
    Literal,
    cast,
    get_args,
)
from openai.types.chat import ChatCompletionMessageParam

from utils import print_prompt_summary

# WebSocket message types
MessageType = Literal[
    "chunk",
    "status",
    "setCode",
    "error",
    "variantComplete",
    "variantError",
    "variantCount",
    "thinking",
]
from image_generation.core import generate_images
from image_processing.cropper import process_image_regions, process_manual_regions
import json
from prompts import create_prompt
from prompts.claude_prompts import VIDEO_PROMPT
from prompts.types import Stack, PromptContent

# from utils import pprint_prompt
from ws.constants import APP_ERROR_WEB_SOCKET_CODE  # type: ignore
from history_manager import HistoryManager

router = APIRouter()


class VariantErrorAlreadySent(Exception):
    """Exception that indicates a variantError message has already been sent to frontend"""

    def __init__(self, original_error: Exception):
        self.original_error = original_error
        super().__init__(str(original_error))


@dataclass
class PipelineContext:
    """Context object that carries state through the pipeline"""

    websocket: WebSocket
    ws_comm: "WebSocketCommunicator | None" = None
    params: Dict[str, str] = field(default_factory=dict)
    extracted_params: "ExtractedParams | None" = None
    prompt_messages: List[ChatCompletionMessageParam] = field(default_factory=list)
    image_cache: Dict[str, str] = field(default_factory=dict)
    variant_models: List[Llm] = field(default_factory=list)
    completions: List[str] = field(default_factory=list)
    variant_completions: Dict[int, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None

    @property
    def send_message(self):
        assert self.ws_comm is not None
        return self.ws_comm.send_message

    @property
    def throw_error(self):
        assert self.ws_comm is not None
        return self.ws_comm.throw_error


class Middleware(ABC):
    """Base class for all pipeline middleware"""

    @abstractmethod
    async def process(
        self, context: PipelineContext, next_func: Callable[[], Awaitable[None]]
    ) -> None:
        """Process the context and call the next middleware"""
        pass


class Pipeline:
    """Pipeline for processing WebSocket code generation requests"""

    def __init__(self):
        self.middlewares: List[Middleware] = []

    def use(self, middleware: Middleware) -> "Pipeline":
        """Add a middleware to the pipeline"""
        self.middlewares.append(middleware)
        return self

    async def execute(self, websocket: WebSocket) -> None:
        """Execute the pipeline with the given WebSocket"""
        context = PipelineContext(websocket=websocket)

        # Build the middleware chain
        async def start(ctx: PipelineContext):
            pass  # End of pipeline

        # History middlewares should be added in stream_code to ensure correct order

        chain = start
        for middleware in reversed(self.middlewares):
            chain = self._wrap_middleware(middleware, chain)

        await chain(context)

    def _wrap_middleware(
        self,
        middleware: Middleware,
        next_func: Callable[[PipelineContext], Awaitable[None]],
    ) -> Callable[[PipelineContext], Awaitable[None]]:
        """Wrap a middleware with its next function"""

        async def wrapped(context: PipelineContext) -> None:
            await middleware.process(context, lambda: next_func(context))

        return wrapped


class WebSocketCommunicator:
    """Handles WebSocket communication with consistent error handling"""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.is_closed = False

    async def accept(self) -> None:
        """Accept the WebSocket connection"""
        await self.websocket.accept()
        print("Incoming websocket connection...")

    async def send_message(
        self,
        type: MessageType,
        value: str,
        variantIndex: int,
    ) -> None:
        """Send a message to the client with debug logging"""
        if self.is_closed:
            return

        # Print for debugging on the backend
        if type == "error":
            print(f"Error (variant {variantIndex + 1}): {value}")
        elif type == "status":
            print(f"Status (variant {variantIndex + 1}): {value}")
        elif type == "variantComplete":
            print(f"Variant {variantIndex + 1} complete")
        elif type == "variantError":
            print(f"Variant {variantIndex + 1} error: {value}")

        try:
            await self.websocket.send_json(
                {"type": type, "value": value, "variantIndex": variantIndex}
            )
        except (ConnectionClosedOK, ConnectionClosedError):
            print(f"WebSocket closed by client, skipping message: {type}")
            self.is_closed = True

    async def throw_error(self, message: str) -> None:
        """Send an error message and close the connection"""
        print(message)
        if not self.is_closed:
            try:
                await self.websocket.send_json({"type": "error", "value": message})
                await self.websocket.close(APP_ERROR_WEB_SOCKET_CODE)
            except (ConnectionClosedOK, ConnectionClosedError):
                print("WebSocket already closed by client")
            self.is_closed = True

    async def receive_params(self) -> Dict[str, str]:
        """Receive parameters from the client"""
        params: Dict[str, str] = await self.websocket.receive_json()
        print("Received params")
        return params

    async def close(self) -> None:
        """Close the WebSocket connection"""
        if not self.is_closed:
            try:
                await self.websocket.close()
            except (ConnectionClosedOK, ConnectionClosedError):
                pass  # Already closed by client
            self.is_closed = True


@dataclass
class ExtractedParams:
    stack: Stack
    input_mode: InputMode
    should_generate_images: bool
    gemini_api_key: str | None
    openai_api_key: str | None  # Kept for compatibility but unused
    anthropic_api_key: str | None # Kept for compatibility but unused
    openai_base_url: str | None
    generation_type: Literal["create", "update"]
    prompt: PromptContent
    history: List[Dict[str, Any]]
    history: List[Dict[str, Any]]
    is_imported_from_code: bool
    is_template_enabled: bool
    template_content: str | None
    include_thoughts: bool
    parent_session_id: str | None
    code_generation_model: str | None


class ParameterExtractionStage:
    """Handles parameter extraction and validation from WebSocket requests"""

    def __init__(self, throw_error: Callable[[str], Coroutine[Any, Any, None]]):
        self.throw_error = throw_error

    async def extract_and_validate(self, params: Dict[str, str]) -> ExtractedParams:
        """Extract and validate all parameters from the request"""
        # Read the code config settings (stack) from the request.
        generated_code_config = params.get("generatedCodeConfig", "")
        if generated_code_config not in get_args(Stack):
            await self.throw_error(
                f"Invalid generated code config: {generated_code_config}"
            )
            raise ValueError(f"Invalid generated code config: {generated_code_config}")
        validated_stack = cast(Stack, generated_code_config)

        # Validate the input mode
        input_mode = params.get("inputMode")
        if input_mode not in get_args(InputMode):
            await self.throw_error(f"Invalid input mode: {input_mode}")
            raise ValueError(f"Invalid input mode: {input_mode}")
        validated_input_mode = cast(InputMode, input_mode)

        gemini_api_key = self._get_from_settings_dialog_or_env(
            params, "geminiApiKey", GEMINI_API_KEY
        )

        openai_api_key = None
        anthropic_api_key = None
        openai_base_url = None

        # Get the image generation flag from the request. Fall back to True if not provided.
        should_generate_images = bool(params.get("isImageGenerationEnabled", True))

        # Extract and validate generation type
        generation_type = params.get("generationType", "create")
        if generation_type not in ["create", "update"]:
            await self.throw_error(f"Invalid generation type: {generation_type}")
            raise ValueError(f"Invalid generation type: {generation_type}")
        generation_type = cast(Literal["create", "update"], generation_type)

        # Extract prompt content
        prompt = params.get("prompt", {"text": "", "images": []})

        # Extract history (default to empty list)
        history = params.get("history", [])

        # Extract imported code flag
        is_imported_from_code = params.get("isImportedFromCode", False)

        # Extract template params
        is_template_enabled = bool(params.get("isTemplateEnabled", False))
        template_content = params.get("templateContent")

        include_thoughts = bool(params.get("includeThoughts", False))
        parent_session_id = params.get("parentSessionId")
        code_generation_model = params.get("codeGenerationModel")

        return ExtractedParams(
            stack=validated_stack,
            input_mode=validated_input_mode,
            should_generate_images=should_generate_images,
            gemini_api_key=gemini_api_key,
            openai_api_key=None,
            anthropic_api_key=None,
            openai_base_url=None,
            generation_type=generation_type,
            prompt=prompt,
            history=history,
            is_imported_from_code=is_imported_from_code,
            is_template_enabled=is_template_enabled,
            template_content=template_content,
            include_thoughts=include_thoughts,
            parent_session_id=parent_session_id,
            code_generation_model=code_generation_model,
        )


    def _get_from_settings_dialog_or_env(
        self, params: dict[str, str], key: str, env_var: str | None
    ) -> str | None:
        """Get value from client settings or environment variable"""
        value = params.get(key)
        if value:
            print(f"Using {key} from client-side settings dialog")
            return value

        if env_var:
            print(f"Using {key} from environment variable")
            return env_var

        return None


class HistoryMiddleware(Middleware):
    """Middleware to manage history recording"""

    def __init__(self):
        self.history_manager = HistoryManager()

    async def process(
        self, context: PipelineContext, next_func: Callable[[], Awaitable[None]]
    ) -> None:
        # Create session if extracted_params exists
        if context.extracted_params:
            # Prepare params for saving
            params_to_save = {
                "input_mode": context.extracted_params.input_mode,
                "generation_type": context.extracted_params.generation_type,
                "prompt": context.extracted_params.prompt,
                "is_imported_from_code": context.extracted_params.is_imported_from_code,
                "parent_session_id": context.extracted_params.parent_session_id,
            }
            context.session_id = self.history_manager.create_session(params_to_save)
            print(f"Created history session: {context.session_id}")

            # Send session ID to client
            if context.websocket:
                await context.websocket.send_json({
                    "type": "session_id",
                    "value": context.session_id
                })

        await next_func()

class ContextInjectionMiddleware(Middleware):
    """Middleware to inject past thoughts if requested"""
    
    def __init__(self):
        self.history_manager = HistoryManager()

    async def process(
        self, context: PipelineContext, next_func: Callable[[], Awaitable[None]]
    ) -> None:
        # Check if we should include past thoughts
        if context.extracted_params and context.extracted_params.include_thoughts:
            print("Including past thoughts in context...")
            latest_thought = self.history_manager.get_latest_thought()
            if latest_thought:
                # Inject into the user prompt or system prompt?
                # Usually best to append to the last user message to give context
                # Or prepend? "Here is your previous thinking process: ..."
                
                # We modify the prompt in extracted_params directly? 
                # Or wait until prompt creation? 
                # extracted_params.prompt is a PromptContent object or dict?
                # PromptContent is a TypedDict usually (or Pydantic model?)
                # In custom_types.py it is probably defined.
                # Let's assume prompt param handling is flexible.
                
                thought_context = f"\n\n[Previous Thinking Process for CONTEXT]:\n{latest_thought}\n\n"
                
                # Check if prompt is text-based update
                # extracted_params.history has previous messages.
                # If this is an update, we usually append to the last user message in history?
                # Or if generation_type == "update", we might want to inform the model 
                # explicitly about its past thought.
                
                # Simplest way: Append to the 'prompt' (which is the new instruction)
                # context.extracted_params.prompt comes from params['prompt'].
                # It has 'text' and 'images'.
                
                # We need to act carefully not to break the object structure.
                # extracted_params is dataclass, so mutable? Yes.
                
                current_text = context.extracted_params.prompt.get("text", "")
                context.extracted_params.prompt["text"] = current_text + thought_context
                print("Injected thought context into prompt.")
            else:
                print("No past thought found to include.")
        
        await next_func()




class ModelSelectionStage:
    """Handles selection of variant models based on available API keys and generation type"""

    def __init__(self, throw_error: Callable[[str], Coroutine[Any, Any, None]]):
        self.throw_error = throw_error

    async def select_models(
        self,
        generation_type: Literal["create", "update"],
        input_mode: InputMode,
        openai_api_key: str | None,
        anthropic_api_key: str | None,
        gemini_api_key: str | None = None,
        code_generation_model: str | None = None,
    ) -> List[Llm]:
        """Select appropriate models based on available API keys"""
        try:
            variant_models = self._get_variant_models(
                generation_type,
                input_mode,
                NUM_VARIANTS,
                openai_api_key,
                anthropic_api_key,
                gemini_api_key,
                code_generation_model,
            )

            # Print the variant models (one per line)
            print("Variant models:")
            for index, model in enumerate(variant_models):
                print(f"Variant {index + 1}: {model.value}")

            return variant_models
        except Exception:
            await self.throw_error(
                "No OpenAI, Anthropic, or Gemini API key found. Please add the environment variable "
                "OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY to backend/.env. "
                "If you add it to .env, make sure to restart the backend server."
            )
            raise Exception("No OpenAI, Anthropic, or Gemini key")

    def _get_variant_models(
        self,
        generation_type: Literal["create", "update"],
        input_mode: InputMode,
        num_variants: int,
        openai_api_key: str | None,
        anthropic_api_key: str | None,
        gemini_api_key: str | None,
        code_generation_model: str | None = None,
    ) -> List[Llm]:
        """Simple model cycling that scales with num_variants"""

        # If a specific model is requested, try to use it
        if code_generation_model:
            try:
                model_enum = Llm(code_generation_model)
                return [model_enum] * num_variants
            except ValueError:
                # If the model string is not a valid Llm enum, fall back to default logic
                print(f"Warning: Unknown model {code_generation_model}, falling back to default selection.")

        # Default to Gemini models as requested
        models = [
            Llm.GEMINI_3_FLASH_PREVIEW_HIGH,
            Llm.GEMINI_3_PRO_PREVIEW_HIGH,
            Llm.GEMINI_2_0_FLASH,
        ]

        # Cycle through models: [A, B] with num=5 becomes [A, B, A, B, A]
        selected_models: List[Llm] = []
        for i in range(num_variants):
            selected_models.append(models[i % len(models)])

        return selected_models


class PromptCreationStage:
    """Handles prompt assembly for code generation"""

    def __init__(self, throw_error: Callable[[str], Coroutine[Any, Any, None]]):
        self.throw_error = throw_error

    async def create_prompt(
        self,
        extracted_params: ExtractedParams,
    ) -> tuple[List[ChatCompletionMessageParam], Dict[str, str]]:
        """Create prompt messages and return image cache"""
        try:
            prompt_messages, image_cache = await create_prompt(
                stack=extracted_params.stack,
                input_mode=extracted_params.input_mode,
                generation_type=extracted_params.generation_type,
                prompt=extracted_params.prompt,
                history=extracted_params.history,
                is_imported_from_code=extracted_params.is_imported_from_code,
                is_template_enabled=extracted_params.is_template_enabled,
                template_content=extracted_params.template_content,
            )

            print_prompt_summary(prompt_messages, truncate=False)

            return prompt_messages, image_cache
        except Exception:
            await self.throw_error(
                "Error assembling prompt. Contact support at support@picoapps.xyz"
            )
            raise


class MockResponseStage:
    """Handles mock AI responses for testing"""

    def __init__(
        self,
        send_message: Callable[[MessageType, str, int], Coroutine[Any, Any, None]],
    ):
        self.send_message = send_message

    async def generate_mock_response(
        self,
        input_mode: InputMode,
    ) -> List[str]:
        """Generate mock response for testing"""

        async def process_chunk(content: str, variantIndex: int):
            await self.send_message("chunk", content, variantIndex)

        completion_results = [
            await mock_completion(process_chunk, input_mode=input_mode)
        ]
        completions = [result["code"] for result in completion_results]

        # Send the complete variant back to the client
        await self.send_message("setCode", completions[0], 0)
        await self.send_message("variantComplete", "Variant generation complete", 0)

        return completions


class VideoGenerationStage:
    """Handles video mode code generation using Claude 3 Opus"""

    def __init__(
        self,
        send_message: Callable[[MessageType, str, int], Coroutine[Any, Any, None]],
        throw_error: Callable[[str], Coroutine[Any, Any, None]],
    ):
        self.send_message = send_message
        self.throw_error = throw_error

    async def generate_video_code(
        self,
        prompt_messages: List[ChatCompletionMessageParam],
        anthropic_api_key: str | None,
    ) -> List[str]:
        """Generate code for video input mode"""
        if not anthropic_api_key:
            await self.throw_error(
                "Video only works with Anthropic models. No Anthropic API key found. "
                "Please add the environment variable ANTHROPIC_API_KEY to backend/.env "
                "or in the settings dialog"
            )
            raise Exception("No Anthropic key")

        async def process_chunk(content: str, variantIndex: int):
            await self.send_message("chunk", content, variantIndex)

        completion_results = [
            await stream_claude_response_native(
                system_prompt=VIDEO_PROMPT,
                messages=prompt_messages,  # type: ignore
                api_key=anthropic_api_key,
                callback=lambda x: process_chunk(x, 0),
                model_name=Llm.CLAUDE_3_OPUS.value,
                include_thinking=True,
            )
        ]
        completions = [result["code"] for result in completion_results]

        # Send the complete variant back to the client
        await self.send_message("setCode", completions[0], 0)
        await self.send_message("variantComplete", "Variant generation complete", 0)

        return completions


class PostProcessingStage:
    """Handles post-processing after code generation completes"""

    def __init__(self):
        pass

    async def process_completions(
        self,
        completions: List[str],
        prompt_messages: List[ChatCompletionMessageParam],
        websocket: WebSocket,
        session_id: str | None = None,
        history_manager: "HistoryManager | None" = None,
    ) -> None:
        """Process completions and perform cleanup"""
        # Only process non-empty completions
        valid_completions = [comp for comp in completions if comp]

        # Write the first valid completion to logs for debugging
        if valid_completions:
            # Strip the completion of everything except the HTML content
            html_content = extract_html_content(valid_completions[0])
            write_logs(prompt_messages, html_content)
        
        # Save to history if session exists
        if history_manager and session_id:
             for i, completion in enumerate(completions):
                if completion:
                     history_manager.save_code(session_id, i, completion)
                     print(f"Saved code for variant {i} to history {session_id}")

        # Note: WebSocket closing is handled by the caller


class ParallelGenerationStage:
    """Handles parallel variant generation using Gemini only"""

    def __init__(
        self,
        send_message: Callable[[MessageType, str, int], Coroutine[Any, Any, None]],
        should_generate_images: bool,
        screenshot_url: str | None = None,
        session_id: str | None = None,
        manual_region_urls: Dict[str, str] | None = None,
    ):
        self.send_message = send_message
        self.should_generate_images = should_generate_images
        self.screenshot_url = screenshot_url
        self.session_id = session_id
        self.manual_region_urls = manual_region_urls or {}

    async def process_variants(
        self,
        variant_models: List[Llm],
        prompt_messages: List[ChatCompletionMessageParam],
        image_cache: Dict[str, str],
        params: Dict[str, str],
        session_id: str | None = None,
        history_manager: "HistoryManager | None" = None,
    ) -> Dict[int, str]:
        """Process all variants in parallel and return completions"""
        tasks = self._create_generation_tasks(variant_models, prompt_messages, params, session_id, history_manager)

        # Dictionary to track variant tasks and their status
        variant_tasks: Dict[int, asyncio.Task[Completion]] = {}
        variant_completions: Dict[int, str] = {}

        # Create tasks for each variant
        for index, task in enumerate(tasks):
            variant_task = asyncio.create_task(task)
            variant_tasks[index] = variant_task

        # Process each variant independently
        variant_processors = [
            self._process_variant_completion(
                index, task, variant_models[index], image_cache, variant_completions, session_id, history_manager
            )
            for index, task in variant_tasks.items()
        ]

        # Wait for all variants to complete
        await asyncio.gather(*variant_processors, return_exceptions=True)

        return variant_completions

    def _create_generation_tasks(
        self,
        variant_models: List[Llm],
        prompt_messages: List[ChatCompletionMessageParam],
        params: Dict[str, str],
        session_id: str | None = None,
        history_manager: "HistoryManager | None" = None,
    ) -> List[Coroutine[Any, Any, Completion]]:
        """Create generation tasks for each variant model"""
        tasks: List[Coroutine[Any, Any, Completion]] = []

        if not GEMINI_API_KEY:
             raise Exception("Gemini API key is missing. Please add GEMINI_API_KEY to backend/.env")

        for index, model in enumerate(variant_models):
             # Force Gemini usage for all logic
             tasks.append(
                stream_gemini_response(
                    prompt_messages,
                    api_key=GEMINI_API_KEY,
                    callback=lambda x, i=index: self._process_chunk(x, i),
                    model_name=model.value,
                    thinking_callback=lambda x, i=index: self._process_thinking(x, i, session_id, history_manager),
                )
            )

        return tasks

    async def _process_chunk(self, content: str, variant_index: int):
        """Process streaming chunks"""
        await self.send_message("chunk", content, variant_index)

    async def _process_thinking(
        self, 
        content: str, 
        variant_index: int,
        session_id: str | None = None,
        history_manager: "HistoryManager | None" = None,
    ):
        """Process thinking/reasoning content"""
        await self.send_message("thinking", content, variant_index)
        
        if history_manager and session_id:
            history_manager.append_thought(session_id, variant_index, content)
    # OpenAI error handling removed


    async def _perform_image_generation(
        self,
        completion: str,
        image_cache: dict[str, str],
    ):
        """Generate images for the completion if needed"""
        if not self.should_generate_images:
            return completion

        replicate_api_key = REPLICATE_API_KEY
        if replicate_api_key:
            image_generation_model = "flux"
            api_key = replicate_api_key
        else:
            if not self.openai_api_key:
                print(
                    "No OpenAI API key and Replicate key found. Skipping image generation."
                )
                return completion
            image_generation_model = "dalle3"
            api_key = self.openai_api_key

        print("Generating images with model: ", image_generation_model)

        return await generate_images(
            completion,
            api_key=api_key,
            base_url=self.openai_base_url,
            image_cache=image_cache,
            model=image_generation_model,
        )

    async def _process_variant_completion(
        self,
        index: int,
        task: asyncio.Task[Completion],
        model: Llm,
        image_cache: Dict[str, str],
        variant_completions: Dict[int, str],
        session_id: str | None = None,
        history_manager: "HistoryManager | None" = None,
    ):
        """Process a single variant completion including image generation"""
        try:
            completion = await task

            print(f"{model.value} completion took {completion['duration']:.2f} seconds")
            variant_completions[index] = completion["code"]
            
            # Save raw code if history manager is present
            if history_manager and session_id:
                 history_manager.save_code(session_id, index, completion["code"])

            try:
                # Process images for this variant
                processed_html = await self._perform_image_generation(
                    completion["code"],
                    image_cache,
                )

                # Extract HTML content
                processed_html = extract_html_content(processed_html)

                # Handle image URLs
                if self.manual_region_urls:
                    # Manual regions: replace __SCREENSHOT_URL__ with user-cropped images
                    # Sort by order in HTML to ensure correct assignment
                    print(f"[MANUAL REGIONS] Replacing with {len(self.manual_region_urls)} cropped URLs")
                    for region_id, url in self.manual_region_urls.items():
                        # Replace first occurrence of __SCREENSHOT_URL__
                        if "__SCREENSHOT_URL__" in processed_html:
                            processed_html = processed_html.replace("__SCREENSHOT_URL__", url, 1)
                            print(f"[MANUAL REGIONS] Replaced {region_id} -> {url}")
                    
                    # Replace any remaining __SCREENSHOT_URL__ with original
                    if self.screenshot_url and "__SCREENSHOT_URL__" in processed_html:
                        processed_html = processed_html.replace("__SCREENSHOT_URL__", self.screenshot_url)
                        
                elif self.screenshot_url and self.session_id:
                    # AI-based cropping: parse comments from generated HTML
                    processed_html = process_image_regions(
                        processed_html,
                        self.screenshot_url,
                        self.session_id,
                    )
                elif self.screenshot_url:
                    # Fallback: Replace __SCREENSHOT_URL__ with actual screenshot URL
                    processed_html = processed_html.replace("__SCREENSHOT_URL__", self.screenshot_url)

                # Send the complete variant back to the client
                await self.send_message("setCode", processed_html, index)
                await self.send_message(
                    "variantComplete",
                    "Variant generation complete",
                    index,
                )
            except Exception as inner_e:
                # If websocket is closed or other error during post-processing
                print(f"Post-processing error for variant {index + 1}: {inner_e}")
                # We still keep the completion in variant_completions
                # And saving happens before image processing so we are good.

        except Exception as e:
            # Handle any errors that occurred during generation
            print(f"Error in variant {index + 1}: {e}")
            traceback.print_exception(type(e), e, e.__traceback__)

            # Only send error message if it hasn't been sent already
            if not isinstance(e, VariantErrorAlreadySent):
                await self.send_message("variantError", str(e), index)


# Pipeline Middleware Implementations


class WebSocketSetupMiddleware(Middleware):
    """Handles WebSocket setup and teardown"""

    async def process(
        self, context: PipelineContext, next_func: Callable[[], Awaitable[None]]
    ) -> None:
        # Create and setup WebSocket communicator
        context.ws_comm = WebSocketCommunicator(context.websocket)
        await context.ws_comm.accept()

        try:
            await next_func()
        finally:
            # Always close the WebSocket
            await context.ws_comm.close()


class ParameterExtractionMiddleware(Middleware):
    """Handles parameter extraction and validation"""

    async def process(
        self, context: PipelineContext, next_func: Callable[[], Awaitable[None]]
    ) -> None:
        # Receive parameters
        assert context.ws_comm is not None
        context.params = await context.ws_comm.receive_params()

        # Extract and validate
        param_extractor = ParameterExtractionStage(context.throw_error)
        context.extracted_params = await param_extractor.extract_and_validate(
            context.params
        )

        # Log what we're generating
        print(
            f"Generating {context.extracted_params.stack} code in {context.extracted_params.input_mode} mode"
        )

        await next_func()


class StatusBroadcastMiddleware(Middleware):
    """Sends initial status messages to all variants"""

    async def process(
        self, context: PipelineContext, next_func: Callable[[], Awaitable[None]]
    ) -> None:
        # Tell frontend how many variants we're using
        await context.send_message("variantCount", str(NUM_VARIANTS), 0)

        for i in range(NUM_VARIANTS):
            await context.send_message("status", "Generating code...", i)

        await next_func()


class PromptCreationMiddleware(Middleware):
    """Handles prompt creation"""

    async def process(
        self, context: PipelineContext, next_func: Callable[[], Awaitable[None]]
    ) -> None:
        prompt_creator = PromptCreationStage(context.throw_error)
        assert context.extracted_params is not None
        context.prompt_messages, context.image_cache = (
            await prompt_creator.create_prompt(
                context.extracted_params,
            )
        )

        await next_func()



class HybridV2GenerationStage:
    """Handles Hybrid V2 (Multi-Slice) generation"""

    def __init__(
        self,
        send_message: Callable[[MessageType, str, int], Coroutine[Any, Any, None]],
        gemini_api_key: str | None,
    ):
        self.send_message = send_message
        self.gemini_api_key = gemini_api_key

    async def generate_hybrid_v2(
        self,
        valid_images: List[str],  # List of data URLs
        prompt_text: str,
        input_mode: InputMode,
        code_generation_model: str = "gemini-2.0-flash",
    ) -> List[str]:
        """Iterate through images, generate sections, and combine."""
        
        combined_html_parts = []
        
        print(f"[HybridV2] Processing {len(valid_images)} slices...")
        
        # Inform frontend that we are only generating 1 variant
        await self.send_message("variantCount", 1, 0)

        # Base HTML wrapper
        combined_html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated LP</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { margin: 0; padding: 0; font-family: sans-serif; }
        .v2-section { width: 100%; }
        /* Floating animation for buttons */
        @keyframes float {
            0% { transform: translate(-50%, 0px); }
            50% { transform: translate(-50%, -5px); }
            100% { transform: translate(-50%, 0px); }
        }
        .animate-float { animation: float 3s ease-in-out infinite; }
    </style>
</head>
<body>
<div class="flex flex-col w-full max-w-[800px] mx-auto shadow-2xl">
""")

        # Process each slice
        for i, image_data_url in enumerate(valid_images):
            print(f"[HybridV2] Generating slice {i+1}/{len(valid_images)}")
            await self.send_message("status", f"Scanning slice {i+1} of {len(valid_images)}...", 0)
            
            # Create Prompt
            from prompts.hybrid_v2 import USER_PROMPT
            
            # Construct messages for this specific slice
            slice_messages: List[ChatCompletionMessageParam] = [
                {
                    "role": "system",
                    "content": "You are an expert web developer. Output only valid HTML code.",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_url, "detail": "high"},
                        },
                        {
                            "type": "text",
                            "text": USER_PROMPT + (f"\n\nUser Note: {prompt_text}" if prompt_text else ""),
                        },
                    ],
                }
            ]

            # Use requested model
            model_name = code_generation_model

            # Stream response for this slice
            slice_html = ""
            
            async def on_chunk(content: str):
                nonlocal slice_html
                slice_html += content
                # We don't stream chunks to frontend directly to avoid confusion, 
                # OR we stream to a console? 
                # Let's just stream "status" updates.

            try:
                # Always use Gemini for Hybrid V2 as requested by user
                # Implement retry logic for rate limits (429)
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await stream_gemini_response(
                            slice_messages,
                            api_key=self.gemini_api_key or GEMINI_API_KEY,
                            callback=on_chunk,
                            model_name=model_name,
                        )
                        break # Success, exit retry loop
                    except Exception as e:
                        is_rate_limit = "429" in str(e) or "ResourceExhausted" in str(e)
                        if is_rate_limit and attempt < max_retries - 1:
                            wait_time = 15 + (attempt * 5)
                            print(f"[HybridV2] Rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                            await self.send_message("status", f"Rate limited. Retrying slice {i+1} in {wait_time}s...", 0)
                            await asyncio.sleep(wait_time)
                            
                            # Clear partial HTML from failed attempt so we don't duplicate it
                            slice_html = "" 
                        else:
                            raise e # Re-raise if not rate limit or out of retries
                
                # Post-process: extract just the <section> part if model returns Markdown
                cleaned_html = extract_html_content(slice_html)
                cleaned_html = cleaned_html.replace("```html", "").replace("```", "")
                
                # Replace placeholder with actual image
                # In a real V2 system, we might upload to S3. Here we use Data URL (heavy) or assume client handling.
                # Since we are returning a single file, Data URL is safest for immediate preview.
                # Optimize: logic to keep it as Data URL.
                cleaned_html = cleaned_html.replace("__SLICE_IMAGE_SRC__", image_data_url)
                
                combined_html_parts.append(cleaned_html)
                
                # Small delay to keep API happy
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Error processing slice {i}: {e}")
                traceback.print_exc()
                await self.send_message("error", f"Error in slice {i+1}: {str(e)}", 0)

        combined_html_parts.append("</div></body></html>")
        
        full_html = "\n".join(combined_html_parts)
        
        # Send final code to frontend
        await self.send_message("setCode", full_html, 0)
        await self.send_message("variantComplete", "Hybrid V2 Generation Complete", 0)
        
        return [full_html]


class CodeGenerationMiddleware(Middleware):
    """Handles the main code generation logic"""

    async def process(
        self, context: PipelineContext, next_func: Callable[[], Awaitable[None]]
    ) -> None:
        if SHOULD_MOCK_AI_RESPONSE:
            # Use mock response for testing
            mock_stage = MockResponseStage(context.send_message)
            assert context.extracted_params is not None
            context.completions = await mock_stage.generate_mock_response(
                context.extracted_params.input_mode
            )
        else:
            try:
                assert context.extracted_params is not None
                
                # Check for Hybrid V2 Trigger: Multiple Images
                images = context.extracted_params.prompt.get("images", [])
                
                # If images is a list and has > 1 item, or if we want to force V2 for single image too?
                # The user context implied "drag drop multiple".
                if isinstance(images, list) and len(images) > 1:
                    print(f"Triggering Hybrid V2 for {len(images)} images")
                    hybrid_stage = HybridV2GenerationStage(
                        send_message=context.send_message,
                        gemini_api_key=context.extracted_params.gemini_api_key,
                    )
                    
                    context.completions = await hybrid_stage.generate_hybrid_v2(
                        valid_images=images,
                        prompt_text=context.extracted_params.prompt.get("text", ""),
                        input_mode=context.extracted_params.input_mode,
                        code_generation_model=context.extracted_params.code_generation_model
                    )
                    
                elif context.extracted_params.input_mode == "video":
                    # Use video generation for video mode
                    video_stage = VideoGenerationStage(
                        context.send_message, context.throw_error
                    )
                    context.completions = await video_stage.generate_video_code(
                        context.prompt_messages,
                        context.extracted_params.anthropic_api_key,
                    )
                else:
                    # Select models
                    model_selector = ModelSelectionStage(context.throw_error)
                    context.variant_models = await model_selector.select_models(
                        generation_type=context.extracted_params.generation_type,
                        input_mode=context.extracted_params.input_mode,
                        openai_api_key=context.extracted_params.openai_api_key,
                        anthropic_api_key=context.extracted_params.anthropic_api_key,
                        gemini_api_key=GEMINI_API_KEY,
                        code_generation_model=context.extracted_params.code_generation_model,
                    )

                    # Generate code for all variants
                    # Get the first image URL for __SCREENSHOT_URL__ replacement
                    images = context.extracted_params.prompt.get("images", [])
                    screenshot_url = images[0] if isinstance(images, list) and len(images) > 0 else None
                    
                    # Check for manual regions in the prompt text
                    manual_region_urls = {}
                    prompt_text = context.extracted_params.prompt.get("text", "")
                    if "__MANUAL_REGIONS__" in prompt_text:
                        try:
                            # Parse regions from prompt
                            import re as region_re
                            region_match = region_re.search(
                                r"__MANUAL_REGIONS__(.+?)__END_REGIONS__",
                                prompt_text,
                                region_re.DOTALL
                            )
                            if region_match and screenshot_url and context.session_id:
                                regions_json = region_match.group(1)
                                manual_regions = json.loads(regions_json)
                                print(f"[MANUAL REGIONS] Found {len(manual_regions)} manual regions in prompt")
                                
                                # Process regions: crop and remove background
                                manual_region_urls = process_manual_regions(
                                    screenshot_url,
                                    manual_regions,
                                    context.session_id,
                                )
                                
                                # Clean the prompt text
                                clean_prompt = prompt_text.replace(
                                    f"__MANUAL_REGIONS__{regions_json}__END_REGIONS__",
                                    ""
                                ).strip()
                                context.extracted_params.prompt["text"] = clean_prompt
                                
                                print(f"[MANUAL REGIONS] Processed {len(manual_region_urls)} regions")
                        except Exception as e:
                            print(f"[MANUAL REGIONS] Error parsing regions: {e}")
                    
                    generation_stage = ParallelGenerationStage(
                        send_message=context.send_message,
                        should_generate_images=context.extracted_params.should_generate_images,
                        screenshot_url=screenshot_url,
                        session_id=context.session_id,
                        manual_region_urls=manual_region_urls,  # Pass processed regions
                    )

                    context.variant_completions = (
                        await generation_stage.process_variants(
                            variant_models=context.variant_models,
                            prompt_messages=context.prompt_messages,
                            image_cache=context.image_cache,
                            params=context.params,
                            session_id=context.session_id,
                            history_manager=HistoryManager(),
                        )
                    )

                    # Check if all variants failed
                    if len(context.variant_completions) == 0:
                        # Cleanup empty session to avoid clogging history
                        if context.session_id:
                            try:
                                # context.session_id is "date_str/session_id"
                                parts = context.session_id.split("/")
                                if len(parts) == 2:
                                    HistoryManager().delete_session(parts[0], parts[1])
                                    print(f"Deleted empty session {context.session_id} due to generation failure.")
                            except Exception as e:
                                print(f"Error deleting empty session: {e}")

                        await context.throw_error(
                            "Error generating code. Please contact support."
                        )
                        return  # Don't continue the pipeline

                    # Convert to list format
                    context.completions = []
                    for i in range(len(context.variant_models)):
                        if i in context.variant_completions:
                            context.completions.append(context.variant_completions[i])
                        else:
                            context.completions.append("")

            except Exception as e:
                print(f"[GENERATE_CODE] Unexpected error: {e}")
                # Print stack trace
                traceback.print_exc()
                await context.throw_error(f"An unexpected error occurred: {str(e)}")
                return  # Don't continue the pipeline

        await next_func()


class PostProcessingMiddleware(Middleware):
    """Handles post-processing and logging"""

    async def process(
        self, context: PipelineContext, next_func: Callable[[], Awaitable[None]]
    ) -> None:
        post_processor = PostProcessingStage()
        await post_processor.process_completions(
            context.completions, 
            context.prompt_messages, 
            context.websocket,
            context.session_id,
            HistoryManager()
        )

        await next_func()


@router.websocket("/generate-code")
async def stream_code(websocket: WebSocket):
    """Handle WebSocket code generation requests using a pipeline pattern"""
    pipeline = Pipeline()

    # Configure the pipeline
    pipeline.use(WebSocketSetupMiddleware())
    pipeline.use(ParameterExtractionMiddleware())
    pipeline.use(HistoryMiddleware())
    pipeline.use(ContextInjectionMiddleware())
    pipeline.use(StatusBroadcastMiddleware())
    pipeline.use(PromptCreationMiddleware())
    pipeline.use(CodeGenerationMiddleware())
    pipeline.use(PostProcessingMiddleware())

    # Execute the pipeline
    await pipeline.execute(websocket)

