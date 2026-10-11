import React from 'react';
import { useAuth } from '../../lib/auth-context';
import { useTranslation, Language } from '../../i18n';
import { LeftRail } from './LeftRail';
import { BottomTabBar } from './BottomTabBar';
import { SegmentedControl } from '../ui/SegmentedControl';
import { Chip } from '../ui/Chip';
import { Sprout, LogOut } from 'lucide-react';

export const Shell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, signOut } = useAuth();
  const { t, language, setLanguage } = useTranslation();

  return (
    <div className="relative min-h-screen w-full bg-[#FAF6EF] text-[#26362F] flex flex-col md:flex-row overflow-x-hidden">
      {/* Background Organic Ambient Blobs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10" aria-hidden="true">
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-[#BFE0C8]/35 blur-3xl animate-pulse" />
        <div className="absolute top-1/4 -right-32 w-[32rem] h-[32rem] rounded-full bg-[#8CC2DD]/25 blur-3xl" />
        <div className="absolute -bottom-32 left-1/3 w-96 h-96 rounded-full bg-[#EBCB8B]/20 blur-3xl" />

        {/* Subtle crop furrow / contour line illustration */}
        <svg
          className="absolute inset-0 w-full h-full opacity-[0.04] stroke-[#26362F]"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
        >
          <path d="M-100 200 C 300 100, 700 350, 1500 150" strokeWidth="2" />
          <path d="M-100 280 C 320 180, 720 430, 1500 230" strokeWidth="2" />
          <path d="M-100 360 C 340 260, 740 510, 1500 310" strokeWidth="2" />
          <path d="M-100 440 C 360 340, 760 590, 1500 390" strokeWidth="2" />
          <path d="M-100 520 C 380 420, 780 670, 1500 470" strokeWidth="2" />
          <path d="M-100 600 C 400 500, 800 750, 1500 550" strokeWidth="2" />
        </svg>
      </div>

      {/* When user is authenticated */}
      {user ? (
        <>
          {/* Desktop Left Rail */}
          <LeftRail />

          {/* Main App Content Area */}
          <div className="flex-1 flex flex-col min-h-screen">
            {/* Mobile Top Header */}
            <header className="md:hidden flex items-center justify-between px-4 py-3 bg-white/80 backdrop-blur-md border-b border-[#26362F]/10 sticky top-0 z-30">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-[#6B9E7A] text-white flex items-center justify-center">
                  <Sprout className="w-5 h-5 stroke-[2.2]" />
                </div>
                <span className="font-bold text-lg text-[#26362F]">{t('app.name')}</span>
                {user.id === 'demo_farmer' && (
                  <Chip label={t('app.demo_badge')} variant="leaf" size="sm" />
                )}
              </div>

              <div className="flex items-center gap-2">
                <SegmentedControl<Language>
                  options={[
                    { value: 'en', label: 'EN' },
                    { value: 'hi', label: 'हि' },
                  ]}
                  value={language}
                  onChange={setLanguage}
                  name="language-toggle-mobile"
                />
                <button
                  type="button"
                  onClick={() => signOut()}
                  className="p-2 rounded-xl text-[#5F6F68] hover:text-[#3D140D] hover:bg-[#FCE8E2] transition-colors cursor-pointer"
                  aria-label={t('nav.sign_out')}
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            </header>

            {/* View container */}
            <main className="flex-1 p-4 sm:p-6 lg:p-10 pb-24 md:pb-10 max-w-7xl mx-auto w-full">
              {children}
            </main>

            {/* Mobile Bottom Navigation */}
            <BottomTabBar />
          </div>
        </>
      ) : (
        /* Unauthenticated views (Sign In, Sign Up) */
        <div className="flex-1 flex flex-col min-h-screen">
          {/* Unauthenticated top bar with language switcher */}
          <header className="w-full flex justify-between items-center px-6 py-4 max-w-7xl mx-auto">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-2xl bg-[#6B9E7A] text-white flex items-center justify-center shadow-xs">
                <Sprout className="w-5 h-5 stroke-[2.2]" />
              </div>
              <span className="font-bold text-xl text-[#26362F] tracking-tight">
                {t('app.name')}
              </span>
            </div>

            <SegmentedControl<Language>
              options={[
                { value: 'en', label: 'English' },
                { value: 'hi', label: 'हिंदी' },
              ]}
              value={language}
              onChange={setLanguage}
              name="language-toggle-unauth"
            />
          </header>

          <main className="flex-1 flex items-center justify-center p-4 sm:p-6 md:p-8">
            {children}
          </main>
        </div>
      )}
    </div>
  );
};
