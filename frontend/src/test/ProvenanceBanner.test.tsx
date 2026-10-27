import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProvenanceBanner } from '../components/common/ProvenanceBanner';

vi.mock('../api', () => ({
  getModelsStatus: vi.fn(),
}));

describe('ProvenanceBanner component', () => {
  it('renders synthetic demo mode banner when demo_mode is active', () => {
    render(
      <ProvenanceBanner
        provenance={{
          overall_status: 'demo_synthetic',
          is_demo_mode: true,
          ui_badge: 'DEMO DATA MODE (SYNTHETIC)',
          banner_message: 'Synthetic template data detected.',
        }}
      />
    );

    expect(screen.getByText(/DEMO MODE ACTIVE:/i)).toBeInTheDocument();
    expect(screen.getByText(/Synthetic Provenance/i)).toBeInTheDocument();
  });

  it('renders authentic mode badge when provenance is verified', () => {
    render(
      <ProvenanceBanner
        provenance={{
          overall_status: 'verified_authentic',
          is_demo_mode: false,
          ui_badge: 'REAL DATA MODE (VERIFIED AUTHENTIC)',
          banner_message: 'Cryptographically verified dataset.',
        }}
      />
    );

    expect(screen.getByText(/AUTHENTIC MODE:/i)).toBeInTheDocument();
    expect(screen.getByText(/Verified Authentic/i)).toBeInTheDocument();
  });
});
