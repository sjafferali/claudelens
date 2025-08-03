import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import SearchBar from '../SearchBar';

describe('SearchBar', () => {
  it('renders with placeholder', () => {
    const onChange = vi.fn();
    render(
      <SearchBar value="" onChange={onChange} placeholder="Search test..." />
    );

    const input = screen.getByPlaceholderText('Search test...');
    expect(input).toBeInTheDocument();
  });

  it('calls onChange with debounced value', async () => {
    const onChange = vi.fn();
    render(<SearchBar value="" onChange={onChange} debounceMs={100} />);

    const input = screen.getByPlaceholderText('Search...');
    fireEvent.change(input, { target: { value: 'test query' } });

    // Should not call immediately
    expect(onChange).not.toHaveBeenCalled();

    // Should call after debounce
    await waitFor(
      () => {
        expect(onChange).toHaveBeenCalledWith('test query');
      },
      { timeout: 200 }
    );
  });

  it('shows clear button when has value', () => {
    const onChange = vi.fn();
    render(<SearchBar value="test" onChange={onChange} />);

    const clearButton = screen.getByLabelText('Clear search');
    expect(clearButton).toBeInTheDocument();
  });

  it('clears value when clear button clicked', () => {
    const onChange = vi.fn();
    render(<SearchBar value="test" onChange={onChange} />);

    const clearButton = screen.getByLabelText('Clear search');
    fireEvent.click(clearButton);

    expect(onChange).toHaveBeenCalledWith('');
  });

  it('clears value on Escape key', () => {
    const onChange = vi.fn();
    render(<SearchBar value="test" onChange={onChange} />);

    const input = screen.getByPlaceholderText('Search...');
    fireEvent.keyDown(input, { key: 'Escape' });

    expect(onChange).toHaveBeenCalledWith('');
  });
});
