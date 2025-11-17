from typing import List, Dict, Any, Optional
import openai
from anthropic import Anthropic
import httpx
from ..config import settings
from ..models import AIModelProvider
from loguru import logger


class AIService:
    """Service for managing multiple AI model providers"""

    def __init__(self):
        # Initialize clients
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.deepseek_api_key = settings.DEEPSEEK_API_KEY

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        provider: AIModelProvider = AIModelProvider.OPENAI,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Generate AI response using the specified provider

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            provider: AI model provider to use
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with 'content' and 'tokens_used'
        """
        try:
            if provider == AIModelProvider.OPENAI:
                return await self._openai_response(messages, system_prompt, temperature, max_tokens)
            elif provider == AIModelProvider.ANTHROPIC:
                return await self._anthropic_response(messages, system_prompt, temperature, max_tokens)
            elif provider == AIModelProvider.DEEPSEEK:
                return await self._deepseek_response(messages, system_prompt, temperature, max_tokens)
            else:
                raise ValueError(f"Unsupported AI provider: {provider}")
        except Exception as e:
            logger.error(f"Error generating AI response with {provider}: {str(e)}")
            raise

    async def _openai_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Generate response using OpenAI"""
        formatted_messages = []

        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})

        formatted_messages.extend(messages)

        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return {
            "content": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens
        }

    async def _anthropic_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Generate response using Anthropic Claude"""
        # Anthropic expects system prompt separately
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt if system_prompt else "",
            messages=messages
        )

        return {
            "content": response.content[0].text,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens
        }

    async def _deepseek_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Generate response using DeepSeek"""
        if not self.deepseek_api_key:
            raise ValueError("DeepSeek API key not configured")

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": formatted_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

        return {
            "content": data["choices"][0]["message"]["content"],
            "tokens_used": data["usage"]["total_tokens"]
        }

    async def generate_agentic_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        lesson_context: Optional[Dict[str, Any]],
        provider: AIModelProvider = AIModelProvider.OPENAI
    ) -> Dict[str, Any]:
        """
        Generate agentic response with coaching context

        Args:
            user_message: Current user message
            conversation_history: Previous conversation messages
            lesson_context: Context about the current lesson
            provider: AI model provider

        Returns:
            AI response with content and metadata
        """
        # Build system prompt for coaching agent
        system_prompt = self._build_coaching_prompt(lesson_context)

        # Combine conversation history with new message
        messages = conversation_history + [{"role": "user", "content": user_message}]

        # Generate response
        return await self.generate_response(
            messages=messages,
            provider=provider,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2000
        )

    def _build_coaching_prompt(self, lesson_context: Optional[Dict[str, Any]]) -> str:
        """Build system prompt for coaching agent"""
        base_prompt = """You are an expert AI business and personal development coach. Your role is to:
1. Guide users through business scenarios and help them develop professional skills
2. Ask probing questions to encourage critical thinking
3. Provide constructive feedback on user responses
4. Identify patterns in behavior and decision-making
5. Adapt your coaching style to the user's level and needs

Your coaching approach should be:
- Supportive yet challenging
- Focused on practical, actionable insights
- Evidence-based and professional
- Culturally sensitive and inclusive
"""

        if lesson_context:
            lesson_prompt = f"""
Current Lesson: {lesson_context.get('title', 'General Coaching')}
Type: {lesson_context.get('lesson_type', 'general')}
Scenario: {lesson_context.get('scenario', 'N/A')}

Objectives for this lesson:
{chr(10).join(f"- {obj}" for obj in lesson_context.get('objectives', []))}

Guide the user through this scenario, helping them meet the learning objectives.
"""
            return base_prompt + lesson_prompt

        return base_prompt


# Singleton instance
ai_service = AIService()
