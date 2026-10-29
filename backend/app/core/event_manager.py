import time
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("crowd_system.alerts")

class AlertRecord:
    def __init__(
        self,
        alert_id: str,
        severity: str,
        message: str,
        source: str,
        metric_value: float,
        threshold_value: float,
        timestamp: float
    ):
        self.alert_id = alert_id
        self.severity = severity  # "moderate", "high", "critical"
        self.message = message
        self.source = source  # "global_count", "global_density", "region:<name>"
        self.metric_value = metric_value
        self.threshold_value = threshold_value
        self.timestamp = timestamp
        self.acknowledged: bool = False
        self.acknowledged_at: Optional[float] = None

    def acknowledge(self):
        self.acknowledged = True
        self.acknowledged_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity,
            "message": self.message,
            "source": self.source,
            "metric_value": self.metric_value,
            "threshold_value": self.threshold_value,
            "timestamp": self.timestamp,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at
        }


class EventManager:
    """
    Manages crowd alert triggers, state machine, cooldown timers,
    and alert history.
    """

    def __init__(
        self,
        moderate_thresh: int = 10,
        high_thresh: int = 25,
        critical_thresh: int = 50,
        cooldown_seconds: float = 15.0
    ):
        self.moderate_thresh = moderate_thresh
        self.high_thresh = high_thresh
        self.critical_thresh = critical_thresh
        self.cooldown_seconds = cooldown_seconds

        self.last_alert_time: Dict[str, float] = {}  # {source: last_timestamp}
        self.alerts_history: List[AlertRecord] = []
        self.current_status: str = "normal"
        self._counter: int = 0

    def evaluate_state(
        self,
        total_count: int,
        density_val: float,
        region_metrics: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluates current system counts against configured thresholds.
        Applies cooldown logic to avoid alert flooding.
        """
        now = time.time()
        new_alerts = []

        # Determine overall global status
        if total_count >= self.critical_thresh:
            severity = "critical"
            msg = f"Critical Crowd Density Alert! {total_count} people detected (Threshold: {self.critical_thresh})"
            target_thresh = self.critical_thresh
        elif total_count >= self.high_thresh:
            severity = "high"
            msg = f"High Crowd Warning: {total_count} people detected (Threshold: {self.high_thresh})"
            target_thresh = self.high_thresh
        elif total_count >= self.moderate_thresh:
            severity = "moderate"
            msg = f"Moderate Crowd Notice: {total_count} people detected (Threshold: {self.moderate_thresh})"
            target_thresh = self.moderate_thresh
        else:
            severity = "normal"
            msg = ""
            target_thresh = 0

        self.current_status = severity

        if severity != "normal":
            last_t = self.last_alert_time.get("global", 0.0)
            if (now - last_t) >= self.cooldown_seconds:
                self._counter += 1
                alert_id = f"alt_{int(now)}_{self._counter}"
                rec = AlertRecord(
                    alert_id=alert_id,
                    severity=severity,
                    message=msg,
                    source="global",
                    metric_value=float(total_count),
                    threshold_value=float(target_thresh),
                    timestamp=now
                )
                self.alerts_history.append(rec)
                new_alerts.append(rec.to_dict())
                self.last_alert_time["global"] = now

        # Region-specific evaluation
        if region_metrics:
            for rid, rdata in region_metrics.items():
                rstatus = rdata.get("status", "normal")
                rcount = rdata.get("count", 0)
                rname = rdata.get("name", rid)
                if rstatus in ("high", "critical"):
                    key = f"region_{rid}"
                    last_t = self.last_alert_time.get(key, 0.0)
                    if (now - last_t) >= self.cooldown_seconds:
                        self._counter += 1
                        alert_id = f"alt_reg_{int(now)}_{self._counter}"
                        rec = AlertRecord(
                            alert_id=alert_id,
                            severity=rstatus,
                            message=f"Region Alert [{rname}]: {rcount} people inside.",
                            source=f"region:{rname}",
                            metric_value=float(rcount),
                            threshold_value=float(rdata.get("area_pixels", 0)),
                            timestamp=now
                        )
                        self.alerts_history.append(rec)
                        new_alerts.append(rec.to_dict())
                        self.last_alert_time[key] = now

        return new_alerts

    def acknowledge_alert(self, alert_id: str) -> bool:
        for rec in self.alerts_history:
            if rec.alert_id == alert_id:
                rec.acknowledge()
                return True
        return False

    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in reversed(self.alerts_history[-limit:])]

    def clear(self):
        self.alerts_history.clear()
        self.last_alert_time.clear()
        self.current_status = "normal"
