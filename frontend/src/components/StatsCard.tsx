import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  color: 'blue' | 'green' | 'red' | 'yellow' | 'purple' | 'gray';
  description?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  loading?: boolean;
}

const colorClasses = {
  blue: {
    background: 'bg-blue-50',
    iconBackground: 'bg-blue-100',
    iconColor: 'text-blue-600',
    textColor: 'text-blue-900',
    trendPositive: 'text-green-600',
    trendNegative: 'text-red-600',
  },
  green: {
    background: 'bg-green-50',
    iconBackground: 'bg-green-100',
    iconColor: 'text-green-600',
    textColor: 'text-green-900',
    trendPositive: 'text-green-600',
    trendNegative: 'text-red-600',
  },
  red: {
    background: 'bg-red-50',
    iconBackground: 'bg-red-100',
    iconColor: 'text-red-600',
    textColor: 'text-red-900',
    trendPositive: 'text-green-600',
    trendNegative: 'text-red-600',
  },
  yellow: {
    background: 'bg-yellow-50',
    iconBackground: 'bg-yellow-100',
    iconColor: 'text-yellow-600',
    textColor: 'text-yellow-900',
    trendPositive: 'text-green-600',
    trendNegative: 'text-red-600',
  },
  purple: {
    background: 'bg-purple-50',
    iconBackground: 'bg-purple-100',
    iconColor: 'text-purple-600',
    textColor: 'text-purple-900',
    trendPositive: 'text-green-600',
    trendNegative: 'text-red-600',
  },
  gray: {
    background: 'bg-gray-50',
    iconBackground: 'bg-gray-100',
    iconColor: 'text-gray-600',
    textColor: 'text-gray-900',
    trendPositive: 'text-green-600',
    trendNegative: 'text-red-600',
  },
};

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon: Icon,
  color,
  description,
  trend,
  loading = false,
}) => {
  const colors = colorClasses[color];

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-full"></div>
            </div>
            <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${colors.background} rounded-lg shadow-sm border border-gray-200 p-6 transition-all duration-200 hover:shadow-md`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className={`text-sm font-medium ${colors.textColor} opacity-70`}>
            {title}
          </p>
          <p className={`text-3xl font-bold ${colors.textColor} mt-2`}>
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>

          {description && (
            <p className={`text-sm ${colors.textColor} opacity-60 mt-1`}>
              {description}
            </p>
          )}

          {trend && (
            <div className="flex items-center mt-2">
              <span
                className={`text-sm font-medium ${
                  trend.isPositive ? colors.trendPositive : colors.trendNegative
                }`}
              >
                {trend.isPositive ? '+' : ''}{trend.value}%
              </span>
              <span className="text-sm text-gray-500 ml-1">前日比</span>
            </div>
          )}
        </div>

        <div className={`${colors.iconBackground} p-3 rounded-lg`}>
          <Icon className={`w-6 h-6 ${colors.iconColor}`} />
        </div>
      </div>
    </div>
  );
};

export default StatsCard;