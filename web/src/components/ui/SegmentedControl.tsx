import React from 'react';

export interface SegmentedControlOption<T extends string> {
  value: T;
  label: React.ReactNode;
}

export interface SegmentedControlProps<T extends string> {
  options: SegmentedControlOption<T>[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
  name?: string;
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className = '',
  name = 'segmented-control',
}: SegmentedControlProps<T>) {
  return (
    <div
      role="radiogroup"
      aria-label={name}
      className={`inline-flex items-center p-1 rounded-full bg-[#26362F]/8 backdrop-blur-xs ${className}`}
    >
      {options.map((opt) => {
        const isSelected = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={isSelected}
            onClick={() => onChange(opt.value)}
            className={`px-4 py-1.5 min-h-[38px] rounded-full text-sm font-semibold transition-all duration-200 select-none cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#6B9E7A] ${
              isSelected
                ? 'bg-white text-[#26362F] shadow-xs'
                : 'text-[#5F6F68] hover:text-[#26362F]'
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
