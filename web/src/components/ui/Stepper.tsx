import React from 'react';
import { Check } from 'lucide-react';

export interface StepItem {
  id: string | number;
  label: string;
}

export interface StepperProps {
  steps: StepItem[];
  currentStepIndex: number;
  className?: string;
}

export const Stepper: React.FC<StepperProps> = ({
  steps,
  currentStepIndex,
  className = '',
}) => {
  return (
    <nav aria-label="Progress" className={`w-full ${className}`}>
      <ol className="flex items-center justify-between w-full">
        {steps.map((step, idx) => {
          const isCompleted = idx < currentStepIndex;
          const isCurrent = idx === currentStepIndex;

          return (
            <li key={step.id} className="relative flex-1 flex flex-col items-center">
              {idx > 0 && (
                <div
                  className={`absolute top-4 -left-1/2 w-full h-[2px] -z-0 transition-colors duration-300 ${
                    idx <= currentStepIndex ? 'bg-[#6B9E7A]' : 'bg-[#26362F]/10'
                  }`}
                  aria-hidden="true"
                />
              )}

              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-200 z-10 ${
                  isCompleted
                    ? 'bg-[#6B9E7A] text-white shadow-xs'
                    : isCurrent
                    ? 'bg-[#BFE0C8] text-[#1E3027] ring-4 ring-[#6B9E7A]/20'
                    : 'bg-white/80 text-[#5F6F68] border border-[#26362F]/15'
                }`}
                aria-current={isCurrent ? 'step' : undefined}
              >
                {isCompleted ? <Check className="w-4 h-4 stroke-[2.5]" /> : idx + 1}
              </div>

              <span
                className={`text-xs mt-2 text-center font-medium transition-colors ${
                  isCurrent
                    ? 'text-[#26362F] font-semibold'
                    : isCompleted
                    ? 'text-[#5F6F68]'
                    : 'text-[#5F6F68]/70'
                }`}
              >
                {step.label}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
};
