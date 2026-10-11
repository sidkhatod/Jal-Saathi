import React from 'react';

export interface ChipProps {
  label: React.ReactNode;
  variant?: 'sage' | 'water' | 'sand' | 'leaf' | 'alert' | 'neutral';
  size?: 'sm' | 'md';
  icon?: React.ReactNode;
  className?: string;
}

export const Chip: React.FC<ChipProps> = ({
  label,
  variant = 'sage',
  size = 'md',
  icon,
  className = '',
}) => {
  const variantStyles = {
    sage: 'bg-[#E1EFE4] text-[#1E3A28] border border-[#6B9E7A]/20',
    water: 'bg-[#D8EDF8] text-[#13384A] border border-[#8CC2DD]/30',
    sand: 'bg-[#FAF0D7] text-[#473612] border border-[#EBCB8B]/40',
    leaf: 'bg-[#E2F4E7] text-[#1E3B27] border border-[#BFE0C8]/40',
    alert: 'bg-[#FCE8E2] text-[#5C1D13] border border-[#EBA896]/30',
    neutral: 'bg-[#EFEBE3] text-[#2E3A33] border border-[#26362F]/10',
  };

  const sizeStyles = {
    sm: 'text-xs px-2.5 py-1',
    md: 'text-sm px-3.5 py-1.5',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {icon && <span className="inline-flex items-center">{icon}</span>}
      <span>{label}</span>
    </span>
  );
};
