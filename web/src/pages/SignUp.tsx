import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from '../i18n';
import { useAuth } from '../lib/auth-context';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { PasswordInput } from '../components/ui/PasswordInput';
import { Card } from '../components/ui/Card';
import { Sprout, ArrowRight } from 'lucide-react';

export const SignUp: React.FC = () => {
  const { t } = useTranslation();
  const { signUp } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !userId.trim() || !password || !confirmPassword) {
      setError(t('auth.fill_all_fields'));
      return;
    }

    if (password.length < 6) {
      setError(t('auth.password_strength.too_short'));
      return;
    }

    if (password !== confirmPassword) {
      setError(t('auth.passwords_do_not_match'));
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      await signUp(name, userId, password);
      navigate('/onboarding');
    } catch (err: any) {
      if (err.message === 'user_already_exists') {
        setError(t('auth.user_already_exists'));
      } else {
        setError(t('common.error'));
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center py-6">
      {/* Desktop Left Column */}
      <div className="hidden lg:flex lg:col-span-6 flex-col gap-6 pr-6">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#E1EFE4] text-[#1E3A28] border border-[#6B9E7A]/25 w-fit text-sm font-semibold">
          <Sprout className="w-4 h-4" />
          <span>{t('app.name')}</span>
        </div>

        <h1 className="text-3xl xl:text-4xl font-extrabold text-[#26362F] leading-tight">
          {t('auth.create_title')}
        </h1>

        <p className="text-base text-[#5F6F68] leading-relaxed">
          {t('auth.create_subtitle')}
        </p>

        <div className="p-5 rounded-2xl bg-white/60 backdrop-blur-xs border border-[#26362F]/8 flex flex-col gap-2">
          <h4 className="font-bold text-[#26362F] text-sm">
            What you receive:
          </h4>
          <ul className="text-xs text-[#5F6F68] flex flex-col gap-2 list-disc list-inside">
            <li>Weekly water need calculations calibrated for your soil</li>
            <li>Season timeline with crop-specific growth stages</li>
            <li>Quality-checked field photo records</li>
          </ul>
        </div>
      </div>

      {/* Right Column: Sign Up Card */}
      <div className="w-full lg:col-span-6 max-w-md mx-auto">
        <Card elevated className="w-full">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-[#26362F]">
              {t('auth.create_title')}
            </h2>
            <p className="text-sm text-[#5F6F68] mt-1.5 leading-relaxed">
              {t('auth.create_subtitle')}
            </p>
          </div>

          {error && (
            <div
              role="alert"
              className="mb-5 p-3.5 rounded-2xl bg-[#FCE8E2] border border-[#EBA896]/50 text-xs font-semibold text-[#5C1D13] leading-relaxed"
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              id="name"
              label={t('auth.name_label')}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('auth.name_hint')}
              autoComplete="name"
              required
            />

            <Input
              id="user-id-signup"
              label={t('auth.user_id_label')}
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder={t('auth.user_id_hint')}
              autoComplete="username"
              required
            />

            <PasswordInput
              id="password-signup"
              label={t('auth.password_label')}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t('auth.password_hint')}
              showStrength
              autoComplete="new-password"
              required
            />

            <PasswordInput
              id="confirm-password"
              label={t('auth.confirm_password_label')}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder={t('auth.confirm_password_hint')}
              autoComplete="new-password"
              required
            />

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isLoading}
              className="w-full mt-3"
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              {isLoading ? t('auth.signing_up') : t('auth.sign_up_btn')}
            </Button>

            <div className="pt-4 border-t border-[#26362F]/10 flex items-center justify-center gap-1.5 text-sm text-[#5F6F68]">
              <span>{t('auth.already_have_account')}</span>
              <Link
                to="/signin"
                className="font-bold text-[#26362F] hover:text-[#375941] underline underline-offset-2 transition-colors"
              >
                {t('auth.sign_in_link')}
              </Link>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
};
