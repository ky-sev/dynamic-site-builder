import { TestBed } from '@angular/core/testing';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render the workflow version heading', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Deal intake');
  });

  it('should render one matching input for each example schema field', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelectorAll('.form-fields .form-field')).toHaveLength(4);
    expect(compiled.querySelector('#dealName')).toBeInstanceOf(HTMLInputElement);
    expect(compiled.querySelector('#dealType')).toBeInstanceOf(HTMLSelectElement);
    expect(compiled.querySelector('#requiresLegalReview')).toBeInstanceOf(HTMLInputElement);
    expect(compiled.querySelector('#notes')).toBeInstanceOf(HTMLTextAreaElement);
  });

  it('should rebuild the form when the workflow JSON changes', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const editor = compiled.querySelector<HTMLTextAreaElement>('#schema-data')!;
    editor.value = JSON.stringify({
      title: 'Vendor review',
      description: 'Review a new vendor.',
      fields: [
        { key: 'vendorName', label: 'Vendor name', type: 'text' },
        { key: 'riskScore', label: 'Risk score', type: 'number' },
        {
          key: 'region',
          label: 'Region',
          type: 'dropdown',
          options: ['North', 'South'],
        },
      ],
    });
    editor.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    expect(compiled.querySelector('h1')?.textContent).toContain('Vendor review');
    expect(compiled.querySelectorAll('.form-fields .form-field')).toHaveLength(3);
    expect(compiled.querySelector('#vendorName')).toBeInstanceOf(HTMLInputElement);
    expect(compiled.querySelector<HTMLInputElement>('#riskScore')?.type).toBe('number');
    expect(compiled.querySelector('#region')).toBeInstanceOf(HTMLSelectElement);
  });

  it('should preview entered form values as JSON', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    const dealName = compiled.querySelector<HTMLInputElement>('#dealName')!;
    dealName.value = 'Northwind';
    dealName.dispatchEvent(new Event('input'));

    const dealType = compiled.querySelector<HTMLSelectElement>('#dealType')!;
    dealType.value = 'Partnership';
    dealType.dispatchEvent(new Event('change'));

    const legalReview = compiled.querySelector<HTMLInputElement>('#requiresLegalReview')!;
    legalReview.checked = true;
    legalReview.dispatchEvent(new Event('change'));

    const notes = compiled.querySelector<HTMLTextAreaElement>('#notes')!;
    notes.value = 'Review the draft terms.';
    notes.dispatchEvent(new Event('input'));

    compiled
      .querySelector<HTMLFormElement>('.workflow-form')!
      .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    fixture.detectChanges();

    const output = JSON.parse(compiled.querySelector('.output pre')!.textContent!) as Record<string, unknown>;
    expect(output).toEqual({
      dealName: 'Northwind',
      dealType: 'Partnership',
      requiresLegalReview: true,
      notes: 'Review the draft terms.',
    });
  });
});
