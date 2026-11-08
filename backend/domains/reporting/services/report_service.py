from typing import Any, Dict, List
from domains.reporting.schemas.report import (
    ChartType,
    DynamicReportResponse,
    ReportColumn,
    ReportWidget,
)


# Projects submissions against active schema fields, grouping reportable fields into typed chart widgets.
def generate_dynamic_report(
    workflow_key: str,
    active_schema: Dict[str, Any],
    active_version: int,
    submissions: List[Dict[str, Any]],
) -> DynamicReportResponse:
    fields: List[Dict[str, Any]] = active_schema.get("fields", [])
    total_submissions = len(submissions)

    columns: List[ReportColumn] = [
        ReportColumn(
            key=f.get("key", ""),
            label=f.get("label", f.get("key", "")),
            type=f.get("type", "text"),
            reportable=f.get("reportable", True),
        )
        for f in fields
    ]

    metrics: Dict[str, Any] = {}
    widgets: List[ReportWidget] = []

    for field in fields:
        f_key = field.get("key")
        f_type = field.get("type")
        f_label = field.get("label", f_key)
        is_reportable = field.get("reportable", True)

        if not f_key:
            continue

        values = [
            sub.get("data", {}).get(f_key)
            for sub in submissions
            if isinstance(sub.get("data"), dict) and f_key in sub.get("data", {})
        ]

        # Calculate metric data
        if f_type == "yesNo":
            true_count = sum(1 for v in values if v is True or str(v).lower() in ("true", "1", "yes"))
            no_count = len(values) - true_count
            completion_rate = round((true_count / (total_submissions or 1)) * 100, 1)
            metric_data = {
                "label": f_label,
                "type": "yesNo",
                "yes_count": true_count,
                "no_count": no_count,
                "completion_rate": completion_rate,
            }
            metrics[f_key] = metric_data

            if is_reportable:
                widgets.append(
                    ReportWidget(
                        id=f"widget_{f_key}",
                        field_key=f_key,
                        title=f_label,
                        chart_type=ChartType.DONUT_CHART,
                        summary=f"{completion_rate}% affirmative",
                        data=[
                            {"label": "Yes", "value": true_count, "color": "#277352"},
                            {"label": "No", "value": no_count, "color": "#cbd5e1"},
                        ],
                    )
                )

        elif f_type == "dropdown":
            options = field.get("options", [])
            distribution = {opt: 0 for opt in options}
            for v in values:
                str_v = str(v)
                distribution[str_v] = distribution.get(str_v, 0) + 1
            metric_data = {
                "label": f_label,
                "type": "dropdown",
                "distribution": distribution,
            }
            metrics[f_key] = metric_data

            if is_reportable:
                chart_data = [
                    {"label": opt, "value": count}
                    for opt, count in distribution.items()
                ]
                widgets.append(
                    ReportWidget(
                        id=f"widget_{f_key}",
                        field_key=f_key,
                        title=f_label,
                        chart_type=ChartType.BAR_CHART,
                        summary=f"{len(distribution)} categories",
                        data=chart_data,
                    )
                )

        elif f_type == "number":
            numeric_vals = [
                float(v) for v in values if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace(".", "", 1).isdigit())
            ]
            if numeric_vals:
                avg_val = round(sum(numeric_vals) / len(numeric_vals), 2)
                min_val = min(numeric_vals)
                max_val = max(numeric_vals)
                count_val = len(numeric_vals)
            else:
                avg_val, min_val, max_val, count_val = 0, 0, 0, 0

            metric_data = {
                "label": f_label,
                "type": "number",
                "count": count_val,
                "min": min_val,
                "max": max_val,
                "avg": avg_val,
            }
            metrics[f_key] = metric_data

            if is_reportable:
                widgets.append(
                    ReportWidget(
                        id=f"widget_{f_key}",
                        field_key=f_key,
                        title=f_label,
                        chart_type=ChartType.STAT_CARD,
                        summary=f"Avg: {avg_val}",
                        data={
                            "average": avg_val,
                            "min": min_val,
                            "max": max_val,
                            "total_counted": count_val,
                        },
                    )
                )

        else:
            # Text, date, textarea
            populated_count = sum(1 for v in values if v is not None and str(v).strip())
            response_rate = round((populated_count / (total_submissions or 1)) * 100, 1)
            metric_data = {
                "label": f_label,
                "type": f_type or "text",
                "populated_count": populated_count,
                "response_rate": response_rate,
            }
            metrics[f_key] = metric_data

            if is_reportable and f_type != "textarea":
                widgets.append(
                    ReportWidget(
                        id=f"widget_{f_key}",
                        field_key=f_key,
                        title=f_label,
                        chart_type=ChartType.STAT_CARD,
                        summary=f"{response_rate}% filled",
                        data={
                            "response_rate": response_rate,
                            "populated_count": populated_count,
                            "total": total_submissions,
                        },
                    )
                )

    # Submission velocity widget (Line Chart by date)
    if total_submissions > 0:
        dates_count: Dict[str, int] = {}
        for sub in submissions:
            created = str(sub.get("created_at", ""))
            date_key = created[:10] if len(created) >= 10 else "Recent"
            dates_count[date_key] = dates_count.get(date_key, 0) + 1

        timeline_data = [
            {"date": d, "count": c}
            for d, c in sorted(dates_count.items())
        ]
        widgets.insert(
            0,
            ReportWidget(
                id="widget_timeline",
                field_key="_timeline",
                title="Submission Activity",
                chart_type=ChartType.LINE_CHART,
                summary=f"{total_submissions} total submissions",
                data=timeline_data,
            ),
        )

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
        widgets=widgets,
        metrics=metrics,
        recent_submissions=recent,
    )
