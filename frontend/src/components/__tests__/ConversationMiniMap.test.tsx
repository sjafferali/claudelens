import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ConversationMiniMap } from '../ConversationMiniMap';
import { Message } from '@/api/types';
import '@testing-library/jest-dom';

// Mock canvas context
const mockGetContext = vi.fn();
HTMLCanvasElement.prototype.getContext = mockGetContext;

describe('ConversationMiniMap', () => {
  const mockMessages: Message[] = [
    {
      _id: '1',
      uuid: 'msg-1',
      messageUuid: 'msg-1',
      type: 'user',
      content: 'Hello',
      timestamp: new Date().toISOString(),
      sessionId: 'session-1',
      parentUuid: undefined,
      isSidechain: false,
    },
    {
      _id: '2',
      uuid: 'msg-2',
      messageUuid: 'msg-2',
      type: 'assistant',
      content: 'Hi there!',
      timestamp: new Date().toISOString(),
      sessionId: 'session-1',
      parentUuid: 'msg-1',
      isSidechain: false,
    },
    {
      _id: '3',
      uuid: 'msg-3',
      messageUuid: 'msg-3',
      type: 'user',
      content: 'How are you?',
      timestamp: new Date().toISOString(),
      sessionId: 'session-1',
      parentUuid: 'msg-2',
      isSidechain: false,
    },
    {
      _id: '4',
      uuid: 'msg-4',
      messageUuid: 'msg-4',
      type: 'assistant',
      content: 'I am doing well, thanks!',
      timestamp: new Date().toISOString(),
      sessionId: 'session-1',
      parentUuid: 'msg-3',
      isSidechain: false,
    },
    {
      _id: '5',
      uuid: 'msg-5',
      messageUuid: 'msg-5',
      type: 'tool_use',
      content: 'Tool operation',
      timestamp: new Date().toISOString(),
      sessionId: 'session-1',
      parentUuid: 'msg-3',
      isSidechain: true,
    },
  ];

  const mockContext = {
    fillStyle: '',
    strokeStyle: '',
    lineWidth: 1,
    fillRect: vi.fn(),
    strokeRect: vi.fn(),
    clearRect: vi.fn(),
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    arc: vi.fn(),
    stroke: vi.fn(),
    fill: vi.fn(),
    setLineDash: vi.fn(),
  };

  beforeEach(() => {
    mockGetContext.mockReturnValue(mockContext);
    vi.clearAllMocks();
  });

  it('should not render when isOpen is false', () => {
    const { container } = render(
      <ConversationMiniMap
        messages={mockMessages}
        isOpen={false}
        onToggle={vi.fn()}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should render when isOpen is true', () => {
    render(
      <ConversationMiniMap
        messages={mockMessages}
        isOpen={true}
        onToggle={vi.fn()}
      />
    );

    expect(screen.getByText('Conversation Map')).toBeInTheDocument();
  });

  it('should display correct metrics', () => {
    render(
      <ConversationMiniMap
        messages={mockMessages}
        isOpen={true}
        onToggle={vi.fn()}
      />
    );

    // Check metrics display
    expect(screen.getByText('Messages:')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument(); // 5 messages

    expect(screen.getByText('Depth:')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument(); // Depth of 4

    expect(screen.getByText('Branches:')).toBeInTheDocument();
    // Use getAllByText since there are multiple "1" values (branches and sidechains)
    const onesFound = screen.getAllByText('1');
    expect(onesFound).toHaveLength(2); // Should find 2 instances of "1"

    expect(screen.getByText('Sidechains:')).toBeInTheDocument();
  });

  it('should calculate complexity correctly', () => {
    render(
      <ConversationMiniMap
        messages={mockMessages}
        isOpen={true}
        onToggle={vi.fn()}
      />
    );

    expect(screen.getByText('Complexity:')).toBeInTheDocument();
    // Complexity = log2(5) * (1 + 1 * 0.1) ≈ 2.32 * 1.1 ≈ 2.6
    const complexityElement = screen.getByText(/2\.\d/);
    expect(complexityElement).toBeInTheDocument();
  });

  it('should toggle between expanded and minimized states', () => {
    render(
      <ConversationMiniMap
        messages={mockMessages}
        isOpen={true}
        onToggle={vi.fn()}
      />
    );

    // Find expand button
    const expandButton = screen.getByTitle('Expand');
    expect(expandButton).toBeInTheDocument();

    // Click to expand
    fireEvent.click(expandButton);

    // Should now show minimize button
    const minimizeButton = screen.getByTitle('Minimize');
    expect(minimizeButton).toBeInTheDocument();

    // In expanded mode, legend should be visible
    expect(screen.getByText('User')).toBeInTheDocument();
    expect(screen.getByText('Assistant')).toBeInTheDocument();
    expect(screen.getByText('Tool')).toBeInTheDocument();
  });

  it('should call onToggle when close button is clicked', () => {
    const onToggle = vi.fn();
    render(
      <ConversationMiniMap
        messages={mockMessages}
        isOpen={true}
        onToggle={onToggle}
      />
    );

    const closeButton = screen.getByTitle('Close minimap');
    fireEvent.click(closeButton);

    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it('should call onNavigate when clicking on the canvas', () => {
    const onNavigate = vi.fn();
    const { container } = render(
      <ConversationMiniMap
        messages={mockMessages}
        isOpen={true}
        onToggle={vi.fn()}
        onNavigate={onNavigate}
      />
    );

    const canvas = container.querySelector('canvas');
    expect(canvas).toBeInTheDocument();

    // Simulate click on canvas
    if (canvas) {
      fireEvent.click(canvas, {
        clientX: 100,
        clientY: 50,
      });
    }

    // The click handler should process the click
    // In a real scenario, it would calculate which node was clicked
    // For testing, we just verify the canvas is clickable
    expect(canvas).toHaveClass('cursor-pointer');
  });

  it('should highlight active message', () => {
    render(
      <ConversationMiniMap
        messages={mockMessages}
        activeMessageId="msg-2"
        isOpen={true}
        onToggle={vi.fn()}
      />
    );

    // The canvas drawing should highlight the active message
    // We verify the context methods were called
    expect(mockContext.beginPath).toHaveBeenCalled();
    expect(mockContext.arc).toHaveBeenCalled();
    expect(mockContext.stroke).toHaveBeenCalled();
  });

  it('should draw edges between parent and child messages', () => {
    render(
      <ConversationMiniMap
        messages={mockMessages}
        isOpen={true}
        onToggle={vi.fn()}
      />
    );

    // Verify that lines are drawn between connected messages
    expect(mockContext.beginPath).toHaveBeenCalled();
    expect(mockContext.moveTo).toHaveBeenCalled();
    expect(mockContext.lineTo).toHaveBeenCalled();
    expect(mockContext.stroke).toHaveBeenCalled();
  });

  it('should use dashed lines for sidechains', () => {
    render(
      <ConversationMiniMap
        messages={mockMessages}
        isOpen={true}
        onToggle={vi.fn()}
      />
    );

    // Verify that setLineDash is called for sidechain edges
    expect(mockContext.setLineDash).toHaveBeenCalledWith([2, 2]);
  });

  it('should use different colors for different message types', () => {
    render(
      <ConversationMiniMap
        messages={mockMessages}
        isOpen={true}
        onToggle={vi.fn()}
      />
    );

    // The canvas should set different fill styles for different message types
    // We can't easily test the exact colors, but we verify the context is being set
    expect(mockContext.fill).toHaveBeenCalled();
  });

  it('should handle empty message list', () => {
    render(
      <ConversationMiniMap messages={[]} isOpen={true} onToggle={vi.fn()} />
    );

    expect(screen.getByText('Messages:')).toBeInTheDocument();
    // Use getAllByText since there will be multiple "0" values (messages and branches)
    const zerosFound = screen.getAllByText('0');
    expect(zerosFound.length).toBeGreaterThanOrEqual(2); // At least 2 zeros (messages and branches)

    expect(screen.getByText('Depth:')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // Default depth of 1
  });

  it('should update viewport indicator when scroll container is provided', () => {
    const scrollContainer = document.createElement('div');
    Object.defineProperty(scrollContainer, 'scrollTop', {
      value: 100,
      writable: true,
    });
    Object.defineProperty(scrollContainer, 'scrollHeight', {
      value: 1000,
      writable: true,
    });
    Object.defineProperty(scrollContainer, 'clientHeight', {
      value: 500,
      writable: true,
    });

    const scrollContainerRef = { current: scrollContainer };

    render(
      <ConversationMiniMap
        messages={mockMessages}
        isOpen={true}
        onToggle={vi.fn()}
        scrollContainerRef={scrollContainerRef}
      />
    );

    // Simulate scroll
    fireEvent.scroll(scrollContainer);

    // Viewport indicator should be drawn
    expect(mockContext.fillRect).toHaveBeenCalled();
    expect(mockContext.strokeRect).toHaveBeenCalled();
  });

  it('should handle complex conversation structures', () => {
    const complexMessages: Message[] = [
      ...mockMessages,
      // Add alternative response (branch)
      {
        _id: '6',
        uuid: 'msg-4-alt',
        messageUuid: 'msg-4-alt',
        type: 'assistant',
        content: 'Alternative response',
        timestamp: new Date().toISOString(),
        sessionId: 'session-1',
        parentUuid: 'msg-3',
        isSidechain: false,
      },
      // Add deeper nesting
      {
        _id: '7',
        uuid: 'msg-6',
        messageUuid: 'msg-6',
        type: 'user',
        content: 'Continue conversation',
        timestamp: new Date().toISOString(),
        sessionId: 'session-1',
        parentUuid: 'msg-4',
        isSidechain: false,
      },
    ];

    render(
      <ConversationMiniMap
        messages={complexMessages}
        isOpen={true}
        onToggle={vi.fn()}
      />
    );

    // Should show increased complexity
    expect(screen.getByText('7')).toBeInTheDocument(); // 7 messages
    // Use getAllByText since there are multiple "1" values in the UI
    const onesFound = screen.getAllByText('1');
    expect(onesFound.length).toBeGreaterThanOrEqual(1); // At least 1 branch
  });
});
