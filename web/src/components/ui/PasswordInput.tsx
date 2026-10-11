import { useState, forwardRef } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { Input, InputProps } from './Input';
import { useTranslation } from '../../i18n';

export interface PasswordInputProps extends Omit<InputProps, 'type' | 'rightIcon'> {
  showStrength?: boolean;
}

export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ showStrength = false, value, onChange, ...props }, ref) => {
    const { t } = useTranslation();
    const [showPassword, setShowPassword] = useState(false);

    const valStr = typeof value === 'string' ? value : '';

    // Calculate strength
    const getStrength = (pass: string): { score: number; labelKey: string } => {
      if (!pass || pass.length < 6) return { score: 1, labelKey: 'auth.password_strength.too_short' };
      let score = 1;
      if (pass.length >= 8) score++;
      if (/[0-9]/.test(pass)) score++;
      if (/[^A-Za-z0-9]/.test(pass)) score++;

      if (score <= 1) return { score: 1, labelKey: 'auth.password_strength.too_short' };
      if (score === 2) return { score: 2, labelKey: 'auth.password_strength.weak' };
      if (score === 3) return { score: 3, labelKey: 'auth.password_strength.fair' };
      return { score: 4, labelKey: 'auth.password_strength.strong' };
    };

    const strength = getStrength(valStr);

    const strengthColors = ['bg-transparent', 'bg-[#EBA896]', 'bg-[#EBCB8B]', 'bg-[#8CC2DD]', 'bg-[#6B9E7A]'];

    return (
      <div className="w-full flex flex-col gap-1">
        <Input
          ref={ref}
          type={showPassword ? 'text' : 'password'}
          value={value}
          onChange={onChange}
          rightIcon={
            <button
              type="button"
              tabIndex={0}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              onClick={() => setShowPassword(!showPassword)}
              className="text-[#5F6F68] hover:text-[#26362F] p-1.5 rounded-full hover:bg-[#26362F]/5 transition-colors cursor-pointer"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          }
          {...props}
        />

        {showStrength && valStr.length > 0 && (
          <div className="mt-1 flex flex-col gap-1">
            <div className="flex gap-1 h-1.5 w-full bg-[#26362F]/10 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 rounded-full ${strengthColors[strength.score]}`}
                style={{ width: `${(strength.score / 4) * 100}%` }}
              />
            </div>
            <p className="text-xs text-[#5F6F68]">{t(strength.labelKey)}</p>
          </div>
        )}
      </div>
    );
  }
);

PasswordInput.displayName = 'PasswordInput';
