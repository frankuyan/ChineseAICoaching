from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models import User, ChatSession, Message, ProgressReport, Lesson
from .ai_service import ai_service
from .vector_service import vector_service
from ..models import AIModelProvider
from loguru import logger


class AnalysisService:
    """Service for analyzing user progress and generating reports"""

    async def generate_progress_report(
        self,
        db: AsyncSession,
        user_id: int,
        days: int = 7
    ) -> ProgressReport:
        """
        Generate a comprehensive progress report for a user

        Args:
            db: Database session
            user_id: User ID
            days: Number of days to analyze

        Returns:
            ProgressReport object
        """
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)

        # Gather session statistics
        session_stats = await self._get_session_stats(db, user_id, period_start, period_end)

        # Analyze conversation patterns using vector DB
        pattern_analysis = await vector_service.analyze_user_patterns(
            user_id=user_id,
            time_window_days=days
        )

        # Get recent messages for AI analysis
        recent_messages = await self._get_recent_user_messages(
            db, user_id, period_start, period_end
        )

        # Generate AI-powered insights
        ai_insights = await self._generate_ai_insights(
            session_stats=session_stats,
            pattern_analysis=pattern_analysis,
            recent_messages=recent_messages
        )

        # Create progress report
        report = ProgressReport(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            analysis=ai_insights['detailed_analysis'],
            summary=ai_insights['summary'],
            strengths=ai_insights['strengths'],
            areas_for_improvement=ai_insights['areas_for_improvement'],
            recommendations=ai_insights['recommendations'],
            total_sessions=session_stats['total_sessions'],
            total_messages=session_stats['total_messages'],
            lessons_completed=session_stats['lessons_completed'],
            engagement_score=self._calculate_engagement_score(session_stats, pattern_analysis)
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        logger.info(f"Generated progress report {report.id} for user {user_id}")
        return report

    async def _get_session_stats(
        self,
        db: AsyncSession,
        user_id: int,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """Get session statistics for the period"""

        # Count total sessions
        session_query = select(func.count(ChatSession.id)).where(
            ChatSession.user_id == user_id,
            ChatSession.created_at >= period_start,
            ChatSession.created_at <= period_end
        )
        result = await db.execute(session_query)
        total_sessions = result.scalar() or 0

        # Count completed lessons
        completed_query = select(func.count(ChatSession.id)).where(
            ChatSession.user_id == user_id,
            ChatSession.lesson_id.isnot(None),
            ChatSession.completed_at.isnot(None),
            ChatSession.created_at >= period_start,
            ChatSession.created_at <= period_end
        )
        result = await db.execute(completed_query)
        lessons_completed = result.scalar() or 0

        # Count total messages
        message_query = select(func.count(Message.id)).join(
            ChatSession, Message.session_id == ChatSession.id
        ).where(
            ChatSession.user_id == user_id,
            Message.created_at >= period_start,
            Message.created_at <= period_end
        )
        result = await db.execute(message_query)
        total_messages = result.scalar() or 0

        # Get average session length
        avg_session_messages = total_messages / total_sessions if total_sessions > 0 else 0

        return {
            "total_sessions": total_sessions,
            "lessons_completed": lessons_completed,
            "total_messages": total_messages,
            "avg_session_messages": avg_session_messages
        }

    async def _get_recent_user_messages(
        self,
        db: AsyncSession,
        user_id: int,
        period_start: datetime,
        period_end: datetime,
        limit: int = 20
    ) -> List[str]:
        """Get recent user messages for analysis"""

        query = select(Message.content).join(
            ChatSession, Message.session_id == ChatSession.id
        ).where(
            ChatSession.user_id == user_id,
            Message.role == "user",
            Message.created_at >= period_start,
            Message.created_at <= period_end
        ).order_by(Message.created_at.desc()).limit(limit)

        result = await db.execute(query)
        messages = result.scalars().all()

        return list(messages)

    async def _generate_ai_insights(
        self,
        session_stats: Dict[str, Any],
        pattern_analysis: Dict[str, Any],
        recent_messages: List[str]
    ) -> Dict[str, Any]:
        """Generate AI-powered insights from user data"""

        # Prepare context for AI analysis
        analysis_context = f"""
Analyze the following user coaching data and provide insights:

Session Statistics:
- Total sessions: {session_stats['total_sessions']}
- Lessons completed: {session_stats['lessons_completed']}
- Total messages: {session_stats['total_messages']}
- Average messages per session: {session_stats['avg_session_messages']:.1f}

Pattern Analysis:
- Total interactions analyzed: {pattern_analysis.get('message_count', 0)}
- Average message length: {pattern_analysis.get('avg_message_length', 0):.1f} characters
- Business focus: {pattern_analysis.get('business_focus', 0) * 100:.1f}%
- Leadership focus: {pattern_analysis.get('leadership_focus', 0) * 100:.1f}%

Sample Recent Messages:
{chr(10).join(f"- {msg[:100]}..." if len(msg) > 100 else f"- {msg}" for msg in recent_messages[:5])}

Please provide:
1. A concise summary (2-3 sentences) of the user's progress
2. Three key strengths demonstrated
3. Three areas for improvement
4. Three specific recommendations for continued growth

Format your response as JSON with keys: summary, strengths, areas_for_improvement, recommendations, detailed_analysis
"""

        try:
            # Use AI to generate insights
            ai_response = await ai_service.generate_response(
                messages=[{"role": "user", "content": analysis_context}],
                provider=AIModelProvider.ANTHROPIC,  # Use Anthropic for analysis
                system_prompt="You are an expert business and leadership coach analyzing user progress. Provide constructive, actionable insights.",
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=1500
            )

            # Parse AI response
            import json
            try:
                insights = json.loads(ai_response['content'])
            except json.JSONDecodeError:
                # Fallback if AI doesn't return valid JSON
                insights = self._generate_fallback_insights(session_stats, pattern_analysis)

            return insights

        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return self._generate_fallback_insights(session_stats, pattern_analysis)

    def _generate_fallback_insights(
        self,
        session_stats: Dict[str, Any],
        pattern_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate basic insights when AI analysis fails"""

        return {
            "summary": f"User completed {session_stats['lessons_completed']} lessons across {session_stats['total_sessions']} sessions with {session_stats['total_messages']} total interactions.",
            "strengths": [
                "Consistent engagement with the platform",
                "Active participation in coaching sessions",
                "Willingness to learn and develop"
            ],
            "areas_for_improvement": [
                "Increase session frequency for better retention",
                "Complete more structured lessons",
                "Engage with more diverse topics"
            ],
            "recommendations": [
                "Set aside regular time for coaching sessions",
                "Focus on completing lesson objectives",
                "Explore new coaching areas to broaden skills"
            ],
            "detailed_analysis": {
                "engagement_level": "moderate",
                "learning_pace": "steady",
                "focus_areas": ["general development"]
            }
        }

    def _calculate_engagement_score(
        self,
        session_stats: Dict[str, Any],
        pattern_analysis: Dict[str, Any]
    ) -> float:
        """Calculate engagement score (0-100)"""

        score = 0.0

        # Session frequency (40 points)
        sessions = session_stats['total_sessions']
        score += min(sessions * 5, 40)

        # Lesson completion (30 points)
        lessons = session_stats['lessons_completed']
        score += min(lessons * 10, 30)

        # Message activity (20 points)
        messages = session_stats['total_messages']
        score += min(messages * 2, 20)

        # Message quality (10 points)
        avg_length = pattern_analysis.get('avg_message_length', 0)
        if avg_length > 50:
            score += 10
        elif avg_length > 20:
            score += 5

        return min(score, 100.0)


# Singleton instance
analysis_service = AnalysisService()
