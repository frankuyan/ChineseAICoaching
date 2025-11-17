"""
Script to seed initial lessons into the database
Run this after setting up the database
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Lesson, LessonType
from app.config import settings

# Sample lessons
LESSONS = [
    {
        "title": "Effective Client Communication",
        "description": "Learn how to communicate effectively with clients in various business scenarios",
        "lesson_type": LessonType.CLIENT_INTERACTION,
        "scenario": """You are meeting with a potential client who is concerned about the cost of your services.
They value quality but are working with a limited budget. Your goal is to address their concerns while
maintaining the value proposition of your offering.""",
        "objectives": [
            "Practice active listening to understand client concerns",
            "Learn to articulate value beyond price",
            "Develop skills in finding win-win solutions",
            "Build rapport and trust with clients"
        ],
        "content": {
            "introduction": "In this lesson, you'll practice handling price objections while maintaining client relationships.",
            "key_concepts": [
                "Value-based selling",
                "Active listening techniques",
                "Objection handling frameworks",
                "Building trust through transparency"
            ],
            "practice_scenarios": [
                "Client questions your pricing structure",
                "Competitor offers lower prices",
                "Client requests additional services without budget increase"
            ]
        },
        "difficulty_level": 2,
        "estimated_duration": 20,
        "tags": ["sales", "communication", "client-management", "negotiation"]
    },
    {
        "title": "Difficult Conversation Management",
        "description": "Master the art of handling difficult conversations with team members",
        "lesson_type": LessonType.LEADERSHIP,
        "scenario": """You need to address performance issues with a long-term team member who has been
underperforming for the past two months. They were previously one of your top performers, and you
suspect personal issues might be affecting their work.""",
        "objectives": [
            "Learn to give constructive feedback with empathy",
            "Practice separating person from performance",
            "Develop skills in creating action plans",
            "Build psychological safety for honest conversations"
        ],
        "content": {
            "introduction": "Navigate challenging conversations while maintaining respect and achieving positive outcomes.",
            "key_concepts": [
                "The SBI (Situation-Behavior-Impact) model",
                "Emotional intelligence in leadership",
                "Creating psychological safety",
                "Performance improvement planning"
            ],
            "practice_scenarios": [
                "Addressing declining performance",
                "Managing team conflicts",
                "Delivering unwelcome news"
            ]
        },
        "difficulty_level": 3,
        "estimated_duration": 25,
        "tags": ["leadership", "feedback", "conflict-resolution", "performance-management"]
    },
    {
        "title": "Strategic Decision Making",
        "description": "Develop frameworks for making complex business decisions",
        "lesson_type": LessonType.DECISION_MAKING,
        "scenario": """Your company has the opportunity to expand into a new market. Initial research is
promising, but it will require significant investment and resources from your current operations.
You need to evaluate this opportunity and make a recommendation to stakeholders.""",
        "objectives": [
            "Learn structured decision-making frameworks",
            "Practice risk assessment and mitigation",
            "Develop skills in stakeholder analysis",
            "Build confidence in making tough calls"
        ],
        "content": {
            "introduction": "Learn to make strategic decisions using proven frameworks and analytical thinking.",
            "key_concepts": [
                "SWOT Analysis",
                "Cost-benefit analysis",
                "Risk assessment matrices",
                "Stakeholder mapping",
                "Decision trees"
            ],
            "practice_scenarios": [
                "Market expansion decisions",
                "Resource allocation choices",
                "Strategic partnership evaluations"
            ]
        },
        "difficulty_level": 4,
        "estimated_duration": 30,
        "tags": ["strategy", "decision-making", "analysis", "leadership"]
    },
    {
        "title": "Negotiation Fundamentals",
        "description": "Master the basics of effective business negotiation",
        "lesson_type": LessonType.NEGOTIATION,
        "scenario": """You're negotiating a contract with a vendor for services your company needs.
The vendor's initial quote is 20% above your budget. You need to reach an agreement that works
for both parties while staying within financial constraints.""",
        "objectives": [
            "Understand BATNA (Best Alternative to Negotiated Agreement)",
            "Practice principled negotiation techniques",
            "Learn to create value in negotiations",
            "Develop win-win negotiation mindset"
        ],
        "content": {
            "introduction": "Learn negotiation strategies that create value for all parties involved.",
            "key_concepts": [
                "Preparation and research",
                "BATNA and reservation points",
                "Interest-based negotiation",
                "Creating and claiming value",
                "Closing techniques"
            ],
            "practice_scenarios": [
                "Vendor contract negotiations",
                "Salary negotiations",
                "Partnership terms discussions"
            ]
        },
        "difficulty_level": 2,
        "estimated_duration": 25,
        "tags": ["negotiation", "contracts", "business-development", "communication"]
    },
    {
        "title": "Building High-Performance Teams",
        "description": "Learn strategies for creating and leading effective teams",
        "lesson_type": LessonType.LEADERSHIP,
        "scenario": """You've just been assigned to lead a newly formed cross-functional team for an
