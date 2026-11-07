from domains.reporting.services.report_service import generate_dynamic_report


def test_generate_dynamic_report_yes_no_and_dropdown():
    active_schema = {
        "title": "Opportunities",
        "fields": [
            {"key": "fundingReceived", "label": "Funding received?", "type": "yesNo"},
            {"key": "contractSigned", "label": "Contract signed?", "type": "yesNo"},
            {
                "key": "dealType",
                "label": "Deal type",
                "type": "dropdown",
                "options": ["Acquisition", "Renewal"],
            },
        ],
    }

    submissions = [
        {
            "id": 1,
            "version": 1,
            "data": {
                "fundingReceived": True,
                "contractSigned": False,
                "dealType": "Acquisition",
            },
            "submitted_by": "user1",
            "created_at": "2026-11-07T12:00:00Z",
        },
        {
            "id": 2,
            "version": 1,
            "data": {
                "fundingReceived": True,
                "contractSigned": True,
                "dealType": "Renewal",
            },
            "submitted_by": "user2",
            "created_at": "2026-11-07T12:05:00Z",
        },
        {
            "id": 3,
            "version": 1,
            "data": {
                "fundingReceived": False,
                "contractSigned": False,
                "dealType": "Acquisition",
            },
            "submitted_by": "user3",
            "created_at": "2026-11-07T12:10:00Z",
        },
    ]

    report = generate_dynamic_report(
        workflow_key="deal_opportunities",
        active_schema=active_schema,
        active_version=1,
        submissions=submissions,
    )

    assert report.total_submissions == 3
    assert len(report.columns) == 3
    assert report.columns[0].key == "fundingReceived"

    # Verify yesNo metric
    funding_metric = report.metrics["fundingReceived"]
    assert funding_metric["yes_count"] == 2
    assert funding_metric["no_count"] == 1
    assert funding_metric["completion_rate"] == 66.7

    # Verify dropdown distribution
    type_metric = report.metrics["dealType"]
    assert type_metric["distribution"]["Acquisition"] == 2
    assert type_metric["distribution"]["Renewal"] == 1

    # Verify recent submissions alignment
    assert len(report.recent_submissions) == 3
    assert report.recent_submissions[0]["values"]["fundingReceived"] is True


def test_generate_dynamic_report_omits_deprecated_fields():
    """
    If an older submission contains a removed field,
    the report reflects only the currently active schema columns.
    """
    active_schema = {
        "title": "Deal intake",
        "fields": [
            {"key": "dealName", "label": "Deal name", "type": "text"},
        ],
    }

    submissions = [
        {
            "id": 1,
            "version": 1,
            "data": {
                "dealName": "Northwind",
                "oldDeprecatedField": "legacy value",
            },
        }
    ]

    report = generate_dynamic_report(
        workflow_key="deal_intake",
        active_schema=active_schema,
        active_version=2,
        submissions=submissions,
    )

    assert len(report.columns) == 1
    assert report.columns[0].key == "dealName"
    assert "oldDeprecatedField" not in report.columns[0].key
    assert "oldDeprecatedField" not in report.metrics
    assert "oldDeprecatedField" not in report.recent_submissions[0]["values"]

