# AI Coaching Platform

An advanced, agentic AI coaching application that leverages multiple AI models (OpenAI, Anthropic, DeepSeek) to provide personalized business and personal development coaching.

## Overview

The AI Coaching Platform is a comprehensive web application designed to help professionals develop their skills through AI-powered conversations, structured lessons, and detailed progress tracking. The platform uses vector databases to store and analyze user interactions, providing personalized insights and recommendations.

### Key Features

- **Multi-Model AI Chat**: Choose between OpenAI GPT-4, Anthropic Claude, and DeepSeek models
- **Agentic Coaching**: Context-aware AI that adapts to your learning style and goals
- **Structured Lessons**: Pre-built scenarios covering:
  - Business practices
  - Client interactions
  - Leadership skills
  - Negotiation techniques
  - Communication strategies
  - Decision-making frameworks
- **Progress Tracking**: AI-powered analysis of your learning journey
- **Team Collaboration**: Share lessons and track progress with team members
- **Vector Database**: All conversations are stored and analyzed for pattern recognition
- **Periodic Reports**: Automated progress reports with strengths, improvements, and recommendations

## Architecture

### Technology Stack

**Backend:**
- FastAPI (Python) - High-performance async web framework
- PostgreSQL - Primary relational database
- ChromaDB - Vector database for conversation embeddings
- Redis - Caching and session management
- SQLAlchemy - ORM with async support

**Frontend:**
- React 18 - Modern UI library
- Vite - Fast build tool and dev server
- TailwindCSS - Utility-first CSS framework
- Zustand - Lightweight state management
- React Router - Client-side routing

**AI Integration:**
- OpenAI GPT-4 - Advanced language model
- Anthropic Claude - Constitutional AI model
- DeepSeek - Open-source alternative
- LangChain - AI orchestration framework

**Infrastructure:**
- Docker & Docker Compose - Containerization
- Nginx - Reverse proxy and load balancing
- AWS/GCP - Cloud deployment options

### System Architecture

```
┌─────────────────┐
│   React App     │
│   (Frontend)    │
└────────┬────────┘
         │
    ┌────▼────┐
    │  Nginx  │ (Reverse Proxy)
    └────┬────┘
         │
    ┌────▼────────┐
    │  FastAPI    │
    │  (Backend)  │
    └─┬─┬─┬─┬────┘
      │ │ │ │
   ┌──┘ │ │ └───┐
   │    │ │     │
┌──▼──┐ │ │  ┌──▼────┐
│ PG  │ │ │  │ Redis │
│ SQL │ │ │  └───────┘
└─────┘ │ │
        │ │
     ┌──▼─▼───────┐
     │  ChromaDB  │
     │  (Vector)  │
     └────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- OpenAI API key
- Anthropic API key
- (Optional) DeepSeek API key

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/ChineseAICoaching.git
cd ChineseAICoaching
```