important project. The team members don't know each other well and come from different departments
with different work styles. Your goal is to quickly build a cohesive, high-performing team.""",
        "objectives": [
            "Understand team development stages",
            "Learn to leverage diverse strengths",
            "Practice setting clear team goals",
            "Develop skills in building team culture"
        ],
        "content": {
            "introduction": "Discover how to transform a group of individuals into a high-performing team.",
            "key_concepts": [
                "Tuckman's stages of team development",
                "Psychological safety",
                "Role clarity and accountability",
                "Team communication norms",
                "Celebrating wins and learning from failures"
            ],
            "practice_scenarios": [
                "Team formation and norming",
                "Resolving team conflicts",
                "Motivating underperforming teams"
            ]
        },
        "difficulty_level": 3,
        "estimated_duration": 30,
        "tags": ["leadership", "team-building", "management", "culture"]
    },
    {
        "title": "Effective Business Presentations",
        "description": "Deliver compelling presentations that drive action",
        "lesson_type": LessonType.COMMUNICATION,
        "scenario": """You need to present your quarterly results and strategy recommendations to the
executive team. You have 15 minutes to present, and the executives are known for asking tough questions.
Your goal is to gain approval for your strategic initiatives.""",
        "objectives": [
            "Structure presentations for maximum impact",
            "Learn to handle challenging questions",
            "Practice executive-level communication",
            "Develop confidence in public speaking"
        ],
        "content": {
            "introduction": "Master the art of creating and delivering presentations that influence decision-makers.",
            "key_concepts": [
                "The pyramid principle",
                "Storytelling in business",
                "Visual design principles",
                "Handling Q&A sessions",
                "Executive presence"
            ],
            "practice_scenarios": [
                "Board presentations",
                "Client pitches",
                "Team updates and all-hands"
            ]
        },
        "difficulty_level": 3,
        "estimated_duration": 25,
        "tags": ["communication", "presentation", "leadership", "influence"]
    },
    {
        "title": "Time Management and Prioritization",
        "description": "Optimize your productivity through effective time management",
        "lesson_type": LessonType.BUSINESS_PRACTICE,
        "scenario": """You're overwhelmed with competing priorities: an urgent client request, a strategic
project deadline, team members needing guidance, and back-to-back meetings. You need to decide what
gets your attention and in what order.""",
        "objectives": [
            "Learn prioritization frameworks",
            "Practice saying no effectively",
            "Develop time blocking strategies",
            "Build sustainable productivity habits"
        ],
        "content": {
            "introduction": "Learn to manage your time effectively and focus on what truly matters.",
            "key_concepts": [
                "Eisenhower Matrix (Urgent/Important)",
                "Time blocking and calendar management",
                "The 80/20 principle (Pareto)",
                "Energy management",
                "Delegation strategies"
            ],
            "practice_scenarios": [
                "Managing competing priorities",
                "Handling interruptions",
                "Delegating effectively"
            ]
        },
        "difficulty_level": 2,
        "estimated_duration": 20,
        "tags": ["productivity", "time-management", "efficiency", "business-practice"]
    },
    {
        "title": "Emotional Intelligence in Leadership",
        "description": "Develop self-awareness and empathy for better leadership",
        "lesson_type": LessonType.LEADERSHIP,
        "scenario": """During a high-stress project, you notice that your frustration is affecting
how you interact with your team. Some team members seem disengaged, and you realize your emotional
state might be impacting team morale and productivity.""",
        "objectives": [
            "Develop self-awareness of emotional triggers",
            "Practice emotional regulation techniques",
            "Learn to read others' emotions",
            "Build empathy in leadership"
        ],
        "content": {
            "introduction": "Harness emotional intelligence to become a more effective and inspiring leader.",
            "key_concepts": [
                "The four domains of EQ",
                "Self-awareness and self-regulation",
                "Social awareness and empathy",
                "Relationship management",
                "Mindfulness practices for leaders"
            ],
            "practice_scenarios": [
                "Managing stress and emotions",
                "Supporting team members emotionally",
                "Building authentic connections"
            ]
        },
        "difficulty_level": 4,
        "estimated_duration": 30,
        "tags": ["leadership", "emotional-intelligence", "self-awareness", "empathy"]
    }
]


async def seed_lessons():
    """Seed initial lessons into the database"""

    # Create async engine
    ASYNC_DATABASE_URL = settings.DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    engine = create_async_engine(ASYNC_DATABASE_URL)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("Seeding lessons...")

        for lesson_data in LESSONS:
            lesson = Lesson(**lesson_data)
            session.add(lesson)
            print(f"Added lesson: {lesson_data['title']}")

        await session.commit()
        print(f"\nSuccessfully seeded {len(LESSONS)} lessons!")


if __name__ == "__main__":
    asyncio.run(seed_lessons())
