import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Clock, BarChart, Play } from 'lucide-react';
import { lessonsAPI, chatAPI } from '../api/client';
import clsx from 'clsx';

const Lessons = () => {
  const navigate = useNavigate();
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadLessons();
  }, [filter]);

  const loadLessons = async () => {
    try {
      const params = filter !== 'all' ? { lesson_type: filter } : {};
      const response = await lessonsAPI.getLessons(params);
      setLessons(response.data);
    } catch (error) {
      console.error('Error loading lessons:', error);
    } finally {
      setLoading(false);
    }
  };

  const startLesson = async (lessonId) => {
    try {
      const lesson = lessons.find((l) => l.id === lessonId);
      const response = await chatAPI.createSession({
        title: `Lesson: ${lesson.title}`,
        lesson_id: lessonId,
      });

      navigate(`/chat/${response.data.id}`);
    } catch (error) {
      console.error('Error starting lesson:', error);
    }
  };

  const lessonTypes = [
    { value: 'all', label: 'All Lessons' },
    { value: 'business_practice', label: 'Business Practice' },
    { value: 'client_interaction', label: 'Client Interaction' },
    { value: 'leadership', label: 'Leadership' },
    { value: 'negotiation', label: 'Negotiation' },
    { value: 'communication', label: 'Communication' },
    { value: 'decision_making', label: 'Decision Making' },
  ];

  const difficultyColors = {
    1: 'bg-green-100 text-green-800',
    2: 'bg-blue-100 text-blue-800',
    3: 'bg-yellow-100 text-yellow-800',
    4: 'bg-orange-100 text-orange-800',
    5: 'bg-red-100 text-red-800',
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Coaching Lessons</h1>
        <p className="text-gray-600 mt-2">
          Structured scenarios to develop your professional skills
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-2">
        {lessonTypes.map((type) => (
          <button
            key={type.value}
            onClick={() => setFilter(type.value)}
            className={clsx(
              'px-4 py-2 rounded-lg font-medium transition-colors',
              filter === type.value
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            )}
          >
            {type.label}
          </button>
        ))}
      </div>

      {/* Lessons Grid */}
      {loading ? (
        <div className="text-center py-12">
          <p className="text-gray-500">Loading lessons...</p>
        </div>
      ) : lessons.length === 0 ? (
        <div className="text-center py-12">
          <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No lessons found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {lessons.map((lesson) => (
            <div
              key={lesson.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-lg font-semibold text-gray-900 flex-1">
                    {lesson.title}
                  </h3>
                  <span
                    className={clsx(
                      'px-2 py-1 text-xs font-medium rounded',
                      difficultyColors[lesson.difficulty_level]
                    )}
                  >
                    Level {lesson.difficulty_level}
                  </span>
                </div>

                <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                  {lesson.description}
                </p>

                <div className="flex items-center space-x-4 mb-4 text-sm text-gray-500">
                  <div className="flex items-center">
                    <Clock className="w-4 h-4 mr-1" />
                    {lesson.estimated_duration || 20} min
                  </div>
                  <div className="flex items-center">
                    <BookOpen className="w-4 h-4 mr-1" />
                    {lesson.lesson_type.replace('_', ' ')}
                  </div>
                </div>

                {/* Objectives */}
                {lesson.objectives && lesson.objectives.length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs font-medium text-gray-700 mb-2">
                      Learning Objectives:
                    </p>
                    <ul className="text-xs text-gray-600 space-y-1">
                      {lesson.objectives.slice(0, 2).map((obj, idx) => (
                        <li key={idx} className="flex items-start">
                          <span className="mr-2">•</span>
                          <span className="line-clamp-1">{obj}</span>
                        </li>
                      ))}
                      {lesson.objectives.length > 2 && (
                        <li className="text-primary-600">
                          +{lesson.objectives.length - 2} more
                        </li>
                      )}
                    </ul>
                  </div>
                )}

                {/* Tags */}
                {lesson.tags && lesson.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-4">
                    {lesson.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                <button
                  onClick={() => startLesson(lesson.id)}
                  className="w-full flex items-center justify-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Start Lesson
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Lessons;
