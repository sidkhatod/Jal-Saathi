import React, { forwardRef } from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, leftIcon, rightIcon, className = '', id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full flex flex-col gap-1.5 text-left">
        {label && (
          <label htmlFor={inputId} className="text-sm font-semibold text-[#26362F]">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3.5 text-[#5F6F68] pointer-events-none flex items-center">
              {leftIcon}
            </div>
          )}
          <input
            id={inputId}
            ref={ref}
            className={`w-full min-h-[48px] px-4 py-2.5 rounded-2xl bg-white/90 text-[#26362F] border ${
              error
                ? 'border-[#EBA896] focus-visible:outline-[#C86047]'
                : 'border-[#26362F]/12 focus-visible:outline-[#6B9E7A]'
            } transition-all duration-200 shadow-xs ${
              leftIcon ? 'pl-11' : ''
            } ${rightIcon ? 'pr-11' : ''} ${className}`}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3.5 flex items-center">{rightIcon}</div>
          )}
        </div>
        {error ? (
          <p className="text-xs font-medium text-[#B83E26] mt-0.5">{error}</p>
        ) : helperText ? (
          <p className="text-xs text-[#5F6F68] mt-0.5">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = 'Input';
