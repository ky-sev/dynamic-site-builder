from typing import Any, Dict, List
from domains.reporting.schemas.report import DynamicReportResponse, ReportColumn


def generate_dynamic_report(
    workflow_key: str,
    active_schema: Dict[str, Any],
    active_version: int,
    submissions: List[Dict[str, Any]],
) -> DynamicReportResponse:
    """
    Dynamically projects submissions against whichever fields are defined
    in the active schema version.
    """
    fields: List[Dict[str, Any]] = active_schema.get("fields", [])
    total_submissions = len(submissions)

    columns: List[ReportColumn] = [
        ReportColumn(
            key=f.get("key", ""),
            label=f.get("label", f.get("key", "")),
            type=f.get("type", "text"),
        )
        for f in fields
    ]

    metrics: Dict[str, Any] = {}

    for field in fields:
        f_key = field.get("key")
        f_type = field.get("type")
        f_label = field.get("label", f_key)

        if not f_key:
            continue

        values = [
            sub.get("data", {}).get(f_key)
            for sub in submissions
            if isinstance(sub.get("data"), dict) and f_key in sub.get("data", {})
        ]

        if f_type == "yesNo":
            true_count = sum(1 for v in values if v is True or str(v).lower() in ("true", "1", "yes"))
            metrics[f_key] = {
                "label": f_label,
                "type": "yesNo",
                "yes_count": true_count,
                "no_count": len(values) - true_count,
                "completion_rate": round((true_count / (total_submissions or 1)) * 100, 1),
            }
        elif f_type == "dropdown":
            options = field.get("options", [])
            distribution = {opt: 0 for opt in options}
            for v in values:
                str_v = str(v)
                distribution[str_v] = distribution.get(str_v, 0) + 1
            metrics[f_key] = {
                "label": f_label,
                "type": "dropdown",
                "distribution": distribution,
            }
        elif f_type == "number":
            numeric_vals = [
                float(v) for v in values if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace(".", "", 1).isdigit())
            ]
            if numeric_vals:
                metrics[f_key] = {
                    "label": f_label,
                    "type": "number",
                    "count": len(numeric_vals),
                    "min": min(numeric_vals),
                    "max": max(numeric_vals),
                    "avg": round(sum(numeric_vals) / len(numeric_vals), 2),
                }
            else:
                metrics[f_key] = {
                    "label": f_label,
                    "type": "number",
                    "count": 0,
                    "min": 0,
                    "max": 0,
                    "avg": 0,
                }
        else:
            # Text, date, textarea
            populated_count = sum(1 for v in values if v is not None and str(v).strip())
            metrics[f_key] = {
                "label": f_label,
                "type": f_type or "text",
                "populated_count": populated_count,
                "response_rate": round((populated_count / (total_submissions or 1)) * 100, 1),
            }

    # Format recent submissions aligning to active columns
    recent = []
    for sub in submissions[:20]:
        data_map = sub.get("data", {}) if isinstance(sub.get("data"), dict) else {}
        row = {
            "id": sub.get("id"),
            "submitted_at": str(sub.get("created_at", "")),
            "submitted_by": sub.get("submitted_by", "anonymous"),
            "version": sub.get("version"),
            "values": {col.key: data_map.get(col.key) for col in columns},
        }
        recent.append(row)

    return DynamicReportResponse(
        workflow_key=workflow_key,
        workflow_title=active_schema.get("title", workflow_key.replace("_", " ").title()),
        active_version=active_version,
        total_submissions=total_submissions,
        columns=columns,
        metrics=metrics,
        recent_submissions=recent,
    )

