import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from '../i18n';
import { useAuth } from '../lib/auth-context';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { PasswordInput } from '../components/ui/PasswordInput';
import { Card } from '../components/ui/Card';
import { Sprout, Droplets, CheckCircle, ArrowRight } from 'lucide-react';

export const SignIn: React.FC = () => {
  const { t } = useTranslation();
  const { signIn } = useAuth();
  const navigate = useNavigate();

  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId.trim() || !password) {
      setError(t('auth.fill_all_fields'));
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      await signIn(userId, password);
      navigate('/');
    } catch {
      setError(t('auth.invalid_credentials'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleUseDemo = async (e: React.MouseEvent) => {
    e.preventDefault();
    setUserId('demo_farmer');
    setPassword('demo123');
    setError(null);
    setIsLoading(true);

    try {
      await signIn('demo_farmer', 'demo123');
      navigate('/');
    } catch {
      setError(t('auth.invalid_credentials'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center py-6">
      {/* Desktop Left Column: Brand & Calm Visuals */}
      <div className="hidden lg:flex lg:col-span-6 flex-col gap-6 pr-6">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#E1EFE4] text-[#1E3A28] border border-[#6B9E7A]/25 w-fit text-sm font-semibold">
          <Sprout className="w-4 h-4" />
          <span>{t('app.name')}</span>
        </div>

        <h1 className="text-3xl xl:text-4xl font-extrabold text-[#26362F] leading-tight">
          {t('app.tagline')}
        </h1>

        <div className="flex flex-col gap-4 mt-2">
          <div className="flex items-start gap-3.5 p-4 rounded-2xl bg-white/60 backdrop-blur-xs border border-[#26362F]/8">
            <div className="w-10 h-10 rounded-xl bg-[#8CC2DD]/30 text-[#13384A] flex items-center justify-center shrink-0">
              <Droplets className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-[#26362F] text-sm">
                Root-zone Soil Moisture
              </h4>
              <p className="text-xs text-[#5F6F68] mt-0.5 leading-relaxed">
                Calibrated against Soil Health Card surveys and local weather patterns.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3.5 p-4 rounded-2xl bg-white/60 backdrop-blur-xs border border-[#26362F]/8">
            <div className="w-10 h-10 rounded-xl bg-[#BFE0C8]/40 text-[#1E3A28] flex items-center justify-center shrink-0">
              <CheckCircle className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-[#26362F] text-sm">
                KVK Aligned Advisories
              </h4>
              <p className="text-xs text-[#5F6F68] mt-0.5 leading-relaxed">
                Reviewed agronomic practices without arbitrary doses or unsafe claims.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column: Sign In Card */}
      <div className="w-full lg:col-span-6 max-w-md mx-auto">
        <Card elevated className="w-full">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-[#26362F]">
              {t('auth.welcome_title')}
            </h2>
            <p className="text-sm text-[#5F6F68] mt-1.5 leading-relaxed">
              {t('auth.welcome_subtitle')}
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
              id="user-id"
              label={t('auth.user_id_label')}
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder={t('auth.user_id_hint')}
              autoComplete="username"
              required
            />

            <PasswordInput
              id="password"
              label={t('auth.password_label')}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t('auth.password_hint')}
              autoComplete="current-password"
              required
            />

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isLoading}
              className="w-full mt-2"
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              {isLoading ? t('auth.signing_in') : t('auth.sign_in_btn')}
            </Button>

            {/* Quiet text link: "Use the demo field" */}
            <div className="text-center pt-2">
              <button
                type="button"
                onClick={handleUseDemo}
                className="text-sm font-semibold text-[#375941] hover:text-[#1E3A28] underline underline-offset-4 decoration-[#6B9E7A]/50 hover:decoration-[#6B9E7A] transition-colors cursor-pointer py-1"
              >
                {t('auth.use_demo_link')}
              </button>
            </div>

            <div className="pt-4 border-t border-[#26362F]/10 flex items-center justify-center gap-1.5 text-sm text-[#5F6F68]">
              <span>{t('auth.no_account_prompt')}</span>
              <Link
                to="/signup"
                className="font-bold text-[#26362F] hover:text-[#375941] underline underline-offset-2 transition-colors"
              >
                {t('auth.create_account_link')}
              </Link>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
};
