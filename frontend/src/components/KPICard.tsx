import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  colorScheme: 'cyan' | 'emerald' | 'amber' | 'rose' | 'indigo';
  badge?: string;
}

const colorMap = {
  cyan: {
    bg: 'from-cyan-500/10 to-blue-500/5',
    border: 'border-cyan-500/20 group-hover:border-cyan-500/40',
    iconBg: 'bg-cyan-500/15 text-cyan-400',
    badge: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
  },
  emerald: {
    bg: 'from-emerald-500/10 to-teal-500/5',
    border: 'border-emerald-500/20 group-hover:border-emerald-500/40',
    iconBg: 'bg-emerald-500/15 text-emerald-400',
    badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
  },
  amber: {
    bg: 'from-amber-500/10 to-orange-500/5',
    border: 'border-amber-500/20 group-hover:border-amber-500/40',
    iconBg: 'bg-amber-500/15 text-amber-400',
    badge: 'bg-amber-500/10 text-amber-400 border-amber-500/20'
  },
  rose: {
    bg: 'from-rose-500/10 to-red-500/5',
    border: 'border-rose-500/20 group-hover:border-rose-500/40',
    iconBg: 'bg-rose-500/15 text-rose-400',
    badge: 'bg-rose-500/10 text-rose-400 border-rose-500/20'
  },
  indigo: {
    bg: 'from-indigo-500/10 to-purple-500/5',
    border: 'border-indigo-500/20 group-hover:border-indigo-500/40',
    iconBg: 'bg-indigo-500/15 text-indigo-400',
    badge: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
  }
};

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  colorScheme,
  badge
}) => {
  const scheme = colorMap[colorScheme];

  return (
    <div className={`group relative overflow-hidden rounded-xl border bg-gradient-to-br ${scheme.bg} ${scheme.border} p-5 glass-panel transition-all duration-300 hover:shadow-xl hover:-translate-y-0.5`}>
      <div className="flex items-center justify-between mb-3">
        <div className={`p-2.5 rounded-lg ${scheme.iconBg}`}>
          <Icon className="w-5 h-5" />
        </div>
        {badge && (
          <span className={`text-xs px-2.5 py-0.5 rounded-full border font-medium ${scheme.badge}`}>
            {badge}
          </span>
        )}
      </div>
      <div>
        <div className="text-2xl font-bold tracking-tight text-white mb-0.5">
          {value}
        </div>
        <div className="text-xs font-medium uppercase tracking-wider text-slate-400">
          {title}
        </div>
        {subtitle && (
          <div className="text-xs text-slate-400 mt-1 truncate">
            {subtitle}
          </div>
        )}
      </div>
    </div>
  );
};
