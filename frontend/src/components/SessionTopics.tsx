import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Lightbulb, Filter, Plus } from 'lucide-react';
import { analyticsApi } from '@/api/analytics';

interface SessionTopicsProps {
  sessionId: string;
  className?: string;
  onTopicFilter?: (topicName: string) => void;
}

interface ExtractedTopic {
  name: string;
  confidence: number;
  category: string;
  relevance_score: number;
  keywords: string[];
}

interface TopicExtractionResponse {
  session_id: string;
  topics: ExtractedTopic[];
  suggested_topics: string[];
  extraction_method: string;
  confidence_threshold: number;
  generated_at: string;
}

export default function SessionTopics({
  sessionId,
  className = '',
  onTopicFilter,
}: SessionTopicsProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.3);

  const {
    data: topicsData,
    isLoading,
    error,
  } = useQuery<TopicExtractionResponse>({
    queryKey: ['sessionTopics', sessionId, confidenceThreshold],
    queryFn: () =>
      analyticsApi.extractSessionTopics(sessionId, confidenceThreshold),
    refetchInterval: 5 * 60 * 1000, // 5 minutes cache
  });

  if (isLoading) {
    return (
      <div className={className}>
        <h3 className="text-base font-medium text-primary-c mb-4">Topics</h3>
        <div className="flex flex-wrap gap-2">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-full animate-pulse"
            >
              <div className="h-3 w-16 bg-layer-secondary rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        <h3 className="text-base font-medium text-primary-c mb-4">Topics</h3>
        <div className="text-sm text-muted-c">
          Unable to extract topics for this session
        </div>
      </div>
    );
  }

  const topics = topicsData?.topics || [];
  const suggestedTopics = topicsData?.suggested_topics || [];

  const getTopicColor = (category: string) => {
    switch (category) {
      case 'Web Development':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-300';
      case 'API Integration':
        return 'border-green-500 bg-green-50 dark:bg-green-950/20 text-green-700 dark:text-green-300';
      case 'Data Visualization':
        return 'border-purple-500 bg-purple-50 dark:bg-purple-950/20 text-purple-700 dark:text-purple-300';
      case 'Machine Learning':
        return 'border-orange-500 bg-orange-50 dark:bg-orange-950/20 text-orange-700 dark:text-orange-300';
      case 'Database Operations':
        return 'border-red-500 bg-red-50 dark:bg-red-950/20 text-red-700 dark:text-red-300';
      case 'DevOps/Deployment':
        return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20 text-yellow-700 dark:text-yellow-300';
      case 'Testing/QA':
        return 'border-pink-500 bg-pink-50 dark:bg-pink-950/20 text-pink-700 dark:text-pink-300';
      case 'Documentation':
        return 'border-gray-500 bg-gray-50 dark:bg-gray-950/20 text-gray-700 dark:text-gray-300';
      default:
        return 'border-gray-500 bg-gray-50 dark:bg-gray-950/20 text-gray-700 dark:text-gray-300';
    }
  };

  const getTopicIcon = (category: string) => {
    switch (category) {
      case 'Web Development':
        return '🌐';
      case 'API Integration':
        return '🔗';
      case 'Data Visualization':
        return '📊';
      case 'Machine Learning':
        return '🤖';
      case 'Database Operations':
        return '🗄️';
      case 'DevOps/Deployment':
        return '🚀';
      case 'Testing/QA':
        return '🧪';
      case 'Documentation':
        return '📝';
      default:
        return '🏷️';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-orange-600 dark:text-orange-400';
  };

  const handleTopicClick = (topicName: string) => {
    if (onTopicFilter) {
      onTopicFilter(topicName);
    }
  };

  if (topics.length === 0 && suggestedTopics.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-base font-medium text-primary-c mb-4">Topics</h3>
        <div className="text-sm text-muted-c">
          No topics detected for this session
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-medium text-primary-c">Topics</h3>
        <div className="flex items-center gap-2">
          {suggestedTopics.length > 0 && (
            <button
              onClick={() => setShowSuggestions(!showSuggestions)}
              className="text-xs text-muted-c hover:text-primary-c transition-colors flex items-center gap-1"
              title="Toggle suggested topics"
            >
              <Lightbulb className="h-3 w-3" />
              {showSuggestions ? 'Hide' : 'Show'} suggestions
            </button>
          )}
          {onTopicFilter && <Filter className="h-3 w-3 text-muted-c" />}
        </div>
      </div>

      {/* Confidence threshold control */}
      {topics.length > 0 && (
        <div className="mb-3">
          <div className="text-xs text-muted-c mb-2">
            Confidence threshold: {Math.round(confidenceThreshold * 100)}%
          </div>
          <input
            type="range"
            min="0.1"
            max="0.9"
            step="0.1"
            value={confidenceThreshold}
            onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
            className="w-full h-1 bg-layer-tertiary rounded-lg appearance-none cursor-pointer slider"
          />
        </div>
      )}

      {/* Extracted Topics */}
      {topics.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {topics.map((topic) => (
            <div
              key={topic.name}
              className={`tag px-3 py-1 border rounded-full text-xs transition-all duration-200 hover:scale-105 cursor-pointer ${getTopicColor(
                topic.category
              )}`}
              onClick={() => handleTopicClick(topic.name)}
              title={`${topic.name}\nCategory: ${topic.category}\nConfidence: ${Math.round(
                topic.confidence * 100
              )}%\nKeywords: ${topic.keywords.join(', ')}`}
            >
              <span className="mr-1">{getTopicIcon(topic.category)}</span>
              <span className="font-medium">{topic.name}</span>
              <span
                className={`ml-1 text-xs ${getConfidenceColor(topic.confidence)}`}
              >
                {Math.round(topic.confidence * 100)}%
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Suggested Topics */}
      {showSuggestions && suggestedTopics.length > 0 && (
        <div>
          <div className="text-xs text-muted-c font-medium mb-2 flex items-center gap-1">
            <Lightbulb className="h-3 w-3" />
            Suggested topics:
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestedTopics.map((topicName) => (
              <div
                key={topicName}
                className="px-3 py-1 bg-layer-tertiary border border-dashed border-primary-c rounded-full text-xs text-muted-c hover:text-primary-c hover:border-solid transition-all duration-200 cursor-pointer"
                onClick={() => handleTopicClick(topicName)}
                title={`Add ${topicName} as a topic`}
              >
                <Plus className="inline h-3 w-3 mr-1" />
                {topicName}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Extraction method info */}
      {topicsData && (
        <div className="mt-3 text-xs text-dim-c">
          Extracted using {topicsData.extraction_method} analysis
        </div>
      )}
    </div>
  );
}
