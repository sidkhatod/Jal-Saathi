import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
  interactive?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  elevated = false,
  interactive = false,
  className = '',
  ...props
}) => {
  const base = elevated ? 'soft-card-elevated' : 'soft-card';
  const interaction = interactive
    ? 'hover:-translate-y-0.5 hover:shadow-md transition-all duration-200 cursor-pointer'
    : '';

  return (
    <div
      className={`${base} p-6 sm:p-8 ${interaction} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
