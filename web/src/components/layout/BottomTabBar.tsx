import React from 'react';
import { Home, CalendarCheck, BarChart2, Info } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from '../../i18n';

export const BottomTabBar: React.FC = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();

  const tabs = [
    { path: '/', label: t('nav.home'), icon: Home },
    { path: '/checkin', label: t('nav.checkin'), icon: CalendarCheck },
    { path: '/impact', label: t('nav.impact'), icon: BarChart2 },
    { path: '/about', label: t('nav.about'), icon: Info },
  ];

  return (
    <nav
      aria-label="Mobile Navigation"
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/90 backdrop-blur-md border-t border-[#26362F]/10 px-4 py-2"
    >
      <div className="flex items-center justify-around max-w-md mx-auto">
        {tabs.map((tab) => {
          const isActive = location.pathname === tab.path;
          const Icon = tab.icon;

          return (
            <button
              key={tab.path}
              type="button"
              onClick={() => navigate(tab.path)}
              className={`flex flex-col items-center justify-center min-w-[48px] min-h-[48px] px-3 py-1 rounded-2xl transition-all duration-200 cursor-pointer ${
                isActive
                  ? 'text-[#1E3A28] font-bold bg-[#E1EFE4]'
                  : 'text-[#5F6F68] hover:text-[#26362F]'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'stroke-[2.5]' : 'stroke-2'}`} />
              <span className="text-[11px] mt-1">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
