import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SkillPill } from '../components/common/SkillPill';

describe('SkillPill component', () => {
  it('renders skill name accurately', () => {
    render(<SkillPill name="Python" />);
    expect(screen.getByText('Python')).toBeInTheDocument();
  });

  it('renders matched status with appropriate styling', () => {
    const { container } = render(<SkillPill name="Machine Learning" variant="matched" />);
    expect(screen.getByText('Machine Learning')).toBeInTheDocument();
    expect(container.firstChild).toHaveClass('bg-emerald-50');
  });

  it('renders missing status with appropriate styling', () => {
    const { container } = render(<SkillPill name="Kubernetes" variant="missing" />);
    expect(screen.getByText('Kubernetes')).toBeInTheDocument();
    expect(container.firstChild).toHaveClass('bg-rose-50');
  });
});
