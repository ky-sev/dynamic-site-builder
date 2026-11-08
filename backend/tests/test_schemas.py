import unittest

from pydantic import ValidationError

from schemas import CreateWorkflowVersionRequest, WorkflowSchema


EXAMPLE_SCHEMA = {
    "title": "Deal intake",
    "description": "Capture the essential details for a new deal.",
    "fields": [
        {
            "key": "dealName",
            "label": "Deal name",
            "type": "text",
            "required": True,
        },
        {
            "key": "dealType",
            "label": "Deal type",
            "type": "dropdown",
            "options": ["Acquisition", "Partnership", "Renewal"],
            "required": True,
        },
        {
            "key": "requiresLegalReview",
            "label": "Does this deal require legal review?",
            "type": "yesNo",
        },
        {
            "key": "notes",
            "label": "Additional notes",
            "type": "textarea",
            "placeholder": "Add any context the team should know...",
        },
    ],
}


# Validates workflow schema parsing, field constraints, and duplication rules.
class WorkflowSchemaTests(unittest.TestCase):
    def test_example_schema_is_valid_and_keeps_field_types(self) -> None:
        schema = WorkflowSchema.model_validate(EXAMPLE_SCHEMA)

        self.assertEqual(len(schema.fields), 4)
        self.assertEqual(
            [field.type for field in schema.fields],
            ["text", "dropdown", "yesNo", "textarea"],
        )
        self.assertEqual(schema.model_dump(mode="json")["title"], "Deal intake")

    def test_duplicate_field_keys_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            WorkflowSchema.model_validate(
                {
                    "fields": [
                        {"key": "dealName", "label": "Deal name", "type": "text"},
                        {"key": "dealName", "label": "Other name", "type": "text"},
                    ]
                }
            )

    def test_unknown_field_type_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            WorkflowSchema.model_validate(
                {
                    "fields": [
                        {"key": "unknown", "label": "Unknown", "type": "file"}
                    ]
                }
            )

    def test_dropdown_requires_options(self) -> None:
        with self.assertRaises(ValidationError):
            WorkflowSchema.model_validate(
                {
                    "fields": [
                        {"key": "dealType", "label": "Deal type", "type": "dropdown"}
                    ]
                }
            )

    def test_request_validates_schema_and_audit_fields(self) -> None:
        request = CreateWorkflowVersionRequest.model_validate(
            {
                "schema_data": EXAMPLE_SCHEMA,
                "updated_by": "  admin@example.com  ",
                "commit_message": "Initial workflow",
            }
        )

        self.assertEqual(request.updated_by, "admin@example.com")
