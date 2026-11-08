from domains.reporting.schemas.report import ChartType
from domains.reporting.services.report_service import generate_dynamic_report


# Verifies widget generation per chart type and confirms reportable=False excludes fields from widgets.
def test_generate_dynamic_report_widgets_and_reportable_flag():
    active_schema = {
        "title": "Deal Flow",
        "fields": [
            {
                "key": "customerName",
                "label": "Customer name",
                "type": "text",
                "reportable": False,  # Should NOT generate a widget
            },
            {
                "key": "dealName",
                "label": "Deal name",
                "type": "text",
                "reportable": True,   # Should generate a STAT_CARD widget
            },
            {
                "key": "fundingReceived",
                "label": "Funding received?",
                "type": "yesNo",
                "reportable": True,   # Should generate a DONUT_CHART widget
            },
            {
                "key": "dealType",
                "label": "Deal type",
                "type": "dropdown",
                "options": ["Acquisition", "Renewal"],
                "reportable": True,   # Should generate a BAR_CHART widget
            },
            {
                "key": "dealAmount",
                "label": "Deal amount",
                "type": "number",
                "reportable": True,   # Should generate a STAT_CARD widget
            },
        ],
    }

    submissions = [
        {
            "id": 1,
            "version": 1,
            "data": {
                "customerName": "Acme Corp",
                "dealName": "Project Falcon",
                "fundingReceived": True,
                "dealType": "Acquisition",
                "dealAmount": 100000,
            },
            "submitted_by": "alice",
            "created_at": "2026-11-08T10:00:00Z",
        },
        {
            "id": 2,
            "version": 1,
            "data": {
                "customerName": "Beta Inc",
                "dealName": "Project Eagle",
                "fundingReceived": False,
                "dealType": "Renewal",
                "dealAmount": 200000,
            },
            "submitted_by": "bob",
            "created_at": "2026-11-08T11:00:00Z",
        },
    ]

    report = generate_dynamic_report(
        workflow_key="deal_opportunities",
        active_schema=active_schema,
        active_version=1,
        submissions=submissions,
    )

    assert report.total_submissions == 2
    assert len(report.columns) == 5

    widget_keys = [w.field_key for w in report.widgets]
    assert "customerName" not in widget_keys  # Verified: reportable=False is excluded from widgets
    assert "fundingReceived" in widget_keys
    assert "dealType" in widget_keys
    assert "dealAmount" in widget_keys
    assert "_timeline" in widget_keys         # Timeline line chart included

    # Verify widget chart types
    funding_widget = next(w for w in report.widgets if w.field_key == "fundingReceived")
    assert funding_widget.chart_type == ChartType.DONUT_CHART

    type_widget = next(w for w in report.widgets if w.field_key == "dealType")
    assert type_widget.chart_type == ChartType.BAR_CHART

    amount_widget = next(w for w in report.widgets if w.field_key == "dealAmount")
    assert amount_widget.chart_type == ChartType.STAT_CARD
    assert amount_widget.data["average"] == 150000.0
