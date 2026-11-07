from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


FieldKey = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_]*$", max_length=100)
]
FieldKind = Literal["text", "yesNo", "dropdown", "textarea", "number", "date"]


# Validates one workflow input field and its type-specific options.
class WorkflowField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: FieldKey
    label: Annotated[str, Field(min_length=1, max_length=200)]
    type: FieldKind
    required: bool = False
    placeholder: str | None = None
    options: list[Annotated[str, Field(min_length=1, max_length=200)]] | None = None

    # Ensures options are present only for dropdown fields.
    @model_validator(mode="after")
    def validate_options(self) -> "WorkflowField":
        if self.type == "dropdown" and not self.options:
            raise ValueError("Dropdown fields require at least one option.")
        if self.type != "dropdown" and self.options is not None:
            raise ValueError("Only dropdown fields may define options.")
        return self


# Validates a complete workflow layout and ensures field keys are unique.
class WorkflowSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: Annotated[str, Field(max_length=200)] | None = None
    description: Annotated[str, Field(max_length=1000)] | None = None
    fields: Annotated[list[WorkflowField], Field(max_length=100)]

    # Ensures every field in the workflow has a unique key.
    @field_validator("fields")
    @classmethod
    def field_keys_must_be_unique(
        cls, fields: list[WorkflowField]
    ) -> list[WorkflowField]:
        keys = [field.key for field in fields]
        if len(keys) != len(set(keys)):
            raise ValueError("Field keys must be unique.")
        return fields


# Validates the payload used to create and deploy a workflow version.
class CreateWorkflowVersionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_data: WorkflowSchema
    updated_by: Annotated[str, Field(min_length=1, max_length=100)]
    commit_message: Annotated[str, Field(max_length=2000)] | None = None

    # Trims and rejects blank updater identifiers.
    @field_validator("updated_by")
    @classmethod
    def updated_by_cannot_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("updated_by cannot be blank.")
        return value


# Represents the active workflow schema returned to the frontend.
class ActiveWorkflowResponse(BaseModel):
    schema_data: dict[str, object]
    version: int


# Represents one workflow version in deployment history.
class WorkflowVersionResponse(BaseModel):
    version: int
    is_active: bool
    updated_by: str
    commit_message: str | None
    created_at: str


# Represents the result of successfully deploying a workflow version.
class DeployWorkflowResponse(BaseModel):
    success: Literal[True] = True
    deployedVersion: int


# Represents the result of successfully rolling back a workflow.
class RollbackWorkflowResponse(BaseModel):
    success: Literal[True] = True
    revertedTo: int
