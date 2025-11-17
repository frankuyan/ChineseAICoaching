import { useEffect, useState } from 'react';
import { TrendingUp, Calendar, CheckCircle, Target } from 'lucide-react';
import { progressAPI } from '../api/client';
import { format } from 'date-fns';

const Progress = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const response = await progressAPI.getReports();
      setReports(response.data);
      if (response.data.length > 0 && !selectedReport) {
        setSelectedReport(response.data[0]);
      }
    } catch (error) {
      console.error('Error loading reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async (days = 7) => {
    setGenerating(true);
    try {
      const response = await progressAPI.generateReport(days);
      setReports([response.data, ...reports]);
      setSelectedReport(response.data);
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Failed to generate report. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Progress & Insights</h1>
            <p className="text-gray-600 mt-2">
              Track your coaching journey and receive AI-powered insights
            </p>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={() => generateReport(7)}
              disabled={generating}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {generating ? 'Generating...' : 'Generate 7-Day Report'}
            </button>
            <button
              onClick={() => generateReport(30)}
              disabled={generating}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {generating ? 'Generating...' : 'Generate 30-Day Report'}
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <p className="text-gray-500">Loading reports...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Reports List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Your Reports</h2>
              </div>

              <div className="p-4 space-y-2 max-h-[600px] overflow-y-auto">
                {reports.length === 0 ? (
                  <p className="text-gray-500 text-sm text-center py-4">
                    No reports yet. Generate your first report!
                  </p>
                ) : (
                  reports.map((report) => (
                    <button
                      key={report.id}
                      onClick={() => setSelectedReport(report)}
                      className={`w-full text-left p-3 rounded-lg transition-colors ${
                        selectedReport?.id === report.id
                          ? 'bg-primary-50 border border-primary-200'
                          : 'hover:bg-gray-50 border border-transparent'
                      }`}
                    >
                      <p className="font-medium text-sm text-gray-900">
                        {format(new Date(report.period_start), 'MMM d')} -{' '}
                        {format(new Date(report.period_end), 'MMM d, yyyy')}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Score: {report.engagement_score?.toFixed(0) || 0}/100
                      </p>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Report Details */}
          <div className="lg:col-span-2">
            {selectedReport ? (
              <div className="space-y-6">
                {/* Stats Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                    <p className="text-sm text-gray-600">Sessions</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {selectedReport.total_sessions}
                    </p>
                  </div>

                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                    <p className="text-sm text-gray-600">Messages</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {selectedReport.total_messages}
                    </p>
                  </div>

                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                    <p className="text-sm text-gray-600">Lessons</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {selectedReport.lessons_completed}
                    </p>
                  </div>

                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                    <p className="text-sm text-gray-600">Engagement</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {selectedReport.engagement_score?.toFixed(0) || 0}
                    </p>
                  </div>
                </div>

                {/* Summary */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center mb-4">
                    <TrendingUp className="w-5 h-5 text-primary-600 mr-2" />
                    <h3 className="text-lg font-semibold text-gray-900">Summary</h3>
                  </div>
                  <p className="text-gray-700 leading-relaxed">{selectedReport.summary}</p>
                </div>

                {/* Strengths */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center mb-4">
                    <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                    <h3 className="text-lg font-semibold text-gray-900">Strengths</h3>
                  </div>
                  <ul className="space-y-2">
                    {selectedReport.strengths.map((strength, idx) => (
                      <li key={idx} className="flex items-start">
                        <span className="text-green-600 mr-2">✓</span>
                        <span className="text-gray-700">{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Areas for Improvement */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center mb-4">
                    <Target className="w-5 h-5 text-amber-600 mr-2" />
                    <h3 className="text-lg font-semibold text-gray-900">
                      Areas for Improvement
                    </h3>
                  </div>
                  <ul className="space-y-2">
                    {selectedReport.areas_for_improvement.map((area, idx) => (
                      <li key={idx} className="flex items-start">
                        <span className="text-amber-600 mr-2">→</span>
                        <span className="text-gray-700">{area}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Recommendations */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center mb-4">
                    <Calendar className="w-5 h-5 text-blue-600 mr-2" />
                    <h3 className="text-lg font-semibold text-gray-900">Recommendations</h3>
                  </div>
                  <ul className="space-y-2">
                    {selectedReport.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start">
                        <span className="text-blue-600 mr-2">•</span>
                        <span className="text-gray-700">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
                <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Select a report to view details</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Progress;
