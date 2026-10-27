import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HeuristicBadge } from '../components/common/HeuristicBadge';

describe('HeuristicBadge component', () => {
  it('renders score and explicit Compatibility Index label', () => {
    render(<HeuristicBadge score={78.4} />);

    expect(screen.getByText('78%')).toBeInTheDocument();
    expect(screen.getByText('Compatibility Index')).toBeInTheDocument();
  });

  it('renders scientific non-probability explanation when requested', () => {
    render(<HeuristicBadge score={85} showExplanation={true} />);

    expect(
      screen.getByText(/Deterministic heuristic index: 50% Text Similarity/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Not a calibrated hiring probability/i)
    ).toBeInTheDocument();
  });

  it('clamps scores to 0-100 range', () => {
    const { rerender } = render(<HeuristicBadge score={120} />);
    expect(screen.getByText('100%')).toBeInTheDocument();

    rerender(<HeuristicBadge score={-15} />);
    expect(screen.getByText('0%')).toBeInTheDocument();
  });
});
