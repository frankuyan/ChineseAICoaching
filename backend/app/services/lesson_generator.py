from typing import List, Dict, Any, Optional
from ..models import AIModelProvider, LessonType
from .ai_service import ai_service
from loguru import logger
import json


class LessonGeneratorService:
    """Service for generating lessons using AI from documents and prompts"""

    def __init__(self):
        self.ai_service = ai_service

    async def generate_lesson_from_documents(
        self,
        prompt: str,
        documents: List[Dict[str, Any]],
        lesson_type: LessonType,
        provider: AIModelProvider = AIModelProvider.ANTHROPIC,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a lesson using AI based on documents and a prompt

        Args:
            prompt: User's prompt describing what lesson to create
            documents: List of parsed documents with content
            lesson_type: Type of lesson to generate
            provider: AI model provider to use
            additional_context: Optional additional context

        Returns:
            Dictionary containing generated lesson data
        """
        try:
            # Build context from documents
            document_context = self._build_document_context(documents)

            # Build the AI prompt
            system_prompt = self._build_lesson_generation_prompt(lesson_type)

            # User message with context
            user_message = self._build_user_message(
                prompt, document_context, additional_context
            )

            # Generate lesson using AI
            response = await self.ai_service.generate_response(
                messages=[{"role": "user", "content": user_message}],
                provider=provider,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=4000
            )

            # Parse the AI response into structured lesson data
            lesson_data = self._parse_lesson_response(response["content"])

            # Add metadata
            lesson_data["ai_provider"] = provider.value
            lesson_data["tokens_used"] = response.get("tokens_used", 0)

            return lesson_data

        except Exception as e:
            logger.error(f"Error generating lesson: {str(e)}")
            raise ValueError(f"Failed to generate lesson: {str(e)}")

    def _build_document_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from multiple documents"""
        context_parts = []

        for idx, doc in enumerate(documents, 1):
            context_parts.append(f"--- Document {idx}: {doc['filename']} ---")
            context_parts.append(doc['content'])
            context_parts.append("")

        return "\n".join(context_parts)

    def _build_lesson_generation_prompt(self, lesson_type: LessonType) -> str:
        """Build system prompt for lesson generation"""
        return f"""You are an expert instructional designer and business coach specializing in creating engaging, practical learning experiences.

Your task is to generate a comprehensive coaching lesson based on provided documents and user requirements.

The lesson should be for the category: {lesson_type.value}

Generate the lesson with the following structure in JSON format:

{{
    "title": "Clear, engaging title for the lesson",
    "description": "Brief description of what the lesson covers (2-3 sentences)",
    "scenario": "A realistic, detailed scenario that learners will work through (3-5 paragraphs)",
    "objectives": [
        "Specific learning objective 1",
        "Specific learning objective 2",
        "Specific learning objective 3"
    ],
    "content": {{
        "introduction": "Engaging introduction to the scenario and context",
        "key_concepts": [
            {{"concept": "Concept name", "description": "Detailed explanation"}},
            {{"concept": "Concept name", "description": "Detailed explanation"}}
        ],
        "practice_questions": [
            "Thought-provoking question 1",
            "Thought-provoking question 2",
            "Thought-provoking question 3"
        ],
        "coaching_tips": [
            "Tip 1 for coaches",
            "Tip 2 for coaches"
        ]
    }},
    "difficulty_level": 1-5 (integer),
    "estimated_duration": estimated time in minutes (integer),
    "tags": ["relevant", "tags", "for", "searchability"]
}}

Requirements:
- Base the lesson content on the provided documents
- Make scenarios realistic and relatable to business professionals
- Ensure objectives are specific, measurable, and achievable
- Include practical, actionable insights
- Use professional but conversational tone
- Focus on real-world application

Return ONLY valid JSON without any markdown formatting or code blocks."""

    def _build_user_message(
        self,
        prompt: str,
        document_context: str,
        additional_context: Optional[str]
    ) -> str:
        """Build user message with all context"""
        message_parts = [
            "Please generate a lesson based on the following:",
            "",
            f"USER REQUEST: {prompt}",
            ""
        ]

        if additional_context:
            message_parts.extend([
                f"ADDITIONAL CONTEXT: {additional_context}",
                ""
            ])

        message_parts.extend([
            "SOURCE DOCUMENTS:",
            document_context,
            "",
            "Generate a comprehensive lesson following the specified JSON structure."
        ])

        return "\n".join(message_parts)

    def _parse_lesson_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response into structured lesson data"""
        try:
            # Clean the response (remove markdown code blocks if present)
            cleaned_response = ai_response.strip()

            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]

            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]

            cleaned_response = cleaned_response.strip()

            # Parse JSON
            lesson_data = json.loads(cleaned_response)

            # Validate required fields
            required_fields = ["title", "description", "scenario", "objectives", "content"]
            for field in required_fields:
                if field not in lesson_data:
                    raise ValueError(f"Missing required field: {field}")

            # Set defaults for optional fields
            lesson_data.setdefault("difficulty_level", 2)
            lesson_data.setdefault("estimated_duration", 30)
            lesson_data.setdefault("tags", [])

            return lesson_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            logger.debug(f"AI Response: {ai_response}")
            raise ValueError(f"AI response was not valid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing lesson response: {str(e)}")
            raise ValueError(f"Failed to parse lesson data: {str(e)}")

    async def refine_lesson(
        self,
        lesson_data: Dict[str, Any],
        refinement_prompt: str,
        provider: AIModelProvider = AIModelProvider.ANTHROPIC
    ) -> Dict[str, Any]:
        """
        Refine an existing lesson based on feedback

        Args:
            lesson_data: Current lesson data
            refinement_prompt: Instructions for refinement
            provider: AI model provider to use

        Returns:
            Refined lesson data
        """
        try:
            system_prompt = """You are an expert instructional designer.
You will receive a lesson in JSON format and instructions for refinement.
Return the refined lesson in the same JSON format, maintaining the structure but improving based on the feedback."""

            user_message = f"""Current Lesson:
{json.dumps(lesson_data, indent=2)}

Refinement Instructions:
{refinement_prompt}

Please refine the lesson according to the instructions and return the complete updated lesson in JSON format."""

            response = await self.ai_service.generate_response(
                messages=[{"role": "user", "content": user_message}],
                provider=provider,
                system_prompt=system_prompt,
                temperature=0.6,
                max_tokens=4000
            )

            refined_data = self._parse_lesson_response(response["content"])
            refined_data["tokens_used"] = response.get("tokens_used", 0)

            return refined_data

        except Exception as e:
            logger.error(f"Error refining lesson: {str(e)}")
            raise ValueError(f"Failed to refine lesson: {str(e)}")


# Singleton instance
lesson_generator = LessonGeneratorService()
