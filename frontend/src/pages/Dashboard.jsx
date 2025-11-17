import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MessageSquare, BookOpen, TrendingUp, Users, ArrowRight } from 'lucide-react';
import { chatAPI, lessonsAPI, teamsAPI } from '../api/client';
import useAuthStore from '../store/authStore';

const Dashboard = () => {
  const { user } = useAuthStore();
  const [stats, setStats] = useState({
    sessions: 0,
    lessons: 0,
    teams: 0,
  });
  const [recentSessions, setRecentSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [sessionsRes, lessonsRes, teamsRes] = await Promise.all([
        chatAPI.getSessions(),
        lessonsAPI.getLessons({ limit: 10 }),
        teamsAPI.getTeams(),
      ]);

      setStats({
        sessions: sessionsRes.data.length,
        lessons: lessonsRes.data.length,
        teams: teamsRes.data.length,
      });

      setRecentSessions(sessionsRes.data.slice(0, 5));
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Chat Sessions',
      value: stats.sessions,
      icon: MessageSquare,
      color: 'bg-blue-500',
      link: '/chat',
    },
    {
      title: 'Available Lessons',
      value: stats.lessons,
      icon: BookOpen,
      color: 'bg-green-500',
      link: '/lessons',
    },
    {
      title: 'Teams',
      value: stats.teams,
      icon: Users,
      color: 'bg-purple-500',
      link: '/teams',
    },
  ];

  return (
    <div className="p-8">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.full_name || user?.username}!
        </h1>
        <p className="text-gray-600 mt-2">
          Here's your coaching journey overview
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <Link
              key={stat.title}
              to={stat.link}
              className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow border border-gray-200"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {loading ? '...' : stat.value}
                  </p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl shadow-sm p-6 text-white">
          <h3 className="text-xl font-semibold mb-2">Start a New Session</h3>
          <p className="text-primary-100 mb-4">
            Begin a coaching conversation with AI
          </p>
          <Link
            to="/chat"
            className="inline-flex items-center px-4 py-2 bg-white text-primary-600 rounded-lg font-medium hover:bg-primary-50 transition-colors"
          >
            Start Chatting
            <ArrowRight className="w-4 h-4 ml-2" />
          </Link>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-sm p-6 text-white">
          <h3 className="text-xl font-semibold mb-2">Explore Lessons</h3>
          <p className="text-green-100 mb-4">
            Discover structured coaching scenarios
          </p>
          <Link
            to="/lessons"
            className="inline-flex items-center px-4 py-2 bg-white text-green-600 rounded-lg font-medium hover:bg-green-50 transition-colors"
          >
            Browse Lessons
            <ArrowRight className="w-4 h-4 ml-2" />
          </Link>
        </div>
      </div>

      {/* Recent Sessions */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Recent Sessions</h2>
          <Link
            to="/chat"
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            View all
          </Link>
        </div>

        <div className="p-6">
          {loading ? (
            <p className="text-gray-500 text-center">Loading...</p>
          ) : recentSessions.length === 0 ? (
            <p className="text-gray-500 text-center">No sessions yet. Start your first chat!</p>
          ) : (
            <div className="space-y-3">
              {recentSessions.map((session) => (
                <Link
                  key={session.id}
                  to={`/chat/${session.id}`}
                  className="block p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{session.title}</p>
                      <p className="text-sm text-gray-500 mt-1">
                        {new Date(session.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {session.is_active ? (
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                          Active
                        </span>
                      ) : (
                        <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs font-medium rounded">
                          Completed
                        </span>
                      )}
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
