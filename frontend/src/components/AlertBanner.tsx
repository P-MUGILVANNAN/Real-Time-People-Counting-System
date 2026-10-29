import React from 'react';
import { AlertTriangle, ShieldAlert, AlertCircle, CheckCircle2 } from 'lucide-react';
import { AlertItem } from '../types';
import { apiService } from '../services/api';

interface AlertBannerProps {
  alerts: AlertItem[];
  onAcknowledge?: (alertId: string) => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({ alerts, onAcknowledge }) => {
  if (!alerts || alerts.length === 0) return null;

  const unacknowledged = alerts.filter(a => !a.acknowledged);
  if (unacknowledged.length === 0) return null;

  const topAlert = unacknowledged[0];

  const handleAck = async (id: string) => {
    try {
      await apiService.acknowledgeAlert(id);
      if (onAcknowledge) onAcknowledge(id);
    } catch (e) {
      console.error('Failed to acknowledge alert:', e);
    }
  };

  const getSeverityStyle = (sev: string) => {
    switch (sev) {
      case 'critical':
        return {
          bg: 'bg-rose-500/15 border-rose-500/40 text-rose-300',
          icon: ShieldAlert,
          iconColor: 'text-rose-400'
        };
      case 'high':
        return {
          bg: 'bg-orange-500/15 border-orange-500/40 text-orange-300',
          icon: AlertTriangle,
          iconColor: 'text-orange-400'
        };
      default:
        return {
          bg: 'bg-amber-500/15 border-amber-500/40 text-amber-300',
          icon: AlertCircle,
          iconColor: 'text-amber-400'
        };
    }
  };

  const style = getSeverityStyle(topAlert.severity);
  const Icon = style.icon;

  return (
    <div className={`flex items-center justify-between px-4 py-3 rounded-xl border ${style.bg} glass-panel shadow-lg animate-pulse mb-6`}>
      <div className="flex items-center space-x-3">
        <Icon className={`w-5 h-5 ${style.iconColor} flex-shrink-0`} />
        <div>
          <span className="text-xs uppercase font-bold tracking-wider mr-2 px-2 py-0.5 rounded bg-black/40">
            {topAlert.severity} Alert
          </span>
          <span className="text-sm font-medium text-white">{topAlert.message}</span>
          <span className="text-xs text-slate-400 ml-2">
            ({new Date(topAlert.timestamp * 1000).toLocaleTimeString()})
          </span>
        </div>
      </div>
      <button
        onClick={() => handleAck(topAlert.alert_id)}
        className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-white/10 hover:bg-white/20 text-white transition-all border border-white/10"
      >
        <CheckCircle2 className="w-3.5 h-3.5" />
        <span>Acknowledge</span>
      </button>
    </div>
  );
};
