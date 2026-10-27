import React from 'react';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '../context/ThemeContext';
import { ThemeToggle } from '../components/layout/ThemeToggle';

describe('Theme System & ThemeToggle component', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  afterEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('renders with an accessible button and default system/light theme', () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    const button = screen.getByRole('button', { name: /Select color theme/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-haspopup', 'true');
    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('toggles dropdown menu on click with accessible choices: Light, Dark, System', () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    const button = screen.getByRole('button', { name: /Select color theme/i });
    fireEvent.click(button);

    expect(button).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('menuitem', { name: /Light/i })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: /Dark/i })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: /System/i })).toBeInTheDocument();
  });

  it('switches to Dark theme, updates root class and persists in localStorage', async () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    const button = screen.getByRole('button', { name: /Select color theme/i });
    fireEvent.click(button);

    const darkOption = screen.getByRole('menuitem', { name: /Dark/i });
    fireEvent.click(darkOption);

    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(true);
      expect(localStorage.getItem('smarthire-theme')).toBe('dark');
    });
  });

  it('switches to Light theme and removes dark class from root', async () => {
    // Pre-seed dark mode
    document.documentElement.classList.add('dark');
    localStorage.setItem('smarthire-theme', 'dark');

    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    const button = screen.getByRole('button', { name: /Select color theme/i });
    fireEvent.click(button);

    const lightOption = screen.getByRole('menuitem', { name: /Light/i });
    fireEvent.click(lightOption);

    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(false);
      expect(localStorage.getItem('smarthire-theme')).toBe('light');
    });
  });
});
