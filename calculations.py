import math
from typing import List, Dict, Any
from models import Assessment

         
# Calculates statistics like current average and needed marks
def compute_stats(assessments: List[Assessment], pass_mark: float = 50.0) -> Dict[str, Any]:
    completed = [a for a in assessments if a.mark is not None]
    completed_weight = sum(a.weight for a in completed)
    contributed = sum(a.weight * (a.mark / 100.0) for a in completed)

    if completed_weight > 1e-9:
        current_avg_completed = (contributed / completed_weight) * 100.0
    else:
        current_avg_completed = None

    planned_weight = sum(a.weight for a in assessments)
    remaining_planned_weight = max(0.0, 100.0 - completed_weight)

    if remaining_planned_weight <= 1e-9:
        if contributed >= pass_mark - 1e-9:
            needed_avg_remaining = 0.0
        else:
            needed_avg_remaining = math.inf
    else:
        needed_avg_remaining = (pass_mark - contributed) / (remaining_planned_weight / 100.0)

    if needed_avg_remaining != math.inf:
        needed_avg_remaining = max(0.0, min(needed_avg_remaining, 9999.0))

    return {
        "completed_weight": completed_weight,
        "planned_weight": planned_weight,
        "contributed": contributed,
        "current_avg_completed": current_avg_completed,
        "needed_avg_remaining": needed_avg_remaining,
        "remaining_planned_weight": remaining_planned_weight,
    }
