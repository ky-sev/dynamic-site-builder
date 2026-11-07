import { CommonModule } from '@angular/common';
import { afterNextRender, Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

interface ActiveWorkflow {
  schema_data: Record<string, unknown>;
  version: number;
}

type WorkflowFieldType = 'text' | 'yesNo' | 'dropdown' | 'textarea' | 'number' | 'date';

interface WorkflowField {
  key: string;
  label: string;
  type: WorkflowFieldType;
  required?: boolean;
  placeholder?: string;
  options?: string[];
}

interface WorkflowVersion {
  version: number;
  is_active: boolean;
  updated_by: string;
  commit_message: string | null;
  created_at: string;
}

interface ApiErrorBody {
  error?: string;
}

export interface DomainNavigationItem {
  key: string;
  title: string;
  description?: string;
  icon?: string;
  nav_order: number;
  route: string;
  workflow_key: string;
  is_active: boolean;
}

export interface DynamicReportColumn {
  key: string;
  label: string;
  type: string;
}

export interface DynamicReportData {
  workflow_key: string;
  workflow_title: string;
  active_version: number;
  total_submissions: number;
  columns: DynamicReportColumn[];
  metrics: Record<string, any>;
  recent_submissions: Array<{
    id: number;
    submitted_at: string;
    submitted_by: string;
    version: number;
    values: Record<string, any>;
  }>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isWorkflowFieldType(type: string): type is WorkflowFieldType {
  return ['text', 'yesNo', 'dropdown', 'textarea', 'number', 'date'].includes(type);
}

const EXAMPLE_SCHEMA: {
  title: string;
  description: string;
  fields: WorkflowField[];
} = {
  title: 'Deal intake',
  description: 'Capture the essential details for a new deal.',
  fields: [
    { key: 'dealName', label: 'Deal name', type: 'text', required: true },
    {
      key: 'dealType',
      label: 'Deal type',
      type: 'dropdown',
      options: ['Acquisition', 'Partnership', 'Renewal'],
      required: true,
    },
    {
      key: 'requiresLegalReview',
      label: 'Does this deal require legal review?',
      type: 'yesNo',
    },
    {
      key: 'notes',
      label: 'Additional notes',
      type: 'textarea',
      placeholder: 'Add any context the team should know…',
    },
  ],
};

@Component({
  selector: 'app-root',
  imports: [CommonModule, FormsModule],
  templateUrl: './workflow-admin.html',
  styleUrl: './workflow-admin.css',
})
export class App {
  protected workflowKey = 'deal_flow';
  protected updatedBy = '';
  protected commitMessage = '';
  protected schemaText = JSON.stringify(EXAMPLE_SCHEMA, null, 2);
  protected adminToken = '';
  protected readonly schemaTitle = signal(EXAMPLE_SCHEMA.title);
  protected readonly schemaDescription = signal(EXAMPLE_SCHEMA.description);
  protected readonly formFields = signal<WorkflowField[]>(EXAMPLE_SCHEMA.fields);
  protected readonly formValues: Record<string, string | boolean> = {
    dealName: '',
    dealType: '',
    requiresLegalReview: false,
    notes: '',
  };
  protected readonly formOutput = signal('');
  protected readonly schemaError = signal('');
  protected readonly active = signal<ActiveWorkflow | null>(null);
  protected readonly versions = signal<WorkflowVersion[]>([]);
  protected readonly navigationDomains = signal<DomainNavigationItem[]>([]);
  protected readonly selectedDomainKey = signal<string>('deal_flow');
  protected readonly reportData = signal<DynamicReportData | null>(null);
  protected readonly loading = signal(false);
  protected readonly saving = signal(false);
  protected readonly message = signal('');
  protected readonly messageIsError = signal(false);

  constructor() {
    afterNextRender(() => {
      void this.initApp();
    });
  }

  protected async initApp(): Promise<void> {
    await this.loadNavigationDomains();
    await this.loadWorkflow();
  }

  protected async loadNavigationDomains(): Promise<void> {
    try {
      const items = await this.request<DomainNavigationItem[]>('/api/domains/navigation');
      this.navigationDomains.set(items);
      if (items.length > 0 && !items.some(d => d.workflow_key === this.workflowKey)) {
        this.selectDomain(items[0]);
      }
    } catch {
      // Fallback silently if navigation fails or running standalone
    }
  }

  protected selectDomain(domain: DomainNavigationItem): void {
    this.selectedDomainKey.set(domain.key);
    this.workflowKey = domain.workflow_key;
    void this.loadWorkflow();
  }

  protected async loadWorkflow(): Promise<void> {
    const key = this.normalizedWorkflowKey();
    if (!key) {
      this.showMessage(
        'Enter a valid workflow key (letters, numbers, underscores, or hyphens; 1-50 characters).',
        true,
      );
      return;
    }

    this.loading.set(true);
    this.message.set('');
    this.active.set(null);
    this.versions.set([]);

    const [activeResult, versionsResult] = await Promise.allSettled([
      this.request<ActiveWorkflow>(`/api/workflow/${encodeURIComponent(key)}`),
      this.adminToken.trim()
        ? this.request<WorkflowVersion[]>(
            `/api/workflow/${encodeURIComponent(key)}/versions`,
            { headers: this.adminHeaders() },
          )
        : Promise.resolve([]),
    ]);

    if (activeResult.status === 'fulfilled') {
      this.active.set(activeResult.value);
      this.schemaText = JSON.stringify(activeResult.value.schema_data, null, 2);
      this.updateFormPreview();
    } else if (!(activeResult.reason instanceof ApiRequestError && activeResult.reason.status === 404)) {
      this.showMessage(this.errorMessage(activeResult.reason), true);
    }

    if (versionsResult.status === 'fulfilled') {
      this.versions.set(versionsResult.value);
    } else if (this.active()) {
      // If no admin token or no version history yet, represent the active/fixture version in the history list
      const activeVer = this.active()!;
      this.versions.set([
        {
          version: activeVer.version,
          is_active: true,
          updated_by: 'system',
          commit_message: 'Initial stage baseline',
          created_at: new Date().toISOString(),
        },
      ]);
    } else {
      this.showMessage(this.errorMessage(versionsResult.reason), true);
    }

    // Also fetch dynamic reporting for this workflow
    void this.loadReportData(key);

    this.loading.set(false);
  }

  protected async loadReportData(key: string): Promise<void> {
    try {
      const data = await this.request<DynamicReportData>(`/api/reporting/${encodeURIComponent(key)}`);
      this.reportData.set(data);
    } catch {
      this.reportData.set(null);
    }
  }

  protected async deployVersion(): Promise<void> {
    const key = this.normalizedWorkflowKey();
    if (!key) {
      this.showMessage(
        'Enter a valid workflow key (letters, numbers, underscores, or hyphens; 1-50 characters).',
        true,
      );
      return;
    }

    let schemaData: unknown;
    try {
      schemaData = JSON.parse(this.schemaText);
    } catch {
      this.showMessage('Workflow schema must be valid JSON.', true);
      return;
    }

    try {
      this.parseWorkflowFields(schemaData);
    } catch (error) {
      this.showMessage(this.errorMessage(error), true);
      return;
    }

    this.saving.set(true);
    try {
      const result = await this.request<{ deployedVersion: number }>(
        `/api/workflow/${encodeURIComponent(key)}/version`,
        {
          method: 'POST',
          headers: this.adminHeaders(),
          body: JSON.stringify({
            schema_data: schemaData,
            updated_by: this.updatedBy,
            commit_message: this.commitMessage,
          }),
        },
      );
      this.commitMessage = '';
      
      // Instantly update active version signal in UI
      if (isRecord(schemaData)) {
        this.active.set({
          schema_data: schemaData,
          version: result.deployedVersion,
        });
      }

      await this.loadWorkflow();
      this.showMessage(`Deployed version ${result.deployedVersion}.`);
    } catch (error) {
      this.showMessage(this.errorMessage(error), true);
    } finally {
      this.saving.set(false);
    }
  }

  protected updateFormPreview(): void {
    try {
      const schema: unknown = JSON.parse(this.schemaText);
      if (!isRecord(schema)) {
        throw new Error('Workflow schema must be a JSON object.');
      }
      const fields = this.parseWorkflowFields(schema);
      this.schemaTitle.set(
        typeof schema['title'] === 'string' && schema['title'].trim()
          ? schema['title']
          : 'Workflow form',
      );
      this.schemaDescription.set(
        typeof schema['description'] === 'string' ? schema['description'] : '',
      );
      for (const field of fields) {
        this.formValues[field.key] ??= field.type === 'yesNo' ? false : '';
      }
      this.formFields.set(fields);
      this.formOutput.set('');
      this.schemaError.set('');
    } catch (error) {
      this.formFields.set([]);
      this.schemaError.set(this.errorMessage(error));
    }
  }

  protected showPreviewOutput(): void {
    const values: Record<string, string | boolean> = {};
    for (const field of this.formFields()) {
      values[field.key] = this.formValues[field.key] ?? '';
    }
    this.formOutput.set(JSON.stringify(values, null, 2));
  }

  private parseWorkflowFields(value: unknown): WorkflowField[] {
    if (!isRecord(value)) {
      throw new Error('Workflow schema must be a JSON object.');
    }

    const schemaFields = value['fields'];
    if (!Array.isArray(schemaFields)) {
      throw new Error('Workflow schema must include a fields array.');
    }
    if (schemaFields.length > 100) {
      throw new Error('Workflow schema cannot contain more than 100 fields.');
    }

    const keys = new Set<string>();

    return schemaFields.map((candidate: unknown, index: number) => {
      if (!isRecord(candidate)) {
        throw new Error(`Field ${index + 1} must be an object.`);
      }

      const field = candidate;
      const key = field['key'];
      if (typeof key !== 'string' || !/^[A-Za-z][A-Za-z0-9_]*$/.test(key)) {
        throw new Error(`Field ${index + 1} needs a valid key.`);
      }
      if (keys.has(key)) {
        throw new Error(`Field key "${key}" is duplicated.`);
      }
      keys.add(key);

      const label = field['label'];
      if (typeof label !== 'string' || label.trim() === '') {
        throw new Error(`Field "${key}" needs a label.`);
      }
      const type = field['type'];
      if (typeof type !== 'string' || !isWorkflowFieldType(type)) {
        throw new Error(
          `Field "${key}" has an unsupported type. Use text, yesNo, dropdown, textarea, number, or date.`,
        );
      }
      const placeholder = field['placeholder'];
      if (
        placeholder !== undefined &&
        typeof placeholder !== 'string'
      ) {
        throw new Error(`Field "${key}" has an invalid placeholder.`);
      }
      const required = field['required'];
      if (
        required !== undefined &&
        typeof required !== 'boolean'
      ) {
        throw new Error(`Field "${key}" has an invalid required setting.`);
      }
      const options = field['options'];
      if (type === 'dropdown') {
        if (
          !Array.isArray(options) ||
          options.length === 0 ||
          !options.every(
            (option: unknown) =>
              typeof option === 'string' && option.trim() !== '',
          )
        ) {
          throw new Error(`Dropdown field "${key}" needs one or more string options.`);
        }
      }

      const normalizedOptions =
        type === 'dropdown' && Array.isArray(options)
          ? options.filter((option): option is string => typeof option === 'string')
          : undefined;

      return {
        key,
        label,
        type,
        required: typeof required === 'boolean' ? required : undefined,
        placeholder: typeof placeholder === 'string' ? placeholder : undefined,
        options: normalizedOptions,
      };
    });
  }

  protected async rollback(version: number): Promise<void> {
    if (!window.confirm(`Activate workflow version ${version}?`)) {
      return;
    }

    const key = this.normalizedWorkflowKey();
    if (!key) {
      this.showMessage(
        'Enter a valid workflow key (letters, numbers, underscores, or hyphens; 1-50 characters).',
        true,
      );
      return;
    }

    this.saving.set(true);
    try {
      const result = await this.request<{ revertedTo: number }>(
        `/api/workflow/${encodeURIComponent(key)}/rollback/${version}`,
        { method: 'PUT', headers: this.adminHeaders() },
      );
      await this.loadWorkflow();
      this.showMessage(`Workflow rolled back to version ${result.revertedTo}.`);
    } catch (error) {
      this.showMessage(this.errorMessage(error), true);
    } finally {
      this.saving.set(false);
    }
  }

  private adminHeaders(): HeadersInit {
    return {
      Authorization: `Bearer ${this.adminToken}`,
      'Content-Type': 'application/json',
    };
  }

  private normalizedWorkflowKey(): string | null {
    const key = this.workflowKey.trim();
    return /^[a-zA-Z0-9][a-zA-Z0-9_-]{0,49}$/.test(key) ? key : null;
  }

  private async request<T>(url: string, options?: RequestInit): Promise<T> {
    const response = await fetch(url, options);
    const body = (await response.json()) as T & ApiErrorBody;
    if (!response.ok) {
      throw new ApiRequestError(
        response.status,
        body.error ?? `Request failed (${response.status}).`,
      );
    }
    return body;
  }

  private errorMessage(error: unknown): string {
    return error instanceof Error ? error.message : 'An unexpected error occurred.';
  }

  private showMessage(message: string, isError = false): void {
    this.message.set(message);
    this.messageIsError.set(isError);
  }
}

class ApiRequestError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}
