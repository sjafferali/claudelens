import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { DirectoryNode, DirectoryTotalMetrics } from '../api/analytics';
import { formatCurrency, formatDate } from '../utils/format';
import { Card } from './common/Card';
import {
  Folder,
  DollarSign,
  MessageSquare,
  Users,
  Clock,
  TrendingUp,
} from 'lucide-react';

interface DirectoryMetricsProps {
  selectedNode?: DirectoryNode;
  totalMetrics: DirectoryTotalMetrics;
  className?: string;
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

export const DirectoryMetrics: React.FC<DirectoryMetricsProps> = ({
  selectedNode,
  totalMetrics,
  className = '',
}) => {
  // Prepare data for charts
  const childrenData =
    selectedNode?.children?.slice(0, 10).map((child) => ({
      name:
        child.name.length > 15
          ? child.name.substring(0, 15) + '...'
          : child.name,
      fullName: child.name,
      cost: child.metrics.cost,
      messages: child.metrics.messages,
      sessions: child.metrics.sessions,
      percentage: child.percentage_of_total,
    })) || [];

  const topDirectoriesData =
    selectedNode?.children?.slice(0, 5).map((child, index) => ({
      name: child.name,
      value: child.metrics.cost,
      percentage: child.percentage_of_total,
      color: COLORS[index % COLORS.length],
    })) || [];

  const CustomTooltip = ({
    active,
    payload,
    label,
  }: {
    active?: boolean;
    payload?: Array<{
      payload: {
        fullName?: string;
        cost: number;
        messages?: number;
        sessions?: number;
        percentage?: number;
      };
    }>;
    label?: string;
  }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">
            {data.fullName || label}
          </p>
          <div className="space-y-1 text-sm">
            <p>
              Cost:{' '}
              <span className="font-medium text-green-600">
                {formatCurrency(data.cost)}
              </span>
            </p>
            <p>
              Messages:{' '}
              <span className="font-medium text-blue-600">
                {data.messages?.toLocaleString()}
              </span>
            </p>
            <p>
              Sessions:{' '}
              <span className="font-medium text-purple-600">
                {data.sessions?.toLocaleString()}
              </span>
            </p>
            <p>
              Share:{' '}
              <span className="font-medium">
                {data.percentage?.toFixed(1)}%
              </span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  if (!selectedNode) {
    return (
      <div className={`p-8 text-center text-gray-500 ${className}`}>
        <Folder className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p className="text-lg font-medium mb-2">No Directory Selected</p>
        <p>
          Select a directory from the treemap or explorer to view detailed
          metrics.
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900 flex items-center">
            <Folder className="w-5 h-5 mr-2 text-blue-500" />
            {selectedNode.name === 'root'
              ? 'All Directories'
              : selectedNode.name}
          </h2>
          <p className="text-sm text-gray-600 mt-1">{selectedNode.path}</p>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Cost</p>
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(selectedNode.metrics.cost)}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-green-500" />
          </div>
          <div className="mt-2 flex items-center text-sm">
            <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
            <span className="text-green-600 font-medium">
              {selectedNode.percentage_of_total.toFixed(1)}%
            </span>
            <span className="text-gray-600 ml-1">of total</span>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Messages</p>
              <p className="text-2xl font-bold text-blue-600">
                {selectedNode.metrics.messages.toLocaleString()}
              </p>
            </div>
            <MessageSquare className="w-8 h-8 text-blue-500" />
          </div>
          <div className="mt-2 text-sm text-gray-600">
            Avg cost per message:{' '}
            {formatCurrency(
              selectedNode.metrics.cost / selectedNode.metrics.messages || 0
            )}
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Sessions</p>
              <p className="text-2xl font-bold text-purple-600">
                {selectedNode.metrics.sessions.toLocaleString()}
              </p>
            </div>
            <Users className="w-8 h-8 text-purple-500" />
          </div>
          <div className="mt-2 text-sm text-gray-600">
            Avg cost per session:{' '}
            {formatCurrency(selectedNode.metrics.avg_cost_per_session)}
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Last Active</p>
              <p className="text-lg font-bold text-gray-900">
                {formatDate(selectedNode.metrics.last_active)}
              </p>
            </div>
            <Clock className="w-8 h-8 text-gray-500" />
          </div>
          <div className="mt-2 text-sm text-gray-600">
            {selectedNode.children?.length || 0} subdirectories
          </div>
        </Card>
      </div>

      {/* Charts */}
      {childrenData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bar Chart */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Subdirectory Cost Distribution
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={childrenData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="name"
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    fontSize={12}
                  />
                  <YAxis
                    tickFormatter={(value) => `$${value.toFixed(2)}`}
                    fontSize={12}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="cost" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Pie Chart */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Top 5 Directories by Cost
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={topDirectoriesData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percentage }) =>
                      `${name} (${percentage.toFixed(1)}%)`
                    }
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {topDirectoriesData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => formatCurrency(value as number)}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      )}

      {/* Detailed Table */}
      {childrenData.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Subdirectory Details
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-2 font-medium text-gray-700">
                    Directory
                  </th>
                  <th className="text-right py-3 px-2 font-medium text-gray-700">
                    Cost
                  </th>
                  <th className="text-right py-3 px-2 font-medium text-gray-700">
                    Messages
                  </th>
                  <th className="text-right py-3 px-2 font-medium text-gray-700">
                    Sessions
                  </th>
                  <th className="text-right py-3 px-2 font-medium text-gray-700">
                    Share
                  </th>
                </tr>
              </thead>
              <tbody>
                {childrenData.map((item, index) => (
                  <tr
                    key={index}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-3 px-2 font-medium text-gray-900">
                      {item.fullName}
                    </td>
                    <td className="py-3 px-2 text-right text-green-600">
                      {formatCurrency(item.cost)}
                    </td>
                    <td className="py-3 px-2 text-right text-blue-600">
                      {item.messages.toLocaleString()}
                    </td>
                    <td className="py-3 px-2 text-right text-purple-600">
                      {item.sessions.toLocaleString()}
                    </td>
                    <td className="py-3 px-2 text-right font-medium">
                      {item.percentage.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Summary */}
      <Card className="p-6 bg-gray-50">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
          <div>
            <p className="font-medium text-gray-900 mb-2">Resource Usage</p>
            <ul className="space-y-1 text-gray-600">
              <li>• Total cost: {formatCurrency(selectedNode.metrics.cost)}</li>
              <li>
                • Average per session:{' '}
                {formatCurrency(selectedNode.metrics.avg_cost_per_session)}
              </li>
              <li>
                • Represents {selectedNode.percentage_of_total.toFixed(1)}% of
                all usage
              </li>
            </ul>
          </div>
          <div>
            <p className="font-medium text-gray-900 mb-2">Activity</p>
            <ul className="space-y-1 text-gray-600">
              <li>
                • {selectedNode.metrics.messages.toLocaleString()} total
                messages
              </li>
              <li>
                • {selectedNode.metrics.sessions.toLocaleString()} unique
                sessions
              </li>
              <li>
                • Last active: {formatDate(selectedNode.metrics.last_active)}
              </li>
            </ul>
          </div>
          <div>
            <p className="font-medium text-gray-900 mb-2">Global Context</p>
            <ul className="space-y-1 text-gray-600">
              <li>• {totalMetrics.unique_directories} total directories</li>
              <li>
                • {totalMetrics.total_messages.toLocaleString()} total messages
              </li>
              <li>• {formatCurrency(totalMetrics.total_cost)} global cost</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};
