import React from 'react';
import { Home, CalendarCheck, BarChart2, Info, LogOut, Sprout } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation, Language } from '../../i18n';
import { useAuth } from '../../lib/auth-context';
import { SegmentedControl } from '../ui/SegmentedControl';
import { Chip } from '../ui/Chip';

export const LeftRail: React.FC = () => {
  const { t, language, setLanguage } = useTranslation();
  const { user, signOut } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const navItems = [
    { path: '/', label: t('nav.home'), icon: Home },
    { path: '/checkin', label: t('nav.checkin'), icon: CalendarCheck },
    { path: '/impact', label: t('nav.impact'), icon: BarChart2 },
    { path: '/about', label: t('nav.about'), icon: Info },
  ];

  return (
    <aside
      aria-label="Desktop Navigation"
      className="hidden md:flex flex-col w-64 lg:w-72 h-screen sticky top-0 bg-white/70 backdrop-blur-xl border-r border-[#26362F]/10 p-6 justify-between select-none"
    >
      <div className="flex flex-col gap-8">
        {/* Logo and Brand */}
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-[#6B9E7A] text-white flex items-center justify-center shadow-xs">
            <Sprout className="w-6 h-6 stroke-[2.2]" />
          </div>
          <div>
            <span className="font-bold text-xl text-[#26362F] tracking-tight block">
              {t('app.name')}
            </span>
            <span className="text-xs text-[#5F6F68] block">
              {language === 'hi' ? 'स्मार्ट सिंचाई साथी' : 'Smart Irrigation'}
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex flex-col gap-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;

            return (
              <button
                key={item.path}
                type="button"
                onClick={() => navigate(item.path)}
                className={`flex items-center gap-3.5 px-4 py-3 min-h-[48px] rounded-2xl font-semibold text-base transition-all duration-200 cursor-pointer ${
                  isActive
                    ? 'bg-[#E1EFE4] text-[#1E3A28] shadow-xs'
                    : 'text-[#5F6F68] hover:bg-[#26362F]/5 hover:text-[#26362F]'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'stroke-[2.5]' : 'stroke-2'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer area with Language Toggle, User profile and Sign out */}
      <div className="flex flex-col gap-5 pt-6 border-t border-[#26362F]/10">
        <div>
          <SegmentedControl<Language>
            options={[
              { value: 'en', label: 'English' },
              { value: 'hi', label: 'हिंदी' },
            ]}
            value={language}
            onChange={setLanguage}
            className="w-full justify-center"
            name="language-toggle-desktop"
          />
        </div>

        {user && (
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div className="overflow-hidden">
                <p className="text-sm font-bold text-[#26362F] truncate">{user.name}</p>
                <p className="text-xs text-[#5F6F68] truncate">ID: {user.id}</p>
              </div>
              {user.id === 'demo_farmer' && (
                <Chip label={t('app.demo_badge')} variant="leaf" size="sm" />
              )}
            </div>

            <button
              type="button"
              onClick={() => signOut()}
              className="flex items-center gap-2 text-sm text-[#5F6F68] hover:text-[#3D140D] hover:bg-[#FCE8E2] px-3 py-2 rounded-xl transition-colors min-h-[44px] cursor-pointer mt-1"
            >
              <LogOut className="w-4 h-4" />
              <span>{t('nav.sign_out')}</span>
            </button>
          </div>
        )}
      </div>
    </aside>
  );
};
