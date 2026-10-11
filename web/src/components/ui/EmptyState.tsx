import React from 'react';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center text-center p-8 sm:p-12 soft-card ${className}`}
    >
      {icon && (
        <div className="w-16 h-16 rounded-full bg-[#BFE0C8]/40 flex items-center justify-center text-[#2F533B] mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-xl font-bold text-[#26362F] mb-2">{title}</h3>
      <p className="text-[#5F6F68] max-w-sm mb-6 text-sm sm:text-base leading-relaxed">
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  );
};
