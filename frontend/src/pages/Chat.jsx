import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Send, Plus, Trash2, CheckCircle, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { format } from 'date-fns';
import useChatStore from '../store/chatStore';
import clsx from 'clsx';

const Chat = () => {
  const { sessionId } = useParams();
  const {
    sessions,
    currentSession,
    messages,
    loading,
    sending,
    loadSessions,
    selectSession,
    createSession,
    sendMessage,
    deleteSession,
    completeSession,
    clearCurrentSession,
  } = useChatStore();

  const [inputMessage, setInputMessage] = useState('');
  const [selectedModel, setSelectedModel] = useState('openai');
  const [showModelSelector, setShowModelSelector] = useState(false);
  const messagesEndRef = useRef(null);

  const aiModels = [
    { value: 'openai', label: 'OpenAI GPT-4', description: 'Most capable model' },
    { value: 'deepseek', label: 'DeepSeek', description: 'Fast and efficient' },
    { value: 'anthropic', label: 'Anthropic Claude', description: 'Constitutional AI' },
  ];

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (sessionId) {
      selectSession(parseInt(sessionId));
    }
  }, [sessionId, selectSession]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || sending) return;

    const message = inputMessage;
    setInputMessage('');

    await sendMessage(message, currentSession?.id, selectedModel);
  };

  const handleCreateSession = async () => {
    await createSession({ title: 'New Chat Session', ai_model: selectedModel });
  };

  const handleDeleteSession = async (id) => {
    if (window.confirm('Are you sure you want to delete this session?')) {
      await deleteSession(id);
    }
  };

  const handleCompleteSession = async (id) => {
    if (window.confirm('Mark this session as completed?')) {
      await completeSession(id);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sessions Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={handleCreateSession}
            className="w-full flex items-center justify-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-5 h-5 mr-2" />
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {loading && sessions.length === 0 ? (
            <p className="text-center text-gray-500 mt-4">Loading sessions...</p>
          ) : sessions.length === 0 ? (
            <p className="text-center text-gray-500 mt-4">No sessions yet</p>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={clsx(
                  'p-3 rounded-lg cursor-pointer transition-colors group relative',
                  currentSession?.id === session.id
                    ? 'bg-primary-50 border border-primary-200'
                    : 'hover:bg-gray-50 border border-transparent'
                )}
                onClick={() => selectSession(session.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {session.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {format(new Date(session.created_at), 'MMM d, yyyy')}
                    </p>
                    {!session.is_active && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 mt-1">
                        Completed
                      </span>
                    )}
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSession(session.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 ml-2 p-1 hover:bg-red-100 rounded transition-opacity"
                  >
                    <Trash2 className="w-4 h-4 text-red-600" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentSession ? (
          <>
            {/* Chat Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  {currentSession.title}
                </h2>
                <p className="text-sm text-gray-500">
                  Model: {currentSession.ai_model}
                </p>
              </div>

              {currentSession.is_active && (
                <button
                  onClick={() => handleCompleteSession(currentSession.id)}
                  className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Complete Session
                </button>
              )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 mt-8">
                  <p className="text-lg font-medium">Start a conversation</p>
                  <p className="text-sm mt-2">
                    Ask questions, practice scenarios, or explore lessons
                  </p>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={clsx(
                      'flex',
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    <div
                      className={clsx(
                        'max-w-3xl rounded-lg px-4 py-3',
                        message.role === 'user'
                          ? 'bg-primary-600 text-white'
                          : 'bg-white border border-gray-200'
                      )}
                    >
                      <div className="prose prose-sm max-w-none">
                        {message.role === 'user' ? (
                          <p className="text-white m-0">{message.content}</p>
                        ) : (
                          <ReactMarkdown>{message.content}</ReactMarkdown>
                        )}
                      </div>
                      <p
                        className={clsx(
                          'text-xs mt-2',
                          message.role === 'user' ? 'text-primary-100' : 'text-gray-400'
                        )}
                      >
                        {format(new Date(message.created_at), 'HH:mm')}
                      </p>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="bg-white border-t border-gray-200 p-4">
              <div className="mb-3 flex items-center justify-between">
                <div className="relative">
                  <button
                    onClick={() => setShowModelSelector(!showModelSelector)}
                    className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    <Bot className="w-4 h-4" />
                    <span className="font-medium">
                      {aiModels.find(m => m.value === selectedModel)?.label}
                    </span>
                  </button>
                  {showModelSelector && (
                    <div className="absolute bottom-full mb-2 left-0 bg-white border border-gray-200 rounded-lg shadow-lg p-2 min-w-[250px] z-10">
                      {aiModels.map((model) => (
                        <button
                          key={model.value}
                          onClick={() => {
                            setSelectedModel(model.value);
                            setShowModelSelector(false);
                          }}
                          className={clsx(
                            'w-full text-left px-3 py-2 rounded-md transition-colors',
                            selectedModel === model.value
                              ? 'bg-primary-50 text-primary-700'
                              : 'hover:bg-gray-50'
                          )}
                        >
                          <div className="font-medium">{model.label}</div>
                          <div className="text-xs text-gray-500">{model.description}</div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <form onSubmit={handleSendMessage} className="flex space-x-4">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Type your message..."
                  disabled={sending || !currentSession.is_active}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <button
                  type="submit"
                  disabled={sending || !inputMessage.trim() || !currentSession.is_active}
                  className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
                >
                  <Send className="w-5 h-5" />
                </button>
              </form>
              {!currentSession.is_active && (
                <p className="text-sm text-amber-600 mt-2">
                  This session is completed. Create a new session to continue chatting.
                </p>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                No session selected
              </h3>
              <p className="text-gray-500 mb-4">
                Select a session or create a new one to start chatting
              </p>
              <button
                onClick={handleCreateSession}
                className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                Create New Session
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Chat;