2. **Set up environment variables**

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
SECRET_KEY=your_random_secret_key_here
```

3. **Start the application**

```bash
docker-compose up -d
```

4. **Seed initial lessons (first time only)**

```bash
docker-compose exec backend python seed_lessons.py
```

5. **Access the application**

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **ChromaDB**: http://localhost:8000

### First Steps

1. Register a new account at http://localhost:3000/register
2. Log in with your credentials
3. Explore the dashboard
4. Start a new chat session or try a lesson
5. Generate your first progress report after completing some sessions

## Features in Detail

### 1. Agentic Chatbot

The AI chatbot provides intelligent, context-aware coaching:

- **Multi-turn conversations**: Maintains context across the entire session
- **Adaptive responses**: Adjusts based on your experience level and goals
- **Probing questions**: Encourages critical thinking and self-reflection
- **Practical insights**: Provides actionable advice grounded in best practices

**Example Use Cases:**
- Practice difficult conversations before they happen
- Get feedback on business decisions
- Develop negotiation strategies
- Improve communication skills

### 2. Structured Lessons

8 pre-built lessons covering essential professional skills:

1. **Effective Client Communication** (Level 2)
   - Handle price objections
   - Build client relationships
   - Practice value-based selling

2. **Difficult Conversation Management** (Level 3)
   - Deliver constructive feedback
   - Address performance issues
   - Create psychological safety

3. **Strategic Decision Making** (Level 4)
   - Use decision frameworks (SWOT, cost-benefit)
   - Assess and mitigate risks
   - Analyze stakeholder impact

4. **Negotiation Fundamentals** (Level 2)
   - Understand BATNA
   - Create win-win outcomes
   - Close effectively

5. **Building High-Performance Teams** (Level 3)
   - Navigate team development stages
   - Leverage diverse strengths
   - Build team culture

6. **Effective Business Presentations** (Level 3)
   - Structure for impact
   - Handle tough questions
   - Develop executive presence

7. **Time Management and Prioritization** (Level 2)
   - Use prioritization frameworks
   - Practice time blocking
   - Delegate effectively

8. **Emotional Intelligence in Leadership** (Level 4)
   - Develop self-awareness
   - Practice emotional regulation
   - Build empathy

**Adding New Lessons:**

Lessons are easily extensible. See `backend/seed_lessons.py` for examples. Each lesson includes:
- Title and description
- Learning objectives
- Difficulty level (1-5)
- Scenario description
- Practice exercises
- Tags for categorization

### 3. Progress Tracking & Analytics

AI-powered analysis of your learning journey:

- **Automated Reports**: Generate 7-day or 30-day progress summaries
- **Engagement Scoring**: 0-100 score based on activity and quality
- **Pattern Recognition**: Identifies themes in your conversations
- **Personalized Insights**: AI analyzes your strengths and improvement areas
- **Actionable Recommendations**: Specific next steps for growth

**Report Components:**
- Summary of period activity
- Key strengths demonstrated
- Areas for improvement
- Specific recommendations
- Engagement metrics

### 4. Team Collaboration

Work together with your team:

- Create teams and invite members
- Assign lessons to teams
- Share progress with team leaders
- Track collective development
- Build a culture of continuous learning

### 5. Vector Database Integration

All conversations are stored as embeddings:

- **Semantic Search**: Find similar past conversations
- **Pattern Analysis**: Identify recurring themes and behaviors
- **Context Retrieval**: Surface relevant past insights during new conversations
- **Long-term Memory**: The AI "remembers" your journey

## API Documentation

### Authentication

All API endpoints (except registration and login) require JWT authentication:

```bash
# Login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer <token>" http://localhost:8001/auth/me
```

### Main Endpoints

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get token
- `GET /auth/me` - Get current user info
- `POST /chat/sessions` - Create chat session
- `GET /chat/sessions` - List user sessions
- `POST /chat/message` - Send message and get AI response
- `GET /lessons` - List available lessons
- `POST /progress/generate` - Generate progress report
- `GET /progress/reports` - List user reports
- `GET /teams` - List user's teams
- `POST /teams` - Create new team

Full API documentation available at: http://localhost:8001/docs

## Development

### Project Structure

```
ChineseAICoaching/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration settings
│   │   ├── database.py          # Database setup
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── routers/            # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── lessons.py
│   │   │   ├── teams.py
│   │   │   └── progress.py
│   │   └── services/           # Business logic
│   │       ├── ai_service.py
│   │       ├── vector_service.py
│   │       ├── auth_service.py
│   │       └── analysis_service.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── seed_lessons.py
├── frontend/
│   ├── src/
│   │   ├── api/                # API client
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── store/              # State management
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── Dockerfile
│   └── vite.config.js
├── docker-compose.yml
├── .env.example
├── README.md
└── DEPLOYMENT.md
```

### Running in Development Mode

```bash
# Start all services
docker-compose up

# Backend only (with auto-reload)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend only (with HMR)
cd frontend
npm install
npm run dev
```

### Database Migrations

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

### Adding New AI Models

To add a new AI model provider:

1. Update `app/models.py` - Add to `AIModelProvider` enum
2. Update `app/services/ai_service.py` - Implement new provider method
3. Update frontend model selector
4. Add API key to environment variables

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions for:

- AWS (ECS, EC2)
- Google Cloud Platform (Cloud Run, Compute Engine)
- Docker Compose on VPS
- Environment configuration
- Scaling strategies
- Monitoring setup

## Security Considerations

- API keys stored in environment variables (never in code)
- JWT-based authentication with configurable expiration
- Password hashing with bcrypt
- SQL injection prevention via SQLAlchemy ORM
- CORS configuration for production
- Input validation with Pydantic
- Rate limiting (recommended for production)
- HTTPS enforcement (configure in nginx/load balancer)

## Performance Optimization

- Async/await throughout the backend
- Database query optimization with eager loading
- Redis caching for frequently accessed data
- Vector DB indexing for fast semantic search
- Frontend code splitting and lazy loading
- Gzip compression
- CDN for static assets (production)

## Future Enhancements

Potential features for future iterations:

- [ ] Mobile application (React Native)
- [ ] Voice interactions
- [ ] Video coaching sessions
- [ ] Gamification and achievements
- [ ] Integration with calendar/CRM systems
- [ ] Advanced analytics dashboard
- [ ] Custom lesson builder
- [ ] Multi-language support
- [ ] Export conversations to PDF
- [ ] API webhooks for integrations

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For questions, issues, or feature requests:

- Open an issue on GitHub
- Check the documentation
- Review existing issues and discussions

## Acknowledgments

- OpenAI for GPT-4 API
- Anthropic for Claude API
- DeepSeek for their open models
- ChromaDB for vector database
- FastAPI and React communities

---

**Built with ❤️ for continuous professional development**
