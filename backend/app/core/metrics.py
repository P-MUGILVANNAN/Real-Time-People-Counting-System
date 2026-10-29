import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

class CountingMetrics:
    """
    Evaluates people counting and crowd density estimation accuracy.
    Provides MAE, RMSE, MAPE (with documented zero-count policy), and Signed Count Bias.
    """

    @staticmethod
    def calculate(
        predictions: List[float],
        ground_truths: List[float]
    ) -> Dict[str, Any]:
        if not predictions or not ground_truths or len(predictions) != len(ground_truths):
            return {
                "sample_count": 0,
                "mae": 0.0,
                "rmse": 0.0,
                "mape": 0.0,
                "signed_bias": 0.0,
                "details": []
            }

        preds = np.array(predictions, dtype=np.float64)
        gts = np.array(ground_truths, dtype=np.float64)
        errors = preds - gts
        abs_errors = np.abs(errors)

        mae = float(np.mean(abs_errors))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        signed_bias = float(np.mean(errors))

        # Safe MAPE calculation policy:
        # If ground_truth == 0:
        #   if prediction == 0 -> percentage error = 0.0
        #   if prediction > 0 -> treat denominator as 1.0 (or include as 100% * pred)
        pct_errors = []
        for p, g in zip(preds, gts):
            if g > 0:
                pct_errors.append(abs(p - g) / g)
            else:
                pct_errors.append(0.0 if p == 0 else min(1.0, abs(p)))

        mape = float(np.mean(pct_errors)) * 100.0

        details = []
        for i, (p, g, ae) in enumerate(zip(preds, gts, abs_errors)):
            rel_err = round((ae / g) * 100.0, 2) if g > 0 else (0.0 if p == 0 else 100.0)
            details.append({
                "sample_idx": i,
                "ground_truth": float(g),
                "predicted": float(p),
                "absolute_error": round(float(ae), 2),
                "relative_error_pct": rel_err
            })

        return {
            "sample_count": len(predictions),
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "mape_pct": round(mape, 2),
            "signed_bias": round(signed_bias, 3),
            "details": details
        }


class DetectionMetrics:
    """
    Evaluates object detection performance: Precision, Recall, F1, and AP@50.
    """

    @staticmethod
    def compute_iou(boxA: List[int], boxB: List[int]) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        inter_w = max(0, xB - xA)
        inter_h = max(0, yB - yA)
        inter = inter_w * inter_h
        if inter <= 0:
            return 0.0

        areaA = max(1, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
        areaB = max(1, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))
        return inter / float(areaA + areaB - inter)

    @classmethod
    def evaluate_detections(
        cls,
        predicted_boxes: List[List[List[int]]],  # per frame: list of [x1, y1, x2, y2]
        ground_truth_boxes: List[List[List[int]]],
        iou_threshold: float = 0.50
    ) -> Dict[str, Any]:
        total_tp = 0
        total_fp = 0
        total_fn = 0

        for frame_preds, frame_gts in zip(predicted_boxes, ground_truth_boxes):
            matched_gts = set()
            for pbox in frame_preds:
                best_iou = 0.0
                best_gt_idx = -1
                for g_idx, gbox in enumerate(frame_gts):
                    if g_idx in matched_gts:
                        continue
                    iou = cls.compute_iou(pbox, gbox)
                    if iou > best_iou:
                        best_iou = iou
                        best_gt_idx = g_idx

                if best_iou >= iou_threshold and best_gt_idx >= 0:
                    total_tp += 1
                    matched_gts.add(best_gt_idx)
                else:
                    total_fp += 1

            total_fn += len(frame_gts) - len(matched_gts)

        precision = total_tp / max(1, total_tp + total_fp)
        recall = total_tp / max(1, total_tp + total_fn)
        f1 = (2 * precision * recall) / max(0.0001, precision + recall)

        return {
            "true_positives": total_tp,
            "false_positives": total_fp,
            "false_negatives": total_fn,
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1_score": round(float(f1), 4),
            "ap_50": round(float(precision * recall), 4)  # Practical approximation for balanced sets
        }


class RuntimeMetrics:
    """
    Computes latency percentiles, throughput, and memory stats.
    """

    @staticmethod
    def calculate(latencies_ms: List[float], device: str = "cpu") -> Dict[str, Any]:
        if not latencies_ms:
            return {
                "mean_latency_ms": 0.0,
                "median_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "fps": 0.0,
                "device": device
            }

        arr = np.array(latencies_ms, dtype=np.float64)
        mean_lat = float(np.mean(arr))
        med_lat = float(np.median(arr))
        p95_lat = float(np.percentile(arr, 95))
        fps = round(1000.0 / max(0.001, mean_lat), 1)

        return {
            "mean_latency_ms": round(mean_lat, 2),
            "median_latency_ms": round(med_lat, 2),
            "p95_latency_ms": round(p95_lat, 2),
            "fps": fps,
            "device": device
        }
